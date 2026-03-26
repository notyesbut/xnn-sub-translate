from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from subtitle_rescue_engine.contracts import TranslationBatch, TranslationPass


@dataclass(slots=True)
class TranslationSettings:
    batch_size: int = 40
    max_attempts: int = 3
    retry_on_schema_error: bool = True
    config_version: str = "v1"
    literal_model: str = "literal-default"
    natural_model: str = "natural-default"
    repair_model: str = "repair-default"

    def __post_init__(self) -> None:
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be positive")

    def model_for(self, pass_type: TranslationPass) -> str:
        if pass_type is TranslationPass.LITERAL:
            return self.literal_model
        if pass_type is TranslationPass.NATURAL:
            return self.natural_model
        return self.repair_model


class TranslationClient(Protocol):
    def translate(self, batch: TranslationBatch, *, model: str) -> dict[str, Any]:
        """Translate one batch and return a raw JSON-like response."""
