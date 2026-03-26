from __future__ import annotations

import re

ASS_OVERRIDE_TAG_RE = re.compile(r"\{[^{}]*\}")
INLINE_WHITESPACE_RE = re.compile(r"[ \t]+")


def normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def normalize_visible_ass_text(text: str) -> str:
    visible_text = ASS_OVERRIDE_TAG_RE.sub("", text)
    visible_text = visible_text.replace("\\N", "\n").replace("\\n", "\n").replace("\\h", " ")
    return visible_text


def normalize_subtitle_text(text: str) -> str:
    normalized_lines: list[str] = []
    for raw_line in normalize_line_endings(text).replace("\xa0", " ").split("\n"):
        cleaned_line = INLINE_WHITESPACE_RE.sub(" ", raw_line).strip()
        if cleaned_line:
            normalized_lines.append(cleaned_line)
    return "\n".join(normalized_lines)
