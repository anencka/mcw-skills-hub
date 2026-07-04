---
name: reference-management
description: Manage citations and reference libraries — accurate metadata, consistent keys, correct style, and clean BibTeX/CSL — with zero fabricated or mismatched references.
version: 1.0.0
metadata:
  hermes:
    tags: [references, citations, bibtex, zotero, bibliography]
    category: reference
---
# Reference & Literature Management

## When to Use
Adding/curating references, generating or fixing BibTeX/CSL, normalizing citation keys, building a
bibliography, or reconciling in-text citations with the reference list.

## First-use setup (read the profile; fill if thin)
Read `~/work-profile/tools-and-systems.md` (reference manager, where the library/.bib lives, how
references flow into writing) and `~/work-profile/communication-style.md` (citation style and key
convention, e.g. `authorYEARkeyword`). If either is still mostly `*(to capture)*`, offer **once**
to fill it — a few questions (hand to `onboarding-interview`, e.g. "let's do tools-and-systems")
or the operator edits it in the Files tab — then proceed; if they skip, note that in memory and
don't re-ask. **Read these fresh each use; never cache their contents — the file is the source of
truth.**

## Procedure
1. **Get metadata from the source of truth.** Pull bibliographic data from the DOI/database
   record — not from memory or a model guess. Verify authors, year, title, venue, DOI.
2. **Normalize keys** to the operator's convention; keep them unique and stable.
3. **Clean BibTeX/CSL:** correct entry types, required fields present, braces protecting
   capitalization/special chars, valid Unicode/LaTeX; no duplicate entries.
4. **Match style:** format to the target style; confirm in-text citations and the reference list
   are consistent and complete (every cite has an entry and vice versa).
5. **Reconcile** on request: list orphan citations (cited, not in library) and unused entries.
6. **Hand off** cleanly to `scientific-writing` / `grant-proposals` (keys + style).

## Pitfalls
- Fabricating a reference or a DOI, or guessing metadata — never; verify from the record.
- Inconsistent or colliding citation keys.
- BibTeX that breaks compilation (bad braces, missing fields, stray Unicode).
- Cited-but-missing or listed-but-uncited references.

## Verification
Every reference's metadata matches its real record (DOI-verified), keys are unique and follow the
convention, the .bib/CSL is valid, and in-text citations reconcile 1:1 with the reference list.
