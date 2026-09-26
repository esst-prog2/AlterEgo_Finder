# AGENTS.md

## Planning log

Whenever we decide something about this project — a requirement, a number,
a name, a tool — append one line to PLANNING_LOG.md: the date, what was
decided, and who's responsible for it:
- "Decided by user" — I originated the decision myself.
- "Proposed by agent, accepted by user" — you proposed it and I accepted it.
- "Decided by agent" — you decided it unilaterally (e.g. an implementation
  detail), without asking me first.

Never rewrite an earlier line.

## Project

AlterEgo Finder — a CLI tool that matches a query face photo against a dataset
of face images using face embeddings and vectorized cosine similarity, with a
calibrated confidence threshold. See [README.md](README.md) for the full
spec: demo walkthrough, scope (in/out), acceptance criteria, and risks.

## Status

MVP complete, matching README section 3's "First useful version" scope:
detection+alignment (YuNet), ArcFace (512-d) embedding, dataset
auto-indexing, calibrated two-threshold confidence classification
(`calibrate.py`), model weights fetched on demand with SHA-256
verification, and a self-contained `summary.html` report. 5 capabilities
under `openspec/specs/`, all archived changes under
`openspec/changes/archive/`, 43 tests passing. See PLANNING_LOG.md for
the decision history.

## Workflow

This repo uses OpenSpec for spec-driven changes (openspec/):

- New work starts as a change proposal, not a direct edit — use
  `/opsx:propose "<idea>"`, or `/opsx:explore` to think it through first.
- Durable specs live under `openspec/specs/`; in-flight work under
  `openspec/changes/`.
- Don't hand-edit files under `openspec/changes/` — use the OpenSpec CLI
  (e.g. `openspec new change ...`) so required metadata stays consistent.
