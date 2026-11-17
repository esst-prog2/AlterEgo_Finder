## Context

DESIGN.md (written from the promo page) is the shared design system. Today the Streamlit page (app.py, Streamlit 1.66) uses the default theme and offers light and dark; its cards colour the label word with Streamlit's `:green[...]` / `:orange[...]` tokens; the similarity target picks ink, muted and faint greys per theme from `_TARGET_PALETTES`. The report (`face_pipeline/report.py`) inlines its own GitHub-grey stylesheet and colours the label word. `.streamlit/config.toml` already binds the server to localhost and turns usage statistics off; the web-ui spec forbids anything leaving the machine, and the summary-report spec requires a single self-contained file.

## Goals / Non-Goals

**Goals:**
- One look on all four surfaces, driven by Streamlit's own theme rather than injected CSS.
- The same three label colours everywhere, readable on the paper ground.
- The logo on the page's sidebar and tab, the report's header and the promo page.

**Non-Goals:**
- Any change to layout structure, widgets, wording of labels, scores, thresholds or the CLI's text output.
- A dark variant of the design system.

## Decisions

1. **Theme through `.streamlit/config.toml`, not CSS injection.** `[theme]` sets `base = "light"`, `primaryColor` navy #1d3c78, `backgroundColor` paper #eef3f8, `secondaryBackgroundColor` paper raised #f8fbfd, `textColor` ink #1f2328, `linkColor` navy, `borderColor` grid line strong, `baseRadius = "none"`, `font`/`headingFont`/`codeFont`, `headingFontWeights` 700, and `greenColor` / `orangeColor` / `grayColor` set to the three label colours. Alternative: a `<style>` block through `st.markdown(unsafe_allow_html=True)`; rejected because it targets Streamlit's internal class names, which change between versions, and the page otherwise avoids unsafe HTML.

2. **Fonts served by the app itself.** The four woff2 files the theme needs (Barlow 400 and 600, Barlow Condensed 600 and 700, SIL OFL) are copied with their licence into a new `static/fonts/` folder, `server.enableStaticServing = true`, and `[[theme.fontFaces]]` points at `app/static/fonts/...`. The server stays bound to localhost, so static files are as private as the page. Alternative: Google Fonts URLs; rejected, the page must load nothing from the network.

3. **The label word stays ink on a wash of its label colour.** On #eef3f8 paper, gold #d4a72c text reaches only about 2:1 contrast, which DESIGN.md's Don'ts forbid. Cards change from `` `0.2109` :orange[**Alter Ego**] `` to `` `0.2109` :orange-background[**Alter Ego**] ``: Streamlit's own highlight, a light wash of the themed label colour behind the ink word, the same washes the target's rings use. A drawn filled dot was tried first, but Material Symbols draw unfilled and Streamlit offers no fill setting; a Unicode dot is ruled out by the craft floor, and HTML would need unsafe markup. The colour tokens stay Streamlit's own (`green`, `orange`, `gray`), themed to the exact label colours. The test's card-line pattern is updated to the new form; the mapping of plain names to CLI labels is unchanged.

4. **The target follows the paper.** With `base = "light"`, `st.context.theme.type` is always "light"; its palette becomes ink #1f2328, muted #46505d (ink soft) and faint #8c959f, and the two threshold rings are drawn in the label colours they bound (green for Same person, gold for Alter Ego), as on the promo page's target. The dark entry stays in the code for a theme value Streamlit might still report, so nothing breaks.

5. **Logo files.** The mark is one SVG (the target in miniature) kept at `static/logo-mark.svg`, the same drawing as `video/tour/assets/logo-mark.svg`. The full lockup (mark plus "AlterEgo Finder" in Barlow Condensed) is rendered once to `static/logo-lockup.png` at 2x, because an SVG shown as an image cannot use the page's fonts. `st.logo(lockup, icon_image=mark)` puts it in the sidebar; `set_page_config(page_icon=mark)` sets the tab icon. The promo page gets the mark inline in its masthead beside the name and `docs/favicon.svg`.

6. **Report: embedded fonts and an inline logo.** The report's stylesheet is rewritten to DESIGN.md (paper ground, 2 px navy frames, square cards, label type) with Barlow 400 and Barlow Condensed 700 embedded as base64 `@font-face` (about 60 KB) and the mark as inline SVG in a header beside the name. Each classification is shown as a dot in its label colour followed by the technical label text in ink. Escaping of names and credits is unchanged.

## Risks / Trade-offs

- [Users who prefer dark mode get the light page] → DESIGN.md defines one paper ground; recorded in the proposal. A dark variant can be added later as `[theme.dark]`.
- [Streamlit theme options change in a later version] → the options used are documented in `streamlit config show` for 1.66 and pinned by `requirements-ui.txt`'s range; a missing option is ignored, not fatal.
- [Static serving exposes `static/` over HTTP] → only on localhost, and the folder holds only fonts and the logo.
- [Report size grows by the embedded fonts] → about 60 KB on a file that already embeds eleven JPEGs.
- [The tour video shows the old look] → its screens are captured again after this change, before Homework 10 is published.

## Migration Plan

No data or API migration. Rollback is reverting the commit; the config section, `static/` folder and stylesheet are self-contained.
