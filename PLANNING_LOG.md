# Planning Log

One line per decision: date, what was decided, who decided it. Append-only — never edit or remove earlier lines.

- 2026-09-22: Adopted this log — every project decision (requirement, number, name, tool) gets one append-only line here. Decided by user.
- 2026-09-22: Adopted OpenSpec CLI (@fission-ai/openspec) v1.13.0 as the spec-driven workflow tool for this repo, configured for Claude Code; Node.js 24.19.0 LTS installed as a prerequisite. Decided by user.
- 2026-09-22: Added AGENTS.md at repo root summarizing project status, the OpenSpec workflow, and the PLANNING_LOG.md convention. Decided by user.
- 2026-09-22: Restructured the planning-log rule in AGENTS.md as a "## Planning log" section (not a blockquote) and added CLAUDE.md as a one-line pointer (`@AGENTS.md`) so Claude Code loads it. Decided by user.
- 2026-09-22: Set global git identity to user.name "prokof2123", user.email "prokof21@gmail.com" (previously unset at both local and global scope). Decided by user.
- 2026-09-22: Chose OpenCV DNN + OpenFace (nn4.small2.v1) for the 128-d face embedding, over face_recognition/dlib, to keep install easy for a grader on Windows (pip-installable prebuilt wheel, no CMake/build tools). Decided by user.
- 2026-09-22: Chose OpenCV's DNN-based face detector (Caffe SSD, res10_300x300) to pair with OpenFace, keeping the same install story (no extra dependency). Decided by user.
- 2026-09-22: data/celebrities/ uses the standard LFW layout, one subfolder per person (data/celebrities/<person_name>/<image_name>.jpg), so match attribution is Path(match).parent.name with no separate metadata/mapping file. Decided by user.
- 2026-09-22: The 0.68 threshold is a configurable CLI parameter of match.py (--threshold, default 0.68), pre-calculated offline by a separate calibrate.py script rather than recomputed at runtime, to keep match.py under the 100ms budget. Decided by user.
- 2026-09-22: calibrate.py writes its computed threshold to data/config.json ({"threshold": 0.68}); match.py loads its --threshold default from that file if present, with manual CLI override still allowed, so the two scripts stay in sync without hand-copying. Decided by user.
- 2026-09-22: data/calibration/ holds a set of LFW identities fully disjoint from data/celebrities/; calibrate.py computes intra-/inter-class distances only on data/calibration/, so match.py's search index never sees the calibration identities. Decided by user.
- 2026-09-22: Confirmed the three-change split (core pipeline / calibration / report) and captured Change 1 as the OpenSpec change "add-face-matching-cli" (proposal, design, two capability specs face-embedding + face-matching-cli, tasks) — validated, ready for implementation. Decided by user.
- 2026-09-22: Within add-face-matching-cli's design, chose to vendor the ~40MB of pretrained model weights (OpenCV SSD detector + OpenFace nn4.small2.v1) directly in the repo rather than download them at first run, to preserve the project's offline-only claim and avoid a network failure mode. Decided by agent.
- 2026-09-22: Implemented add-face-matching-cli end to end (all 16 tasks): match.py CLI, face_pipeline/{detector,embedder,index}.py, vendored model weights, requirements.txt/-dev.txt, and 15 passing tests. Loosened numpy's pin from <2 to unpinned after discovering numpy<2 has no Python 3.13 wheel on Windows and would otherwise try to compile from source. Decided by agent.
- 2026-09-22: Synced add-face-matching-cli's delta specs into openspec/specs/{face-embedding,face-matching-cli}/spec.md as the project's first durable capability specs, and archived the change to openspec/changes/archive/2026-09-22-add-face-matching-cli/. Decided by user.
