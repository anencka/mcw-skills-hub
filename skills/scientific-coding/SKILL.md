---
name: scientific-coding
description: Write, debug, and refactor code for research and analysis — matching the operator's stack and repo conventions, with verification (run it, test it) before claiming it works.
version: 1.0.0
metadata:
  hermes:
    tags: [coding, python, refactor, debugging, tests]
    category: coding
---
# Scientific & Research Coding

## When to Use
Writing scripts/notebooks/modules, debugging, refactoring, adding tests, or extending an existing
codebase for research, analysis, or tooling.

## First-use setup (read the profile; fill if thin)
Read `~/work-profile/tools-and-systems.md` (languages/libraries, env manager, where code lives,
repo + test conventions) and `~/work-profile/preferences-and-constraints.md` (output rules; what
to never do without asking). If either is still mostly `*(to capture)*`, offer **once** to fill it
— a few questions (hand to `onboarding-interview`, e.g. "let's do tools-and-systems") or the
operator edits it in the Files tab — then proceed; if they skip, note that in memory and don't
re-ask. **Read these fresh each use; never cache their contents — the file is the source of truth.**
Confirm before commits/pushes (a standing rule).

## Procedure
1. **Read before writing.** Inspect the surrounding code and match its style, naming, and idioms;
   don't impose a foreign pattern.
2. **State the plan** (files to touch, approach) for non-trivial work; confirm if it's risky.
3. **Make focused changes**, then **run them** — execute the script/tests, read the actual
   output. Do not claim success you haven't observed.
4. **Add or update tests** for new behavior where a test framework exists.
5. **Debug methodically:** reproduce → isolate (prints/logging/minimal case) → fix root cause →
   re-run to confirm. Explain the cause, not just the patch.
6. **Show a diff/summary.** Keep changes reviewable. Don't reformat unrelated code.
7. **Version control:** only commit/push when asked; write clear messages; never commit secrets,
   large data, or credentials.

## Pitfalls
- Claiming code works without running it.
- Sprawling rewrites when a targeted fix suffices; reformatting unrelated lines.
- Inventing API/library behavior — check the docs or test it.
- Committing secrets, data, or env files; pushing without approval.

## Verification
The code runs and produces the intended result (shown, not assumed); tests pass; the diff is
focused and matches repo conventions; nothing sensitive was committed.
