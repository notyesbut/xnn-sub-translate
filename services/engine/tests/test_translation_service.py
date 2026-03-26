import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from subtitle_rescue_engine.contracts import GlossaryTerm, Project, TranslationPass, TranslationSegmentInput
from subtitle_rescue_engine.project_service import ProjectService
from subtitle_rescue_engine.storage import ProjectRepository
from subtitle_rescue_engine.translation import (
    OpenAIResponsesTranslationClient,
    TranslationSchemaError,
    TranslationService,
    TranslationSettings,
    TranslationTransientError,
    build_translation_batches,
    validate_translation_response,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "subtitles"


class ScriptedTranslationClient:
    def __init__(self, responses) -> None:
        self.responses = list(responses)
        self.calls: list[dict] = []

    def translate(self, batch, *, model: str) -> dict:
        self.calls.append(
            {
                "batch_id": batch.batch_id,
                "pass_type": batch.pass_type.value,
                "model": model,
                "segment_ids": [segment.id for segment in batch.segments],
            }
        )
        outcome = self.responses.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeHTTPResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = json.dumps(payload).encode("utf-8")
        self.headers = {}

    def read(self) -> bytes:
        return self.payload

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class TranslationBatchingTestCase(unittest.TestCase):
    def test_build_translation_batches_preserves_ids_and_changes_cache_key(self) -> None:
        inputs = [
            TranslationSegmentInput(id=1, source_text="a", normalized_source_text="a"),
            TranslationSegmentInput(id=2, source_text="b", normalized_source_text="b"),
            TranslationSegmentInput(id=3, source_text="c", normalized_source_text="c"),
        ]
        glossary_terms = [
            GlossaryTerm(
                term_id="term_001",
                project_id="proj_001",
                source_term="hero",
                target_term="Hero",
            )
        ]

        batches = build_translation_batches(
            project_id="proj_001",
            pass_type=TranslationPass.LITERAL,
            source_language="zh",
            target_language="en",
            segments=inputs,
            glossary_terms=glossary_terms,
            locked_names=["Akira"],
            batch_size=2,
            config_version="v1",
        )
        changed_batches = build_translation_batches(
            project_id="proj_001",
            pass_type=TranslationPass.LITERAL,
            source_language="zh",
            target_language="en",
            segments=inputs,
            glossary_terms=[
                GlossaryTerm(
                    term_id="term_001",
                    project_id="proj_001",
                    source_term="hero",
                    target_term="Lead",
                )
            ],
            locked_names=["Akira"],
            batch_size=2,
            config_version="v1",
        )

        self.assertEqual([[segment.id for segment in batch.segments] for batch in batches], [[1, 2], [3]])
        self.assertNotEqual(batches[0].cache_key, changed_batches[0].cache_key)


class TranslationSchemaTestCase(unittest.TestCase):
    def test_validate_translation_response_accepts_valid_payload(self) -> None:
        batch = build_translation_batches(
            project_id="proj_001",
            pass_type=TranslationPass.LITERAL,
            source_language="zh",
            target_language="en",
            segments=[
                TranslationSegmentInput(id=1, source_text="你好", normalized_source_text="你好"),
                TranslationSegmentInput(id=2, source_text="再见", normalized_source_text="再见"),
            ],
            batch_size=10,
        )[0]

        result = validate_translation_response(
            batch,
            {
                "results": [
                    {"id": 1, "translated_text": "Hello", "confidence": 0.9, "warnings": []},
                    {"id": 2, "translated_text": "Goodbye", "confidence": 0.8, "warnings": []},
                ]
            },
        )

        self.assertEqual([item.translated_text for item in result.results], ["Hello", "Goodbye"])

    def test_validate_translation_response_rejects_missing_or_extra_ids(self) -> None:
        batch = build_translation_batches(
            project_id="proj_001",
            pass_type=TranslationPass.LITERAL,
            source_language="zh",
            target_language="en",
            segments=[
                TranslationSegmentInput(id=1, source_text="你好", normalized_source_text="你好"),
                TranslationSegmentInput(id=2, source_text="再见", normalized_source_text="再见"),
            ],
            batch_size=10,
        )[0]

        with self.assertRaises(TranslationSchemaError):
            validate_translation_response(batch, {"results": [{"id": 1, "translated_text": "Hello"}]})
        with self.assertRaises(TranslationSchemaError):
            validate_translation_response(
                batch,
                {
                    "results": [
                        {"id": 1, "translated_text": "Hello"},
                        {"id": 2, "translated_text": "Goodbye"},
                        {"id": 3, "translated_text": "Unexpected"},
                    ]
                },
            )

    def test_validate_translation_response_rejects_invalid_confidence_and_warnings(self) -> None:
        batch = build_translation_batches(
            project_id="proj_001",
            pass_type=TranslationPass.LITERAL,
            source_language="zh",
            target_language="en",
            segments=[TranslationSegmentInput(id=1, source_text="你好", normalized_source_text="你好")],
            batch_size=10,
        )[0]

        with self.assertRaises(TranslationSchemaError):
            validate_translation_response(
                batch,
                {"results": [{"id": 1, "translated_text": "Hello", "confidence": 2.0, "warnings": []}]},
            )
        with self.assertRaises(TranslationSchemaError):
            validate_translation_response(
                batch,
                {"results": [{"id": 1, "translated_text": "Hello", "warnings": "bad"}]},
            )


class TranslationServiceTestCase(unittest.TestCase):
    def test_translate_pass_retries_transient_failure_and_records_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            _create_imported_project(workspace_root)
            client = ScriptedTranslationClient(
                [
                    TranslationTransientError("temporary failure"),
                    _translation_payload(
                        [
                            "Hello!",
                            "This is the second line.",
                            "The subtitles end here.",
                        ]
                    ),
                ]
            )
            service = TranslationService(
                workspace_root,
                client,
                settings=TranslationSettings(batch_size=10, max_attempts=2),
            )

            results = service.translate_pass("proj_001", TranslationPass.LITERAL)
            repository = ProjectRepository(
                Path(temp_dir) / "projects" / "proj_001" / "project.db"
            )
            batches = repository.list_translation_batches("proj_001", pass_type=TranslationPass.LITERAL)

            self.assertEqual(len(results), 1)
            self.assertEqual(len(client.calls), 2)
            self.assertEqual(repository.list_segments("proj_001")[0].literal_en, "Hello!")
            self.assertEqual(batches[0]["attempt_count"], 2)
            self.assertEqual(batches[0]["status"], "completed")

    def test_translate_pass_uses_cache_without_calling_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            _create_imported_project(workspace_root)

            initial_client = ScriptedTranslationClient(
                [
                    _translation_payload(
                        [
                            "Hello!",
                            "This is the second line.",
                            "The subtitles end here.",
                        ]
                    )
                ]
            )
            service = TranslationService(
                workspace_root,
                initial_client,
                settings=TranslationSettings(batch_size=10, max_attempts=2),
            )
            service.translate_pass("proj_001", TranslationPass.LITERAL)

            repository = ProjectRepository(
                Path(temp_dir) / "projects" / "proj_001" / "project.db"
            )
            segments = repository.list_segments("proj_001")
            for segment in segments:
                segment.literal_en = None
                segment.translation_confidence = None
            repository.replace_segments("proj_001", segments)

            cached_client = ScriptedTranslationClient([])
            cached_service = TranslationService(
                workspace_root,
                cached_client,
                settings=TranslationSettings(batch_size=10, max_attempts=2),
            )
            results = cached_service.translate_pass("proj_001", TranslationPass.LITERAL)
            batches = repository.list_translation_batches("proj_001", pass_type=TranslationPass.LITERAL)

            self.assertEqual(len(results), 1)
            self.assertEqual(len(cached_client.calls), 0)
            self.assertEqual(repository.list_segments("proj_001")[1].literal_en, "This is the second line.")
            self.assertEqual(batches[-1]["status"], "cached")

    def test_translate_pass_with_real_openai_client_and_stubbed_transport(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            _create_imported_project(workspace_root)
            client = OpenAIResponsesTranslationClient(api_key="test-key")
            service = TranslationService(
                workspace_root,
                client,
                settings=TranslationSettings(batch_size=10, max_attempts=2),
            )
            response_payload = {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps(_translation_payload(["Hello!", "This is the second line.", "The subtitles end here."])),
                            }
                        ],
                    }
                ]
            }

            with patch(
                "subtitle_rescue_engine.translation.openai_client.request.urlopen",
                return_value=FakeHTTPResponse(response_payload),
            ):
                service.translate_pass("proj_001", TranslationPass.LITERAL)

            project_root = Path(temp_dir) / "projects" / "proj_001"
            repository = ProjectRepository(project_root / "project.db")

            self.assertEqual(repository.list_segments("proj_001")[0].literal_en, "Hello!")
            self.assertTrue(any(project_root.joinpath("batches", "requests").iterdir()))
            self.assertTrue(any(project_root.joinpath("batches", "responses").iterdir()))
            self.assertTrue(any(project_root.joinpath("batches", "cache").iterdir()))


def _create_imported_project(workspace_root: Path) -> None:
    service = ProjectService(workspace_root)
    service.create_project(
        Project(
            project_id="proj_001",
            name="Movie Subtitle Rescue",
            source_language="zh",
        )
    )
    service.import_subtitle("proj_001", FIXTURES_DIR / "simple.srt", asset_id="asset_001")


def _translation_payload(texts: list[str]) -> dict:
    return {
        "results": [
            {"id": index, "translated_text": text, "confidence": 0.9, "warnings": []}
            for index, text in enumerate(texts, start=1)
        ]
    }


if __name__ == "__main__":
    unittest.main()
