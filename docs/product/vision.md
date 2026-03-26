# Product Vision

## Problem

Users often have a video release without English subtitles, but can only find subtitles in another language such as Chinese, Malay, or Japanese. Existing subtitle tooling is fragmented, technical, and difficult to use unless the user already understands OCR, media containers, encoding, subtitle timing, and command-line tools.

## Product Vision

Subtitle Rescue should feel like a guided desktop utility that takes a user from raw subtitle input to a usable English export with clear steps, transparent progress, and a trustworthy preview workflow.

## Target User

The primary user is not a subtitle engineer. They may be comfortable downloading files, but they should not need to understand subtitle formats, OCR tuning, API details, or timing math to complete the core flow.

## Jobs To Be Done

- Turn foreign subtitles into usable English subtitles.
- Adjust subtitles to match a different video release.
- Review risky lines before export.
- Export a file that can be used immediately.

## UX Principles

- Lead with a wizard, not with settings.
- Keep the default path simple and local-first.
- Show progress in product language, not engineering language.
- Use preview to build trust before export.
- Surface warnings as actionable cards, not logs.
- Keep advanced controls available, but hidden by default.

## Non-Goals For Early Releases

- cloud collaboration
- web-first deployment
- full professional subtitle editing suite behavior
- broad video transcoding features
- automated burn-in rendering

