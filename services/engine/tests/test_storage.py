import tempfile
import unittest
from pathlib import Path

from subtitle_rescue_engine.contracts import (
    ExportArtifact,
    ExportStatus,
    Job,
    JobStatus,
    JobType,
    Project,
    ProjectAsset,
    ProjectAssetKind,
    QAFlag,
    QAFlagSeverity,
    SubtitleFormat,
    SubtitleSegment,
)
from subtitle_rescue_engine.storage import ProjectRepository


class ProjectRepositoryTestCase(unittest.TestCase):
    def test_initialize_creates_expected_tables(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = ProjectRepository(Path(temp_dir) / "project.db")

            repository.initialize()

            self.assertEqual(
                repository.list_table_names(),
                [
                    "export_artifacts",
                    "glossary_terms",
                    "jobs",
                    "project_assets",
                    "projects",
                    "qa_flags",
                    "subtitle_segments",
                    "translation_batch_segments",
                    "translation_batches",
                    "translation_cache",
                ],
            )

    def test_round_trip_persists_project_assets_segments_and_exports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "project.db"
            repository = ProjectRepository(database_path)
            repository.initialize()

            repository.upsert_project(
                Project(
                    project_id="proj_001",
                    name="Movie Subtitle Rescue",
                    source_language="zh",
                    source_subtitle_type=SubtitleFormat.SRT,
                )
            )
            repository.upsert_project_asset(
                ProjectAsset(
                    asset_id="asset_001",
                    project_id="proj_001",
                    kind=ProjectAssetKind.SUBTITLE,
                    original_name="simple.srt",
                    stored_path="source/asset_001_simple.srt",
                    checksum="abc123",
                    format=SubtitleFormat.SRT,
                )
            )
            repository.replace_segments(
                "proj_001",
                [
                    SubtitleSegment(
                        id=1,
                        start_ms=1_000,
                        end_ms=3_200,
                        source_text="你好",
                        normalized_source_text="你好",
                        final_en="Hello",
                    ),
                    SubtitleSegment(
                        id=2,
                        start_ms=4_000,
                        end_ms=6_500,
                        source_text="再见",
                        normalized_source_text="再见",
                        final_en="Goodbye",
                    ),
                ],
            )
            repository.upsert_job(
                Job(
                    job_id="job_001",
                    project_id="proj_001",
                    type=JobType.IMPORT,
                    status=JobStatus.COMPLETED,
                    progress=1.0,
                )
            )
            repository.replace_qa_flags(
                "proj_001",
                [
                    QAFlag(
                        flag_id="flag_001",
                        project_id="proj_001",
                        segment_id=2,
                        rule="long_line",
                        severity=QAFlagSeverity.WARNING,
                        message="Line may be too long to read comfortably.",
                    )
                ],
            )
            repository.record_export(
                ExportArtifact(
                    export_id="export_001",
                    project_id="proj_001",
                    format=SubtitleFormat.SRT,
                    path="exports/translated.srt",
                    status=ExportStatus.COMPLETED,
                )
            )

            reopened_repository = ProjectRepository(database_path)

            self.assertEqual(reopened_repository.get_project("proj_001").name, "Movie Subtitle Rescue")
            self.assertEqual(reopened_repository.list_project_assets("proj_001")[0].original_name, "simple.srt")
            self.assertEqual(reopened_repository.list_segments("proj_001")[1].final_en, "Goodbye")
            self.assertEqual(reopened_repository.list_jobs("proj_001")[0].status, JobStatus.COMPLETED)
            self.assertEqual(reopened_repository.list_qa_flags("proj_001")[0].rule, "long_line")
            self.assertEqual(reopened_repository.list_exports("proj_001")[0].path, "exports/translated.srt")


if __name__ == "__main__":
    unittest.main()
