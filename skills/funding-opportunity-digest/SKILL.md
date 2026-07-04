---
name: funding-opportunity-digest
description: Find and rank live funding opportunities matched to the operator's research profile — NIH, Grants.gov, NSF — and deliver a concise digest. Works one-off or as a scheduled cron digest.
version: 1.0.0
metadata:
  hermes:
    tags: [grants, funding, nih, digest, cron]
    category: grants
    related_skills: [grant-proposals, literature-alerts, research-investigator]
    blueprint:
      schedule: "0 12 * * 1"
      prompt: "Run the funding-opportunity-digest skill: refresh ~/work/funding-watch.md queries against Grants.gov, NIH RePORTER, and NSF; build the ranked what's-new digest; email it via himalaya; update the seen list."
---
# Funding Opportunity Digest

## When to Use
The operator asks "what funding is out there for my work", wants a recurring funding-watch
digest, or is planning the next proposal cycle and needs candidate mechanisms/deadlines.

## First-use setup (read the profile; fill if thin)
Read `~/work-profile/current-projects.md` and `~/work-profile/domain-knowledge.md` for the
research topics, methods, and career stage that drive matching. If either is mostly
`*(to capture)*`, offer **once** to fill it (hand to `onboarding-interview`), then proceed.
**Read these fresh each use; never cache.** Keep a persistent watch config at
`~/work/funding-watch.md`: search keywords, funders to include, mechanisms of interest
(e.g. R01/R21/K-series), and anything already reviewed-and-rejected so it isn't re-surfaced.

## Data sources (all free, no key; use these exact calls)
- **Grants.gov (posted opportunities):**
  `curl -s -X POST https://api.grants.gov/v1/api/search2 -H 'Content-Type: application/json' -d '{"keyword":"<terms>","oppStatuses":"posted","rows":25}'`
  Fields per hit include title, agency, openDate/closeDate, oppNum.
- **NIH RePORTER (what NIH actually funds in this space — calibrates fit):**
  `curl -s -X POST https://api.reporter.nih.gov/v2/projects/search -H 'Content-Type: application/json' -d '{"criteria":{"advanced_text_search":{"search_text":"<terms>"}},"limit":20,"include_fields":["ProjectTitle","AgencyIcAdmin","ActivityCode","FiscalYear","AwardAmount"]}'`
- **NSF awards (same calibration for NSF):**
  `curl -s 'https://api.nsf.gov/services/v1/awards.json?keyword=<terms>&rpp=20'`
- NIH Guide notices/PARs surface through Grants.gov; when the operator names a specific
  mechanism, also check the funder page by URL and cite it.

## Procedure
1. **Load the watch config** (or build it from the profile on first run; confirm with the
   operator before saving).
2. **Query each source** with the config's keyword sets. Capture title, funder, mechanism,
   deadline, link/oppNum for every candidate — from the API response, never from memory.
3. **Filter and rank by fit**: topic match to current projects, mechanism/career-stage fit,
   deadline feasibility (flag anything closing < 30 days), and novelty (drop items already in
   the reviewed list).
4. **Deliver the digest**: a short ranked table (opportunity — funder/mechanism — deadline —
   one-line why-it-fits — link), then a "calibration" note of 2-3 recently funded awards in
   the same space from RePORTER/NSF. Plain text that reads well in email.
5. **Update the watch file** with what was surfaced so the next run only reports new items.
6. If the operator wants this recurring, set it up as a **cron job** (the scheduling tool /
   `hermes cron`) that runs this skill and sends the digest via himalaya email — never
   `hermes send` for unattended runs.

## Pitfalls
- Inventing opportunities or deadlines — every line in the digest must come from an API
  response or a fetched funder page. If a source is down, say so; never fill the gap.
- Re-surfacing the same items every run (that trains the operator to ignore the digest) —
  the seen-list in the watch file is what makes this a *digest* and not a search dump.
- Ranking by keyword overlap alone; mechanism and career-stage fit matter as much as topic.
- Deadlines in the wrong timezone/format — quote the funder's stated close date verbatim.

## Verification
Every listed opportunity has a live link/oppNum that resolves; deadlines match the source;
nothing from the reviewed/seen list reappears; the watch file was updated.
