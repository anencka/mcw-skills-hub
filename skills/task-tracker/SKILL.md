---
name: task-tracker
description: Capture and manage the operator's tasks and hard deadlines — grant due dates, RPPRs, IRB/IACUC expirations, training renewals — in a single registry the deadline sentinel watches. Use when the operator mentions a deadline or asks what's due.
version: 1.0.0
metadata:
  hermes:
    tags: [productivity, tasks, deadlines, registry]
    category: productivity
    related_skills: [deadline-sentinel, email-and-scheduling, calendar]
---
# Task & Deadline Tracker

## When to Use
The operator mentions a dated obligation ("the RPPR is due July 20th", "my CITI expires
next month"), asks what's due or overdue, or wants a task marked done. Also use it to
capture deadlines you encounter while doing other work (an email with a submission date,
a notice period in a document) — **ask before adding**, then add.

## The registry
One file: `~/work/tasks/tasks.json`. **Never edit it by hand** — all reads and writes go
through the bundled CLI, which does the date arithmetic in code and returns JSON:

```bash
PY=python3
T=/opt/mcwagent/hermes-skills/productivity/task-tracker/scripts/tasks.py
$PY $T add --title "RPPR for R01 CA-123" --due 2026-07-20 --lead 14 --project CIR
$PY $T list            # open tasks by due date        (--all includes done)
$PY $T due             # buckets: overdue / due_soon (within lead) / upcoming (--horizon 30)
$PY $T done t3         # also: reopen, edit, remove
```

## Procedure
1. **Capture**: title (what + identifying detail), due date (ISO — confirm ambiguous dates
   with the operator; "next Friday" gets resolved to a real date out loud), lead time
   (how many days of warning they want — default 7; grants deserve 14+), project, source.
2. **Report**: for "what's due", run `due` and present the buckets worst-first — overdue,
   then due-soon with days remaining, then upcoming. Short and scannable.
3. **Maintain**: mark things done when the operator says so; adjust dates when deadlines
   move; use `edit`, never delete-and-re-add (history matters).
4. **Seed**: on first use, offer to sweep the calendar (`calendar` skill) and any deadline
   emails the operator points at for date-bearing obligations, and add the confirmed ones.

## Pitfalls
- Guessing a date the operator implied ("end of the month") — resolve it and confirm.
- Editing tasks.json directly — you'll break the registry other runs depend on.
- Adding every to-do: this registry is for **dated obligations**; freeform notes belong
  with `note-taker`.
- Silently absorbing a deadline from a document without telling the operator you added it.

## Verification
The `add`/`edit` output echoes the stored task — read it back to the operator. `due`
buckets match what the operator expects (spot-check one date's arithmetic if challenged).
