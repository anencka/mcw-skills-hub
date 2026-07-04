---
name: specific-aims-redteam
description: Run a mock study section on a Specific Aims page or full proposal — score it like NIH reviewers (Significance, Investigator, Innovation, Approach, Environment; Overall Impact), find the fatal flaws, and rank the fixes.
version: 1.0.0
metadata:
  hermes:
    tags: [grants, review, study-section, red-team, nih]
    category: grants
---
# Specific Aims Red-Team (Mock Study Section)

## When to Use
A Specific Aims page or proposal draft is ready enough to be attacked: the operator wants
the reviewer's-eye critique **before** reviewers see it. Complements `grant-proposals`
(which builds the argument) — this skill tries to break it.

## First-use setup (read the profile; fill if thin)
Read `~/work-profile/domain-knowledge.md` (field norms, what this study section rewards and
punishes) and `~/work-profile/current-projects.md` (preliminary-data reality, so feasibility
critique is grounded in what the operator actually has). Ask which mechanism and, if known,
which study section — review culture differs.

## Procedure
1. **Read as three reviewers, not one.** Write three short independent critiques with
   different postures: the skeptical methodologist (rigor, power, controls, statistics), the
   field expert (novelty vs. what's known — is this incremental?), and the busy generalist
   (does the aims page alone convey significance and payoff in one read?).
2. **Score like the panel.** For each NIH criterion — Significance, Investigator(s),
   Innovation, Approach, Environment — give a 1-9 score with a one-paragraph justification
   in reviewer register ("enthusiasm is dampened by…"). Then an Overall Impact score with
   the summary-statement-style paragraph.
3. **Hunt the classic kills**, explicitly checking each: aims that are methods, not
   objectives; interdependent aims (Aim 2 dies if Aim 1 fails); hypothesis that is untestable
   or unfalsifiable; feasibility unsupported by preliminary data; overambition for the
   mechanism/timeline; missing rigor elements (power, sex as a biological variable,
   validation of key resources); innovation claimed but not argued; payoff that doesn't
   matter to the funder's mission.
4. **Rank the fixes.** A prioritized list: fatal (would sink the application) → major
   (drops the score) → polish. Each with the concrete edit that addresses it.
5. **Offer the rewrite loop:** hand the top fixes to `grant-proposals` to revise, then
   re-run this red-team on the new draft and report the score movement.

## Pitfalls
- Being kind. The value is in the harshest defensible critique — reviewers won't be gentler.
- Vague criticism ("strengthen the approach") — every point names the line/claim and the fix.
- Inventing field facts to support a critique; if a novelty claim needs checking, search the
  literature (hand to `literature-research`) rather than asserting.
- Scoring everything 5 (uninformative center-of-scale) — commit to the number the critique
  implies, and let the three reviewer postures disagree when they genuinely would.

## Verification
Three distinguishable reviewer critiques exist; every criterion has a score + justification;
each classic-kill check is explicitly marked found/not-found; the fix list is ranked with
concrete edits; nothing in the critique relies on an invented factual claim.
