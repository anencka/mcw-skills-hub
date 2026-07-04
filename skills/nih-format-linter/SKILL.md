---
name: nih-format-linter
description: Mechanically check a grant document against the funder's format and structure rules — required sections, page/word budgets, aims count, citation hygiene, attachment checklist — and report pass/fail per rule. Honest about what needs the final PDF.
version: 1.0.0
metadata:
  hermes:
    tags: [grants, nih, compliance, linter, checklist]
    category: grants
---
# Grant Format Linter

## When to Use
A proposal draft is nearing submission and the operator wants a compliance pass: is anything
missing, over budget, or structurally wrong before the grants office sees it?

## Ground rules
This is a **mechanical lint, not a scientific review** (that's `specific-aims-redteam` /
`grant-proposals`). Report findings as a checklist with pass / fail / can't-verify-from-source
for every rule. Never silently skip a rule.

## Procedure
1. **Identify the ruleset.** Ask which funder/mechanism and fetch the current instructions if
   there's any doubt (NIH: the How-to-Apply application guide and the specific FOA — the FOA
   overrides the general guide). Quote the rules you're linting against with their source.
2. **Structural checks** (verifiable from the draft text):
   - Required sections present and in order (e.g. R01 Research Strategy = Significance,
     Innovation, Approach; Aims page separate).
   - Aims page: one page; aims are objectives, not methods; count matches what Approach
     delivers.
   - Page/word budgets: estimate pages honestly (≈500-560 words/page at 11-pt Arial,
     0.5-inch margins, single-spaced, no figures); state the estimate AND that the real
     check is the rendered PDF.
   - Citation hygiene: every `[NEED CITATION]`/`[TODO]` flagged; references complete; no
     URLs in the Research Strategy where the funder forbids hyperlinks.
   - Figures/tables referenced in text actually exist, and vice versa.
   - Forbidden content per current rules (e.g. no hypertext links except where allowed, no
     appendix material smuggled into strategy sections).
3. **Attachment checklist**: from the FOA, list every required document (biosketches, Other
   Support if JIT, facilities, equipment, budget justification, human subjects/vertebrate
   animals sections, authentication of resources, letters) and mark which exist in the
   workspace folder vs missing.
4. **Can't-verify list** — be explicit: font size, margins, line spacing, and true page
   counts are properties of the **final rendered PDF**; tell the operator to confirm those
   on the PDF and how (open it, check fonts embedded, count pages).
5. **Deliver** the lint report as a table (rule — source — status — where/what to fix),
   worst first. Offer to fix the mechanical failures directly in the draft.

## Pitfalls
- Linting against remembered rules when the FOA differs — the FOA always wins; fetch it.
- Claiming a page count is compliant from a word count alone — it's an estimate; say so.
- Passing a section because a heading exists while its required content is missing (e.g. a
  rigor/statistics paragraph, sex-as-a-biological-variable, dissemination plans).
- Rewriting science during a lint. Flag; don't editorialize.

## Verification
Every rule in the report cites its source; every fail has a location and a concrete fix;
the can't-verify list is present; nothing in the FOA's required-documents list is
unaccounted for.
