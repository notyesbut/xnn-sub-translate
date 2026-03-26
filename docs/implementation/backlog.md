# Initial Backlog

## P0: Contracts And Storage

- define project, segment, job, QA flag, glossary term, and export contracts
- define project folder layout
- design SQLite schema for MVP entities
- decide where batch cache and request logs live

## P0: Engine Parsing

- add text subtitle parsing for `.srt` and `.ass`
- normalize encoding and line breaks
- preserve source timing and line identity
- create fixture-based tests for parse and export round-trips

## P0: Translation Pipeline

- design batch builder
- implement schema-validated translation responses
- add retry and caching behavior
- implement literal pass and natural English pass
- persist batch metadata and failures

## P0: Export

- generate valid `.srt` output
- carry forward final English text and adjusted timing
- store export metadata and output paths

## P1: Desktop Shell

- scaffold Tauri + React app
- implement new project wizard
- show job progress and warnings
- add review table and export actions

## P1: QA Layer

- add flags for line length, CPS, timing, overlap, and untranslated fragments
- expose flag filters in review UI
- support lock and accept actions

## P2: Glossary

- persist glossary terms per project
- apply glossary terms during translation and repair
- add basic glossary UI

## P2: Sync

- implement global offset
- implement stretch
- add preview-assisted timing adjustments

## P3: OCR

- add subtitle image extraction
- add OCR confidence scoring
- add fallback repair queue

