## Why

README section 1 still describes the week-one demo: a terminal run of `match.py`
"within 100 ms" (never measured), on a projector, for three minutes. The final
demo is a five-minute slide presentation to an audience that never reads the
code and scores whether they get the program, whether it matters and whether
they would use it. Section 1 is the target for the remaining two weeks, so it
has to describe the path we will actually show, now, while there is time to
build it.

## What Changes

- **README section 1 (The demo)** is rewritten, in the present tense, as a
  three-beat walk through a local web UI (Streamlit, built by the follow-up
  change `streamlit-web-ui`):
  1. *Lookalike.* I drop `data/my_photo/PK.jpg` onto the page with the
     `data/celebrities` dataset selected. The top match is a celebrity with a
     low score (0.2146 in our run) labelled `LOW_CONFIDENCE`: looks somewhat
     like me, and the calibrated thresholds say it is not me.
  2. *Self-match.* I switch the dataset dropdown to `data/celebrities_plus_me`,
     the same 500 identities plus my second photo (a different day and place).
     My own photo is ranked #1 (0.4322) and labelled `HIGH_CONFIDENCE`: the
     threshold that rejected every celebrity accepts the real person. Worded
     as what it is: one self-match, at a threshold set for a 1% false-accept
     rate, not proof of identity verification.
  3. *No face.* I drop an image with no face on it; the page shows
     "No face detected" instead of results.
  The beats name the HTML report and the threshold slider only where the
  path uses them. The unmeasured "within 100 ms" claim is removed.
- **README section 2 (The shape)** names the browser page as a second front
  end next to the CLI, both on the same pipeline.
- **README section 3 (The size)** adds the local Streamlit UI to the scope,
  and narrows the "Not this term" item "Full web application / React frontend
  dashboard" to a hosted, multi-user web application. The Wikidata candidate
  pool is **not** added here: it is a stretch goal and its own change
  (`online-candidate-pool`) adds it to the README when it is built. The item
  "Automated web scraping or live downloads from external image APIs" stays
  out of scope for now.
- **README section 5 (What could stop this)**: the privacy mitigation says
  the web UI runs only on localhost, so the uploaded photo is processed on
  this machine and never sent anywhere.

## Capabilities

### New Capabilities

None. This change rewrites the project description; the web UI's
requirements are specified by `streamlit-web-ui`.

### Modified Capabilities

None. No spec-level behavior changes; the change sets `skip_specs: true`
and is archived with `openspec archive --skip-specs`.

## Impact

- `README.md` sections 1, 2, 3 and 5. Section 4 (acceptance criteria) is
  unchanged; its criteria are still the CLI's, and `streamlit-web-ui` adds
  the UI's.
- No code, tests or specs change. Until `streamlit-web-ui` is built, section 1
  describes a UI that does not exist yet; that is intended (section 1 is the
  target, written as if it already worked).
- `data/celebrities_plus_me/` and the second photo are gitignored (logged
  2026-10-16), so section 1 says in one sentence how that dataset is made,
  without committing the photo.
- The final section 1 is handed in on Canvas.
