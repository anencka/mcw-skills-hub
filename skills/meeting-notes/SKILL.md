---
name: meeting-notes
description: Turn a meeting transcript into structured notes — minutes, decisions, action items with owners and dates — and offer to file the action items into the task registry. Use when the operator has a transcript or says "build notes from my meeting."
version: 1.0.0
metadata:
  hermes:
    tags: [notes, meetings, minutes, action-items, transcription]
    category: notes
    related_skills: [note-taker, task-tracker, plain-language-summary]
---
# Meeting Notes

## When to Use
A transcript exists (usually `~/work/meetings/<id>/transcript.md`, produced by the
Meetings tab) and the operator wants minutes, or asks "what did we decide / who owes
what" about a recorded meeting.

## Procedure
1. **Read the whole transcript first.** Note the header (date, segments); if the
   transcript marks `[inaudible]` passages or unlabeled speakers, carry that uncertainty
   into the notes rather than papering over it.
2. **Write `notes.md` next to the transcript** with exactly these sections:
   - **Summary** — 3-5 sentences: purpose, what moved, overall outcome.
   - **Decisions** — one line each, verbatim-anchored: the decision, who made/confirmed
     it (as attributable from the transcript), and where (quote a short anchor phrase).
   - **Action items** — table: what — owner — due date. Only owners and dates that are
     actually in the transcript; mark the rest `(unassigned)` / `(no date)` — never
     invent either.
   - **Open questions** — raised but unresolved.
   - **Attendance** — only if determinable (named speakers); otherwise omit the section.
3. **Attribute cautiously.** Speaker labels from transcription are guesses; write
   "Speaker 2 (possibly <name> per context)" rather than asserting identity.
4. **Offer the task handoff:** list the action items that look like the operator's own
   dated obligations and ask which to add via `task-tracker` (never add silently).
   Items with `(no date)` need a date from the operator before they enter the registry.
5. If the operator wants a shareable version, hand the notes to
   `plain-language-summary` or reformat to their template — but `notes.md` stays the
   faithful record.

## Pitfalls
- Inventing owners, dates, or decisions the transcript doesn't support — the cardinal
  sin of minutes. `(unassigned)` is a fine answer.
- Summarizing so hard the disagreements disappear; minority positions and unresolved
  objections belong in the notes.
- Treating transcription-guessed speaker identity as fact.
- Adding tasks to the registry without an explicit yes.

## Verification
Every decision and action item can be traced to transcript text (spot-checkable via the
anchor phrases); no owner/date appears that the transcript doesn't contain; the operator
approved any registry additions.
