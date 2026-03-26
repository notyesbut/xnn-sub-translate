# ADR-0001: Monorepo And MVP Stack

## Status

Accepted

## Context

The product needs:

- a desktop user experience for local files and previews
- a strong subtitle-processing backend
- a stable contract boundary between the UI and the engine
- room to grow into OCR and sync features without a future rewrite

## Decision

Use a lightweight monorepo with:

- Tauri + React in `apps/desktop`
- a local Python engine in `services/engine`
- shared schemas and DTOs in `packages/contracts`
- optional shared UI building blocks in `packages/ui`
- project-local SQLite storage and artifact folders

## Rationale

- Tauri is well suited to a desktop-first, local-file-heavy workflow.
- Python is a strong fit for subtitle processing, parsing, OCR tooling, and pipeline orchestration.
- Shared contracts reduce coupling and make app-engine integration explicit.
- A monorepo supports coordinated delivery across UI, engine, docs, and contracts.

## Consequences

Positive:

- clean ownership boundaries
- easier vertical slices
- simpler future OCR and sync expansion

Trade-offs:

- two runtime stacks must be managed
- packaging the Python sidecar will need explicit attention later

