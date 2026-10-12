---
name: funding-data-validation
description: Validate and normalize funding-opportunity and funded-award API data (Grants.gov, NIH RePORTER, NSF) before ranking, reporting, or updating a persistent seen list — fail-closed envelope checks, nonblank identifiers, discovery vs calibration labeling, no secrets in artifacts.
version: 1.0.1
metadata:
  hermes:
    tags: [grants, funding, api, validation, provenance]
    category: grants
    related_skills: [funding-opportunity-digest, grant-proposals, research-investigator]
---
# Funding Data Validation

## When to Use
Use this skill whenever funding opportunities or funded-award calibration records are
collected from Grants.gov, NIH RePORTER, NSF, or another structured source and will be
ranked, emailed, persisted to a watch list, or used to support proposal strategy.

This is a data-quality companion to opportunity-search and proposal-writing skills. It does
not decide scientific fit; it makes the evidence used for that decision traceable and
structurally reliable. The `funding-opportunity-digest` collector already implements every
check below — use this skill to audit its output, or to apply the same rules when you must
query a source by hand.

## Procedure
1. **Preserve source evidence safely.** Save a project-local, reproducible source artifact
   before ranking. Prefer a deterministic normalized extract that keeps every field needed
   for provenance. If an API envelope must be retained, strip response-generated tokens,
   access keys, credentials, PHI, and unrelated metadata before writing it. Never store those
   values in artifacts, logs, or Git.
2. **Validate the request and the envelope before normalizing.** Assert the documented query
   contract and response shape for each source (see `references/grants-api-normalization.md`).
   Grants.gov records are `data.oppHits`; NIH RePORTER records are `results`; NSF awards are
   `response.award`. Require the record key to exist and hold a list, even when empty; reject
   a missing key, wrong type, or API error indicator so an HTTP-200 schema/error response
   cannot become a false zero-result run. For NIH advanced text search, send `operator`,
   `search_field`, and `search_text`, include `ProjectNum` and `ApplId` in `include_fields`,
   and verify distinct terms do not return an unexplained identical result set.
3. **Validate every record fail-closed.** Each record must be an object with a nonblank source
   identifier (`number`, `project_num`, or `id`). If any record is malformed, mark that source
   request failed rather than emitting `identifier: null` under `status: ok`. For every valid
   record retain the source, identifier, title, agency, mechanism/activity code, opening
   date, closing date, and a resolvable link. Keep source date strings verbatim for
   reporting; compute normalized dates separately for comparisons.
4. **Separate discovery from calibration.** Grants.gov opportunities are candidate actions.
   NIH RePORTER and NSF award records are evidence about what has been funded, not open
   solicitations. Label them in the artifact itself (`use: discovery` / `use: calibration`),
   not only in downstream prose.
5. **Rank only after validation.** Apply topic, mechanism/career-stage, deadline-feasibility,
   and novelty filters to normalized records. Never rank on keyword overlap alone.
6. **Update seen lists idempotently, and only through code.** Deduplicate the new batch by
   source identifier before appending; append only `new_ids = current_ids − historical_ids`
   with the run date, after the artifact that records the run exists. Keep the seen log as
   machine state separate from operator config. For the digest, that is
   `refresh.py mark-seen` writing `state/seen.jsonl`; never hand-edit it. Preserve historical
   entries; report pre-existing duplicates as a data-quality note rather than silently
   rewriting history during a routine run.
7. **Verify links and artifacts.** Check that every reported opportunity link resolves,
   confirm the digest artifact exists, and re-read the updated seen list.

## Reusable verification checks
- All expected source kinds are represented, and each recorded request has `status: ok` or
  an explicit failure with the actual error text.
- Every emitted record has a nonblank source identifier traceable to the preserved artifact.
- Distinct search terms produce plausibly term-specific results; identical result sets are
  investigated before use.
- New seen-list identifiers are unique within the batch and absent from history.
- Reported opportunities have resolvable links; calibration awards are explicitly labeled.
- A recursive scan of retained JSON keys finds no `token`, `access_token`, `api_key`,
  `password`, `secret`, credential, or PHI fields.
- The bundled collector tests pass:
  `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s /opt/mcwagent/hermes-skills/grants/funding-opportunity-digest/tests`
  They cover request payloads, missing/malformed envelopes, missing identifiers,
  source-failure exit status, output containment, and repeated same-date writes. Prefer
  them over an ad-hoc check; if you must verify something they don't cover, do it in a
  one-liner you don't save, and say "ad-hoc verification", never "test suite passed".

## Pitfalls
- Assuming a top-level `oppHits` field — Grants.gov nests it under `data`.
- Treating a well-formed zero-hit envelope the same as malformed JSON; require the
  documented record key and list type before accepting zero results.
- Letting missing identifiers through because today's live response happens to include
  them; enforce nonblank identifiers in every normalizer so schema drift fails visibly.
- Testing response parsing without testing the outgoing request payload; a syntactically
  valid but incomplete NIH query returns broad, identical, unusable calibration sets.
- Rewriting or deduplicating the whole historical seen list when only the new batch needs
  idempotent handling.
- Presenting weakly related NIH/NSF keyword matches as direct evidence of fit.
- Leaving temporary verification scripts, transcripts, or `__pycache__` in the project.

## Verification
The digest is reproducible from a preserved source artifact; every record has a nonblank
identifier; every listed opportunity has source-backed metadata and a live link; calibration
records are labeled; malformed source data fails visibly; and the seen-list update is
auditable without exposing secrets or PHI.
