# Translation Pipeline

## Design Goals

- preserve line identity
- preserve meaning
- produce natural subtitle English
- support selective repair without rerunning the whole file
- keep costs predictable

## Batch Design

Do not send one subtitle line per request.

Current batch policy:

- batch size is configurable and deterministic
- preserve segment IDs
- include neighboring context where useful
- attach source language, target language, glossary terms, and locked names
- compute a stable cache key from pass type, config version, glossary, locked names, and normalized segment payload

## Pass Strategy

### Pass A: Literal Draft

Purpose:

- preserve meaning
- minimize omissions
- keep output aligned to input IDs

Current implementation:

- updates `literal_en`
- persists successful batches immediately

### Pass B: Natural Subtitle English

Purpose:

- remove overly literal phrasing
- improve readability
- keep lines compact enough for subtitles

Current implementation:

- consumes the literal draft when available
- updates `natural_en` and `final_en`

### Pass C: QA And Repair

Purpose:

- repair only flagged lines
- fix inconsistent names and obvious OCR damage
- reduce overlong or awkward lines

Current implementation status:

- repair pass contract exists
- repair orchestration is still pending

## Structured Output Contract

The engine requires strict structured JSON output for every batch response. A response must always map each input segment ID to exactly one result record.

Core response fields:

- `id`
- `translated_text`
- `notes`
- `confidence`
- `warnings`

Current implementation modules:

- `translation/batching.py`
- `translation/schema.py`
- `translation/service.py`
- `translation/client.py`
- `translation/openai_client.py`

## Reliability Rules

- validate every response against schema
- retry transient failures with backoff
- log per-batch request and response metadata
- cache successful batches by stable content hash
- rerun only failed or invalid batches

Current validator behavior rejects:

- missing IDs
- duplicate IDs
- unexpected IDs
- invalid confidence values
- malformed notes or warnings fields

Current retry/cache behavior:

- transient provider failures are retried up to configured limits
- schema-invalid payloads can be retried or failed immediately based on settings
- cached validated payloads bypass the provider call and still update persisted segments
- literal pass updates `literal_en`
- natural pass updates `natural_en` and `final_en`

Current persisted translation artifacts:

- `translation_batches`
- `translation_batch_segments`
- `translation_cache`
- `batches/requests/*.json`
- `batches/responses/*.json`
- `batches/cache/*.json`

## Cost Control

- keep model selection configurable
- use a lower-cost model tier for literal pass
- use a higher-quality pass for rewrite only where needed
- run repair only for flagged segments
- avoid OCR recovery model calls unless confidence is low

Model selection remains configurable so the implementation can evolve without changing the product contract.

## Current Gap

The orchestration layer and OpenAI adapter are implemented, but the repository still needs live end-to-end verification with configured credentials plus desktop integration.
