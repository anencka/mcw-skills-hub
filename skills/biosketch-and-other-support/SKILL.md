---
name: biosketch-and-other-support
description: Draft or update an NIH biosketch or Other Support document from the operator's real publication and grant record (ORCID, PubMed, NIH RePORTER) — current format, no fabricated entries.
version: 1.0.0
metadata:
  hermes:
    tags: [grants, biosketch, other-support, nih, orcid]
    category: grants
---
# Biosketch & Other Support

## When to Use
A submission or JIT request needs an NIH biosketch or Other Support page; an existing one is
stale; or a co-investigator's needs assembling from public records.

## First-use setup (read the profile; fill if thin)
Read `~/work-profile/identity.md` (name variants, ORCID iD, eRA Commons username, position,
education) and `~/work-profile/current-projects.md` (active/pending support the public record
may lag). If the ORCID iD is missing, ask for it once and save it to `identity.md`. Keep the
living copies at `~/work/biosketch/` so updates are diffs, not rewrites.

## Data sources (all free; use these exact calls)
- **ORCID public record** (works, employment, education):
  `curl -s -H 'Accept: application/json' https://pub.orcid.org/v3.0/<ORCID-iD>/record`
  and `/v3.0/<ORCID-iD>/works` for the full publication list.
- **PubMed** for publication verification and citation details:
  `curl -s 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=<Name>[Author]&retmax=100&retmode=json'`
  then `esummary.fcgi?db=pubmed&id=<ids>&retmode=json` for full citations.
- **NIH RePORTER** for the grant record (numbers, titles, dates, role):
  `curl -s -X POST https://api.reporter.nih.gov/v2/projects/search -H 'Content-Type: application/json' -d '{"criteria":{"pi_names":[{"any_name":"<Surname>"}]},"limit":50,"include_fields":["ProjectNum","ProjectTitle","FiscalYear","AwardAmount","ProjectStartDate","ProjectEndDate"]}'`
- The operator is the source of truth for non-NIH and pending support — always confirm.

## Procedure
1. **Pull the record** from ORCID + PubMed + RePORTER; reconcile against name variants;
   present the merged list to the operator to confirm it's them (common-name collisions are
   the classic failure).
2. **Biosketch (current NIH format):** Section A Personal Statement tailored to the specific
   application (ask what it's for); B Positions/Honors from ORCID + profile; C Contributions
   to Science — up to 5 contributions, each a short narrative + up to 4 real citations drawn
   from the verified list. Respect the 5-page limit.
3. **Other Support:** active + pending, with project numbers, dates, effort (person-months —
   operator supplies; never guess effort), and overlap statements. Flag anything RePORTER
   shows that the operator didn't mention, and vice versa.
4. **Deliver** as markdown (and Word via pandoc if asked) in the funder's section order, and
   note that NIH increasingly expects SciENcv-generated PDFs — this draft is the content to
   paste/load there, formatted to match.
5. **Save** to `~/work/biosketch/` with a dated filename; on later runs, diff and update
   rather than regenerate.

## Pitfalls
- Fabricated or misattributed publications — every citation must come from the verified
  PubMed/ORCID pull. Wrong-author contamination from common surnames is the top risk.
- Guessing effort/person-months or pending-award details — operator-confirmed only.
- Stale format assumptions: if unsure of the current NIH template details, fetch the NIH
  biosketch instructions page and follow what it says today, citing it.
- Overlap statements that ignore a grant the databases clearly show — reviewers check.

## Verification
Every publication and grant listed exists in the pulled record or was explicitly supplied by
the operator; page limits respected; the operator has confirmed effort numbers and pending
items; the file is saved under `~/work/biosketch/`.
