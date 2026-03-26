from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from subtitle_rescue_engine.contracts import ProjectStatus, QAFlag, QAFlagSeverity, SubtitleSegment
from subtitle_rescue_engine.project_layout import ProjectLayout
from subtitle_rescue_engine.storage import ProjectRepository


class QAService:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = Path(workspace_root)

    def run(self, project_id: str) -> list[QAFlag]:
        layout = ProjectLayout.from_workspace(self.workspace_root, project_id).create()
        repository = ProjectRepository(layout.database)
        repository.initialize()
        project = repository.get_project(project_id)
        if project is None:
            raise KeyError(f"Unknown project: {project_id}")

        segments = repository.list_segments(project_id)
        flags = _build_flags(project_id, segments)
        repository.replace_qa_flags(project_id, flags)

        open_rules_by_segment: dict[int, list[str]] = {}
        for flag in flags:
            open_rules_by_segment.setdefault(flag.segment_id, []).append(flag.rule)
        for segment in segments:
            segment.flags = open_rules_by_segment.get(segment.id, [])
        repository.replace_segments(project_id, segments)
        repository.upsert_project(replace(project, status=ProjectStatus.EXPORT_READY))
        return flags


def _build_flags(project_id: str, segments: list[SubtitleSegment]) -> list[QAFlag]:
    flags: list[QAFlag] = []
    previous_segment: SubtitleSegment | None = None
    for segment in segments:
        export_text = _effective_text(segment)
        if not export_text:
            flags.append(_flag(project_id, segment.id, "missing_translation", QAFlagSeverity.ERROR, "No English text is available for export."))
        else:
            if _normalize_compare(export_text) == _normalize_compare(segment.normalized_source_text or segment.source_text):
                flags.append(_flag(project_id, segment.id, "source_text_leak", QAFlagSeverity.WARNING, "The English text still matches the source text and may be untranslated."))
            if segment.translation_confidence is not None and segment.translation_confidence < 0.75:
                flags.append(_flag(project_id, segment.id, "low_translation_confidence", QAFlagSeverity.WARNING, "The translation confidence is low and should be reviewed."))
            if _has_long_line(export_text):
                flags.append(_flag(project_id, segment.id, "long_line", QAFlagSeverity.WARNING, "The subtitle line may be too long to read comfortably."))
            if _has_high_reading_speed(export_text, segment):
                flags.append(_flag(project_id, segment.id, "high_reading_speed", QAFlagSeverity.WARNING, "The subtitle may read too quickly on screen."))
        if previous_segment is not None and segment.start_ms < previous_segment.end_ms:
            flags.append(_flag(project_id, segment.id, "timing_overlap", QAFlagSeverity.ERROR, "This subtitle overlaps the previous subtitle timing."))
        previous_segment = segment
    return flags


def _effective_text(segment: SubtitleSegment) -> str:
    return (
        segment.final_en
        or segment.natural_en
        or segment.literal_en
        or ""
    ).strip()


def _normalize_compare(text: str) -> str:
    return " ".join(text.lower().split())


def _has_long_line(text: str) -> bool:
    lines = text.split("\n")
    return any(len(line) > 42 for line in lines) or len(text.replace("\n", "")) > 84


def _has_high_reading_speed(text: str, segment: SubtitleSegment) -> bool:
    duration_seconds = max((segment.end_ms - segment.start_ms) / 1000, 0.001)
    return len(text.replace("\n", "")) / duration_seconds > 20.0


def _flag(
    project_id: str,
    segment_id: int,
    rule: str,
    severity: QAFlagSeverity,
    message: str,
) -> QAFlag:
    return QAFlag(
        flag_id=f"{project_id}:{segment_id}:{rule}",
        project_id=project_id,
        segment_id=segment_id,
        rule=rule,
        severity=severity,
        message=message,
    )
