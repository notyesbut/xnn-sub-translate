# Translation Pipeline

## Design Goals

- preserve line identity
- preserve meaning
- produce natural subtitle English
- support selective repair without rerunning the whole file
- keep costs predictable

## Batch Design

Do not send one subtitle line per request.

Initial batch policy:

- batch size target: 20 to 80 segments
- preserve segment IDs
- include neighboring context where useful
- attach source language, target language, glossary terms, and locked names

## Pass Strategy

### Pass A: Literal Draft

Purpose:

- preserve meaning
- minimize omissions
- keep output aligned to input IDs

### Pass B: Natural Subtitle English

Purpose:

- remove overly literal phrasing
- improve readability
- keep lines compact enough for subtitles

### Pass C: QA And Repair

Purpose:

- repair only flagged lines
- fix inconsistent names and obvious OCR damage
- reduce overlong or awkward lines

## Structured Output Contract

The engine should require strict structured JSON output for every batch response. A response must always map each input segment ID to exactly one result record.

Core response fields:

- `id`
- `translated_text`
- `notes`
- `confidence`
- `warnings`

## Reliability Rules

- validate every response against schema
- retry transient failures with backoff
- log per-batch request and response metadata
- cache successful batches by stable content hash
- rerun only failed or invalid batches

## Cost Control

- use a lower-cost model tier for literal pass
- use a higher-quality pass for rewrite only where needed
- run QA pass only on flagged segments
- avoid OCR recovery model calls unless confidence is low

Model selection must remain configurable so the implementation can evolve without changing the product contract.

