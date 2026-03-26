from __future__ import annotations

import re

from subtitle_rescue_engine.contracts import SubtitleSegment

from .exceptions import SubtitleParseError
from .normalization import normalize_line_endings, normalize_subtitle_text, normalize_visible_ass_text

ASS_TIMESTAMP_RE = re.compile(r"^(?P<h>\d+):(?P<m>\d{2}):(?P<s>\d{2})\.(?P<cs>\d{2})$")


def parse_ass(text: str) -> list[SubtitleSegment]:
    lines = normalize_line_endings(text).lstrip("\ufeff").split("\n")
    in_events_section = False
    format_columns: list[str] | None = None
    segments: list[SubtitleSegment] = []

    for line_number, raw_line in enumerate(lines, start=1):
        stripped_line = raw_line.strip()
        if not stripped_line or stripped_line.startswith(";"):
            continue
        if stripped_line.startswith("[") and stripped_line.endswith("]"):
            in_events_section = stripped_line.lower() == "[events]"
            continue
        if not in_events_section:
            continue
        if stripped_line.lower().startswith("format:"):
            format_columns = [
                column.strip().lower() for column in stripped_line.partition(":")[2].split(",")
            ]
            continue
        if not stripped_line.lower().startswith("dialogue:"):
            continue
        if format_columns is None:
            raise SubtitleParseError(
                f"ASS dialogue line {line_number} was found before the events format was declared"
            )

        values = stripped_line.partition(":")[2].lstrip().split(",", len(format_columns) - 1)
        if len(values) != len(format_columns):
            raise SubtitleParseError(f"ASS dialogue line {line_number} does not match the format line")

        record = dict(zip(format_columns, values, strict=True))
        if "start" not in record or "end" not in record or "text" not in record:
            raise SubtitleParseError("ASS events format must contain Start, End, and Text columns")

        source_text = normalize_visible_ass_text(record["text"]).strip()
        if not source_text:
            continue

        segments.append(
            SubtitleSegment(
                id=len(segments) + 1,
                start_ms=_parse_ass_timestamp(record["start"].strip()),
                end_ms=_parse_ass_timestamp(record["end"].strip()),
                source_text=source_text,
                normalized_source_text=normalize_subtitle_text(source_text),
            )
        )

    if not segments:
        raise SubtitleParseError("ASS content does not contain any dialogue lines")

    return segments


def _parse_ass_timestamp(value: str) -> int:
    match = ASS_TIMESTAMP_RE.match(value)
    if match is None:
        raise SubtitleParseError(f"Invalid ASS timestamp: {value}")

    hours = int(match.group("h"))
    minutes = int(match.group("m"))
    seconds = int(match.group("s"))
    centiseconds = int(match.group("cs"))
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + centiseconds * 10
