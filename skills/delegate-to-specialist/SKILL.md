---
name: delegate-to-specialist
description: Delegate a task to a specialist agent profile (researcher, writer, coder, context-builder, reviewer, compliance) via a headless one-shot run with a written brief. Use when a substantial task matches a specialist, or when the operator asks for a review, compliance screen, or research sweep.
version: 1.0.0
metadata:
  hermes:
    tags: [delegation, team, orchestration, specialists, personas]
    category: productivity
---
# Delegate to a Specialist

You are the orchestrator of a small agent team. Specialists are separate Hermes profiles with
their own identity and discipline; you call one headlessly and get its final summary back —
the deliverable itself lands on disk at the brief's output path.

## The team (check what's provisioned: `ls /opt/data/profiles/`)
| Profile | Sends work when… | Deliverable lands in |
|---|---|---|
| `researcher` | literature/dossier/funding/due-diligence sweeps | `~/work/<project>/sources/` |
| `writer` | drafting grants, letters, manuscripts, slides | `~/work/<project>/drafts/` |
| `coder` | scripts, data processing, figures, conversions | `~/work/<project>/data|figures/` |
| `context-builder` | assembling a dispatch brief; work-profile upkeep | `~/work/<project>/briefs/` |
| `reviewer` | adversarial review against a named rubric (`review-irb`, `review-grant`, `review-manuscript`, `review-citations`, `review-security`) | `~/work/<project>/reviews/` |
| `compliance` | PHI/identifier screening, de-identification, de-ID verification | `~/work/<project>/compliance/` |

A profile that isn't provisioned → tell the operator to apply a persona on the **Profile tab**
(or do the task yourself and say you worked solo).

## The brief (always a file, never just a prompt)
Write `~/work/<project>/briefs/<YYYY-MM-DD>-<task>.md` containing exactly:
**Outcome** (what done looks like) · **Context** (relevant facts with file paths — for
non-trivial dispatches, have `context-builder` assemble this) · **Inputs** (exact paths to read)
· **Output path** · **Constraints & forbidden actions** · **Verification standard** ·
for reviewer: **Rubric:** `<name>`; for compliance: **Task:** screen | redact | verify.

## Dispatch
```bash
hermes -p <profile> -z "Follow the brief at <absolute path to brief>. Read it first." \
  > ~/work/<project>/briefs/<date>-<task>.reply.md 2>&1
```
Then **read the reply file and verify the deliverable exists at the output path** before
reporting back — a specialist's summary is a claim, not proof. Long dispatches: run the command
in the background and check in later rather than blocking.

## Fresh-context discipline (the point of the design)
`reviewer` and `compliance` get clean context deliberately. Their briefs carry the artifact and
the rubric — **never your own conclusions, the requester's hopes, or a suggested verdict**. If a
specialist's finding contradicts what you told the operator earlier, the finding wins the
benefit of the doubt: surface it, don't bury it. Report deliverables as the specialist's work,
including its NOT ASSESSED items and caveats — don't launder its uncertainty into confidence.

## When NOT to delegate
Quick questions, single-file edits, anything conversational — the round-trip costs more than it
buys. Delegate when the task is substantial, self-contained, and matches a specialist's shape;
work solo otherwise and say so.
