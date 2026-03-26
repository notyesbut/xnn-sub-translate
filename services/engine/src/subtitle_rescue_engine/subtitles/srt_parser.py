from __future__ import annotations

import re

from subtitle_rescue_engine.contracts import SubtitleSegment

from .exceptions import SubtitleParseError
from .normalization import normalize_line_endings, normalize_subtitle_text

TIMING_LINE_RE = re.compile(
    r"^(?P<start>\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(?P<end>\d{2}:\d{2}:\d{2}[,.]\d{3})(?:\s+.*)?$"
)


def parse_srt(text: str) -> list[SubtitleSegment]:
    normalized_text = normalize_line_endings(text).lstrip("\ufeff").strip()
    if not normalized_text:
        raise SubtitleParseError("SRT content is empty")

    segments: list[SubtitleSegment] = []
    blocks = [block for block in re.split(r"\n{2,}", normalized_text) if block.strip()]
    for block_index, block in enumerate(blocks, start=1):
        lines = block.split("\n")
        if lines and lines[0].strip().isdigit():
            lines = lines[1:]
        if len(lines) < 2:
            raise SubtitleParseError(f"SRT cue {block_index} is incomplete")

        timing_line = lines[0].strip()
        timing_match = TIMING_LINE_RE.match(timing_line)
        if timing_match is None:
            raise SubtitleParseError(f"SRT cue {block_index} has an invalid timing line")

        raw_source_text = "\n".join(line.strip() for line in lines[1:]).strip()
        if not raw_source_text:
            raise SubtitleParseError(f"SRT cue {block_index} does not contain subtitle text")

        segments.append(
            SubtitleSegment(
                id=block_index,
                start_ms=_parse_srt_timestamp(timing_match.group("start")),
                end_ms=_parse_srt_timestamp(timing_match.group("end")),
                source_text=raw_source_text,
                normalized_source_text=normalize_subtitle_text(raw_source_text),
            )
        )

    return segments


def _parse_srt_timestamp(value: str) -> int:
    match = re.match(r"^(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2})[,.](?P<ms>\d{3})$", value)
    if match is None:
        raise SubtitleParseError(f"Invalid SRT timestamp: {value}")

    hours = int(match.group("h"))
    minutes = int(match.group("m"))
    seconds = int(match.group("s"))
    milliseconds = int(match.group("ms"))
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + milliseconds
