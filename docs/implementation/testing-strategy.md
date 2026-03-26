# Testing Strategy

## Principles

- prefer deterministic tests around parsing, contracts, and export
- isolate API-dependent logic behind mocks and fixtures
- use golden subtitle fixtures for round-trip confidence
- verify user-critical flows end to end once the desktop shell exists

## Test Layers

### Unit Tests

- parsing and normalization helpers
- batch builder behavior
- QA rules
- sync math
- export formatting

### Integration Tests

- import to storage flow
- translation batch request and response validation
- retry and cache behavior
- project save and reload

### Golden Fixture Tests

- `.srt` parse and export round-trip
- `.ass` import normalization
- later OCR output comparisons for known samples

### Desktop Tests

- wizard happy path
- translation progress visibility
- review and export flow

## Manual Acceptance Checks

- import a real subtitle file
- run translation on a medium-sized sample
- edit a flagged line
- apply a global timing shift
- export `.srt` and validate playback

## Required Verification For Future Changes

- subtitle-domain logic changes require automated tests
- contract changes require both engine and app validation
- export changes require golden file comparison

