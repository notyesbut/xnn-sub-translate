import unittest

from subtitle_rescue_engine.contracts import (
    ExportArtifact,
    ExportStatus,
    GlossaryTerm,
    Job,
    JobStatus,
    JobType,
    Project,
    ProjectAsset,
    ProjectAssetKind,
    ProjectStatus,
    QAFlag,
    QAFlagSeverity,
    QAFlagStatus,
    SubtitleFormat,
    SubtitleSegment,
    TranslationBatch,
    TranslationBatchResult,
    TranslationPass,
    TranslationSegmentInput,
    TranslationSegmentResult,
)


class ContractsTestCase(unittest.TestCase):
    def test_project_dump_serializes_status_and_subtitle_format(self) -> None:
        project = Project(
            project_id="proj_001",
            name="Movie Subtitle Rescue",
            source_language="zh",
            source_subtitle_type=SubtitleFormat.SRT,
            status=ProjectStatus.TRANSLATING,
        )

        payload = project.model_dump()

        self.assertEqual(payload["project_id"], "proj_001")
        self.assertEqual(payload["status"], "translating")
        self.assertEqual(payload["target_language"], "en")
        self.assertEqual(payload["source_subtitle_type"], "srt")

    def test_segment_rejects_inverted_timing(self) -> None:
        with self.assertRaises(ValueError):
            SubtitleSegment(
                id=1,
                start_ms=4000,
                end_ms=3999,
                source_text="test",
            )

    def test_job_progress_is_bounded(self) -> None:
        with self.assertRaises(ValueError):
            Job(
                job_id="job_translate_001",
                project_id="proj_001",
                type=JobType.TRANSLATION,
                progress=1.1,
            )

    def test_additional_entities_dump_cleanly(self) -> None:
        asset = ProjectAsset(
            asset_id="asset_001",
            project_id="proj_001",
            kind=ProjectAssetKind.SUBTITLE,
            original_name="simple.srt",
            stored_path="source/simple.srt",
            checksum="abc123",
            format=SubtitleFormat.SRT,
        )
        flag = QAFlag(
            flag_id="flag_001",
            project_id="proj_001",
            segment_id=14,
            rule="long_line",
            severity=QAFlagSeverity.WARNING,
            message="Line may be too long to read comfortably.",
            status=QAFlagStatus.OPEN,
        )
        glossary_term = GlossaryTerm(
            term_id="term_001",
            project_id="proj_001",
            source_term="senpai",
            target_term="Senpai",
        )
        export = ExportArtifact(
            export_id="export_001",
            project_id="proj_001",
            format=SubtitleFormat.SRT,
            path="/tmp/out.srt",
            status=ExportStatus.COMPLETED,
        )
        job = Job(
            job_id="job_qa_001",
            project_id="proj_001",
            type=JobType.QA,
            status=JobStatus.RUNNING,
            progress=0.5,
        )

        self.assertEqual(asset.model_dump()["kind"], "subtitle")
        self.assertEqual(flag.model_dump()["severity"], "warning")
        self.assertEqual(glossary_term.model_dump()["target_term"], "Senpai")
        self.assertEqual(export.model_dump()["status"], "completed")
        self.assertEqual(job.model_dump()["type"], "qa")

    def test_translation_entities_dump_cleanly(self) -> None:
        batch = TranslationBatch(
            batch_id="batch_001",
            project_id="proj_001",
            pass_type=TranslationPass.LITERAL,
            source_language="zh",
            target_language="en",
            segments=[
                TranslationSegmentInput(
                    id=1,
                    source_text="你好",
                    normalized_source_text="你好",
                )
            ],
        )
        result = TranslationBatchResult(
            batch_id="batch_001",
            pass_type=TranslationPass.LITERAL,
            results=[
                TranslationSegmentResult(
                    id=1,
                    translated_text="Hello",
                    confidence=0.91,
                    warnings=["locked_name"],
                )
            ],
        )

        self.assertEqual(batch.model_dump()["pass_type"], "literal")
        self.assertEqual(result.model_dump()["results"][0]["warnings"], ["locked_name"])


if __name__ == "__main__":
    unittest.main()
