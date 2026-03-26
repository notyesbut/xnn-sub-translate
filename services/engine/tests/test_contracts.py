import unittest

from subtitle_rescue_engine.contracts import (
    ExportArtifact,
    ExportStatus,
    GlossaryTerm,
    Job,
    JobStatus,
    JobType,
    Project,
    ProjectStatus,
    QAFlag,
    QAFlagSeverity,
    QAFlagStatus,
    SubtitleSegment,
)


class ContractsTestCase(unittest.TestCase):
    def test_project_dump_serializes_status(self) -> None:
        project = Project(
            project_id="proj_001",
            name="Movie Subtitle Rescue",
            source_language="zh",
            status=ProjectStatus.TRANSLATING,
        )

        payload = project.model_dump()

        self.assertEqual(payload["project_id"], "proj_001")
        self.assertEqual(payload["status"], "translating")
        self.assertEqual(payload["target_language"], "en")

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
            format="srt",
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

        self.assertEqual(flag.model_dump()["severity"], "warning")
        self.assertEqual(glossary_term.model_dump()["target_term"], "Senpai")
        self.assertEqual(export.model_dump()["status"], "completed")
        self.assertEqual(job.model_dump()["type"], "qa")


if __name__ == "__main__":
    unittest.main()
