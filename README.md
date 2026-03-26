# Subtitle Rescue

Subtitle Rescue is a local-first desktop application for turning hard-to-find foreign subtitles into usable English subtitles for a specific video release.

The product is aimed at non-technical users who may have a video file, a foreign subtitle file, or both, and need a guided workflow that hides OCR, subtitle internals, container tools, and API complexity behind a simple step-by-step interface.

## Current Status

This repository now has a real engine-side MVP slice instead of bootstrap-only scaffolding.

Implemented so far:

- `.srt` and `.ass` subtitle import
- subtitle normalization into stable segment contracts
- project-local SQLite persistence plus artifact folders
- translation batching, strict response validation, retry, and cache orchestration
- OpenAI Responses API translation client adapter
- basic QA flag generation for review
- `.srt` export
- fixture-backed engine tests for parsing, persistence, translation orchestration, QA, and export

Next implementation target:

1. verify the live OpenAI translation path with configured credentials
2. expose the workflow through the minimal desktop shell
3. add source language detect/manual override and review UI

## Product Promise

The application should let users:

1. upload subtitles or video
2. detect subtitle type and source language
3. translate into English
4. review flagged lines
5. retime subtitles when needed
6. export usable subtitle files

The primary UX goal is simplicity. Users should see clear steps and friendly warnings, not low-level media tooling concepts.

## Chosen MVP Architecture

- `apps/desktop`: Tauri + React desktop shell
- `services/engine`: local Python processing engine
- `packages/contracts`: shared project and job contracts
- `packages/ui`: reusable desktop UI components
- `docs`: product, architecture, implementation, and operations documentation

The desktop shell will launch and control the local engine. Project data is stored locally with SQLite plus project-specific artifact folders.

Implemented engine project layout:

- `source/`: copied original inputs
- `extracted/segments.json`: normalized subtitle snapshot
- `batches/requests`: serialized translation requests
- `batches/responses`: serialized translation responses
- `batches/cache`: validated cached translation payloads
- `exports/`: exported subtitle files
- `logs/`: engine and job logs
- `project.db`: SQLite project database

## Repository Layout

```text
apps/
  desktop/
services/
  engine/
packages/
  contracts/
  ui/
docs/
  adr/
  architecture/
  glossary/
  implementation/
  operations/
  product/
```

## Key Documents

- [Project Agent Rules](./AGENTS.md)
- [Product Vision](./docs/product/vision.md)
- [MVP Scope](./docs/product/mvp-scope.md)
- [Architecture Overview](./docs/architecture/overview.md)
- [Implementation Roadmap](./docs/implementation/roadmap.md)
- [Agent Workflows](./docs/implementation/agent-workflows.md)

## Current Verification Commands

- `pnpm docs:list`
- `pnpm engine:test`
- `pnpm engine:compile`

## Working Principles

- Keep the user-facing workflow simple and guided.
- Keep processing local-first for privacy and easier file handling.
- Build the subtitle pipeline before advanced UX and OCR work.
- Add advanced sync and image subtitle support after the text-subtitle MVP is solid.
- Treat docs and contracts as first-class implementation artifacts.
