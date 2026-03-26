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

Owns parsing, normalization, detection, translation orchestration, QA rules, sync logic, export generation, job execution, and storage access.

### Shared Contracts

Define project metadata, subtitle segment shape, job status shape, flag shape, and engine request and response payloads. Contracts are the stability point between the app and the engine.

### Local Storage

Each project gets local state with:

- SQLite database for structured metadata
- source and derived files
- batch and request logs
- export artifacts

## Architectural Priorities

- local-first privacy
- reliable batch processing
- restartable jobs
- explicit module boundaries
- future OCR and sync expansion without destabilizing the text pipeline

