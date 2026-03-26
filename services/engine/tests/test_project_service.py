import tempfile
import unittest
from pathlib import Path

from subtitle_rescue_engine.contracts import Project
from subtitle_rescue_engine.project_service import ProjectService
from subtitle_rescue_engine.storage import ProjectRepository
from subtitle_rescue_engine.translation import TranslationSettings

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "subtitles"


class ScriptedTranslationClient:
    def __init__(self, responses: list[dict]) -> None:
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
        return self.responses.pop(0)


class ProjectServiceTestCase(unittest.TestCase):
    def test_create_translate_flag_and_export_vertical_slice(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            service = ProjectService(workspace_root)
            project = Project(
                project_id="proj_001",
                name="Movie Subtitle Rescue",
                source_language="zh",
            )

            layout = service.create_project(project)
            import_result = service.import_subtitle(
                "proj_001",
                FIXTURES_DIR / "simple.srt",
                asset_id="asset_001",
            )
            client = ScriptedTranslationClient(
                [
                    _translation_payload(
                        [
                            "Hello!",
                            "This is the second line.",
                            "The subtitles end here.",
                        ]
                    ),
                    _translation_payload(
                        [
                            "Hello!\nWelcome to the film.",
                            "This is the second line.",
                            "The subtitles end here.",
                        ],
                        confidences=[0.93, 0.61, 0.95],
                    ),
                ]
            )

            results = service.translate_project(
                "proj_001",
                client,
                settings=TranslationSettings(batch_size=10, max_attempts=2),
            )
            flags = service.run_qa("proj_001")
            artifact = service.export_project_srt("proj_001", export_id="export_001")

            repository = ProjectRepository(layout.database)
            exported_text = (layout.project_root / artifact.path).read_text(encoding="utf-8")
            expected_text = (FIXTURES_DIR / "export_expected.srt").read_text(encoding="utf-8")

            self.assertEqual(import_result.format.value, "srt")
            self.assertEqual(len(results), 2)
            self.assertEqual(len(client.calls), 2)
            self.assertTrue((layout.source / "asset_001_simple.srt").exists())
            self.assertTrue((layout.extracted / "segments.json").exists())
            self.assertEqual(exported_text, expected_text)
            self.assertEqual(repository.list_exports("proj_001")[0].path, "exports/translated.srt")
            self.assertIn("low_translation_confidence", [flag.rule for flag in flags])
            self.assertEqual(repository.get_project("proj_001").status.value, "export_ready")


def _translation_payload(texts: list[str], confidences: list[float] | None = None) -> dict:
    confidence_values = confidences or [0.9] * len(texts)
    return {
        "results": [
            {
                "id": index,
                "translated_text": text,
                "confidence": confidence_values[index - 1],
                "warnings": [],
            }
            for index, text in enumerate(texts, start=1)
        ]
    }


if __name__ == "__main__":
    unittest.main()
