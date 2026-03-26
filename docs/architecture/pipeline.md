# Processing Pipeline

## End-To-End Stages

### 1. Import

Input can be:

- subtitle file
- video file
- subtitle folder
- optional reference video
- optional glossary

The current text-subtitle import flow:

- creates the project workspace if needed
- copies the original subtitle file into `source/`
- computes a checksum and records a `project_assets` row
- parses `.srt` or `.ass` into normalized `SubtitleSegment` rows
- writes a normalized snapshot to `extracted/segments.json`

### 2. Detect

The system determines:

- subtitle type: text or image
- probable language
- encoding and formatting traits
- obvious quality flags

Current implementation status:

- subtitle type is inferred from the imported file extension
- encoding is normalized during text decoding
- language autodetect is still pending

### 3. Extract

- text subtitles are parsed into normalized events and persisted into SQLite
- image subtitles are converted into OCR-ready image events later

### 4. Cleanup

The current engine:

- stabilizes formatting
- removes ASS style tags from visible text
- normalizes line breaks
- prepares segments for translation batches

### 5. Batch

Segments are grouped into stable translation batches with:

- preserved line IDs
- neighboring context
- glossary terms and locked names
- a stable cache key for replay-safe retries

### 6. Translate

The translation path uses staged passes:

- literal meaning-preserving draft
- natural subtitle English rewrite
- QA and repair only for flagged entries later

Current implementation status:

- literal and natural passes are implemented through a provider abstraction
- an OpenAI Responses API client is implemented behind that abstraction
- each batch is schema-validated before segment updates are persisted
- successful batches are cached by stable content hash
- failed batches are retryable without rerunning completed batches
- live credential verification is still pending

### 7. Review And QA

Rule-based checks and consistency passes identify risky lines for user review.

Current implemented QA rules:

- missing translation
- source text leak
- low translation confidence
- long line
- high reading speed
- timing overlap

### 8. Sync

The MVP begins with global offset and later expands to stretch, anchors, and audio-assisted alignment.

### 9. Export

Outputs include:

- `.srt`
- later `.ass`
- project save data
- optional mux recipe

Current `.srt` export text selection order:

1. `final_en`
2. `natural_en`
3. `literal_en`
4. `normalized_source_text`
5. `source_text`

## Failure Handling

- failed batches must be isolated and retryable
- malformed source lines must not crash the whole project
- low-confidence OCR segments must be routed to fallback or review later
- export should remain possible even if some flags remain unresolved
