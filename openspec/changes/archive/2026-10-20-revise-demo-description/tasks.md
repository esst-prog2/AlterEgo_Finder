## 1. Rewrite README sections

- [x] 1.1 Rewrite section 1 as the three beats in proposal.md (lookalike LOW_CONFIDENCE, self-match HIGH_CONFIDENCE via the dataset dropdown, no-face error), present tense, with the scores from the logged runs (0.2146, 0.4322) and one sentence on how `data/celebrities_plus_me/` is made; verify by reading it against proposal.md and checking that "100 ms", "true identity verification" and "mathematically accurate" do not appear (`grep -n` on README.md)
- [x] 1.2 Update section 2 (The shape) to name the local browser page as a second front end on the same pipeline; verify the in/out lines still match what `match.py` does today
- [x] 1.3 Update section 3: add the local Streamlit UI to the scope, narrow "Full web application / React frontend dashboard" to a hosted, multi-user web application, and leave "Automated web scraping or live downloads from external image APIs" in "Not this term"; verify that no Wikidata or online-pool text was added (`grep -ni wikidata README.md` prints nothing)
- [x] 1.4 Update section 5's privacy mitigation: the web UI runs only on localhost, and the uploaded photo is processed on this machine and never sent anywhere; verify that the existing note on the one-time model-weight download is kept

## 2. Check and record

- [x] 2.1 Check that every fact in sections 1-5 is true of the repo or is planned by `streamlit-web-ui` (file paths exist or are gitignored on purpose, scores match PLANNING_LOG.md 2026-10-08 and 2026-10-16), and that section 4 is unchanged (`git diff README.md` shows no section-4 lines)
- [x] 2.2 Run `openspec validate revise-demo-description --strict` and verify it passes with `skip_specs: true`
- [x] 2.3 Append the outcome to PLANNING_LOG.md, and copy the final section 1 for the Canvas hand-in
