---
name: review-irb
description: Rubric pack for the reviewer specialist — checklist-driven review of an IRB protocol packet (protocol/SmartForm, consent forms, recruitment materials) against the federal approval criteria. Use when a brief names the review-irb rubric.
version: 1.0.0
metadata:
  hermes:
    tags: [review, irb, regulatory, human-subjects, rubric]
    category: review
---
# IRB Protocol Review (rubric)

Adversarial, checklist-driven review of a human-subjects protocol packet. You are producing a
**reviewer's memo an IRB member could start from** — findings with citations into the packet —
not an approval decision. Never guess: every answer cites the protocol section and quotes it, or
is marked NOT ASSESSED with the reason (e.g., document not provided).

## Inputs to expect in the brief
The protocol/application (SmartForm PDF or equivalent), consent form(s), and any recruitment
materials. If consent forms are referenced but missing, that is itself a finding.

## Rubric

### A. Approval criteria (45 CFR 46.111 — answer every one)
1. Risks minimized — sound design; procedures already performed for other purposes used where possible.
2. Risks reasonable relative to anticipated benefits and importance of knowledge.
3. Subject selection equitable — recruitment source, inclusion/exclusion justified; no convenience
   targeting of vulnerable groups.
4. Informed consent will be **sought** from each subject or LAR (or waiver properly justified).
5. Informed consent will be **documented** (or documentation waiver justified).
6. Data monitored for safety where appropriate (DSMB/monitoring plan matches risk).
7. Privacy protected and confidentiality of data maintained (storage, coding, sharing plans).
8. Additional safeguards for vulnerable subjects (children, prisoners, impaired
   decision-making, economically/educationally disadvantaged).

### B. Consent form contents (46.116 basic elements — check each against the actual form)
Research statement + purpose/duration/procedures; risks; benefits; alternatives; confidentiality;
compensation/injury language (greater-than-minimal-risk only); contacts for questions/rights/
injury; voluntary participation + no penalty for withdrawal; plus applicable additional elements
(unforeseeable risks, involuntary termination, added costs, withdrawal consequences, new
findings, number of subjects). Flag readability (target ~8th grade) and any exculpatory language.

### C. Special determinations (when applicable)
- **Children (Subpart D):** correct 46.404/405/406/407 category with justification; assent plan
  and parental permission (one vs. both signatures) match the category.
- **Waivers:** consent waiver/alteration (46.116(f)) and HIPAA waiver criteria individually
  addressed, not asserted.
- **Recruitment materials:** no undue inducement, no overstated benefit, no "new treatment"
  framing, compensation not emphasized, required elements present.

## Output
Memo to the brief's output path: verdict summary; findings ordered by severity, each with rubric
item, packet location, direct quote, and CONFIRMED/PLAUSIBLE grade; then the full item-by-item
table including passes and NOT ASSESSED items. Close with: *"Advisory analysis to support — not
replace — IRB member review."*
