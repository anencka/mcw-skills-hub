---
name: review-citations
description: Rubric pack for the reviewer specialist — verify that a document's citations exist, are correctly attributed, and actually support the claims made on them. Use when a brief names the review-citations rubric.
version: 1.0.0
metadata:
  hermes:
    tags: [review, citations, verification, references, rubric]
    category: review
---
# Citation Verification (rubric)

Fabricated and mis-supporting citations are the single most damaging error class in AI-assisted
writing. Assume every citation is wrong until verified. This rubric REQUIRES live lookup — if the
brief's toolset denies web access, report NOT ASSESSED for existence checks rather than
"verifying" from memory (your memory of a paper is not verification).

## Procedure — for every citation in the document
1. **Existence:** find the actual work (DOI resolver, PubMed, Crossref, publisher page, arXiv).
   Record the resolved URL/DOI.
2. **Attribution accuracy:** authors, year, title, venue, volume/pages match the reference entry.
   Small errors (year off by one, mangled author initials) are findings too.
3. **Support check** — the important one: read at least the abstract (the relevant section when
   the claim is specific) and grade whether the cited work supports the claim made at the
   citation site:
   - **SUPPORTS** — the work says what the document uses it for.
   - **PARTIAL** — related but weaker/narrower than the claim (quote both sides).
   - **DOES NOT SUPPORT** — the work says something else (or the opposite).
   - **NOT FOUND** — could not locate the work at all: treat as presumed-fabricated and
     highest severity.
4. **Coverage spot-check:** note claims that *need* a citation and lack one (quantitative
   assertions, "studies show", prior-work characterizations).

## Output
Memo to the brief's output path: a verification table (cite # / entry / resolved DOI-URL /
attribution OK? / support grade / evidence quote), findings ordered NOT FOUND → DOES NOT
SUPPORT → PARTIAL → attribution errors, and a ≤10-line summary with counts per grade. State
plainly how many citations were checked out of how many present; a partial pass must say so.
