# AGENTS.md

## Planning log

Whenever we decide something about this project — a requirement, a number,
a name, a tool — append one line to PLANNING_LOG.md: the date, what was
decided, and whether I decided it or you did. Never rewrite an earlier line.

## Project

AlterEgo Finder — a CLI tool that matches a query face photo against a dataset
of face images using face embeddings and vectorized cosine similarity, with a
calibrated confidence threshold. See [README.md](README.md) for the full
spec: demo walkthrough, scope (in/out), acceptance criteria, and risks.

## Status

Pre-implementation. No source code exists yet — only README.md,
PLANNING_LOG.md, and OpenSpec scaffolding (openspec/). The embedding/detection
library and other implementation details are not yet decided.

## Workflow

This repo uses OpenSpec for spec-driven changes (openspec/):

- New work starts as a change proposal, not a direct edit — use
  `/opsx:propose "<idea>"`, or `/opsx:explore` to think it through first.
- Durable specs live under `openspec/specs/`; in-flight work under
  `openspec/changes/`.
- Don't hand-edit files under `openspec/changes/` — use the OpenSpec CLI
  (e.g. `openspec new change ...`) so required metadata stays consistent.
