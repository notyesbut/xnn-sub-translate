from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

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
    TranslationCacheEntry,
    TranslationPass,
    TranslationSegmentResult,
    utc_now_iso,
)


class ProjectRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(_SCHEMA_SQL)
            connection.execute("PRAGMA user_version = 1")

    def list_table_names(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
        return [row["name"] for row in rows]

    def upsert_project(self, project: Project) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO projects (
                    project_id,
                    name,
                    source_language,
                    target_language,
                    source_subtitle_type,
                    target_video_path,
                    reference_video_path,
                    status,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    name = excluded.name,
                    source_language = excluded.source_language,
                    target_language = excluded.target_language,
                    source_subtitle_type = excluded.source_subtitle_type,
                    target_video_path = excluded.target_video_path,
                    reference_video_path = excluded.reference_video_path,
                    status = excluded.status,
                    created_at = excluded.created_at
                """,
                (
                    project.project_id,
                    project.name,
                    project.source_language,
                    project.target_language,
                    str(project.source_subtitle_type) if project.source_subtitle_type else None,
                    project.target_video_path,
                    project.reference_video_path,
                    str(project.status),
                    project.created_at,
                ),
            )

    def get_project(self, project_id: str) -> Project | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()
        if row is None:
            return None
        return Project(
            project_id=row["project_id"],
            name=row["name"],
            source_language=row["source_language"],
            target_language=row["target_language"],
            source_subtitle_type=SubtitleFormat(row["source_subtitle_type"])
            if row["source_subtitle_type"]
            else None,
            target_video_path=row["target_video_path"],
            reference_video_path=row["reference_video_path"],
            status=ProjectStatus(row["status"]),
            created_at=row["created_at"],
        )

    def upsert_project_asset(self, asset: ProjectAsset) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO project_assets (
                    asset_id,
                    project_id,
                    kind,
                    original_name,
                    stored_path,
                    checksum,
                    format,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    kind = excluded.kind,
                    original_name = excluded.original_name,
                    stored_path = excluded.stored_path,
                    checksum = excluded.checksum,
                    format = excluded.format,
                    created_at = excluded.created_at
                """,
                (
                    asset.asset_id,
                    asset.project_id,
                    str(asset.kind),
                    asset.original_name,
                    asset.stored_path,
                    asset.checksum,
                    str(asset.format) if asset.format else None,
                    asset.created_at,
                ),
            )

    def list_project_assets(self, project_id: str) -> list[ProjectAsset]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM project_assets WHERE project_id = ? ORDER BY created_at, asset_id",
                (project_id,),
            ).fetchall()
        return [
            ProjectAsset(
                asset_id=row["asset_id"],
                project_id=row["project_id"],
                kind=ProjectAssetKind(row["kind"]),
                original_name=row["original_name"],
                stored_path=row["stored_path"],
                checksum=row["checksum"],
                format=SubtitleFormat(row["format"]) if row["format"] else None,
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def replace_segments(self, project_id: str, segments: list[SubtitleSegment]) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM subtitle_segments WHERE project_id = ?", (project_id,))
            connection.executemany(
                """
                INSERT INTO subtitle_segments (
                    project_id,
                    segment_id,
                    ordinal,
                    start_ms,
                    end_ms,
                    source_text,
                    normalized_source_text,
                    literal_en,
                    natural_en,
                    final_en,
                    ocr_confidence,
                    translation_confidence,
                    flags_json,
                    locked
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        project_id,
                        segment.id,
                        ordinal,
                        segment.start_ms,
                        segment.end_ms,
                        segment.source_text,
                        segment.normalized_source_text,
                        segment.literal_en,
                        segment.natural_en,
                        segment.final_en,
                        segment.ocr_confidence,
                        segment.translation_confidence,
                        json.dumps(segment.flags, ensure_ascii=False),
                        int(segment.locked),
                    )
                    for ordinal, segment in enumerate(segments, start=1)
                ],
            )

    def list_segments(self, project_id: str) -> list[SubtitleSegment]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM subtitle_segments
                WHERE project_id = ?
                ORDER BY ordinal, segment_id
                """,
                (project_id,),
            ).fetchall()
        return [
            SubtitleSegment(
                id=row["segment_id"],
                start_ms=row["start_ms"],
                end_ms=row["end_ms"],
                source_text=row["source_text"],
                normalized_source_text=row["normalized_source_text"],
                literal_en=row["literal_en"],
                natural_en=row["natural_en"],
                final_en=row["final_en"],
                ocr_confidence=row["ocr_confidence"],
                translation_confidence=row["translation_confidence"],
                flags=json.loads(row["flags_json"]) if row["flags_json"] else [],
                locked=bool(row["locked"]),
            )
            for row in rows
        ]

    def apply_translation_results(
        self,
        project_id: str,
        pass_type: TranslationPass,
        results: list[TranslationSegmentResult],
    ) -> None:
        segments = self.list_segments(project_id)
        segment_by_id = {segment.id: segment for segment in segments}
        for result in results:
            segment = segment_by_id[result.id]
            if pass_type is TranslationPass.LITERAL:
                segment.literal_en = result.translated_text
            elif pass_type is TranslationPass.NATURAL:
                segment.natural_en = result.translated_text
                segment.final_en = result.translated_text
            else:
                segment.final_en = result.translated_text
            segment.translation_confidence = result.confidence
        self.replace_segments(project_id, segments)

    def upsert_job(self, job: Job) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO jobs (job_id, project_id, type, status, progress, error)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    type = excluded.type,
                    status = excluded.status,
                    progress = excluded.progress,
                    error = excluded.error
                """,
                (
                    job.job_id,
                    job.project_id,
                    str(job.type),
                    str(job.status),
                    job.progress,
                    job.error,
                ),
            )

    def list_jobs(self, project_id: str) -> list[Job]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM jobs WHERE project_id = ? ORDER BY job_id",
                (project_id,),
            ).fetchall()
        return [
            Job(
                job_id=row["job_id"],
                project_id=row["project_id"],
                type=JobType(row["type"]),
                status=JobStatus(row["status"]),
                progress=row["progress"],
                error=row["error"],
            )
            for row in rows
        ]

    def replace_qa_flags(self, project_id: str, flags: list[QAFlag]) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM qa_flags WHERE project_id = ?", (project_id,))
            connection.executemany(
                """
                INSERT INTO qa_flags (flag_id, project_id, segment_id, rule, severity, message, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        flag.flag_id,
                        flag.project_id,
                        flag.segment_id,
                        flag.rule,
                        str(flag.severity),
                        flag.message,
                        str(flag.status),
                    )
                    for flag in flags
                ],
            )

    def list_qa_flags(self, project_id: str) -> list[QAFlag]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM qa_flags WHERE project_id = ? ORDER BY segment_id, flag_id",
                (project_id,),
            ).fetchall()
        return [
            QAFlag(
                flag_id=row["flag_id"],
                project_id=row["project_id"],
                segment_id=row["segment_id"],
                rule=row["rule"],
                severity=QAFlagSeverity(row["severity"]),
                message=row["message"],
                status=QAFlagStatus(row["status"]),
            )
            for row in rows
        ]

    def replace_glossary_terms(self, project_id: str, terms: list[GlossaryTerm]) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM glossary_terms WHERE project_id = ?", (project_id,))
            connection.executemany(
                """
                INSERT INTO glossary_terms (term_id, project_id, source_term, target_term, notes, locked)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        term.term_id,
                        term.project_id,
                        term.source_term,
                        term.target_term,
                        term.notes,
                        int(term.locked),
                    )
                    for term in terms
                ],
            )

    def list_glossary_terms(self, project_id: str) -> list[GlossaryTerm]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM glossary_terms WHERE project_id = ? ORDER BY term_id",
                (project_id,),
            ).fetchall()
        return [
            GlossaryTerm(
                term_id=row["term_id"],
                project_id=row["project_id"],
                source_term=row["source_term"],
                target_term=row["target_term"],
                notes=row["notes"],
                locked=bool(row["locked"]),
            )
            for row in rows
        ]

    def record_translation_batch(
        self,
        batch: TranslationBatch,
        *,
        ordinal: int,
        request_path: str | None = None,
        response_path: str | None = None,
        error: str | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        created_timestamp = created_at or utc_now_iso()
        updated_timestamp = updated_at or created_timestamp
        content_hash = batch.cache_key or batch.batch_id
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO translation_batches (
                    batch_id,
                    project_id,
                    pass_type,
                    ordinal,
                    content_hash,
                    status,
                    attempt_count,
                    request_path,
                    response_path,
                    error,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(batch_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    pass_type = excluded.pass_type,
                    ordinal = excluded.ordinal,
                    content_hash = excluded.content_hash,
                    status = excluded.status,
                    attempt_count = excluded.attempt_count,
                    request_path = excluded.request_path,
                    response_path = excluded.response_path,
                    error = excluded.error,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at
                """,
                (
                    batch.batch_id,
                    batch.project_id,
                    str(batch.pass_type),
                    ordinal,
                    content_hash,
                    str(batch.status),
                    batch.attempt_count,
                    request_path,
                    response_path,
                    error,
                    created_timestamp,
                    updated_timestamp,
                ),
            )
            connection.execute(
                "DELETE FROM translation_batch_segments WHERE batch_id = ?",
                (batch.batch_id,),
            )
            connection.executemany(
                """
                INSERT INTO translation_batch_segments (batch_id, segment_id, ordinal)
                VALUES (?, ?, ?)
                """,
                [
                    (batch.batch_id, segment.id, ordinal)
                    for ordinal, segment in enumerate(batch.segments, start=1)
                ],
            )

    def list_translation_batches(
        self,
        project_id: str,
        *,
        pass_type: TranslationPass | None = None,
    ) -> list[dict[str, Any]]:
        if pass_type is None:
            query = """
                SELECT *
                FROM translation_batches
                WHERE project_id = ?
                ORDER BY pass_type, ordinal, batch_id
            """
            parameters = (project_id,)
        else:
            query = """
                SELECT *
                FROM translation_batches
                WHERE project_id = ? AND pass_type = ?
                ORDER BY ordinal, batch_id
            """
            parameters = (project_id, str(pass_type))

        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
            segment_rows = connection.execute(
                """
                SELECT batch_id, segment_id
                FROM translation_batch_segments
                WHERE batch_id IN (
                    SELECT batch_id FROM translation_batches WHERE project_id = ?
                )
                ORDER BY batch_id, ordinal
                """,
                (project_id,),
            ).fetchall()

        segment_ids_by_batch: dict[str, list[int]] = {}
        for row in segment_rows:
            segment_ids_by_batch.setdefault(row["batch_id"], []).append(row["segment_id"])

        return [
            {
                "batch_id": row["batch_id"],
                "project_id": row["project_id"],
                "pass_type": row["pass_type"],
                "ordinal": row["ordinal"],
                "content_hash": row["content_hash"],
                "status": row["status"],
                "attempt_count": row["attempt_count"],
                "request_path": row["request_path"],
                "response_path": row["response_path"],
                "error": row["error"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "segment_ids": segment_ids_by_batch.get(row["batch_id"], []),
            }
            for row in rows
        ]

    def get_translation_cache(
        self,
        cache_key: str,
        *,
        pass_type: TranslationPass,
    ) -> TranslationCacheEntry | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM translation_cache
                WHERE cache_key = ? AND pass_type = ?
                """,
                (cache_key, str(pass_type)),
            ).fetchone()
        if row is None:
            return None
        return TranslationCacheEntry(
            cache_key=row["cache_key"],
            pass_type=TranslationPass(row["pass_type"]),
            source_hash=row["source_hash"],
            response_payload=json.loads(row["response_payload"]),
            created_at=row["created_at"],
        )

    def upsert_translation_cache(self, entry: TranslationCacheEntry) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO translation_cache (
                    cache_key,
                    pass_type,
                    source_hash,
                    response_payload,
                    created_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    pass_type = excluded.pass_type,
                    source_hash = excluded.source_hash,
                    response_payload = excluded.response_payload,
                    created_at = excluded.created_at
                """,
                (
                    entry.cache_key,
                    str(entry.pass_type),
                    entry.source_hash,
                    json.dumps(entry.response_payload, ensure_ascii=False),
                    entry.created_at,
                ),
            )

    def record_export(self, export: ExportArtifact) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO export_artifacts (export_id, project_id, format, path, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(export_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    format = excluded.format,
                    path = excluded.path,
                    status = excluded.status,
                    created_at = excluded.created_at
                """,
                (
                    export.export_id,
                    export.project_id,
                    str(export.format),
                    export.path,
                    str(export.status),
                    export.created_at,
                ),
            )

    def list_exports(self, project_id: str) -> list[ExportArtifact]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM export_artifacts WHERE project_id = ? ORDER BY created_at, export_id",
                (project_id,),
            ).fetchall()
        return [
            ExportArtifact(
                export_id=row["export_id"],
                project_id=row["project_id"],
                format=SubtitleFormat(row["format"]),
                path=row["path"],
                status=ExportStatus(row["status"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source_language TEXT NOT NULL,
    target_language TEXT NOT NULL,
    source_subtitle_type TEXT,
    target_video_path TEXT,
    reference_video_path TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_assets (
    asset_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    original_name TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    checksum TEXT NOT NULL,
    format TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS subtitle_segments (
    project_id TEXT NOT NULL,
    segment_id INTEGER NOT NULL,
    ordinal INTEGER NOT NULL,
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL,
    source_text TEXT NOT NULL,
    normalized_source_text TEXT,
    literal_en TEXT,
    natural_en TEXT,
    final_en TEXT,
    ocr_confidence REAL,
    translation_confidence REAL,
    flags_json TEXT NOT NULL DEFAULT '[]',
    locked INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (project_id, segment_id),
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    progress REAL NOT NULL,
    error TEXT,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS qa_flags (
    flag_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    segment_id INTEGER NOT NULL,
    rule TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(project_id, segment_id) REFERENCES subtitle_segments(project_id, segment_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS glossary_terms (
    term_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_term TEXT NOT NULL,
    target_term TEXT NOT NULL,
    notes TEXT,
    locked INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS translation_batches (
    batch_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    pass_type TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    request_path TEXT,
    response_path TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS translation_batch_segments (
    batch_id TEXT NOT NULL,
    segment_id INTEGER NOT NULL,
    ordinal INTEGER NOT NULL,
    PRIMARY KEY (batch_id, segment_id),
    FOREIGN KEY(batch_id) REFERENCES translation_batches(batch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS translation_cache (
    cache_key TEXT PRIMARY KEY,
    pass_type TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    response_payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS export_artifacts (
    export_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    format TEXT NOT NULL,
    path TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
"""
