## Why

The second Impeccable critique of the page (26/40, `.impeccable/critique/2026-11-17T11-05-26Z__app-py.md`) found the most visible remaining problems: at the peak moment the verdict says "LEONARDO_DICAPRIO", because person names are dataset folder names; the on-page report preview ends the page on `LOW_CONFIDENCE` / `NO_MATCH`, against the commitment to plain label names; the author's own folders sit among the public datasets; the report download is a pale secondary button; and the upload hint misses 4.5:1. These show in the tour video's screens, which are captured again next.

## What Changes

- Person names on the page read as names: underscores become spaces ("Leonardo DiCaprio") in the verdict, cards, the target's names and tooltips, and alt text. Matching, order, scores and labels stay the CLI's; the CLI keeps folder names.
- The report shows each label as its plain name with the technical label in parentheses: "Alter Ego (LOW_CONFIDENCE)". The report's names are unchanged.
- The dataset list puts the public datasets first (the pool, then LFW); other folders follow in name order under their exact folder names (README section 1 names `wikidata_plus_me`).
- The report download becomes the navy primary button; the upload hint and the file size text reach at least 4.5:1.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `web-ui`: new requirement "Readable person names"; "Verdict line" refers to it; "Dataset selection" orders public datasets first; "Readable on any screen" covers upload hints and the primary download.
- `summary-report`: "Confidence status displayed per candidate" shows the plain name with the technical label.

## Impact

- `app.py`: a `_display_name` helper used by the verdict, cards, target and alt text; dataset ordering; `type="primary"` on the download; two stylesheet rules for the upload hint and file size.
- `face_pipeline/report.py`: label text.
- Tests: `tests/test_app.py` (card names compared through the helper; dataset order; primary download), `tests/test_report.py` (label text). CLI tests unchanged.
