---
name: funding-opportunity-digest
description: Find and rank live funding opportunities matched to the operator's research profile — NIH, Grants.gov, NSF — and deliver a concise digest. Works one-off or as a scheduled cron digest, with a bundled collector that keeps every run reproducible.
version: 3.0.0
metadata:
  hermes:
    tags: [grants, funding, nih, digest, cron]
    category: grants
    related_skills: [funding-data-validation, grant-proposals, literature-alerts, research-investigator]
    blueprint:
      schedule: "0 7 * * 1"
      prompt: "Run the funding-opportunity-digest skill. Work only inside ~/work/funding-digest/. Determine today's local date, run the bundled collector (scripts/refresh.py) to refresh config/funding-watch.md queries against Grants.gov, NIH RePORTER, and NSF, validate and rank only the collector's new_candidates, and write this run only under runs/YYYY-MM-DD/. If substantive candidates exist, queue the digest to the recipient named in config/funding-watch.md via himalaya using the account that matches the recipient's tier (external addresses REQUIRE `-a external`; never write a From header). If there are no substantive candidates, do not queue email — write runs/YYYY-MM-DD/run-summary.md instead. After the digest or run summary is written, run the collector's mark-seen command for today's date; never edit the seen log by hand. Never regenerate the collector or create funding files elsewhere under ~/work/."
---
# Funding Opportunity Digest

## When to Use
The operator asks "what funding is out there for my work", wants a recurring funding-watch
digest, or is planning the next proposal cycle and needs candidate mechanisms/deadlines.

## Paths (this container)
- **Bundled collector + tests (read-only):**
  `/opt/mcwagent/hermes-skills/grants/funding-opportunity-digest/scripts/refresh.py`
  `/opt/mcwagent/hermes-skills/grants/funding-opportunity-digest/tests/`
- **Project root:** `~/work/funding-digest/` — the only place this skill writes. Layout:
  - `config/funding-watch.md` — search keywords, funders, mechanisms, **delivery**, and the
    operator's **Do Not Surface** list. Operator-owned; you edit it only with their consent.
  - `state/seen.jsonl` — the machine seen log, one JSON record per identifier. Written **only**
    by the collector's `mark-seen` command. Never edit it, and never append identifiers to the
    config yourself.
  - `runs/YYYY-MM-DD/sources.json` — the run's normalized, sanitized API evidence, including
    each Grants.gov record's `seen` flag and the run's `new_candidates` list
  - `runs/YYYY-MM-DD/digest.txt` — the digest, when substantive candidates exist
  - `runs/YYYY-MM-DD/run-summary.md` — the no-results or source-failure record otherwise

Never create funding-related files loose under `~/work/`, invent another funding directory,
write a replacement collector or analysis script, or leave `__pycache__`/temp scripts in the
project.

**Upgrading an older install** (tell the operator what you did):
- A loose `~/work/funding-watch.md` (pre-2.0.0) moves to
  `~/work/funding-digest/config/funding-watch.md` once.
- If the collector exits 2 saying the config still holds a `## Reviewed/Seen` list (pre-3.0.0),
  run the one-time migration, which moves those identifiers into `state/seen.jsonl` and renames
  the section to `## Do Not Surface`:
  ```bash
  python3 /opt/mcwagent/hermes-skills/grants/funding-opportunity-digest/scripts/refresh.py \
    migrate --project-root ~/work/funding-digest
  ```

## First-use setup (read the profile; fill if thin)
Read `~/work-profile/current-projects.md` and `~/work-profile/domain-knowledge.md` for the
research topics, methods, and career stage that drive matching. If either is mostly
`*(to capture)*`, offer **once** to fill it (hand to `onboarding-interview`), then proceed.
**Read these fresh each use; never cache.** On first run, draft `config/funding-watch.md`
from the profile and confirm it with the operator before saving. It must contain:

```markdown
# Funding Watch Configuration
## Search Keywords
- <one keyword phrase per line — each is one query against every source>
## Funders
- NIH (all institutes)
## Mechanisms of Interest
- R01, R21, K-series
## Delivery
- recipient: <where the digest goes — an institutional address, or the operator's
  internal agents.<domain> mailbox>
- notify-when-empty: no
## Do Not Surface
<!-- Operator's manual list: one identifier per line; never reported. The machine seen
     log is state/seen.jsonl, written by `refresh.py mark-seen`. -->
```

Only `## Search Keywords` is read by the collector; the rest is read by you.

## Data sources (all free, no key)
The collector issues these exact calls for every keyword phrase:
- **Grants.gov `search2`** (discovery — the candidate opportunities). Records are nested at
  `data.oppHits`; the opportunity number is the `number` field (not `oppNum`) and the detail
  page is `https://www.grants.gov/search-results-detail/<id>`.
- **NIH RePORTER `projects/search`** (calibration — what NIH actually funds in this space).
  The request sends `operator`, `search_field`, and `search_text` under
  `advanced_text_search` and includes `ProjectNum`/`ApplId` so every award has a durable
  identifier and link. Without those fields distinct terms return identical, unusable sets.
- **NSF Awards API** (calibration for NSF). Records are at `response.award`.
- NIH Guide notices/PARs surface through Grants.gov; when the operator names a specific
  mechanism, also check the funder page by URL and cite it.

