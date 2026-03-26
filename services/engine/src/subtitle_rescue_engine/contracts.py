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


@dataclass(slots=True)
class Project:
    project_id: str
    name: str
    source_language: str
    target_language: str = "en"
    source_subtitle_type: str | None = None
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
    format: str
    path: str
    status: ExportStatus = ExportStatus.PENDING
    created_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        _require_non_empty("export_id", self.export_id)
        _require_non_empty("project_id", self.project_id)
        _require_non_empty("format", self.format)
        _require_non_empty("path", self.path)

    def model_dump(self) -> dict[str, Any]:
        return _serialize(self)
