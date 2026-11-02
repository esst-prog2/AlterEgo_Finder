## Context

Datasets are folders of `<Person>/<image>` under `data/`. `get_or_build_index` and
the page's dropdown already handle any such folder with `.matchcache/`. Thresholds
are read from `<dataset parent>/config.json` in both `match.py` and `app.py`, so all
datasets share one file. `calibrate.main` fits `threshold_high` using every
calibration identity as an absent stranger. `render_report` builds cards from
`IndexEntry`. Spike findings: a global Wikidata ranking returns 504; by-occupation
queries take 3-35 s and sometimes return 502; Commons returned 429 at about one
request per second or faster but not at one per 3 s; some people have no English label.

## Goals / Non-Goals

**Goals:**
- A recognisable pool that, once built, behaves like any other dataset.
- Licences respected: every image credited wherever it is shown or exported.
- A thin end-to-end path first (100 people), then scale.

**Non-Goals:**
- Fetching at match time, or searching with the query photo.
- User-typed names (anyone could be typed in).
- More than one image per person: `P18` gives one, so same-person scores for pool
  members rest on a single reference photo.
- Changing README section 1 (a follow-up change).

## Decisions

### D1. A committed list, like `lfw_split.json`
`data/wikidata_people.json` holds `qid`, `name`, `folder`, `file` (the Commons title),
`occupation` and `sitelinks`, ordered by round-robin across occupations and by
sitelinks within each, with about 650 entries so skipped people still leave 500.
`refresh_wikidata_list.py` runs one query per occupation with retries on 502/504,
drops people without an English label and anyone who might still be under 18 (only
birth years are compared, so the cutoff is year of refresh - 19), removes duplicates,
and writes atomically. Anyone also tagged politician, statesperson, monarch or
revolutionary is left out, whatever their other occupations: Wikidata lists Fidel Castro
and Kim Jong-il as film actors. `EXCLUDED_QIDS` is a backstop in case tags change. Setup never queries for people, so the
flaky endpoint cannot break a build, and everyone gets the same selection.
*Alternative rejected:* querying at setup time, for the reasons above.

### D2. `face_pipeline/wikidata_pool.py`, driven by `setup_data.py --wikidata`
Steps: base setup (the pool needs `data/calibration`), then for each listed person
without an image, until the limit is reached:
1. metadata comes from the Commons API in batches of 50 titles (`imageinfo` with
   `extmetadata`, `url`, `thumburl` at width 500);
2. check the licence and author, then that the thumbnail URL is `https` on
   `upload.wikimedia.org` or `thumb.wikimedia.org` (the real build showed Commons
   uses both);
3. wait 3 s, download with a timeout and a 5 MB cap, then decode;
4. require a detectable face; write `<folder>/<folder>_0001.jpg` by temp name and
   rename (D8).

`attribution.json` is rewritten after each saved image, so an interruption loses
nothing, and a skip list inside it stops rejected people being refetched on resume.
Requests carry a descriptive User-Agent, as Wikimedia's policy asks.

### D3. Rate limits
On 429, wait for `Retry-After` (at most 5 minutes; 60 s if absent) and retry once. A
second 429 stops the build with exit 1 and a resume message. The 3 s gap is a
constant, and there is no parallel fetching. The limit is respected, not worked around.

### D4. Allowed licences
`CC0`, `Public domain` and `CC BY` / `CC BY-SA` in any version. Anything else is
skipped and counted, including the sample's one `GODL-India`: reviewing unusual
licences by hand is not worth it when the pool has spare people. `NC` and `ND`
variants never pass.

### D5. Attribution is data, and untrusted
`Artist` in `extmetadata` is HTML from strangers. `html.parser` strips it to text at
build time, capped at 200 characters. `face_pipeline/attribution.py` has
`load_attribution(dataset)`, returning an entry per image or `{}` when there is no
file. Cards and tooltips show at most 60 characters of the author (a real credit ran
to seven lines); the source page and the report have it in full. Rendering treats it
as untrusted anyway: `html.escape` in the report, `st.text`
on cards, and links only when the URL starts with `https://commons.wikimedia.org/`.

### D6. Per-dataset thresholds
`matching.config_path_for(dataset)` returns `<dataset>/config.json` if it exists,
otherwise `<dataset parent>/config.json`; `match.py` and `app.py` both use it.
`config.json` sits at the dataset's top level, where the indexer ignores it, as it
does `attribution.json`.

### D7. Excluding overlap in calibration
`calibrate.py` normalises names (NFKD accent removal, letters and digits only, casefold,
so `George_W_Bush` matches `George_W._Bush`, a leak the real pool exposed) and removes matching calibration people from the strangers used for
`threshold_high`. The low threshold still uses all pairs. On the disjoint LFW split
nothing is removed, so `data/config.json` must reproduce exactly (task 2.3). Names
can miss (a nickname, say), so some overlap may slip through; the build prints how
many were removed.

### D8. Folder and file names are plain ASCII
`folder` comes from the English label with accents converted (`Pele`,
`Kimi_Raikkonen`), spaces to underscores and Windows-illegal characters removed; a
name with no ASCII form drops that person. `cv2.imread` and `cv2.imwrite` silently
fail on non-ASCII paths on Windows, so accented folders would vanish from the pool
without an error (77 of the first 650). Each image is saved as
`<folder>/<folder>_0001.jpg` whatever the Commons file type was (`.webp` and `.tif`
appear, and the indexer takes only jpg and png), re-encoded when not already JPEG.
Names are stored in the committed list, so they are identical everywhere.

## Risks / Trade-offs

- [Thresholds fitted with LFW strangers against Commons portraits] → a domain shift
  that the refit cannot remove. The spike's different-person scores (max 0.27) look
  fine, and task 5.3 measures the same-person gap; the README states the limit.
- [Wrong or unusual images: a painting, a group photo] → born from 1920 on reduces
  paintings, and the largest-face rule handles groups. A manual look at the top
  matches in 5.3; a person can be removed from the list.
- [Living people's faces are biometric data] → public figures only, adults only,
  stays local, not committed; README section 5 says so plainly. This is a course
  project's position, not legal advice.
- [The build is slow] → optional, resumable, and the time is stated up front.
- [Licence text is required wherever images are reused] → the cards and report carry
  it. Slides with these faces need the same credit (noted for the slides work).
- [Commons changes an image later] → the file title stays, content may differ; scores
  in the README are stated as "in our run".

## Migration Plan

Additive. Without `data/wikidata/`, everything behaves as today; LFW stays the
fallback. Rollback: delete the folder and revert.
