import tempfile
import unittest
from pathlib import Path

from subtitle_rescue_engine.project_layout import ProjectLayout


class ProjectLayoutTestCase(unittest.TestCase):
    def test_create_materializes_expected_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            layout = ProjectLayout.from_workspace(workspace_root, "proj_001").create()

            self.assertTrue(layout.project_root.exists())
            self.assertTrue(layout.source.exists())
            self.assertTrue(layout.extracted.exists())
            self.assertTrue(layout.ocr.exists())
            self.assertTrue(layout.batches.exists())
            self.assertTrue(layout.batch_requests.exists())
            self.assertTrue(layout.batch_responses.exists())
            self.assertTrue(layout.batch_cache.exists())
            self.assertTrue(layout.exports.exists())
            self.assertTrue(layout.logs.exists())
            self.assertEqual(layout.database.name, "project.db")

    def test_from_workspace_requires_non_empty_project_id(self) -> None:
        with self.assertRaises(ValueError):
            ProjectLayout.from_workspace(Path("/tmp"), "")


if __name__ == "__main__":
    unittest.main()
