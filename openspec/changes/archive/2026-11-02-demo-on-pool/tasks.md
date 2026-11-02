## 1. Local dataset

- [x] 1.1 Add `data/wikidata_plus_me/` to `.gitignore` and confirm with `git check-ignore`, before the folder exists
- [x] 1.2 Copy `data/wikidata` to `data/wikidata_plus_me`, add the user's second photo as `Me_PK/`, and index it once. Confirm its `config.json` is the pool's, and the index has 501 faces

## 2. Measure

- [x] 2.1 In Chromium, with `PK.jpg` on `wikidata`: record the top 10 with scores and labels, how many names sit in the Alter Ego band, that nobody is inside the inner ring, and that credits show on the cards
- [x] 2.2 Switch to `wikidata_plus_me` without uploading again: record `Me_PK`'s rank, score, label and ring, the best public figure's score and the report download. Then drop `data/demo/no_face.jpg` and record the error
- [x] 2.3 Run the section 1 CLI command on `data/wikidata`: same top 10 as the page, `data/results/summary.html` written, and exit code 1 with the exact message on the no-face image

## 3. Write it

- [x] 3.1 Rewrite Beats 1 and 2 and the CLI paragraph in README section 1 from the measurements in 2.x (design D4); check Beat 3 still holds
- [x] 3.2 Update README section 2's example, the privacy risk in section 5 if it would be incomplete, and section 6's self-match steps, including that the pool needs `--wikidata` first. Leave the Giguere "try this" line, which is what a plain setup gives
- [x] 3.3 Follow the new section 6 self-match steps as written, in a scratch copy, to confirm they work

## 4. Proof and record

- [x] 4.1 Walk all three beats in Chromium against the final README text, word by word
- [x] 4.2 Confirm no private photo is tracked or staged, the LFW datasets still give Giguere 0.2146 and `Me_PK` 0.4322 on `celebrities_plus_me`, and `pytest` still passes
- [x] 4.3 Replace AGENTS.md's "Next" line, append the outcome to PLANNING_LOG.md, and give the user the final section 1 for Canvas
