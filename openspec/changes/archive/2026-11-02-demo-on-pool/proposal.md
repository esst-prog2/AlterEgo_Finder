## Why

README section 1 is the demo description pasted on Canvas (due 2026-11-07), and its
Beats 1 and 2 still use LFW, where the top match is a name most of the audience won't
know (Jean-Sebastien Giguere, 0.2146). The public-figure pool now exists and works, and
a lookalike the room recognises (Psy, 0.2702) tells the story better. The log recorded
that section 1 would move once the pool's numbers were measured; they now are.

## What Changes

- **README section 1:** Beats 1 and 2 run on `data/wikidata` and a new local
  `data/wikidata_plus_me`, with measured scores and a mention of photo credits on the
  cards. Beat 3 keeps its story. The CLI paragraph uses the pool too.
- **README section 2:** the example input becomes `data/wikidata/`.
- **README section 5 (privacy risk):** names the pool's licensed Wikimedia photos next
  to LFW, if the current text would otherwise be incomplete.
- **README section 6:** the self-match steps copy the pool. Plain `setup_data.py` still
  builds only LFW, so the steps say the demo's datasets need `--wikidata` first.
- **`.gitignore`:** adds `data/wikidata_plus_me/`, which holds the user's private photo.
- **AGENTS.md:** the "Next" line is replaced with the new state.

Not changing: application code, the pool, thresholds, and the LFW datasets, which stay
in the dropdown as the fallback.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None: no requirement names a demo dataset, and the page and CLI already handle these
folders. This change declares `skip_specs`.

## Impact

- Documentation and one `.gitignore` line. No code, no dependencies.
- Locally: one new gitignored dataset, not in the repository.
- A classmate's pool would be built from the same list, but Commons files can change,
  so section 1's scores are "in our run", as they are today.
