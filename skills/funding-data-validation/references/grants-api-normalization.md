# Grants and Award API Normalization Reference

## Envelope map

| Source | Request | Records path | Identifier | Useful fields |
|---|---|---|---|---|
| Grants.gov `search2` | `POST https://api.grants.gov/v1/api/search2` body `{"keyword":…, "oppStatuses":"posted", "rows":25}` | `data.oppHits` | `number` | `id` (detail-page id), `title`, `agency`, `agencyCode`, `openDate`, `closeDate`, `oppStatus` |
| NIH RePORTER `projects/search` | `POST https://api.reporter.nih.gov/v2/projects/search` body `{"criteria":{"advanced_text_search":{"operator":"and","search_field":"all","search_text":…},"use_relevance":true},"limit":20,"include_fields":["ApplId","ProjectNum","ProjectTitle","AgencyIcAdmin","ActivityCode","FiscalYear","AwardAmount"]}` | `results` | `project_num` | `appl_id` (link id), `project_title`, `agency_ic_admin.name`, `activity_code`, `fiscal_year`, `award_amount` |
| NSF Awards API | `GET https://api.nsf.gov/services/v1/awards.json?keyword=…&rpp=20` | `response.award` | `id` | `title`, `date`, `awardeeName`, `fundsObligatedAmt` |

Links: Grants.gov `https://www.grants.gov/search-results-detail/<id>`; NIH RePORTER
`https://reporter.nih.gov/project-details/<appl_id>`; NSF
`https://www.nsf.gov/awardsearch/showAward?AWD_ID=<id>`.

Always inspect one response's top-level keys before writing a parser. Accept a zero-result
response only when the documented record key exists and holds an empty list. Treat a missing
key, wrong type, API error indicator (Grants.gov `errorcode` ≠ 0), non-object record, or
blank identifier as a source failure. A nonzero record count does not prove topical fit.

The Grants.gov envelope carries a response-generated `token` field. Never persist it.

## Provenance rules

- Preserve a deterministic normalized artifact before filtering. Keep the search term
  alongside each record set.
- Label Grants.gov records `record_type: opportunity, use: discovery` and NIH/NSF records
  `record_type: award, use: calibration` in the artifact itself, not only in prose.
- Quote deadline strings exactly as returned by the funder when writing a digest.
- Build links only from returned ids, and check that the resulting URL resolves before
  reporting it.

## Seen-list audit

For a routine refresh, compute `new_ids = current_ids − historical_ids`, then append only the
new identifiers with the run date. Check uniqueness inside `new_ids`. If historical
duplicates exist, flag them as a data-quality note instead of rewriting the history.

## Verifying a collector

Run the bundled tests for the digest collector rather than writing throwaway scripts:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s /opt/mcwagent/hermes-skills/grants/funding-opportunity-digest/tests -v
```

If a check is needed that those tests don't cover (e.g. inspecting one live artifact), do it
in a one-off command whose output you report, leave nothing behind in the project, and call
the result "ad-hoc verification" — not a test-suite pass.
