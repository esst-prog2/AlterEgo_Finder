## Context

The page lists any folder under `data/` with a `.matchcache`, in alphabetical order, so
`celebrities` is selected first. `config_path_for` prefers a dataset's own `config.json`
over its parent's, and `load_attribution` reads `attribution.json` from the dataset
folder. A person with no entry in that file simply has no credit.

Measured so far on the pool (low 0.1864, high 0.3706): `PK.jpg` gets Psy at 0.2702, and
against the user's second photo 0.4322. Across sources, 0.9% of strangers' best scores
reach Same person, 97% land in Alter Ego and 2.1% in Not You.

## Goals / Non-Goals

**Goals:**
- Section 1 describes exactly what the page does on the pool, and every number in it is
  measured on this machine.
- The self-match dataset stays private and out of git.

**Non-Goals:**
- Slides (due 2026-11-28), or any change to the page's look or behaviour.
- Making the pool part of plain `setup_data.py`. It stays optional, because of its
  30-minute build.

## Decisions

### D1: `wikidata_plus_me` is a whole-folder copy plus `Me_PK`

Copying `data/wikidata` brings its `config.json` and `attribution.json`, so the plus-me
dataset has the pool's exact thresholds and credits with no new code. Without its own
config it would fall back to `data/config.json`, LFW's thresholds, and the slider would
silently show the wrong values. The thresholds are not refitted: "the threshold that
kept every public figure out lets the real person in" needs the same threshold in both
beats.

### D2: The dropdown default stays as it is

The presenter picks `wikidata`, one click, and the README says so. Changing the default
would need code and a spec change, and would select a folder most clones don't have.

### D3: LFW stays what plain setup builds and the fallback

The section 6 "try this" line still gives Giguere at 0.2146, since that is what a fresh
clone gets. If the pool ever failed on the day, the old beats still work unchanged.

### D4: Measure first, then write

Section 1 says things a score alone doesn't: how many names sit in the Alter Ego band,
that nobody is inside the inner ring, how the self-match compares with the best public
figure. Each is read off the real page first. The old "about twice" won't carry over:
0.4322 against 0.2702 is about 1.6 times.

## Risks / Trade-offs

- **The Alter Ego band is wide on the pool.** 97% of strangers' best scores land there,
  so the label means "the closest public figure, and not you" rather than "a striking
  likeness". The wording in Beat 1 must not oversell it.
- **Thresholds cross sources.** They are fitted with LFW faces as the strangers, while
  the pool comes from Commons. Beat 2 keeps its "evidence, not proof" wording and quotes
  the measured 0.9% alongside "about 1 in 100" only if it reads clearly.
- **The private photo is one wrong `git add` away.** The `.gitignore` line goes in before
  the folder exists, and `git check-ignore` confirms it.
