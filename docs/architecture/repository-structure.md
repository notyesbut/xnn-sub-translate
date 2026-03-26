# Repository Structure

## Top-Level Layout

```text
apps/
  desktop/        # Tauri + React application
services/
  engine/         # Python subtitle processing engine
packages/
  contracts/      # Shared schemas and DTOs
  ui/             # Shared UI primitives
docs/
  product/        # Vision and scope
  architecture/   # System design
  implementation/ # Roadmap, backlog, testing
  operations/     # Local setup and decisions
  glossary/       # Domain vocabulary
  adr/            # Architecture decision records
```

## Ownership Rules

- UI and desktop packaging concerns stay under `apps/desktop`.
- Subtitle-domain logic stays under `services/engine`.
- Shared payload and persistence contracts stay under `packages/contracts`.
- Cross-cutting documentation stays under `docs`.

## Why A Monorepo

- The desktop app and engine are separate runtimes.
- Shared contracts need a stable location.
- Future agent work can be assigned safely by directory.
- The project will benefit from vertical slices that touch UI, engine, and contracts in one repository.