## Procedure
1. **Load** the profile files and `config/funding-watch.md` fresh. Get today's local date
   with `date +%F` (the container runs in the operator's timezone).
2. **Collect** — from the project root:
   ```bash
   cd ~/work/funding-digest
   PYTHONDONTWRITEBYTECODE=1 python3 \
     /opt/mcwagent/hermes-skills/grants/funding-opportunity-digest/scripts/refresh.py \
     refresh --project-root . --run-date $(date +%F)
   ```
   It prints one JSON line (`output`, `terms`, `source_failures`, `new_candidates`) and exits
   1 if any source failed, or 2 on a configuration problem (nothing written). On failure, read the `status`/`message` for that source in
   `sources.json`, continue with the sources that succeeded, and disclose the missing
   coverage in the digest or run summary. Do not modify or replace the collector.
3. **Validate before ranking** (the `funding-data-validation` skill is the checklist):
   Grants.gov records (`use: discovery`) are the candidate opportunities. NIH RePORTER and
   NSF records (`use: calibration`) are evidence of what gets funded — never present them
   as open solicitations.
4. **Take the candidates from `new_candidates`** in `sources.json`. The collector has already
   removed everything in the seen log and the Do Not Surface list; do not re-derive this by hand.
5. **Rank only those new candidates** by topic fit to current projects,
   mechanism/career-stage fit, eligibility, and deadline feasibility (flag anything the
   source says closes in < 30 days). Keyword overlap alone is not fit.
6. **Verify** every opportunity you will report against its live Grants.gov detail link, and
   keep the source's deadline text verbatim. Never invent, infer, or "repair" an identifier
   or date.
7. **Deliver.** If substantive candidates exist, write `runs/YYYY-MM-DD/digest.txt`: a short
   ranked list (opportunity — funder/mechanism — source-stated deadline — one-line
   why-it-fits — link), a "screened but not recommended" line so the operator sees what
   was considered, a clearly labeled **calibration** note of 2-3 recently funded awards,
   and a coverage line (terms run, sources ok/failed). Plain text that reads well in email.
   Then queue exactly that text to the `## Delivery` recipient, **choosing the account by
   recipient tier** — the internal mailbox cannot reach the outside world (its plane has no
   external relay by design), so an institutional/public address MUST go out on the
   external tier:
   ```bash
   # external recipient (e.g. name@<institution>.edu, gmail, icloud):
   printf 'To: <recipient>\nSubject: Funding digest %s\n\n%s' "$(date +%F)" "$(cat runs/$(date +%F)/digest.txt)" \
     | himalaya template send -a external
   # internal recipient (<you>@agents.<domain>) — default account, no -a needed:
   printf 'To: <recipient>\nSubject: ...\n\n<digest>' | himalaya template send
   ```
   **Never write a `From:` header.** The account selected with `-a` IS the sending identity
   and supplies the address itself; a guessed From is rewritten by the send shim and, if it
   ever reached delivery, refused by the broker (E6). Either way the send is queued as an
   outbox draft for operator approval (external is approval-only by design and can never be
   autonomous) — that is expected, not an error. Do NOT "fix" a refusal by widening a
   credential: `550 5.7.1 not authorized` means the agent credential is read-only on purpose.
   **If there are no substantive candidates, do not queue an email** (unless
   `notify-when-empty: yes`). Write `runs/YYYY-MM-DD/run-summary.md` instead: source
   coverage, how many candidates were screened, and why none was recommended.
8. **Mark the run's identifiers seen**, only after `digest.txt` or `run-summary.md` exists:
   ```bash
   PYTHONDONTWRITEBYTECODE=1 python3 \
     /opt/mcwagent/hermes-skills/grants/funding-opportunity-digest/scripts/refresh.py \
     mark-seen --project-root . --run-date $(date +%F)
   ```
   It appends every screened Grants.gov identifier not already seen — recommended or rejected —
   and refuses (exit 2) if the run's digest or summary has not been written yet, so a crashed
   run never loses items. Re-running it is harmless. The log is deliberately broad: it records
   everything the keywords returned, relevant or not, which is what makes dedup reliable.
9. If a source or the collector failed, record the source and the actual error text in the
   run summary. Never manufacture replacement data.
10. If the operator wants this recurring, register the blueprint above as a **cron job**
    (Automations tab / `hermes cron`) — email via himalaya, never `hermes send`, for
    unattended runs.

## Data minimization
`sources.json` holds normalized records and per-request status, not API envelopes. It must
never contain keys named `token`, `access_token`, `api_key`, `password`, or `secret`, nor
PHI or unrelated response metadata. Do not save shell transcripts, temporary scripts, or
duplicate raw downloads in the project.

## Pitfalls
- Inventing opportunities or deadlines — every line in the digest must trace to a record in
  `sources.json` or a fetched funder page. If a source is down, say so; never fill the gap.
- Re-surfacing the same items every run (that trains the operator to ignore the digest) —
  the seen log is what makes this a *digest* and not a search dump.
- Editing `state/seen.jsonl` or appending identifiers to the config by hand. Only `mark-seen`
  writes the log; only the operator writes Do Not Surface.
- Presenting NIH/NSF calibration awards as open opportunities.
- Treating an HTTP-200 schema error as "zero results" — the collector fails closed on a
  missing record key or blank identifier; trust its `status`, not the record count.
- Ranking by keyword overlap alone; mechanism and career-stage fit matter as much as topic.
- Deadlines in the wrong timezone/format — quote the funder's stated close date verbatim.
- Emailing an empty digest.

## Verification
Before finishing: all run artifacts are under `~/work/funding-digest/`; `sources.json` has no
forbidden keys; each listed candidate is present in `sources.json` and its link resolves;
calibration records are labeled as awards; `mark-seen` ran after the digest or summary was
written and reported the expected `appended` count; a queued email exists only when a substantive digest was produced; the final response
names the exact artifact paths and any source failures.
