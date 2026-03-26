import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from subtitle_rescue_engine.contracts import TranslationPass, TranslationSegmentInput
from subtitle_rescue_engine.translation import (
    OpenAIResponsesTranslationClient,
    TranslationError,
    TranslationTransientError,
    build_translation_batches,
)


class FakeHTTPResponse:
    def __init__(self, payload: dict, headers: dict[str, str] | None = None) -> None:
        self.payload = json.dumps(payload).encode("utf-8")
        self.headers = headers or {}

    def read(self) -> bytes:
        return self.payload

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class OpenAIResponsesTranslationClientTestCase(unittest.TestCase):
    def test_requires_api_key(self) -> None:
        with self.assertRaises(ValueError):
            OpenAIResponsesTranslationClient(api_key="")

    def test_build_request_payload_uses_responses_api_shape(self) -> None:
        client = OpenAIResponsesTranslationClient(api_key="test-key")
        batch = _sample_batch()

        payload = client.build_request_payload(batch, model="gpt-5")

        self.assertEqual(payload["model"], "gpt-5")
        self.assertFalse(payload["store"])
        self.assertEqual(payload["input"][0]["role"], "developer")
        self.assertEqual(payload["input"][1]["role"], "user")
        self.assertEqual(payload["text"]["format"]["type"], "json_schema")
        self.assertEqual(payload["text"]["format"]["name"], "translation_batch")
        self.assertTrue(payload["text"]["format"]["strict"])
        self.assertEqual(json.loads(payload["input"][1]["content"][0]["text"])["batch_id"], batch.batch_id)

    def test_translate_parses_structured_output_text(self) -> None:
        client = OpenAIResponsesTranslationClient(api_key="test-key")
        batch = _sample_batch()
        response_payload = {
            "model": "gpt-5",
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": json.dumps(
                                {
                                    "results": [
                                        {
                                            "id": 1,
                                            "translated_text": "Hello",
                                            "notes": "",
                                            "confidence": 0.9,
                                            "warnings": [],
                                        }
                                    ]
                                }
                            ),
                        }
                    ],
                }
            ],
        }

        with patch(
            "subtitle_rescue_engine.translation.openai_client.request.urlopen",
            return_value=FakeHTTPResponse(response_payload, headers={"openai-processing-ms": "321"}),
        ):
            parsed = client.translate(batch, model="gpt-5")

        self.assertEqual(parsed["results"][0]["translated_text"], "Hello")
        self.assertEqual(parsed["provider_latency_ms"], 321)
        self.assertEqual(parsed["model"], "gpt-5")

    def test_translate_raises_on_missing_output_text(self) -> None:
        client = OpenAIResponsesTranslationClient(api_key="test-key")
        batch = _sample_batch()

        with patch(
            "subtitle_rescue_engine.translation.openai_client.request.urlopen",
            return_value=FakeHTTPResponse({"output": []}),
        ):
            with self.assertRaises(TranslationError):
                client.translate(batch, model="gpt-5")

    def test_translate_raises_on_malformed_json_output(self) -> None:
        client = OpenAIResponsesTranslationClient(api_key="test-key")
        batch = _sample_batch()
        response_payload = {
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": "{not json"}],
                }
            ]
        }

        with patch(
            "subtitle_rescue_engine.translation.openai_client.request.urlopen",
            return_value=FakeHTTPResponse(response_payload),
        ):
            with self.assertRaises(TranslationError):
                client.translate(batch, model="gpt-5")

    def test_translate_maps_retryable_and_fatal_http_errors(self) -> None:
        client = OpenAIResponsesTranslationClient(api_key="test-key")
        batch = _sample_batch()
        retryable_error = HTTPError(
            url="https://api.openai.com/v1/responses",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=io.BytesIO(b'{"error":{"message":"rate limited"}}'),
        )
        fatal_error = HTTPError(
            url="https://api.openai.com/v1/responses",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=io.BytesIO(b'{"error":{"message":"bad schema"}}'),
        )

        with patch(
            "subtitle_rescue_engine.translation.openai_client.request.urlopen",
            side_effect=retryable_error,
        ):
            with self.assertRaises(TranslationTransientError):
                client.translate(batch, model="gpt-5")

        with patch(
            "subtitle_rescue_engine.translation.openai_client.request.urlopen",
            side_effect=fatal_error,
        ):
            with self.assertRaises(TranslationError):
                client.translate(batch, model="gpt-5")

    def test_translate_sends_expected_headers(self) -> None:
        client = OpenAIResponsesTranslationClient(
            api_key="test-key",
            organization="org_123",
            project="proj_123",
        )
        batch = _sample_batch()
        captured_request = {}

        def fake_urlopen(request_obj, timeout):
            captured_request["request"] = request_obj
            captured_request["timeout"] = timeout
            return FakeHTTPResponse(
                {
                    "output": [
                        {
                            "type": "message",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": json.dumps(
                                        {
                                            "results": [
                                                {
                                                    "id": 1,
                                                    "translated_text": "Hello",
                                                    "notes": "",
                                                    "confidence": 0.9,
                                                    "warnings": [],
                                                }
                                            ]
                                        }
                                    ),
                                }
                            ],
                        }
                    ]
                }
            )

        with patch(
            "subtitle_rescue_engine.translation.openai_client.request.urlopen",
            side_effect=fake_urlopen,
        ):
            client.translate(batch, model="gpt-5")

        request_obj = captured_request["request"]
        self.assertEqual(request_obj.full_url, "https://api.openai.com/v1/responses")
        self.assertEqual(request_obj.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(request_obj.get_header("Content-type"), "application/json")
        self.assertEqual(request_obj.get_header("Openai-project"), "proj_123")
        self.assertEqual(request_obj.get_header("Openai-organization"), "org_123")
        self.assertEqual(request_obj.get_header("X-client-request-id"), batch.batch_id)


def _sample_batch():
    return build_translation_batches(
        project_id="proj_001",
        pass_type=TranslationPass.LITERAL,
        source_language="zh",
        target_language="en",
        segments=[TranslationSegmentInput(id=1, source_text="你好", normalized_source_text="你好")],
        batch_size=10,
    )[0]


if __name__ == "__main__":
    unittest.main()
