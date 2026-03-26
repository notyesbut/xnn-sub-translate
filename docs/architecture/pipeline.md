# Processing Pipeline

## End-To-End Stages

### 1. Import

Input can be:

- subtitle file
- video file
- subtitle folder
- optional reference video
- optional glossary

The import step copies or links source assets into the local project workspace and records metadata.

### 2. Detect

The system determines:

- subtitle type: text or image
- probable language
- encoding and formatting traits
- obvious quality flags

### 3. Extract

- text subtitles are parsed into normalized events
- image subtitles are converted into OCR-ready image events

### 4. Cleanup

The engine removes duplicate noise, stabilizes formatting, normalizes line breaks, and prepares segments for translation.

### 5. Batch

Segments are grouped into stable translation batches with preserved line IDs and enough local context for better quality.

### 6. Translate

The translation path uses staged passes:

- literal meaning-preserving draft
- natural subtitle English rewrite
- QA and repair only for flagged entries

### 7. Review And QA

Rule-based checks and consistency passes identify risky lines for user review.

### 8. Sync

The MVP begins with global offset and later expands to stretch, anchors, and audio-assisted alignment.

### 9. Export

Outputs include:

- `.srt`
- later `.ass`
- project save data
- optional mux recipe

## Failure Handling

- failed batches must be isolated and retryable
- malformed source lines must not crash the whole project
- low-confidence OCR segments must be routed to fallback or review
- export should remain possible even if some flags remain unresolved

