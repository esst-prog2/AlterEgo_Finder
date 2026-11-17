## 1. Shared assets

- [x] 1.1 Create `static/fonts/` with Barlow 400 and 600 and Barlow Condensed 600 and 700 (copied from `docs/fonts/`) and `OFL-barlow.txt`; verify the five files are present and the woff2 sizes match `docs/fonts/`.
- [x] 1.2 Save the mark as `static/logo-mark.svg` (same drawing as `video/tour/assets/logo-mark.svg`) and render the lockup (mark plus "AlterEgo Finder" in Barlow Condensed 700) to `static/logo-lockup.png` at 2x with a transparent background; verify by opening both images.

## 2. The web page

- [x] 2.1 Add the `[theme]` section, `[[theme.fontFaces]]` and `server.enableStaticServing = true` to `.streamlit/config.toml` (keeping `address = "localhost"` and usage statistics off); verify `streamlit config show` reports the values and `http://localhost:8501/app/static/fonts/barlow-latin-400-normal.woff2` returns 200 while the page runs.
- [x] 2.2 In `app.py`, call `st.logo` with the lockup and the mark and set `page_icon` to the mark; verify in a browser that the sidebar shows the logo and the tab shows the icon.
- [x] 2.3 Change the card label line to `` `score` :color-background[**Plain name**] `` and update `CARD_LINE` in `tests/test_app.py`; verify `pytest tests/test_app.py` passes.
- [x] 2.4 Update the target palette (ink, ink soft, not-you grey) and draw the high ring in green and the low ring in gold; verify `pytest tests/test_app.py tests/test_target.py` passes and a screenshot shows the coloured rings.
- [x] 2.5 Add tests: the config's label colours equal the target's label colours (#1a7f37, #d4a72c, #8c959f), and the page's config loads no font or stylesheet from a non-local URL; verify they pass.

## 3. The report

- [x] 3.1 Rewrite the report's stylesheet in `face_pipeline/report.py` to DESIGN.md with embedded Barlow 400 and Barlow Condensed 700 and an inline logo header; show each classification as a coloured dot plus the label text; verify `pytest tests/test_report.py` passes.
- [x] 3.2 Add tests: the report contains the logo inline, a dot colour per classification, and no `http`/`https` reference except credit source links; verify they pass.

## 4. The promo page

- [x] 4.1 Add the mark beside the name in `docs/index.html`'s masthead and `docs/favicon.svg` as its icon; verify on desktop and phone screenshots that the masthead still fits and nothing overflows.

## 5. Check the whole

- [x] 5.1 Run the full test suite (`python -m pytest tests/`) and verify every test passes.
- [x] 5.2 Run the app on the pool with the DiCaprio photo, take screenshots of the empty page, the result and the cards, and verify they follow DESIGN.md (paper, navy, fonts, label dots, logo) and that the browser made no request to a host other than localhost.
- [x] 5.3 Open a rendered `summary.html` from disk with networking off and verify fonts, logo and images display.
