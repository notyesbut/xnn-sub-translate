from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _require_non_empty(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must not be empty")


def _require_non_negative(name: str, value: int) -> None:
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


def _require_probability(name: str, value: float | None) -> None:
    if value is None:
        return
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0.0 and 1.0")


def _serialize(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return str(value)
    if is_dataclass(value):
        return {key: _serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


class SubtitleFormat(StrEnum):
    SRT = "srt"
    ASS = "ass"


class ProjectAssetKind(StrEnum):
    SUBTITLE = "subtitle"
    VIDEO = "video"
    GLOSSARY = "glossary"


class ProjectStatus(StrEnum):
    CREATED = "created"
    DETECTING = "detecting"
    TRANSLATING = "translating"
    REVIEWING = "reviewing"
    SYNCING = "syncing"
    EXPORT_READY = "export_ready"
    FAILED = "failed"


class JobType(StrEnum):
    IMPORT = "import"
    DETECT = "detect"
    OCR = "ocr"
    TRANSLATION = "translation"
    QA = "qa"
    SYNC = "sync"
    EXPORT = "export"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class QAFlagSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class QAFlagStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class ExportStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class TranslationPass(StrEnum):
    LITERAL = "literal"
    NATURAL = "natural"
    REPAIR = "repair"


class TranslationBatchStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


@dataclass(slots=True)
class Project:
    project_id: str
    name: str
    source_language: str
    target_language: str = "en"
    source_subtitle_type: SubtitleFormat | None = None
    target_video_path: str | None = None
    reference_video_path: str | None = None
    status: ProjectStatus = ProjectStatus.CREATED
    created_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        _require_non_empty("project_id", self.project_id)
        _require_non_empty("name", self.name)
        _require_non_empty("source_language", self.source_language)
        _require_non_empty("target_language", self.target_language)

    def model_dump(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(slots=True)
class ProjectAsset:
    asset_id: str
    project_id: str
    kind: ProjectAssetKind
    original_name: str
    stored_path: str
    checksum: str
    format: SubtitleFormat | None = None
    created_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        _require_non_empty("asset_id", self.asset_id)
        _require_non_empty("project_id", self.project_id)
        _require_non_empty("original_name", self.original_name)
        _require_non_empty("stored_path", self.stored_path)
        _require_non_empty("checksum", self.checksum)

    def model_dump(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(slots=True)
class SubtitleSegment:
    id: int
    start_ms: int
    end_ms: int
    source_text: str
    normalized_source_text: str | None = None
    literal_en: str | None = None
    natural_en: str | None = None
    final_en: str | None = None
    ocr_confidence: float | None = None
    translation_confidence: float | None = None
    flags: list[str] = field(default_factory=list)
    locked: bool = False

    def __post_init__(self) -> None:
        _require_non_negative("id", self.id)
        _require_non_negative("start_ms", self.start_ms)
        _require_non_negative("end_ms", self.end_ms)
        if self.end_ms < self.start_ms:
            raise ValueError("end_ms must be greater than or equal to start_ms")
        _require_non_empty("source_text", self.source_text)
        _require_probability("ocr_confidence", self.ocr_confidence)
        _require_probability("translation_confidence", self.translation_confidence)

    def model_dump(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(slots=True)
class Job:
    job_id: str
    project_id: str
    type: JobType
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    error: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty("job_id", self.job_id)
        _require_non_empty("project_id", self.project_id)
        _require_probability("progress", self.progress)

    def model_dump(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(slots=True)
class QAFlag:
    flag_id: str
    project_id: str
    segment_id: int
    rule: str
    severity: QAFlagSeverity
    message: str
    status: QAFlagStatus = QAFlagStatus.OPEN

    def __post_init__(self) -> None:
        _require_non_empty("flag_id", self.flag_id)
        _require_non_empty("project_id", self.project_id)
        _require_non_negative("segment_id", self.segment_id)
        _require_non_empty("rule", self.rule)
        _require_non_empty("message", self.message)

    def model_dump(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(slots=True)
class GlossaryTerm:
    term_id: str
    project_id: str
    source_term: str
    target_term: str
    notes: str | None = None
    locked: bool = True

    def __post_init__(self) -> None:
        _require_non_empty("term_id", self.term_id)
        _require_non_empty("project_id", self.project_id)
        _require_non_empty("source_term", self.source_term)
        _require_non_empty("target_term", self.target_term)

    def model_dump(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(slots=True)
class ExportArtifact:
    export_id: str
    project_id: str
    format: SubtitleFormat
    path: str
    status: ExportStatus = ExportStatus.PENDING
    created_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        _require_non_empty("export_id", self.export_id)
        _require_non_empty("project_id", self.project_id)
        _require_non_empty("path", self.path)

    def model_dump(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(slots=True)
class TranslationSegmentInput:
    id: int
    source_text: str
    normalized_source_text: str
    context_before: str | None = None
    context_after: str | None = None

    def __post_init__(self) -> None:
        _require_non_negative("id", self.id)
        _require_non_empty("source_text", self.source_text)
        _require_non_empty("normalized_source_text", self.normalized_source_text)

    def model_dump(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(slots=True)
class TranslationSegmentResult:
    id: int
    translated_text: str
    notes: str | None = None
    confidence: float | None = None
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_non_negative("id", self.id)
        _require_non_empty("translated_text", self.translated_text)
        _require_probability("confidence", self.confidence)

    def model_dump(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(slots=True)
class TranslationBatch:
    batch_id: str
    project_id: str
    pass_type: TranslationPass
    source_language: str
    target_language: str
    segments: list[TranslationSegmentInput]
    glossary_terms: list[GlossaryTerm] = field(default_factory=list)
    locked_names: list[str] = field(default_factory=list)
    cache_key: str | None = None
    attempt_count: int = 0
    status: TranslationBatchStatus = TranslationBatchStatus.PENDING

    def __post_init__(self) -> None:
        _require_non_empty("batch_id", self.batch_id)
        _require_non_empty("project_id", self.project_id)
        _require_non_empty("source_language", self.source_language)
        _require_non_empty("target_language", self.target_language)
        if not self.segments:
            raise ValueError("segments must not be empty")
        _require_non_negative("attempt_count", self.attempt_count)

    def model_dump(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(slots=True)
class TranslationBatchResult:
    batch_id: str
    pass_type: TranslationPass
    results: list[TranslationSegmentResult]
    raw_response_text: str | None = None
    model: str | None = None
    provider_latency_ms: int | None = None

    def __post_init__(self) -> None:
        _require_non_empty("batch_id", self.batch_id)
        if not self.results:
            raise ValueError("results must not be empty")
        if self.provider_latency_ms is not None:
            _require_non_negative("provider_latency_ms", self.provider_latency_ms)

    def model_dump(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(slots=True)
class TranslationCacheEntry:
    cache_key: str
    pass_type: TranslationPass
    source_hash: str
    response_payload: dict[str, Any]
    created_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        _require_non_empty("cache_key", self.cache_key)
        _require_non_empty("source_hash", self.source_hash)

    def model_dump(self) -> dict[str, Any]:
        return _serialize(self)
