---
name: deadline-sentinel
description: The daily deadline watch — read the task registry, escalate what's overdue or entering its warning window, and email the operator a short, honest nag. Designed to run unattended on a schedule.
version: 1.0.0
metadata:
  hermes:
    tags: [productivity, deadlines, digest, cron, sentinel]
    category: productivity
    related_skills: [task-tracker, email-and-scheduling, funding-opportunity-digest]
    blueprint:
      schedule: "0 11 * * 1-5"
      prompt: "Run the deadline-sentinel skill: read the task registry via the task-tracker CLI's `due` command, and if anything is overdue or inside its warning window, email the operator a short prioritized digest via himalaya. If nothing needs attention, send nothing."
---
# Deadline Sentinel

## When to Use
As a scheduled job (weekday mornings — see the blueprint), or when the operator asks
"anything about to bite me?". This skill **reports and escalates**; capture and edits
belong to `task-tracker`.

## Procedure
1. **Read the registry through the CLI** (never parse tasks.json yourself):
   ```bash
   python3 /opt/mcwagent/hermes-skills/productivity/task-tracker/scripts/tasks.py due
   ```
   The JSON buckets are the whole truth: `overdue`, `due_soon` (inside each task's own
   lead window), `upcoming` (context only).
2. **Decide whether to speak.** Overdue or due-soon items → send the digest. Only
   `upcoming` → stay silent (a daily "all clear" email trains the operator to ignore you).
   Exception: on Mondays include a one-line upcoming preview at the bottom.
3. **Compose the digest**, worst first, one line per item:
   `OVERDUE 4d — CITI training renewal` / `Due in 4d (Jul 8) — IRB continuing review
   PRO-456 [CIR]`. Escalate tone with lateness; overdue items lead and repeat daily until
   done or rescheduled. End with the one-liner: reply or tell the agent "done t3" /
   "move t1 to Aug 1".
4. **Deliver via himalaya** (unattended runs must never use `hermes send` — that only
   posts to chat). Subject: `Deadlines: <N> need attention`.
5. **Never modify the registry from the sentinel.** If a due date looks wrong or a task
   seems stale (overdue > 30 days), say so in the digest and suggest the fix — the
   operator (via `task-tracker`) makes the change.

## Pitfalls
- Doing date math yourself instead of trusting `days_until_due` from the CLI.
- Padding quiet days with filler, or burying one overdue item under ten upcoming ones.
- Dropping an overdue item because it was already reported — it repeats until resolved.
- Sending to chat from an unattended run (nobody is there).

## Verification
Every line in the digest maps to a task in the CLI output with matching days-remaining;
nothing overdue/due-soon was omitted; no email was sent on a genuinely quiet day.
