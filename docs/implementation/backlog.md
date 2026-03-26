# Initial Backlog

## Completed P0 Work

- defined project, segment, asset, translation batch, QA flag, glossary term, and export contracts
- defined the project folder layout and artifact directories
- implemented the SQLite schema for MVP entities
- implemented `.srt` and `.ass` text subtitle parsing with normalization
- preserved source timing and line identity through fixture-backed tests
- implemented translation batch building, schema validation, retry behavior, cache persistence, and batch logs
- implemented basic QA flag generation and `.srt` export with persisted export metadata

## Open P0 Work

- verify the live OpenAI translation path with configured credentials and tune prompts/models
- add source language autodetect with manual override support
- expose the engine workflow through stable desktop-facing API endpoints or commands

## P1: Desktop Shell

- scaffold Tauri + React app
- implement new project wizard
- show job progress and warnings
- add review table and export actions

## P1: QA Layer

- expose flag filters in the review UI
- support lock and accept actions
- expand QA beyond the initial readability and translation-safety rules

## P2: Glossary

- persist glossary terms per project in the desktop workflow
- apply glossary terms during translation and repair in a real provider flow
- add basic glossary UI

## P2: Sync

- implement global offset
- implement stretch
- add preview-assisted timing adjustments

## P3: OCR

- add subtitle image extraction
- add OCR confidence scoring
- add fallback repair queue
