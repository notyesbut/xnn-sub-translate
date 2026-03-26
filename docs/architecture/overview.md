# Architecture Overview

## System Summary

Subtitle Rescue is designed as a local-first desktop application with a clear split between the desktop user experience and the subtitle-processing engine.

Core layers:

- desktop shell: Tauri + React
- local engine: Python sidecar service
- shared contracts: project schema and API DTOs
- local storage: SQLite and project artifact folders

## High-Level Flow

```text
User Input
  -> Desktop UI
  -> Local App Bridge
  -> Python Engine API
  -> Subtitle Pipeline
  -> SQLite + Project Files
  -> Review + Export
```

## Major Components

### Desktop Shell

Owns screens, navigation, view models, video preview, and user interaction. It should remain thin and treat the engine as the source of truth for subtitle processing state.

### Python Engine

Owns parsing, normalization, translation orchestration, QA rules, sync logic, export generation, job execution, and storage access.

Implemented engine modules now cover:

- text subtitle import for `.srt` and `.ass`
- subtitle normalization
- project creation/import/export orchestration
- translation batching with strict schema validation, retry, and cache
- OpenAI Responses API provider adaptation
- basic QA flag generation

Still pending inside the engine:

- source language autodetect
- live provider verification with credentials and prompt tuning
- sync controls beyond the persistence-ready structure

### Shared Contracts

Define project metadata, subtitle segment shape, project asset shape, job status shape, QA flag shape, translation batch contracts, and engine request and response payloads. Contracts are the stability point between the app and the engine.

### Local Storage

Each project gets local state with:

- SQLite database for structured metadata
- copied source files
- normalized extracted artifacts
- translation batch request/response/cache files
- exported subtitle artifacts

Current project layout under each `projects/<project_id>/` workspace:

- `source/`
- `extracted/segments.json`
- `ocr/`
- `batches/requests/`
- `batches/responses/`
- `batches/cache/`
- `exports/`
- `logs/`
- `project.db`

Current SQLite entities:

- `projects`
- `project_assets`
- `subtitle_segments`
- `jobs`
- `qa_flags`
- `glossary_terms`
- `translation_batches`
- `translation_batch_segments`
- `translation_cache`
- `export_artifacts`

## Architectural Priorities

- local-first privacy
- reliable batch processing
- restartable jobs
- explicit module boundaries
- future OCR and sync expansion without destabilizing the text pipeline
