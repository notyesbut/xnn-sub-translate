from __future__ import annotations

from typing import Any

from subtitle_rescue_engine.contracts import TranslationBatch, TranslationBatchResult, TranslationSegmentResult

from .errors import TranslationSchemaError


def validate_translation_response(
    batch: TranslationBatch,
    payload: dict[str, Any],
) -> TranslationBatchResult:
    if not isinstance(payload, dict):
        raise TranslationSchemaError("Translation response must be a dictionary")

    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        raise TranslationSchemaError("Translation response must contain a list of results")

    expected_ids = {segment.id for segment in batch.segments}
    seen_ids: set[int] = set()
    validated_results: list[TranslationSegmentResult] = []
    for raw_result in raw_results:
        if not isinstance(raw_result, dict):
            raise TranslationSchemaError("Each translation result must be a dictionary")
        result_id = raw_result.get("id")
        if not isinstance(result_id, int):
            raise TranslationSchemaError("Each translation result must contain an integer id")
        if result_id in seen_ids:
            raise TranslationSchemaError(f"Duplicate translation id: {result_id}")
        if result_id not in expected_ids:
            raise TranslationSchemaError(f"Unexpected translation id: {result_id}")

        notes = raw_result.get("notes")
        if notes is not None and not isinstance(notes, str):
            raise TranslationSchemaError("Translation notes must be a string when present")

        warnings = raw_result.get("warnings", [])
        if not isinstance(warnings, list) or any(not isinstance(item, str) for item in warnings):
            raise TranslationSchemaError("Translation warnings must be a list of strings")

        confidence = raw_result.get("confidence")
        if confidence is not None and not isinstance(confidence, (int, float)):
            raise TranslationSchemaError("Translation confidence must be numeric when present")

        try:
            validated_results.append(
                TranslationSegmentResult(
                    id=result_id,
                    translated_text=raw_result.get("translated_text", ""),
                    notes=notes,
                    confidence=float(confidence) if confidence is not None else None,
                    warnings=warnings,
                )
            )
        except ValueError as error:
            raise TranslationSchemaError(str(error)) from error
        seen_ids.add(result_id)

    if seen_ids != expected_ids:
        missing_ids = sorted(expected_ids - seen_ids)
        raise TranslationSchemaError(f"Missing translation ids: {missing_ids}")

    return TranslationBatchResult(
        batch_id=batch.batch_id,
        pass_type=batch.pass_type,
        results=validated_results,
        raw_response_text=payload.get("raw_response_text"),
        model=payload.get("model"),
        provider_latency_ms=payload.get("provider_latency_ms"),
    )
