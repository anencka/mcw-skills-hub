---
name: email-and-scheduling
description: Read, search, and (with approval) send email from the agent's own mailbox using the himalaya CLI, plus meeting prep and task triage — in the operator's voice, never auto-send, no PHI in messages.
version: 2.2.0
metadata:
  hermes:
    tags: [email, scheduling, communication, admin]
    category: communication
---
# Email, Scheduling & Admin

## When to Use
Drafting or replying to email, preparing for meetings, summarizing threads, or triaging
to-dos and correspondence.

## First-use setup (read the profile; fill if thin)
Read `~/work-profile/team-and-relationships.md` (who the operator writes to + per-person context),
`~/work-profile/communication-style.md` (tone by audience, signature), and
`~/work-profile/preferences-and-constraints.md` (availability, non-negotiables). If any is still
mostly `*(to capture)*`, offer **once** to fill it — a few questions (hand to
`onboarding-interview`, e.g. "let's do team-and-relationships") or the operator edits it in the
Files tab — then proceed; if they skip, note that in memory and don't re-ask. **Read these fresh
each use; never cache their contents — the file is the source of truth.**
- **Hard rule:** never send, reply, accept, or decline on the operator's behalf without explicit
  per-message approval.

## Mailbox access — `himalaya` is the email tool (read AND send)
The agent has its own mailbox (e.g. `your-agent@example.org`), configured **once** in the
**Settings tab** (stored as the native `EMAIL_*` keys in `/opt/data/.env`). The container pre-wires
**himalaya** to that same mailbox — it is the one sanctioned email client for both reading and
sending. **Never hand-roll an SMTP/IMAP script and never connect to Gmail/Outlook/any other
provider; the configured mailbox is the only one.** (The "no bespoke SMTP/IMAP" rule is about
improvised scripts and foreign providers — himalaya is the built-in tool, so it's allowed.)
If himalaya reports it's unconfigured, the operator just needs to fill Settings → Email; never guess
credentials.

> **`hermes send` does NOT send email.** It only posts to chat platforms (Telegram/Slack/Discord/
> Signal/SMS/WhatsApp). There is no `email:` target — never use it for email; it would silently
> fail to deliver. Email out = himalaya.

- **Read / search (on demand):** `himalaya envelope list` (inbox), `himalaya envelope list --folder
  Sent`, `himalaya message read <id>`; search via the list query, e.g.
  `himalaya envelope list from <addr>` / `... subject "<text>"`. Reading is unrestricted — use it
  freely when the operator asks ("what's in my inbox?", "find the email from X", "summarize that
  thread").
- **Send a new email (APPROVAL-GATED):** draft it, show the operator, and send **only on an explicit
  yes** for that message — via `himalaya template send` (From is filled from the account):
  ```
  himalaya template send <<'EOF'
  To: recipient@example.com
  Subject: <subject>

  <body>
  EOF
  ```
- **Reply in a thread (APPROVAL-GATED):** `himalaya template reply <id>` generates a quoted reply
  template; edit the body, then pipe it to `himalaya template send`. Same draft-then-approve rule.
- **Inbound push — the email gateway (separate, autonomous):** when enabled (Settings → "Inbound
  email"), the gateway polls IMAP and **auto-replies in-thread via SMTP** to allow-listed senders
  (`EMAIL_ALLOWED_USERS`) — that loop is the operator's deliberate, pre-authorized automation, run by
  the adapter, not something you invoke. For anything you compose yourself, use himalaya as above.

For anything calendar/scheduling, use the **`calendar`** skill (CalDAV agenda / free-busy / create).

## Procedure
1. **Draft first; never send without a yes.** Compose the message in the operator's voice, show it,
   and only then `himalaya template send` after explicit approval of *that* message.
2. **Match register and brevity** to the audience; lead with the ask or the point; keep it short and
   unambiguous. Offer 1–2 variants when tone is delicate.
3. **For replies/threads:** read the full thread, capture the actual asks and commitments, and
   address each; don't invent context or agreements.
4. **Meeting prep:** assemble agenda, relevant docs/links, and the decisions needed; produce a
   concise brief. Afterward, turn notes into clear action items with owners.
5. **Triage:** group and prioritize tasks/messages; propose next actions; flag anything
   time-sensitive. Keep the operator's task list/notes updated if they use one.
6. **Privacy:** never include PHI, identifiers, or secrets in drafts or stored notes; flag if the
   source material contains them.

## Pitfalls
- Improvising email — never write a bespoke SMTP/IMAP script or connect to a generic provider
  (Gmail/Outlook). Use **himalaya** for all email read + send on the configured mailbox.
- Using `hermes send` for email — it only posts to chat platforms (no `email:` target) and would
  silently fail to deliver. Email out = `himalaya template send`.
- Sending or making calendar changes without explicit approval — never.
- Wrong register (too casual to leadership, too stiff to a close collaborator).
- Inventing commitments/context not in the thread.
- Leaking sensitive info into a message or a stored summary.

## Verification
Output is a review-ready draft (nothing sent until approved), in the right tone, addressing the
actual asks, with no PHI/secrets; any send went through `himalaya` on the configured mailbox.
