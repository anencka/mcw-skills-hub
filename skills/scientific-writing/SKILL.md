---
name: scientific-writing
description: Draft and revise academic/technical prose and manuscripts (Markdown, LaTeX, Word) in the operator's voice, with correct structure, citations, and no invented results.
version: 1.0.0
metadata:
  hermes:
    tags: [writing, manuscript, latex, markdown, editing]
    category: writing
---
# Scientific Writing & Manuscripts

## When to Use
Drafting, restructuring, or polishing papers, reports, abstracts, methods, or any academic/
technical prose — and converting between Markdown, LaTeX, and Word.

## First-use setup (read the profile; fill if thin)
Read `~/work-profile/communication-style.md` (voice, format/formatting preferences, AI-isms to
avoid), `~/work-profile/domain-knowledge.md` (field norms + how much to explain), and
`~/work-profile/identity.md` (who's authoring). If any is still mostly `*(to capture)*`, offer
**once** to fill it — a few questions (hand to `onboarding-interview`, e.g. "let's do
communication-style") or the operator edits it in the Files tab — then proceed; if they skip, note
that in memory and don't re-ask. **Read these fresh each use; never cache their contents — the file
is the source of truth.** Venue/template/citation specifics not in the profile: ask for the task at
hand (and see `reference-management`).

## Procedure
1. **Outline before prose.** Agree the section structure and the argument each section must make;
   confirm key claims and which results/citations support them.
2. **Draft in the operator's format and voice.** Match their tense/person/hedging. Keep claims
   tied to evidence the operator has supplied — **never invent data, numbers, or results.**
3. **Citations:** use the operator's style + manager; insert real keys/DOIs only. Mark any
   needed-but-missing citation as `[CITATION NEEDED: ...]` rather than fabricating one.
4. **For LaTeX:** sanitize Unicode to LaTeX equivalents (×→\times, →→\rightarrow, µ→\mu, etc.);
   keep the document compilable; report build errors with the offending line.
5. **Convert** between formats with `pandoc` (md⇄docx, md→pdf via LaTeX); preserve refs/figures.
6. **Revise in passes:** structure → argument/evidence → clarity/concision → grammar/style. Show
   a diff or change summary so the operator can review.

## Pitfalls
- Inventing results, citations, or significance claims — never.
- Drifting from the operator's voice into generic "AI" prose.
- LaTeX that won't compile (stray Unicode, unbalanced braces, missing packages).
- Over-editing meaning while "polishing"; preserve the author's intent and claims.

## Verification
The document is in the requested format and compiles/opens; every claim traces to supplied
evidence; citations are real and in the right style; the operator's voice is intact.
