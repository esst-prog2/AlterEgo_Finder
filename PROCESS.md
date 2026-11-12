# Process

How the promo page (Homework 9) was made: after each step, one row with the step, what the tool did, and what I decided.

| Step | What the tool did | What I decided |
|---|---|---|
| 1. Working rule | Saved the rule for this session and later ones, created this file and the branch `promo-page` from the latest `main`. | After each step from now on, commit, and add a row to PROCESS.md: the step, what the tool did, and what I decided. |
| 3a. Install Impeccable | Read the install steps on impeccable.style and checked the npm package matches its GitHub repo (pbakaus/impeccable). Installed version 4.8.2 into this project for Claude Code only, without automatic hooks (`npx impeccable install --project --no-hooks --providers=claude`): the skills, 4 agents and a 21 MB Windows program, which runs here. | Keep Impeccable out of git, since it is a tool for making the page, not part of the program. Turn its anonymous usage data off. |
| 2a. Install gstack | Cloned gstack (garrytan/gstack, v1.99.2.0) into the user-level skills folder, read its setup script, installed Bun 1.4.4 with winget because setup needs it, and ran `./setup`. It registered gstack's skills (including `/office-hours`) for Claude Code, downloaded a 123 MB headless Chromium, and added one Stop hook to the global Claude Code settings, after backing them up. `/cso` is unavailable without the C++ build tools. | Install Bun with winget. Run setup with its default options. |
