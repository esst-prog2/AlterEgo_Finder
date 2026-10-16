## 1. Tests for the default paths

- [ ] 1.1 Add a match.py test: dataset at tmp/data/celebrities with tmp/data/config.json (low 0.0, high 1.0) and no --config or threshold flags; verify exit 0 and no HIGH_CONFIDENCE labels (the config was read)
- [ ] 1.2 Add a calibrate.py test: calibration fixtures copied to tmp/data/calibration, no --config-out; verify tmp/data/config.json is written with both thresholds
- [ ] 1.3 Red/green: point match.py's default config path at dataset_path / "config.json" and verify test 1.1 fails; restore and verify all tests pass; log both runs

## 2. Docs

- [ ] 2.1 Check README, AGENTS.md and the two CLIs' --help texts describe the same default paths (help texts were fixed in HW6 review 4); verify by reading them
