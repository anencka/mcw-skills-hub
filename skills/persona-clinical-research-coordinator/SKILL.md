---
name: persona-clinical-research-coordinator
description: Persona pack — Clinical Research Coordinator. Installing it adds a "Clinical Research Coordinator" user persona to the Profile tab picker (writer/context-builder/reviewer/compliance team, IRB + citation rubrics, CRC-tuned work-profile prefills). It composes the baked specialist archetypes; it adds no new agents and no new tools.
version: 1.0.0
metadata:
  hermes:
    tags: [persona, clinical-research, coordinator, irb, compliance]
    category: personas
    curated: true
    persona: clinical-research-coordinator
    owner: mcwAgent maintainers
---
# Persona pack: Clinical Research Coordinator

This is a **persona pack**, not an executable skill: installing it delivers the
`persona.yaml` manifest (plus role-tuned work-profile prefills) that the web app's
**Profile tab** offers as a selectable user persona. It is the hub-delivered extension
path from PERSONAS_PLAN.md phase 3 — institutions add personas by publishing packs like
this one, with no container image rebuild.

## What applying the persona does
- Sets the orchestrator's persona overlay for coordinator work: protocol logistics,
  participant scheduling, source-document prep, IRB submissions and continuing reviews,
  monitor-visit readiness.
- Provisions the **writer**, **context-builder**, **reviewer**, and **compliance**
  specialists (baked archetypes — this pack cannot introduce new agents or tools).
- Installs role-tuned prefills for `role-and-responsibilities.md` and
  `domain-knowledge.md` (marked `Persona-prefilled`; the onboarding interview confirms
  and fills them with the operator).

## For the agent
If the operator asks about this skill: explain that it takes effect from the Profile
tab ("apply persona"), not by invoking it in conversation. Never treat the prefill
templates as facts about the operator.
