## Context

`match.py` ranks the whole index with `rank_matches()`, labels every
candidate, prints all of them, and passes the full list to
`render_report()`, which keeps the first `REPORT_TOP_K` (10). See
proposal.md for why the printed list needs a cap.

## Goals / Non-Goals

**Goals:**
- Cap printed output at N, default 10, settable with `--top`.

**Non-Goals:**
- Changing the HTML report's own cap; it stays at `REPORT_TOP_K` whatever
  `--top` is (summary-report spec, "Candidate list capped").
- Grouping by person (one line per identity). A person with two indexed
  photos can still appear twice, as today.

## Decisions

- **Default N = `REPORT_TOP_K`, imported from `face_pipeline.report`.**
  Terminal and report then show the same candidates by default, from one
  constant. Alternative: a separate constant in match.py, which could
  drift from the report's.
- **Slice when printing, not inside `rank_matches()`.** Ranking still
  covers the whole index, and the report still receives the full ranked
  list and applies its own cap. Alternative: truncate in `rank_matches()`,
  which would couple the report's cap to `--top`.
- **`--top` below 1 is an argparse error (exit 2).** argparse already
  handles bad option values this way, and it happens before any model or
  index is loaded. Alternative: treat 0 as "print all", rejected as a
  hidden special value; a large N prints everything.

## Risks / Trade-offs

- [Scripts that parsed all 500 lines now get 10] → pass `--top` with the
  index size; no such scripts exist in this repo.
