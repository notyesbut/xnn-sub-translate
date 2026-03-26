from __future__ import annotations

import json
import time
from dataclasses import replace
from pathlib import Path
from typing import Callable

from subtitle_rescue_engine.contracts import (
    ProjectStatus,
    TranslationBatch,
    TranslationBatchResult,
    TranslationBatchStatus,
    TranslationCacheEntry,
    TranslationPass,
    TranslationSegmentInput,
)
from subtitle_rescue_engine.project_layout import ProjectLayout
from subtitle_rescue_engine.storage import ProjectRepository

from .batching import build_translation_batches
from .client import TranslationClient, TranslationSettings
from .errors import TranslationSchemaError, TranslationTransientError
from .schema import validate_translation_response


class TranslationService:
    def __init__(
        self,
        workspace_root: Path,
        client: TranslationClient,
        *,
        settings: TranslationSettings | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        self.workspace_root = Path(workspace_root)
        self.client = client
        self.settings = settings or TranslationSettings()
        self.sleeper = sleeper or time.sleep

    def translate_project(
        self,
        project_id: str,
        *,
        locked_names: list[str] | None = None,
    ) -> list[TranslationBatchResult]:
        literal_results = self.translate_pass(
            project_id,
            TranslationPass.LITERAL,
            locked_names=locked_names,
        )
        natural_results = self.translate_pass(
            project_id,
            TranslationPass.NATURAL,
            locked_names=locked_names,
        )
        repository = self._repository(project_id)
        project = repository.get_project(project_id)
        if project is not None:
            repository.upsert_project(replace(project, status=ProjectStatus.REVIEWING))
        return literal_results + natural_results

    def translate_pass(
        self,
        project_id: str,
        pass_type: TranslationPass,
        *,
        locked_names: list[str] | None = None,
    ) -> list[TranslationBatchResult]:
        layout = ProjectLayout.from_workspace(self.workspace_root, project_id).create()
        repository = self._repository(project_id)
        project = repository.get_project(project_id)
        if project is None:
            raise KeyError(f"Unknown project: {project_id}")

        repository.upsert_project(replace(project, status=ProjectStatus.TRANSLATING))
        segments = repository.list_segments(project_id)
        pending_inputs = self._build_inputs(segments, pass_type)
        if not pending_inputs:
            return []

        glossary_terms = repository.list_glossary_terms(project_id)
        batches = build_translation_batches(
            project_id=project_id,
            pass_type=pass_type,
            source_language=project.source_language,
            target_language=project.target_language,
            segments=pending_inputs,
            glossary_terms=glossary_terms,
            locked_names=locked_names,
            batch_size=self.settings.batch_size,
            config_version=self.settings.config_version,
        )

        batch_results: list[TranslationBatchResult] = []
        for ordinal, batch in enumerate(batches, start=1):
            batch_results.append(self._run_batch(layout, repository, batch, ordinal=ordinal))
        return batch_results

    def _run_batch(
        self,
        layout: ProjectLayout,
        repository: ProjectRepository,
        batch: TranslationBatch,
        *,
        ordinal: int,
    ) -> TranslationBatchResult:
        request_path = layout.batch_requests / f"{batch.pass_type.value}-{ordinal:04d}-{batch.cache_key[:12]}.json"
        response_path = layout.batch_responses / f"{batch.pass_type.value}-{ordinal:04d}-{batch.cache_key[:12]}.json"
        cache_path = layout.batch_cache / f"{batch.cache_key}.json"
        self._write_json(request_path, batch.model_dump())

        cache_entry = repository.get_translation_cache(batch.cache_key or batch.batch_id, pass_type=batch.pass_type)
        if cache_entry is not None:
            result = validate_translation_response(batch, cache_entry.response_payload)
            batch.status = TranslationBatchStatus.CACHED
            repository.record_translation_batch(
                batch,
                ordinal=ordinal,
                request_path=str(request_path.relative_to(layout.project_root)),
                response_path=str(cache_path.relative_to(layout.project_root)),
            )
            repository.apply_translation_results(batch.project_id, batch.pass_type, result.results)
            self._write_json(cache_path, cache_entry.response_payload)
            return result

        last_error: Exception | None = None
        for attempt in range(1, self.settings.max_attempts + 1):
            batch.attempt_count = attempt
            batch.status = TranslationBatchStatus.RUNNING
            try:
                raw_payload = self.client.translate(
                    batch,
                    model=self.settings.model_for(batch.pass_type),
                )
                result = validate_translation_response(batch, raw_payload)
            except TranslationTransientError as error:
                last_error = error
                if attempt >= self.settings.max_attempts:
                    break
                self.sleeper(0.0)
                continue
            except TranslationSchemaError as error:
                last_error = error
                if not self.settings.retry_on_schema_error or attempt >= self.settings.max_attempts:
                    break
                self.sleeper(0.0)
                continue
            else:
                batch.status = TranslationBatchStatus.COMPLETED
                repository.record_translation_batch(
                    batch,
                    ordinal=ordinal,
                    request_path=str(request_path.relative_to(layout.project_root)),
                    response_path=str(response_path.relative_to(layout.project_root)),
                )
                repository.apply_translation_results(batch.project_id, batch.pass_type, result.results)
                self._write_json(response_path, raw_payload)
                cached_payload = result.model_dump()
                repository.upsert_translation_cache(
                    TranslationCacheEntry(
                        cache_key=batch.cache_key or batch.batch_id,
                        pass_type=batch.pass_type,
                        source_hash=batch.cache_key or batch.batch_id,
                        response_payload=cached_payload,
                    )
                )
                self._write_json(cache_path, cached_payload)
                return result

        batch.status = TranslationBatchStatus.FAILED
        repository.record_translation_batch(
            batch,
            ordinal=ordinal,
            request_path=str(request_path.relative_to(layout.project_root)),
            error=str(last_error) if last_error else "Unknown translation failure",
            response_path=str(response_path.relative_to(layout.project_root)) if response_path.exists() else None,
        )
        if last_error is None:
            raise TranslationTransientError("Translation batch failed without a specific error")
        raise last_error

    def _build_inputs(
        self,
        segments: list,
        pass_type: TranslationPass,
    ) -> list[TranslationSegmentInput]:
        pending_segments = [segment for segment in segments if not segment.locked and _needs_pass(segment, pass_type)]
        inputs: list[TranslationSegmentInput] = []
        for index, segment in enumerate(pending_segments):
            inputs.append(
                TranslationSegmentInput(
                    id=segment.id,
                    source_text=_source_text_for_pass(segment, pass_type),
                    normalized_source_text=_source_text_for_pass(segment, pass_type),
                    context_before=_source_text_for_pass(pending_segments[index - 1], pass_type)
                    if index > 0
                    else None,
                    context_after=_source_text_for_pass(pending_segments[index + 1], pass_type)
                    if index + 1 < len(pending_segments)
                    else None,
                )
            )
        return inputs

    def _repository(self, project_id: str) -> ProjectRepository:
        layout = ProjectLayout.from_workspace(self.workspace_root, project_id).create()
        repository = ProjectRepository(layout.database)
        repository.initialize()
        return repository

    @staticmethod
    def _write_json(path: Path, payload: dict) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _needs_pass(segment, pass_type: TranslationPass) -> bool:
    if pass_type is TranslationPass.LITERAL:
        return not segment.literal_en
    if pass_type is TranslationPass.NATURAL:
        return not segment.natural_en or not segment.final_en
    return not segment.final_en


def _source_text_for_pass(segment, pass_type: TranslationPass) -> str:
    if pass_type is TranslationPass.LITERAL:
        return segment.normalized_source_text or segment.source_text
    if pass_type is TranslationPass.NATURAL:
        return segment.literal_en or segment.normalized_source_text or segment.source_text
    return segment.final_en or segment.natural_en or segment.literal_en or segment.normalized_source_text or segment.source_text
