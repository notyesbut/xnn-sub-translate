from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from subtitle_rescue_engine.contracts import SubtitleFormat, SubtitleSegment

from .ass_parser import parse_ass
from .exceptions import SubtitleDecodeError, UnsupportedSubtitleFormatError
from .srt_parser import parse_srt

SUPPORTED_ENCODINGS = ("utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "cp1252")


@dataclass(frozen=True, slots=True)
class SubtitleImportResult:
    format: SubtitleFormat
    encoding: str
    segments: list[SubtitleSegment]


def detect_subtitle_format(path: Path) -> SubtitleFormat:
    suffix = path.suffix.lower().lstrip(".")
    try:
        return SubtitleFormat(suffix)
    except ValueError as error:
        raise UnsupportedSubtitleFormatError(f"Unsupported subtitle format: {path.suffix}") from error


def import_subtitle_file(path: Path) -> SubtitleImportResult:
    subtitle_format = detect_subtitle_format(path)
    text, encoding = _decode_subtitle_file(path)
    parser = parse_srt if subtitle_format is SubtitleFormat.SRT else parse_ass
    return SubtitleImportResult(
        format=subtitle_format,
        encoding=encoding,
        segments=parser(text),
    )


def _decode_subtitle_file(path: Path) -> tuple[str, str]:
    payload = path.read_bytes()
    for encoding in SUPPORTED_ENCODINGS:
        try:
            text = payload.decode(encoding)
        except UnicodeDecodeError:
            continue
        if "\x00" in text and not encoding.startswith("utf-16"):
            continue
        return text, encoding

    raise SubtitleDecodeError(f"Could not decode subtitle file: {path}")
