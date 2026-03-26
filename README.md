# Subtitle Rescue

Subtitle Rescue is a local-first desktop application for turning hard-to-find foreign subtitles into usable English subtitles for a specific video release.

The product is aimed at non-technical users who may have a video file, a foreign subtitle file, or both, and need a guided workflow that hides OCR, subtitle internals, container tools, and API complexity behind a simple step-by-step interface.

## Current Status

This repository is in foundation phase.

Completed in this bootstrap:

- public GitHub repository creation
- product and architecture documentation
- initial repository structure for desktop app, engine, and shared contracts
- project-specific agent instructions

Next implementation target:

1. text subtitle import for `.srt` and `.ass`
2. internal project model and SQLite storage
3. batched English translation pipeline
4. `.srt` export
5. minimal desktop review workflow

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

The desktop shell will launch and control the local engine. Project data will be stored locally with SQLite plus project-specific artifact folders.

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

## Working Principles

- Keep the user-facing workflow simple and guided.
- Keep processing local-first for privacy and easier file handling.
- Build the subtitle pipeline before advanced UX and OCR work.
- Add advanced sync and image subtitle support after the text-subtitle MVP is solid.
- Treat docs and contracts as first-class implementation artifacts.

