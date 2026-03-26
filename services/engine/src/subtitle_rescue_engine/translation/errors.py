class TranslationError(Exception):
    """Base translation orchestration error."""


class TranslationTransientError(TranslationError):
    """Raised when a translation request can be retried safely."""


class TranslationSchemaError(TranslationError):
    """Raised when a provider response fails strict validation."""
