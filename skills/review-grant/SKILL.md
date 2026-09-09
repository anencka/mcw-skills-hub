---
name: review-grant
description: Rubric pack for the reviewer specialist — compliance and study-section-style critique of a grant application against its RFA/FOA. Use when a brief names the review-grant rubric.
version: 1.0.0
metadata:
  hermes:
    tags: [review, grants, rfa, compliance, rubric]
    category: review
---
# Grant Application Review (rubric)

Two passes, kept separate in the memo: a **compliance audit** (binary, against the announcement)
and a **reviewer-style critique** (judgment, clearly labeled as such). The brief should provide
the application draft *and* the RFA/FOA (or its extracted requirements); reviewing a draft
without its announcement is a finding, not an obstacle to work around.

## Pass 1 — Compliance audit (answer every item; cite the RFA line and the draft location)
1. **Responsiveness:** does the proposed work match the announcement's stated scope, purposes,
   and any required elements? List each RFA "must/required" phrase and where the draft satisfies
   it — or doesn't.
2. **Structure:** every required section/attachment present (aims, strategy, required plans —
   e.g., data sharing, authentication, human-subjects/vertebrate docs, letters); nothing required
   is missing, nothing prohibited is included.
3. **Limits:** page limits, budget caps and allowable costs, eligibility constraints, font/format
   rules if stated, deadline realities the requester flagged.
4. **Internal consistency:** budget ↔ personnel ↔ proposed work; timeline ↔ aims; facilities
   claims ↔ what the science needs; numbers that appear in multiple places agree.
5. **Citation integrity:** spot-check references — do the cited works exist and plausibly support
   the claims made on them? (Escalate a full pass to `review-citations` when the brief asks.)

## Pass 2 — Reviewer-style critique (label as judgment, mirror the funder's criteria)
Score-driving questions in the funder's own vocabulary (for NIH: Significance, Innovation,
Approach, Investigator, Environment; for others, the announcement's stated criteria). For each:
the strongest point, the most exploitable weakness a skeptical panelist would raise, and the
single highest-leverage fix. Call out: aims that are dependent on each other's success,
underpowered or vague evaluation plans, overclaiming, and rigor/reproducibility gaps.

## Output
Memo to the brief's output path: compliance table first (item / requirement / where satisfied /
CONFIRMED-PLAUSIBLE-FAIL-NOT ASSESSED), then the labeled critique, then the ≤10-line summary
with the three fixes that would most change the outcome.
