# AGENTS.md

## Project Mission

Build a local-first desktop application that helps non-technical users turn foreign subtitles into readable English subtitles for their exact video release, while hiding low-level concepts such as OCR internals, muxing tools, subtitle containers, token accounting, and timing math behind a guided workflow.

## Language Rule

All repository documentation, inline project planning, issue descriptions, code comments, and user-facing strings added in this repository must be written in English. Conversation with the project owner may remain in Russian.

## Current Phase

The project is in foundation and architecture phase.

Active goal:

- bootstrap the monorepo
- implement the text-subtitle MVP first
- lock core contracts and storage decisions before large UI work

Not in immediate scope:

- cloud deployment
- multi-user collaboration
- production-grade OCR for image subtitles
- audio-assisted sync
- mux automation beyond recipe generation

## Product Guardrails

- The product must feel simple to a non-technical user.
- Default UX must hide implementation details such as `ffmpeg`, OCR stages, JSON schemas, subtitle container terms, and model configuration.
- The primary workflow is wizard-driven: Upload, Detect, Translate, Review, Sync, Export.
- Preview before export is a required trust-building surface.

## Architecture Guardrails

- Desktop shell: Tauri + React.
- Processing engine: Python service running locally as a sidecar.
- Storage: project-local SQLite plus artifact folders.
- Boundary rule: frontend talks to the engine through stable local API contracts; core subtitle logic must stay in the engine, not in the UI.
- Keep the system local-first. Do not add mandatory remote infrastructure for MVP.
- OCR and advanced sync must remain separate modules, not mixed into the text subtitle translation path.

## Repository Ownership Map

- `apps/desktop`
  - desktop shell, React screens, UI state, local app bridge
- `services/engine`
  - parsing, translation, QA, sync logic, export logic, storage, job execution
- `packages/contracts`
  - project schema, API DTOs, batch payload contracts, shared types
- `packages/ui`
  - reusable UI components and styling primitives
- `docs`
  - product, architecture, roadmap, testing, and operations docs

## Preferred Delivery Order

1. shared contracts and project storage model
2. text subtitle import and normalization
3. translation batching and OpenAI integration
4. QA flags and `.srt` export
5. minimal desktop flow for import, progress, review, and export
6. manual sync controls
7. glossary management
8. OCR and image subtitle support
9. advanced sync
10. packaging and polish

## Agent Workflow Rules

- Start with the relevant docs before editing code.
- Use parallel scouting for independent read-only questions, then merge conclusions serially.
- Keep edits inside a clear subsystem boundary whenever possible.
- Do not introduce overlapping changes across desktop, engine, and contracts without updating the corresponding docs.
- If a change affects behavior, contracts, or scope, update docs in the same task.
- Prefer small vertical slices that end in a verifiable outcome.

## Editing Rules

- Preserve the simple UX positioning of the product.
- Do not expose low-level technical terminology in primary user-facing flows unless the UI is explicitly in advanced mode.
- Keep model choice configurable rather than hardcoding a specific model family into core logic.
- Avoid premature optimization and avoid building OCR-first. Text subtitle flow is the first release path.
- Keep file and folder names explicit and consistent with the repository structure docs.

## Verification Rules

- New parsing logic must be covered by fixture-based tests.
- Translation logic must support deterministic mocked tests around request building, schema validation, retry behavior, and cache hits.
- Export logic must be verified with golden subtitle outputs.
- UI flows should prefer component and end-to-end coverage once the desktop shell exists.
- If verification cannot be run, note that clearly in the task summary.

## Docs Maintenance Rule

Update the relevant files under `docs/` whenever one of these changes:

- repository structure
- architecture boundaries
- entity schemas
- pipeline stages
- MVP scope
- implementation order

## Definition Of Done

A task is done only when:

- code and docs are aligned
- contracts are updated if needed
- relevant checks or tests were run, or the gap is explicitly stated
- new risks or follow-up work are captured in backlog docs when they materially affect the plan

