# OCR Strategy

## Status

OCR is planned after the text-subtitle MVP. The architecture is documented now so later implementation can fit cleanly into the existing pipeline.

## MVP OCR Plan

1. extract subtitle image events from source assets
2. crop and preprocess subtitle regions
3. run OCR
4. map OCR text back to timestamps
5. score confidence per segment
6. route low-confidence segments to fallback or review

## Planned Tooling

- `ffmpeg` and `ffprobe` for extraction and inspection
- subtitle stream extraction helpers for embedded subtitle tracks
- Tesseract as the first OCR baseline
- optional selective vision-model repair for low-confidence edge cases

## Preprocessing Steps

- grayscale conversion
- contrast adjustment
- denoise
- thresholding
- subtitle region cropping

## Confidence And Fallback

Every OCR-derived segment should store:

- OCR confidence
- source image reference
- fallback attempts
- review status

Low-confidence flow:

1. retry with alternate preprocessing
2. retry with alternate OCR parameters
3. optionally send to selective repair pass
4. expose in the user review queue

## Product Rule

OCR complexity must remain hidden from non-technical users in simple mode. The primary UX should surface only understandable warnings such as "Some lines may need another pass."

