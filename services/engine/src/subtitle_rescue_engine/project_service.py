from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from subtitle_rescue_engine.contracts import (
    ExportArtifact,
    ExportStatus,
    Project,
    ProjectAsset,
    ProjectAssetKind,
    QAFlag,
    SubtitleFormat,
    TranslationBatchResult,
)
from subtitle_rescue_engine.project_layout import ProjectLayout
from subtitle_rescue_engine.qa import QAService
from subtitle_rescue_engine.storage import ProjectRepository
from subtitle_rescue_engine.subtitles import SubtitleImportResult, import_subtitle_file, write_srt_file
from subtitle_rescue_engine.translation import TranslationClient, TranslationService, TranslationSettings


class ProjectService:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = Path(workspace_root)

    def create_project(self, project: Project) -> ProjectLayout:
        layout = ProjectLayout.from_workspace(self.workspace_root, project.project_id).create()
        repository = ProjectRepository(layout.database)
        repository.initialize()
        repository.upsert_project(project)
        return layout

    def import_subtitle(
        self,
        project_id: str,
        subtitle_path: Path,
        *,
        asset_id: str | None = None,
    ) -> SubtitleImportResult:
        layout = ProjectLayout.from_workspace(self.workspace_root, project_id).create()
        repository = ProjectRepository(layout.database)
        repository.initialize()

        project = repository.get_project(project_id)
        if project is None:
            raise KeyError(f"Unknown project: {project_id}")

        import_result = import_subtitle_file(subtitle_path)
        stored_asset_id = asset_id or uuid4().hex
        stored_file_name = f"{stored_asset_id}_{subtitle_path.name}"
        stored_file_path = layout.source / stored_file_name
        shutil.copy2(subtitle_path, stored_file_path)

        repository.upsert_project(
            replace(
                project,
                source_subtitle_type=import_result.format,
            )
        )
        repository.upsert_project_asset(
            ProjectAsset(
                asset_id=stored_asset_id,
                project_id=project_id,
                kind=ProjectAssetKind.SUBTITLE,
                original_name=subtitle_path.name,
                stored_path=str(stored_file_path.relative_to(layout.project_root)),
                checksum=_file_sha256(stored_file_path),
                format=import_result.format,
            )
        )
        repository.replace_segments(project_id, import_result.segments)

        snapshot_path = layout.extracted / "segments.json"
        snapshot_payload = {
            "project_id": project_id,
            "format": str(import_result.format),
            "encoding": import_result.encoding,
            "segments": [segment.model_dump() for segment in import_result.segments],
        }
        snapshot_path.write_text(
            json.dumps(snapshot_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        return import_result

    def translate_project(
        self,
        project_id: str,
        client: TranslationClient,
        *,
        settings: TranslationSettings | None = None,
        locked_names: list[str] | None = None,
    ) -> list[TranslationBatchResult]:
        translation_service = TranslationService(
            self.workspace_root,
            client,
            settings=settings,
        )
        return translation_service.translate_project(project_id, locked_names=locked_names)

    def run_qa(self, project_id: str) -> list[QAFlag]:
        return QAService(self.workspace_root).run(project_id)

    def export_project_srt(
        self,
        project_id: str,
        *,
        export_id: str | None = None,
        file_name: str = "translated.srt",
    ) -> ExportArtifact:
        layout = ProjectLayout.from_workspace(self.workspace_root, project_id).create()
        repository = ProjectRepository(layout.database)
        repository.initialize()

        project = repository.get_project(project_id)
        if project is None:
            raise KeyError(f"Unknown project: {project_id}")

        segments = repository.list_segments(project_id)
        if not segments:
            raise ValueError(f"Project {project_id} does not contain any subtitle segments")

        export_path = layout.exports / file_name
        write_srt_file(export_path, segments)

        artifact = ExportArtifact(
            export_id=export_id or uuid4().hex,
            project_id=project_id,
            format=SubtitleFormat.SRT,
            path=str(export_path.relative_to(layout.project_root)),
            status=ExportStatus.COMPLETED,
        )
        repository.record_export(artifact)
        return artifact


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()
