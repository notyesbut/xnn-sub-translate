# Local Development

## Current Status

The repository now includes:

- product and architecture docs
- a root workspace bootstrap
- a first Python engine package with core domain contracts
- project layout helpers and unit tests

## Planned Tooling

- Node.js for the desktop app toolchain
- Rust for Tauri packaging
- Python 3.12+ for the engine
- SQLite for local project storage
- `ffmpeg` and `ffprobe` for media inspection
- Tesseract later for OCR

## Development Conventions

- keep docs and code comments in English
- keep user-facing terminology simple
- prefer local fixtures over brittle remote dependencies
- keep MVP development focused on text subtitle flow first

## Current Commands

- `pnpm docs:list`
- `pnpm engine:test`
- `pnpm engine:compile`

## Expected Future Commands

These will expand once more scaffolding lands:

- install desktop dependencies
- run desktop dev mode
- run engine integration tests
- run full project verification

## Local Asset Policy

Large media files and project exports should remain out of git. Use fixture-sized samples for automated testing and keep local project outputs in ignored directories.
