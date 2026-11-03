## Context

`data/wikidata` has 500 people, one photo each, with thresholds low 0.1864 and high 0.3706.
159 of them are also in LFW, with 1,008 LFW photos, which gives same-person queries from a
different source than the gallery. LFW has 5,749 people and 13,233 photos in `data/lfw/lfw`,
and 1,680 people have two or more. `data/lfw/spike_embeddings.npz` holds embeddings from the
HW4 spike, reusable where they still match. `face_pipeline/wikidata_pool.py` already has the
rate-limited requests and licence rules, and `calibration.py` has `compute_index_high_threshold`,
`absent_strangers` and `normalise_name`.

## Goals / Non-Goals

**Goals:**
- Compare the four ways of scoring on the same people, each at a threshold fitted its own way.
- Measure the walk under the best possible conditions: a perfect face search.
- Keep it reproducible: fixed seeds, and results committed without photos.

**Non-Goals:**
- Changing the program, or production quality in this script.
- Any online search, or any request carrying a query photo or its embedding.
- A verdict on 2,000 photos. This measures 50 people, and says so.

## Decisions

### D1: Who is in the gallery

About 50 people: `PK.jpg`'s top 10 in the pool, Bruce Springsteen, and the rest drawn with a
fixed seed from the 159 people also in LFW, spread across the five occupations. Same-person
results use only people with LFW photos.

### D2: Which extra photos

For each person, list the files in their Commons category (Wikidata P373), keep those passing
the pool's licence rules, and download at most 8 at the pool's 3 s gap. Keep a photo only if
it has exactly one detected face and scores at least 0.25 against the person's pool photo.
Then pick up to 3 by taking the one least like those already chosen, so the set is varied.
Commons has no reliable "young" or "glasses" tags, so this is the only variety we can ask for.

The 0.25 floor removes wrong people, but also the hardest real variation, which flatters same-
person results. So evaluation repeats at floors of 0.15 and 0.35, offline. People with fewer
photos stay in with what they have, and the counts are reported.

### D3: The four arms, on the same 50 people

| Arm | Score for a person |
|---|---|
| One photo | their pool photo |
| Best photo | the highest of their photos |
| Averaged | their photos' normalised mean |
| Top 10 only | one photo first, then best photo for those 10 |

### D4: Fair thresholds

Each arm fits its own `threshold_high` to absent strangers' top-1 scores, as `calibrate.py`
does at 1%, on 1,000 LFW people not in the gallery, and is tested on 1,000 other LFW people.
"Top 10 only" is also tested at the one-photo threshold, because that is what would happen
if the extra chances were added with no refit.

A 50-person gallery has lower thresholds than 500, so `PK.jpg`'s own labels are reported at
each arm's fitted threshold and read only as a comparison between arms.

### D5: The walk

The stand-in web is one LFW photo per person, about 5,700 faces, with each face linked to its
k nearest (k = 5, 10, 20), which simulates a perfect face search. A walk starts at the nearest
graph face to the query's top match in the pool. At each step it compares the current face's
neighbours with the query, moves to the best if that is better, and otherwise stops, for at
most 10 steps. Queries, all kept out of the graph as photos:

- `PK.jpg`
- 200 strangers, whose people are not in the graph: any *Same person* ending is false.
- 100 people with a second photo in the graph: did the walk lead back to their own face?

Reported against exact search over the same graph: the score reached, how often it finds the
true best, faces checked, and strangers ending at or above 0.3706.

### D6: Predictions and decision rule, fixed before the run

Predictions: best photo raises same-person scores and its threshold. Averaged raises them with
little threshold growth. Top 10 only breaks the 1% rate at the one-photo threshold. The walk
gets close to the true best while checking far fewer faces, and often leads back to the person.

A full build gets proposed only if one arm, at its own fitted threshold, turns at least half of
the one-photo arm's same-person misses into hits, keeps strangers at or below 2% on the held-out
1,000, and does not put `PK.jpg`'s top public figure in *Same person*. Otherwise the pool stays
as it is, and the result goes on a slide. Whatever the walk shows, no online search gets built
on this evidence alone: it measures whether the idea works, not the privacy objections to it.

## Risks / Trade-offs

- **Small numbers.** Results are reported as counts, and one person can move them. Springsteen
  alone is an anecdote.
- **The filter shapes the result.** D2's floor is why it runs at three values.
- **LFW is not the web.** It is smaller, tidier and has celebrities only, so the walk result is a
  best case.
- **A bystander's photo.** Commons may hold private people in a person's category. The exactly
  one face rule and the floor reduce this, the photos stay local and gitignored, and only
  scores and the 50 public figures' names are committed.
