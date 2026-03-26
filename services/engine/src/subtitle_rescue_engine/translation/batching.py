from __future__ import annotations

import hashlib
import json

from subtitle_rescue_engine.contracts import (
    GlossaryTerm,
    TranslationBatch,
    TranslationPass,
    TranslationSegmentInput,
)


def build_translation_batches(
    *,
    project_id: str,
    pass_type: TranslationPass,
    source_language: str,
    target_language: str,
    segments: list[TranslationSegmentInput],
    glossary_terms: list[GlossaryTerm] | None = None,
    locked_names: list[str] | None = None,
    batch_size: int = 40,
    config_version: str = "v1",
) -> list[TranslationBatch]:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    glossary = glossary_terms or []
    locked = sorted(locked_names or [])
    batches: list[TranslationBatch] = []
    for batch_index, start in enumerate(range(0, len(segments), batch_size), start=1):
        batch_segments = segments[start : start + batch_size]
        cache_key = build_translation_cache_key(
            pass_type=pass_type,
            source_language=source_language,
            target_language=target_language,
            segments=batch_segments,
            glossary_terms=glossary,
            locked_names=locked,
            config_version=config_version,
        )
        batches.append(
            TranslationBatch(
                batch_id=f"{project_id}-{pass_type.value}-{batch_index:04d}-{cache_key[:12]}",
                project_id=project_id,
                pass_type=pass_type,
                source_language=source_language,
                target_language=target_language,
                segments=batch_segments,
                glossary_terms=glossary,
                locked_names=locked,
                cache_key=cache_key,
            )
        )
    return batches


def build_translation_cache_key(
    *,
    pass_type: TranslationPass,
    source_language: str,
    target_language: str,
    segments: list[TranslationSegmentInput],
    glossary_terms: list[GlossaryTerm],
    locked_names: list[str],
    config_version: str,
) -> str:
    payload = {
        "config_version": config_version,
        "glossary_terms": [
            {
                "source_term": term.source_term,
                "target_term": term.target_term,
                "notes": term.notes,
                "locked": term.locked,
            }
            for term in glossary_terms
        ],
        "locked_names": sorted(locked_names),
        "pass_type": str(pass_type),
        "segments": [segment.model_dump() for segment in segments],
        "source_language": source_language,
        "target_language": target_language,
    }
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    return digest.hexdigest()
