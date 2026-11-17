## Context

See proposal.md. Person names come from `IndexEntry.person` (the dataset folder name), used raw by the verdict, `st.text` on the cards, the target's name layer and tooltip, and the alt text. The CLI prints the same raw names, and `tests/test_app.py::_cards` compares cards with the CLI's lines.

## Goals / Non-Goals

**Goals:** readable names and plain labels wherever a user reads them; public datasets first.
**Non-Goals:** the CLI's output, names inside the report (the report is the CLI's file too), renaming any folder.

## Decisions

1. **One helper, `_display_name(person) = person.replace("_", " ")`,** applied at display time only; escaping stays where it is (`html.escape` in `st.html`, `st.text`, Vega text). The target's `person` field becomes the display name, so its names and tooltips match. Tests compare cards with the CLI by applying the same helper to the CLI's names. Alternative: strip in `face_pipeline` (rejected: the CLI and report must keep folder names).
2. **Report label text** is built from a `_LABEL_TEXT` map in `report.py`; the dot colour stays keyed by the technical label.
3. **Dataset order:** a sort key `(rank of wikidata/celebrities, name)`; `_default_dataset_index` keeps picking `wikidata`. Own folders keep their exact names.
4. **Primary download:** `st.download_button(..., type="primary")` takes the theme's navy; the upload hint and file size get the caption colour (#46505d at full opacity) through `[data-testid="stFileUploaderDropzoneInstructions"]` and `[data-testid="stFileChip"]`, added to the stylesheet's id list and its test.

## Risks / Trade-offs

- [A name whose underscores are meaningful, e.g. a deliberate "a_b"] → shown with a space; the folder name is still in the CLI and the report.
