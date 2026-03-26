# Data Model

## Core Entities

### Project

Represents one subtitle rescue effort tied to source assets, processing state, language settings, and output artifacts.

Key fields:

- `project_id`
- `name`
- `created_at`
- `source_language`
- `target_language`
- `source_subtitle_type`
- `target_video_path`
- `reference_video_path`
- `status`

### Subtitle Segment

Represents one subtitle event throughout the pipeline.

Key fields:

- `id`
- `start_ms`
- `end_ms`
- `source_text`
- `normalized_source_text`
- `literal_en`
- `natural_en`
- `final_en`
- `ocr_confidence`
- `translation_confidence`
- `flags`
- `locked`

### Job

Represents long-running work such as parsing, OCR, translation, QA, or export.

Key fields:

- `job_id`
- `project_id`
- `type`
- `status`
- `progress`
- `error`

### QA Flag

Represents a reviewable issue such as line length, speed, overlap, OCR confidence, or consistency risk.

Key fields:

- `flag_id`
- `project_id`
- `segment_id`
- `rule`
- `severity`
- `message`
- `status`

### Glossary Term

Represents a preferred translation or naming rule.

Key fields:

- `term_id`
- `project_id`
- `source_term`
- `target_term`
- `notes`
- `locked`

### Export Artifact

Represents a generated output file or mux recipe.

Key fields:

- `export_id`
- `project_id`
- `format`
- `path`
- `created_at`
- `status`

## Storage Shape

The MVP should use SQLite tables aligned to the entities above, plus a project folder that stores source files, cached batches, logs, and exports.

