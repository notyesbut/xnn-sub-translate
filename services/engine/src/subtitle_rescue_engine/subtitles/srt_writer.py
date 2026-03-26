from __future__ import annotations

from pathlib import Path

from subtitle_rescue_engine.contracts import SubtitleSegment


def render_srt(segments: list[SubtitleSegment]) -> str:
    rendered_lines: list[str] = []
    for index, segment in enumerate(segments, start=1):
        rendered_lines.append(str(index))
        rendered_lines.append(
            f"{_format_srt_timestamp(segment.start_ms)} --> {_format_srt_timestamp(segment.end_ms)}"
        )
        rendered_lines.extend(_resolve_export_text(segment).split("\n"))
        rendered_lines.append("")

    return "\n".join(rendered_lines).rstrip() + "\n"


def write_srt_file(path: Path, segments: list[SubtitleSegment]) -> Path:
    path.write_text(render_srt(segments), encoding="utf-8")
    return path


def _resolve_export_text(segment: SubtitleSegment) -> str:
    export_text = (
        segment.final_en
        or segment.natural_en
        or segment.literal_en
        or segment.normalized_source_text
        or segment.source_text
    )
    return export_text.strip()


def _format_srt_timestamp(value_ms: int) -> str:
    hours, remainder = divmod(value_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
