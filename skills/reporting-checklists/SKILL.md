---
name: reporting-checklists
description: Audit a manuscript or protocol against the right reporting guideline — CONSORT, PRISMA, STROBE, ARRIVE, SPIRIT, CARE — item by item, with locations, gaps, and the filled checklist journals require at submission.
version: 1.0.0
metadata:
  hermes:
    tags: [writing, reporting, consort, prisma, strobe, arrive, compliance]
    category: writing
    related_skills: [scientific-writing, response-to-reviewers]
---
# Reporting-Guideline Checklists

## When to Use
A manuscript or protocol is heading to submission and the journal requires a completed
reporting checklist, or the operator wants the gaps found before an editor does.

## Pick the right guideline
Match design → guideline: randomized trial → **CONSORT** (protocol → **SPIRIT**); systematic
review/meta-analysis → **PRISMA**; observational (cohort/case-control/cross-sectional) →
**STROBE**; animal research → **ARRIVE**; case report → **CARE**; diagnostic accuracy →
**STARD**; prediction models → **TRIPOD**. If unsure, ask about the design, or check the
EQUATOR Network catalog (equator-network.org). Journals may mandate a specific version —
use the version the journal names; when in doubt, fetch the current checklist from the
guideline's official site rather than reciting items from memory.

## Procedure
1. **Confirm design + guideline + version** with the operator; fetch the official checklist
   items so the audit runs against the real, current wording.
2. **Audit item by item.** For each checklist item: reported / partially / not reported /
   not applicable (with justification), plus the exact location (section, page/paragraph)
   when reported. Quote the manuscript text that satisfies the item — no charitable
   hand-waving.
3. **Report the gaps** in priority order: items editors/reviewers most often bounce
   (e.g. CONSORT flow diagram and randomization details; PRISMA search strategy and flow
   diagram; ARRIVE sample-size justification; STROBE bias discussion). For each gap,
   draft the sentence-level fix or the data the operator must supply.
4. **Produce the submission artifact**: the filled checklist as a table (item — page/section
   — status) in the format journals accept, saved beside the manuscript.
5. **Flow diagrams:** if one is required and missing, draft it (participant/study flow
   numbers come from the operator or the manuscript — never invent an N) as a mermaid or
   drawio file the operator can refine in the editor.
6. Re-run after revisions; the checklist locations must track the final page numbers.

## Pitfalls
- Auditing against a remembered or outdated checklist — item wording and numbering change
  between versions; fetch the current one.
- Marking an item "reported" because the topic is mentioned, when the item's specifics
  (e.g. who was blinded, how randomization was concealed) are absent.
- Inventing Ns, dates, or search strings for diagrams and PRISMA items.
- Forgetting that N/A needs a stated reason, not a shrug.

## Verification
Every item of the correct, current guideline is dispositioned; every "reported" has a
location and supporting quote; gaps carry concrete fixes; the filled checklist file exists
beside the manuscript and matches its latest revision.
