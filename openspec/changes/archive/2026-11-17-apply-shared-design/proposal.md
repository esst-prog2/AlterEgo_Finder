## Why

The promo page and the tour video now share one look, written down in DESIGN.md ("The Scoresheet"), but the program itself still shows Streamlit's default theme and the report a plain grey card layout. Someone who watches the video or reads the page and then runs the program meets a different-looking product, and the new logo appears nowhere in it. Homework 10's video shows the real app, so the app has to match before the video is captured again.

## What Changes

- The local web page takes the DESIGN.md look through Streamlit's own theme: paper background, navy as the only accent, ink text, square corners, Barlow for text and Barlow Condensed for headings, both shipped with the project and served from the app's own static folder on localhost.
- The page's green, orange and grey label colours become the shared label colours (Same person #1a7f37, Alter Ego #d4a72c, Not You #8c959f), so a card's label matches the target's dots, the promo page and the video.
- The AlterEgo Finder logo (the target in miniature beside the name) appears at the top of the page's sidebar and as the browser-tab icon.
- The similarity target's own text and rings take the shared ink and navy instead of GitHub greys.
- The HTML report (summary.html) takes the same look: paper, navy rules, square cards, the label dot, the logo in its header, with the fonts and logo embedded so it stays one self-contained file.
- The promo page shows the logo in its masthead and as its favicon.
- No change to matching, scores, labels, thresholds, the CLI's text output or privacy: nothing is fetched from the network; fonts and the logo are local files.
- The page offers only the light look; Streamlit's dark mode is no longer offered, because DESIGN.md defines one paper ground.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `web-ui`: a new requirement that the page follows the shared design system (theme, fonts, label colours, logo) without loading anything from the network.
- `summary-report`: a new requirement that the report follows the shared design system and carries the logo, while staying self-contained.

## Impact

- `.streamlit/config.toml`: a `[theme]` section and `[[theme.fontFaces]]`; `server.enableStaticServing = true` (served on localhost only, like the page).
- New `static/` folder at the repo root: the four font files the theme uses and the logo SVG.
- `app.py`: `st.logo`, `set_page_config(page_icon=...)`, the target palette, the card label line (still Streamlit's colour tokens, now themed).
- `face_pipeline/report.py`: new stylesheet, embedded fonts and logo, label dots; label text and escaping unchanged.
- `docs/index.html`: logo in the masthead, favicon.
- Tests: `tests/test_report.py` and `tests/test_app.py` gain checks for the logo, the label colours and that nothing external is loaded; existing tests keep passing.
- The tour video's app screenshots are captured again afterwards (outside this change).
