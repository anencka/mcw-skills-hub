---
name: literature-alerts
description: Maintain living literature alerts — saved PubMed/preprint queries run on a schedule, deduplicated against what the operator has already seen, synthesized into a short what's-actually-new digest.
version: 1.0.0
metadata:
  hermes:
    tags: [research, literature, pubmed, alerts, digest, cron]
    category: research
    related_skills: [literature-research, reference-management, funding-opportunity-digest]
    blueprint:
      schedule: "0 12 * * 1"
      prompt: "Run the literature-alerts skill: run every query in ~/work/lit-alerts/queries.md against PubMed (and preprints where configured), dedupe against seen.txt, email the what's-new digest via himalaya, then update seen.txt."
---
# Living Literature Alerts

## When to Use
The operator wants to stay current in defined topic areas without hand-searching: "watch the
literature on X", "weekly digest of new papers about Y", or a standing alert feeding a
living review.

## First-use setup (read the profile; fill if thin)
Read `~/work-profile/domain-knowledge.md` and `~/work-profile/current-projects.md` to draft
good queries. Alert state lives at `~/work/lit-alerts/`: `queries.md` (one section per
alert: the PubMed query string, cadence, why the operator cares) and `seen.txt` (one PMID
or DOI per line — the dedupe memory). Build `queries.md` with the operator on first run;
show them the raw query strings so they can tune them.

## Data sources (free, no key; use these exact calls)
- **PubMed — new items in the window:**
  `curl -s 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=<query>&retmax=50&retmode=json&datetype=edat&reldate=<days>'`
  then details via `esummary.fcgi?db=pubmed&id=<id1,id2,...>&retmode=json`
  and abstracts via `efetch.fcgi?db=pubmed&id=<ids>&rettype=abstract&retmode=text`.
  Be polite: ≤3 requests/second, batch ids into single esummary/efetch calls.
- **Preprints** (when the alert asks for them): bioRxiv/medRxiv API
  `curl -s 'https://api.biorxiv.org/details/biorxiv/<YYYY-MM-DD>/<YYYY-MM-DD>/0'` filtered
  by the query terms client-side.

## Procedure
1. **Load `queries.md` and `seen.txt`.** Set the lookback window to the alert cadence plus
   a couple of days of overlap (missing a paper is worse than re-checking one).
2. **Run each query**, collect PMIDs/DOIs, and **drop everything already in `seen.txt`** —
   the digest is only what's new.
3. **Read before ranking**: pull abstracts for the survivors; rank by relevance to the
   alert's stated "why", not by journal name alone.
4. **Write the digest** per alert: 1-2 sentence plain summary per paper of what's new
   (from the abstract — not a rephrased title), full citation with PMID/DOI link, and a
   one-line "why it matters to you" tied to the operator's projects. Nothing new this
   period → say exactly that in one line; never pad.
5. **Append the surfaced ids to `seen.txt`** — this is what keeps the alert trustworthy.
6. **Deliver + schedule**: send via himalaya email for unattended runs (never
   `hermes send` from a schedule). If this isn't recurring yet, offer to register the cron
   job at the requested cadence. Offer to push kept papers to `reference-management`.

## Pitfalls
- Fabricating or embellishing citations/abstract claims — quote the record; if an abstract
  is unavailable, say "abstract not available" rather than inventing a summary.
- Forgetting to update `seen.txt` (repeats destroy trust in the digest) or updating it
  before the digest actually went out (a failed send then loses those papers forever).
- Queries that silently return 0 forever — if an alert returns nothing for several runs,
  flag it once and suggest loosening the query, don't just stay quiet.
- Ranking by recency alone; the operator's "why" line in `queries.md` is the ranking rubric.

## Verification
Every digest item is new (absent from prior `seen.txt`), has a resolving PMID/DOI, and its
summary is grounded in the actual abstract; `seen.txt` was updated after successful
delivery; empty periods are reported honestly.
