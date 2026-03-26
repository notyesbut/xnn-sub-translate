class SubtitleError(Exception):
    """Base subtitle import/export error."""


class UnsupportedSubtitleFormatError(SubtitleError):
    """Raised when a subtitle file extension is not supported."""


class SubtitleDecodeError(SubtitleError):
    """Raised when a subtitle file cannot be decoded into text."""


class SubtitleParseError(SubtitleError):
    """Raised when a subtitle file cannot be parsed safely."""
