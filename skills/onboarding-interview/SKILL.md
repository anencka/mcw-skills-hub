---
name: onboarding-interview
description: Interview the operator one question at a time to build their work-profile portfolio (~/work-profile/*.md). Runs the core three files on first use; fills the rest on demand. Use on first contact, when a profile file is missing/thin, or when the operator says "onboard me" / "let's do <file>".
version: 2.0.0
metadata:
  hermes:
    tags: [onboarding, profile, context, portfolio, setup]
    category: onboarding
---
# Onboarding Interview

## When to Use
- **First contact**, or whenever a `~/work-profile/*.md` file you need is blank or thin.
- The operator says "onboard me", "set up my context", or **"let's do `<file>`"** (single-file mode).
- After a major change in their role, projects, or toolchain.

## The portfolio
The profile is a folder of small, visible markdown files at `~/work-profile/`
(`/home/agent/workspace/work-profile/`) — the operator can also edit them directly in the Files
tab. This skill and those files are two ways to fill the **same** documents. `identity.md` is the
read-first file. The container seeds every file pre-structured with `*(to capture)*` placeholders.

**Before interviewing, READ the relevant file(s) first** (and anything already captured in other
files). Only work on what's blank or thin — never re-ask what the operator already wrote.

## Scope: tiered, not all-at-once
- **Default onboarding = the core three**, in order: `identity.md` → `role-and-responsibilities.md`
  → `current-projects.md`. These cover most of what you need day to day. ~10 minutes.
- **The other seven** (`team-and-relationships`, `tools-and-systems`, `communication-style`,
  `goals-and-priorities`, `preferences-and-constraints`, `domain-knowledge`, `decision-log`) are
  filled **on demand** — when the operator asks, or when a domain skill first needs one.
- **Single-file mode:** if the operator says "let's do `<file>`", do just that one.

Don't try to capture everything in one sitting. The portfolio is living and improves over time.

## Procedure (per file)
1. **Read the file first.** Note what's already filled; plan to ask only about the gaps.
2. **Set up (once, at the start of a session):** say in one sentence what you're doing and that
   answers are saved to `~/work-profile/` (local files, not shared, no PHI). Invite "skip" on
   anything.
3. **Interview one question at a time.** Use the question bank in
   `references/interview-questions.md` for this file. **Ask exactly one question, then stop and
   wait.** Never ask compound questions, never present a list, never propose or pre-fill answers.
   When an answer is vague, push for a specific: "What does that look like on a Tuesday?" or "Can
   you give me an example?" Stop asking as soon as you have enough — respect their time.
4. **Draft the file in place**, filling only what you learned into the existing headings. Leave
   untouched sections as `*(to capture)*`. Write it in the operator's own words and register — it
   should sound like them, not like an AI describing them.
5. **Reaction pass.** Present the draft and say: *"Tell me what's wrong — anything that feels off,
   that I assumed, or that's missing."* If they say it's fine, ask once: *"Pick the weakest or most
   generic line and make it more specifically you."* Revise once. One push, not two — then move on.
6. **Record salient facts to your persistent memory** so you carry them between sessions.
7. **Transition** (multi-file runs): "That's `<file>` done. Next is `<file>` — `<one line>`. Ready?"
   Wait for confirmation.

## After the core three
Summarize what you captured in a few bullets, apply any corrections, and point to next steps: name
the domain skills relevant to their work, and note the remaining profile files fill in over time
(or now, if they want — "we can do communication-style whenever").

## One-question-at-a-time rules
- Never more than one question per message. Never a list of questions.
- Use what you learned in earlier files to inform later ones; don't re-ask.
- If a tangent is useful for another file, note it mentally and use it there — don't interrupt.
- If the operator skips a file or stops mid-file, note where you are so they can resume.

## Pitfalls
- **Don't pre-fill or guess.** Record only what the operator actually told you; everything else
  stays `*(to capture)*`. A blank field is the correct state — guessed values are worse than blanks
  because they get silently trusted later.
- **Don't interrogate.** Accept partial answers and move on; the portfolio is living.
- **Don't re-ask** what's already in the files.
- **Never record PHI, credentials, or anything flagged sensitive.** Confirm the no-PHI boundary;
  don't relitigate it.
- On the reaction pass, push **once**, not twice.

## Verification
The file(s) you worked on exist under `~/work-profile/`, contain the operator's real answers (not
placeholders for the sections you covered), and you read each draft back and applied corrections.
