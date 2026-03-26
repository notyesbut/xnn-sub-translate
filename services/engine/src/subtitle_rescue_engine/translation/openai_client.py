from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request

from subtitle_rescue_engine.contracts import TranslationBatch, TranslationPass

from .errors import TranslationError, TranslationSchemaError, TranslationTransientError

_RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}


class OpenAIResponsesTranslationClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        organization: str | None = None,
        project: str | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required to use OpenAIResponsesTranslationClient")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.organization = organization or os.getenv("OPENAI_ORGANIZATION_ID") or os.getenv("OPENAI_ORGANIZATION")
        self.project = project or os.getenv("OPENAI_PROJECT_ID")
        self.timeout_seconds = timeout_seconds

    def translate(self, batch: TranslationBatch, *, model: str) -> dict[str, Any]:
        payload = self.build_request_payload(batch, model=model)
        http_request = request.Request(
            f"{self.base_url}/responses",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=self._headers(batch.batch_id),
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=self.timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
                response_payload = json.loads(raw_body)
                processing_ms = response.headers.get("openai-processing-ms")
        except error.HTTPError as http_error:
            body = http_error.read().decode("utf-8", errors="replace")
            self._raise_http_error(http_error.code, body)
        except error.URLError as url_error:
            raise TranslationTransientError(f"OpenAI request failed: {url_error.reason}") from url_error

        output_text = _extract_output_text(response_payload)
        try:
            parsed_output = json.loads(output_text)
        except json.JSONDecodeError as json_error:
            raise TranslationSchemaError("OpenAI structured output was not valid JSON") from json_error
        if not isinstance(parsed_output, dict):
            raise TranslationSchemaError("OpenAI structured output must be a JSON object")

        parsed_output.setdefault("model", response_payload.get("model"))
        if processing_ms is not None and "provider_latency_ms" not in parsed_output:
            try:
                parsed_output["provider_latency_ms"] = int(processing_ms)
            except ValueError:
                pass
        parsed_output.setdefault("raw_response_text", output_text)
        return parsed_output

    def build_request_payload(self, batch: TranslationBatch, *, model: str) -> dict[str, Any]:
        return {
            "model": model,
            "store": False,
            "input": [
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "input_text",
                            "text": _instructions_for_pass(
                                batch.pass_type,
                                batch.source_language,
                                batch.target_language,
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps(batch.model_dump(), ensure_ascii=False),
                        }
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "translation_batch",
                    "strict": True,
                    "schema": _response_schema(),
                }
            },
        }

    def _headers(self, batch_id: str) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Client-Request-Id": batch_id,
        }
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        if self.project:
            headers["OpenAI-Project"] = self.project
        return headers

    @staticmethod
    def _raise_http_error(status_code: int, body: str) -> None:
        try:
            payload = json.loads(body)
            message = payload.get("error", {}).get("message", body)
        except json.JSONDecodeError:
            message = body
        if status_code in _RETRYABLE_STATUS_CODES:
            raise TranslationTransientError(f"OpenAI request failed with {status_code}: {message}")
        raise TranslationError(f"OpenAI request failed with {status_code}: {message}")


def _extract_output_text(payload: dict[str, Any]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    for item in payload.get("output", []):
        if item.get("type") == "refusal":
            raise TranslationError("OpenAI refused to provide a translation response")
        if item.get("type") != "message":
            continue
        for content_item in item.get("content", []):
            if content_item.get("type") == "output_text" and isinstance(content_item.get("text"), str):
                return content_item["text"]
            if content_item.get("type") == "refusal":
                raise TranslationError("OpenAI refused to provide a translation response")

    raise TranslationSchemaError("OpenAI response did not contain output_text content")


def _instructions_for_pass(pass_type: TranslationPass, source_language: str, target_language: str) -> str:
    purpose_by_pass = {
        TranslationPass.LITERAL: "Preserve meaning closely while keeping one result per subtitle segment id.",
        TranslationPass.NATURAL: "Rewrite the existing draft into natural subtitle English while keeping one result per subtitle segment id.",
        TranslationPass.REPAIR: "Repair only the supplied subtitle lines and keep one result per subtitle segment id.",
    }
    return (
        "You are translating subtitle segments. "
        f"Translate from {source_language} to {target_language}. "
        f"{purpose_by_pass[pass_type]} "
        "Return only the structured JSON that matches the provided schema. "
        "Keep ids unchanged. Keep subtitle wording concise and readable."
    )


def _response_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "id": {"type": "integer", "minimum": 0},
                        "translated_text": {"type": "string", "minLength": 1},
                        "notes": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "warnings": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["id", "translated_text", "notes", "confidence", "warnings"],
                },
            }
        },
        "required": ["results"],
    }
