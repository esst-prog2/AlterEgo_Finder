## Context

See proposal.md for why. After `apply-shared-design`, the page's look comes only from Streamlit's theme (`.streamlit/config.toml`), which reaches colours, fonts and radius but not borders, grids, text case or the size of inline code. The critique's measurements: captions render at 60% opacity of ink, 4.09:1 on the paper; the target is a fixed 640 x 460 Vega-Lite spec shown with `width="content"`, clipped at 390 px; card names are `st.text`, scores are inline code; the results heading is `st.subheader` (h3) under `st.title` (h1); the threshold slider is `_threshold_slider` with a per-dataset key, used by four tests. README section 1 (the submitted demo) names the folders `wikidata` and `wikidata_plus_me`.

## Goals / Non-Goals

**Goals:**
- The page states its answer in a sentence and looks like DESIGN.md, at desktop and phone width.
- Every label, score and candidate stays exactly what the CLI prints.

**Non-Goals:**
- The report's look (already restyled), the CLI, matching, calibration, the target's layout algorithm (`place_names`).
- Re-capturing the tour video (a later step, if wanted).

## Decisions

1. **One scoped stylesheet, injected once with `st.html`.** The theme cannot draw borders, grids or capitals, so a single `<style>` block in a module constant styles Streamlit's stable test ids (`stApp`, `stCaption`, `stAlert`, `stVerticalBlockBorderWrapper`, `stHeading`, `stFileUploaderDropzone`) plus a few classes of our own. Alternative: a CSS file under `static/` linked by `<link>`; rejected because Streamlit offers no supported way to add a `<link>` to the page head, and an inline block keeps the page self-contained. The critique's verdict ("only colours applied") cannot be fixed without it, which `apply-shared-design`'s decision 1 deferred; this change takes the step, keeping all selectors in one place and covered by a test that the block names only those ids.

2. **The verdict line is `st.html` with escaped text.** A pure function `_verdict(labeled)` returns `(kind, name, score)`; the page renders it as `<p class="ae-verdict">` with `html.escape` on the name, the label chip as a coloured dot plus the plain name (the same chip as the promo page, drawable here because it is our own markup), and the score in the display face. AppTest reads it through `at.html`. Alternative: `st.markdown`, which would need Markdown escaping of folder names and cannot draw the dot.

3. **Cards become framed containers; names and scores keep their element types.** Each card is `st.container(border=True)`, restyled to 2 px navy by the stylesheet. The name stays `st.text` (untrusted text, and the tests read names from `at.text`) and is set in the display face in capitals by CSS on its container; the score line stays the `st.markdown` `` `0.6867` :green-background[**Same person**] `` form the tests parse, and CSS sets the code element in ink Barlow Condensed at 1.35 rem. So the Labels-match-the-CLI tests stay valid unchanged.

4. **Card photos with a text alternative.** `st.image` has no alt parameter, so card photos are rendered with `st.html` as `<img alt="Photo of {escaped name}" src="data:image/jpeg;base64,...">` from the existing square crop (encoded once per card, as the report already does).

5. **Target fits any width.** The spec gets `"autosize": {"type": "fit", "contains": "padding"}` and a `description` (Vega-Lite turns it into the SVG's `aria-label`): "Similarity target: N faces shown; a inside the Same person ring, b between the rings (Alter Ego), c outside (Not You)". The chart is drawn with `width="stretch"`, and CSS caps it at its natural 640 px and lets it shrink with the column; names keep their pixel sizes, so at 390 px they shrink with the chart rather than being clipped. The legend moves below the circle into a caption. Alternative: recompute coordinates for the container width, which would change `place_names`' inputs (a non-goal).

6. **Layout of the result row.** Photo (thumbnail, 160 px) and face crop stack in one narrow column; the target takes the rest. At phone width Streamlit stacks the columns.

7. **Thresholds.** `_threshold_slider` and its notice go; `main` passes the calibrated `low, high` straight to `label_results`, `_target_spec` and `render_report`. The help text that explained the zones moves to the page as one line under the verdict: "Same person: 0.3706 or more. Alter Ego: from 0.1864, the closest public figures, but not you. Not You: below 0.1864." with the dataset's numbers.

8. **Datasets.** `_dataset_label(path)` maps `wikidata` to "Public figures (wikidata)" and `celebrities` to "LFW faces (celebrities)", and leaves any other folder name as it is; the selectbox's `index` is the position of `wikidata` when present. README section 1 keeps working: its folder names are still visible.

9. **Toolbar and headings.** `[client] toolbarMode = "viewer"` hides Deploy and the developer menu; `st.subheader` becomes `st.header` (h2).

10. **Captions.** The stylesheet sets `stCaption` to ink soft #46505d at full opacity (7.4:1 on the paper).

## Risks / Trade-offs

- [Streamlit renames its test ids in a later version, and the stylesheet stops matching] → the page still works with the theme alone; a test pins the ids used, and the pinned range in `requirements-ui.txt` limits drift.
- [Removing the slider removes a way to explore thresholds on the page] → the CLI keeps `--threshold-low/--threshold-high`; README section 3 is updated to say so.
- [st.html images bypass Streamlit's media cache] → ten JPEGs of a few kB each per run; the report already embeds the same.
- [The tour video now shows the slider and the earlier layout] → noted in the proposal; re-capturing is a separate step.

## Migration Plan

No data migration. Rollback is reverting the commit. Tests that drove the slider are replaced, not deleted silently: their behaviours (labels from calibrated thresholds, rings at the thresholds, report labels) are kept as calibrated-only tests.
