---
name: plain-language-summary
description: Rewrite scientific or administrative content at a target reading level — funder-required lay summaries, participant-facing materials, community communications — with a readability score to prove it.
version: 1.0.0
metadata:
  hermes:
    tags: [writing, plain-language, lay-summary, readability, community]
    category: writing
    related_skills: [scientific-writing, brand-guidelines]
---
# Plain-Language Summary

## When to Use
A funder requires a lay/public abstract; a consent form, recruitment flyer, patient-facing
page, or community newsletter needs to land at a specific reading level; or the operator
says "explain this for a general audience."

## First-use setup (read the profile; fill if thin)
Read `~/work-profile/communication-style.md` and, for outward-facing materials,
`brand-guidelines`. Ask two anchors up front if not given: **audience** (general public,
patients, 8th-grade, funders' lay reviewers, press) and **target reading level** (default:
6th–8th grade for patient/community materials; NIH lay abstracts aim for an educated
non-specialist).

## Procedure
1. **Extract the load-bearing content first**: what was/will be done, why it matters to the
   reader, what changes for them. Cut everything that only matters to specialists.
2. **Rewrite, don't decorate**: short sentences (aim under 20 words); active voice; one idea
   per sentence; concrete verbs; second person where appropriate. Replace every term of art
   or expand it on first use — "high blood pressure (hypertension)", not the reverse.
   Numbers as people-scale comparisons ("about 1 in 5"), not rates per 100,000.
3. **Score it honestly.** Compute Flesch-Kincaid grade level and Flesch Reading Ease with a
   small script (count sentences, words, syllables — do the arithmetic in code, not in your
   head) and report the numbers. If above target, shorten sentences and swap polysyllables,
   then re-score; iterate until the target is met or the operator accepts the level.
4. **Accuracy pass against the source**: plain never means wrong. No overclaiming (research
   "may help", it doesn't "will cure"), no dropped caveats that change meaning, no invented
   examples presented as fact.
5. **Deliver** the summary plus the scores and a one-line note of anything simplification
   necessarily blurred, so the operator can judge the trade.
6. For translations of the finished plain-language text, draft, then **back-translate** to
   English and compare — flag every drift for a human bilingual check; machine translation
   alone is not a clinical-materials pipeline.

## Pitfalls
- Reporting a reading level you didn't compute — always run the score in code.
- "Plain" text that's still structured like a paper (background → methods → …). Lead with
  what the reader cares about.
- Patronizing tone. Plain language is respectful and direct, not dumbed down.
- Losing a safety-relevant caveat (side effects, limitations, eligibility) in the cut —
  those survive every simplification.

## Verification
Computed readability scores meet the stated target (or the operator accepted the gap);
a claim-by-claim check against the source found no meaning changes; audience and level are
recorded with the deliverable.
