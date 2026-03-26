# Local Development

## Current Status

The repository is currently documentation-first. Application scaffolding and runtime commands will be added in the next implementation phase.

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

## Expected Future Commands

These will be finalized once scaffolding lands:

- install desktop dependencies
- create Python virtual environment
- run desktop dev mode
- run engine tests
- run full project verification

## Local Asset Policy

Large media files and project exports should remain out of git. Use fixture-sized samples for automated testing and keep local project outputs in ignored directories.

