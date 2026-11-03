## Why

Homework 8 asks for the final demo description in three to six sentences, pasted on Canvas
and identical to README section 1. Section 1 is about 20 sentences and 460 words. The demo
itself still fits the brief: the path, tense, filenames and numbers stay. Only the length
has to change, and this is the last point where section 1 can change.

## What Changes

- **README section 1** becomes these six sentences:

  > I run `streamlit run app.py`, open `http://localhost:8501`, pick the `wikidata` dataset
  > (500 well-known people, one licensed Wikimedia Commons photo each) and drop
  > `data/my_photo/PK.jpg` on the page, which never leaves my machine. The page shows the ten
  > closest public figures as cards with scores and plain labels, next to a similarity target
  > with me at the centre and every face at a distance of exactly one minus its score. The top
  > card is Psy at 0.2702, labelled *Alter Ego*, and nobody reaches the inner *Same person*
  > ring at 0.3706. I switch the dropdown to `wikidata_plus_me`, which adds a second photo of
  > me from another day, and `Me_PK` jumps to first at 0.4322, labelled *Same person*, the one
  > face inside that ring. It is one self-match, at a threshold about 1 in 100 people absent
  > from the dataset would still reach: evidence that the labels mean something, not proof of
  > identity. Finally I drop `data/demo/no_face.jpg`, and the page shows "No face detected"
  > instead of cards.

- **Left out of section 1, not removed from the program:** the CLI run and the report
  download, which section 2 already names, and the card counts, hover photos, photo credits
  and threshold slider, which can go on the slides.
- **README section 6:** the "(Beat 2)" heading no longer has a beat to point to, so it is
  reworded.
- **AGENTS.md:** the demo status is brought up to date.
- **`setup_data.py`'s docstring:** it says section 1's scores reproduce with LFW, which has
  been out of date since section 1 moved onto the pool. It points to section 6's LFW score.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None: no requirement names the demo's text. This change declares `skip_specs`.

## Impact

- Documentation, and one docstring. No behaviour changes.
- The Homework 8 text is the new section 1, pasted after this change is merged.
