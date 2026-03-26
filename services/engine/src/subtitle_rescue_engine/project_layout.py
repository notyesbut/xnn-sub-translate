from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def _validate_project_id(project_id: str) -> None:
    if not project_id.strip():
        raise ValueError("project_id must not be empty")


@dataclass(frozen=True, slots=True)
class ProjectLayout:
    project_root: Path
    source: Path
    extracted: Path
    ocr: Path
    batches: Path
    batch_requests: Path
    batch_responses: Path
    batch_cache: Path
    exports: Path
    logs: Path
    database: Path

    @classmethod
    def from_workspace(cls, workspace_root: Path, project_id: str) -> "ProjectLayout":
        _validate_project_id(project_id)
        project_root = workspace_root / "projects" / project_id
        return cls(
            project_root=project_root,
            source=project_root / "source",
            extracted=project_root / "extracted",
            ocr=project_root / "ocr",
            batches=project_root / "batches",
            batch_requests=project_root / "batches" / "requests",
            batch_responses=project_root / "batches" / "responses",
            batch_cache=project_root / "batches" / "cache",
            exports=project_root / "exports",
            logs=project_root / "logs",
            database=project_root / "project.db",
        )

    def create(self) -> "ProjectLayout":
        self.project_root.mkdir(parents=True, exist_ok=True)
        self.source.mkdir(parents=True, exist_ok=True)
        self.extracted.mkdir(parents=True, exist_ok=True)
        self.ocr.mkdir(parents=True, exist_ok=True)
        self.batches.mkdir(parents=True, exist_ok=True)
        self.batch_requests.mkdir(parents=True, exist_ok=True)
        self.batch_responses.mkdir(parents=True, exist_ok=True)
        self.batch_cache.mkdir(parents=True, exist_ok=True)
        self.exports.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
        return self

    def as_dict(self) -> dict[str, str]:
        return {
            "project_root": str(self.project_root),
            "source": str(self.source),
            "extracted": str(self.extracted),
            "ocr": str(self.ocr),
            "batches": str(self.batches),
            "batch_requests": str(self.batch_requests),
            "batch_responses": str(self.batch_responses),
            "batch_cache": str(self.batch_cache),
            "exports": str(self.exports),
            "logs": str(self.logs),
            "database": str(self.database),
        }
