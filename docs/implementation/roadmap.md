# Implementation Roadmap

## Phase 0: Foundation

Goal:

- create the repository
- lock product direction
- document architecture and delivery order

Deliverables:

- public repository
- repo structure
- core docs and ADR
- agent workflow rules

## Phase 1: Engine MVP For Text Subtitles

Goal:

- working subtitle pipeline without polished UI

Deliverables:

- `.srt` and `.ass` import
- normalization and internal segment model
- SQLite project storage
- translation batching and retry flow
- `.srt` export

## Phase 2: Minimal Desktop Workflow

Goal:

- make the MVP usable by a non-technical user

Deliverables:

- project wizard
- dashboard with job progress
- review table
- export flow

## Phase 3: Quality Layer

Goal:

- improve trust and editability

Deliverables:

- QA flags
- glossary terms
- retry selected lines
- clearer warning cards

## Phase 4: OCR Support

Goal:

- support image-based subtitle inputs

Deliverables:

- subtitle image extraction
- OCR confidence
- fallback and review flow

## Phase 5: Sync Expansion

Goal:

- support more release mismatch cases

Deliverables:

- stretch support
- anchor-based sync
- preview-driven fine tuning

## Phase 6: Product Polish

Goal:

- package the product for real users

Deliverables:

- presets and profiles
- improved editor
- reports
- packaging
- onboarding

