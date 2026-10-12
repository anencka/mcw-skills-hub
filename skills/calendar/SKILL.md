---
name: calendar
description: Read the operator's calendar (agenda, free/busy) and, with approval, create events via CalDAV. Pairs with email-and-scheduling for meeting prep and reminders.
version: 1.2.0
metadata:
  hermes:
    tags: [calendar, caldav, scheduling, agenda, events]
    category: communication
---
# Calendar (CalDAV)

Read and (with approval) write the operator's calendar over CalDAV. Credentials live in
`/opt/data/.env` (`CALDAV_URL`, `CALDAV_USERNAME`, `CALDAV_PASSWORD`), set in the **Settings tab**.

## First-use setup (read the profile; fill if thin)
Read `~/work-profile/preferences-and-constraints.md` (time zone, availability windows, hard
commitments) and `~/work-profile/team-and-relationships.md` (who meetings are with). If thin, offer
**once** to fill them (hand to `onboarding-interview`, or the operator edits the Files tab), else
skip and note it in memory. **Read fresh each use; never cache — the file is the source of truth.**

## Calendar access (bundled CLI)
Run with the dedicated venv (it has the `caldav` library):
```bash
PY=/opt/mcwagent/.venv/bin/python3
CAL=/opt/mcwagent/hermes-skills/communication/calendar/scripts/caldav_cli.py
$PY $CAL test                              # connect + list calendars
$PY $CAL agenda --days 7 [--calendar NAME] # upcoming events
$PY $CAL freebusy --days 7                 # busy blocks (for scheduling around)
$PY $CAL create --summary "<title>" --start 2026-06-12T14:00 --end 2026-06-12T15:00 [--desc "..."] [--calendar NAME]
```
**Exit codes and the INCOMPLETE banner** (read them every time):
- `0` — every calendar was read; the output is complete.
- `1` — partial or failed. `agenda`/`freebusy` then print a first line starting
  `INCOMPLETE:` naming each calendar that could not be read and why. Tell the operator the
  agenda is missing those calendars, and never present it (or "no events", or a free slot) as
  complete. A free/busy answer with a failed calendar is not evidence that the slot is free.
- `2` — not configured (missing `CALDAV_*` values or the venv). The calendar isn't set up —
  tell the operator to add it in the Settings tab; don't guess credentials.

## Procedure
1. **Read freely; never create/modify without a yes.** Use `agenda`/`freebusy` to answer "what's on
   my calendar", prep meetings, or find open slots. `create` writes to the calendar — produce the
   event details, show them, and call `create` only after the operator explicitly approves.
2. **Times:** use ISO `YYYY-MM-DDTHH:MM`. Respect the operator's time zone and availability windows
   from the profile; when proposing slots, check `freebusy` first.
3. **Meeting prep:** combine the agenda with `email-and-scheduling` (attendees, threads) and
   `current-projects` to assemble a brief.
4. **No secrets** in event titles, descriptions, or anything stored. **PHI and other protected
   information:** only where your policy (SOUL, rule 2) permits it — and an invitation is sent to
   other people, so leave it out of anything attendees will see unless the operator asks for it.

## Pitfalls
- Creating or changing events without explicit approval — never.
- Naive time-zone handling that lands an event an hour off — confirm the zone.
- Reporting an agenda or an open slot as complete when the output began with `INCOMPLETE:`.
- Leaking sensitive detail into an event title/description.

## Verification
`test` connects; `agenda` exits 0 (or its `INCOMPLETE` calendars were disclosed) and reflects real events; any created event appears with the right title and
start/end on the intended calendar, and only after explicit approval.
