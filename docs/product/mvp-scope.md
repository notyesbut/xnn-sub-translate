# MVP Scope

## Release Goal

Deliver a first usable version that lets a non-technical user import a text subtitle file, translate it into English, review flagged lines, optionally apply a simple timing shift, and export an `.srt` file.

## Included In MVP

- project creation and local project persistence
- import for `.srt` and `.ass`
- source language autodetect with manual override
- translation to English using batched API calls
- second-pass natural English polishing
- basic QA flags for readability and consistency
- review table for flagged lines
- manual global offset sync
- `.srt` export

## Deferred After MVP

- `.sup`, `.pgs`, `.sub`, and `.idx` OCR flow
- audio-assisted sync
- anchor-based advanced sync
- `.ass` style-preserving export
- mux automation beyond recipe generation
- cloud storage or hosted processing

## Acceptance Criteria

- A user can create a project from a text subtitle file in under three guided steps.
- The engine can translate a full subtitle file in batches without losing line identity.
- Failed batches can be retried without rerunning the whole job.
- Exported `.srt` files are valid and readable.
- Flagged lines are visible before export.
- The UI does not require the user to understand implementation details.

## Phase Ordering

1. foundation and contracts
2. text subtitle engine
3. minimal desktop workflow
4. QA and glossary improvements
5. OCR support
6. advanced sync
7. packaging and polish

