---
name: research-investigator
description: Compile an investigator dossier — publications (PubMed), grants (NIH Reporter), and a web-research profile — for a named researcher, with false-positive review. Also supports CSV batch mode and a lighter theranostics-relevance screen.
version: 1.0.0
metadata:
  hermes:
    tags: [research, investigator, pubmed, nih-reporter, grants, dossier]
    category: research
---
# Research Investigator

Build a profile of an academic investigator's scholarly output by searching **PubMed** (publications)
and **NIH Reporter** (grants), reviewing both for false positives, doing focused web research, and
collating a summary. The two search scripts are bundled with this skill and use only public APIs —
no keys required.

## Paths (this container)
- **Scripts:** `/opt/mcwagent/hermes-skills/research/research-investigator/scripts/`
- **Project:** all work lives under a project folder — `~/work/<project>/` (one folder per project;
  never write loose in `~/work/`). Ask the operator which project this is for, or propose a name to
  create (e.g. `~/work/theranostics-2026/`). `<project>` below is that folder.
- **Output:** `~/work/<project>/investigator-profiles/<name_slug>/` (visible in the Files tab).
  `<name_slug>` is the name lowercased with underscores, e.g. `kevin_koch`.

## Inputs
Investigator **name**, **institution** (full or abbreviation, e.g. "MCW"), and a **year range**.
Ask for any that are missing. For year-only ranges, use `YYYY-01-01` … `YYYY-12-31`.

## Workflow (single investigator)

1. **Set up output:** `mkdir -p ~/work/<project>/investigator-profiles/<name_slug>`

2. **PubMed search:**
   ```bash
   python3 /opt/mcwagent/hermes-skills/research/research-investigator/scripts/pubmed_search.py \
       "<name>" "<institution>" "<start_date>" "<end_date>" \
       --output ~/work/<project>/investigator-profiles/<name_slug>/pubmed_raw.json
   ```

3. **Review PubMed for false positives.** Read `pubmed_raw.json`; for each paper confirm the target
   is actually an author (last name + first name/initial match) with a matching institution
   affiliation. **Handle name variants flexibly** — PubMed uses formal names; nicknames map to them
   (Tim→Timothy, Mike→Michael, Bob→Robert, Bill→William, Jim→James, Tom→Thomas, Chris→Christopher,
   Dan→Daniel, Dave→David, Joe→Joseph, Nick→Nicholas, Pat→Patrick/Patricia, Rich→Richard,
   Steve→Steven, Tony→Anthony). First-initial matches are valid ("T Meier" = "Timothy B Meier"). Do
   **not** reject on a first-name variant alone. Drop coincidental matches (different person, no
   affiliation match). Write cleaned `publications.json` adding `verified` (high/medium/low) and
   `verification_notes` to each.

4. **NIH Reporter search:**
   ```bash
   python3 /opt/mcwagent/hermes-skills/research/research-investigator/scripts/nih_reporter_search.py \
       "<name>" "<institution>" <start_year> <end_year> \
       --output ~/work/<project>/investigator-profiles/<name_slug>/nih_reporter_raw.json
   ```

5. **Review NIH Reporter for false positives.** Confirm the target is a PI / contact PI (not an
   org-only match), same name-variant flexibility. Write cleaned `grants.json` with `verified` +
   `verification_notes`.

6. **Focused web research** (use your own web-search / browser tools — there is no separate
   research subagent here). **Efficiency rules (important on open-weight models):** search first and
   read snippets; fetch **at most ~3 pages**, and on any slow/failed fetch skip immediately — do not
   retry. Prefer, in order: the institutional faculty profile, the lab website, Google Scholar.
   Capture research areas, current position, recent grants, key collaborators. Save to
   `research_report.md` regardless of how many pages loaded. (For a deeper pass, the
   `literature-research` skill applies.)

7. **Summarize** into `investigator-profiles/<name_slug>/investigator_summary.md`:
   - Header (name, institution, year range, date generated).
   - **Research Overview** — focus/expertise, publication activity, grant funding (institutes,
     mechanisms like R01/K08, totals, active vs. completed).
   - **Publications (N)** — numbered list: authors, title, journal, year, vol(issue):pages, DOI, PMID.
   - **Grant Funding (N, $total)** — per grant: award #, title, dates, mechanism, institute, amount,
     status.
   - **Data Files** — point to `publications.json`, `grants.json`, `research_report.md`.

8. **Report** counts (publications, grants, total funding), key themes, and the output location.

## Batch mode (CSV)
If given a CSV with columns `name, institution, start_year, end_year`: validate the columns, then
run the single-investigator workflow **for each row, one at a time** (this agent is a single loop —
process sequentially, not in parallel). Track success/failure per investigator and keep going if one
fails. At the end write `~/work/<project>/investigator-profiles/batch_summary.md` with a results table
(investigator, institution, #pubs, #grants, total funding, status) and lists of successful and
failed rows. The search scripts already pace their own API calls.

## Screening mode (theranostics relevance)
A lighter pass for triaging many people: run PubMed + NIH Reporter only (**skip step 6 web
research**), then classify each investigator from titles/MeSH/keywords/journals and grant
titles+abstracts with one or more labels — `developer` (makes targeting molecules: radio/medicinal
chemists, ligand/antibody/peptide design), `beneficiary` (disease biology/targets theranostics
could address), `clinical_user` (would administer/interpret agents: nuclear medicine, oncology,
diagnostic radiology), `adjacent` (imaging physics, dosimetry, PET/SPECT instrumentation,
radiobiology), or `none` — each with a 1–2 sentence rationale. Output a summary CSV
(investigator, institution, labels, rationale, #pubs, #grants) plus a short report under
`~/work/<project>/theranostics-screen/`.

## Error handling
- PubMed fails → check connectivity and the `YYYY-MM-DD` date format; try a simpler institution name.
- NIH Reporter fails → use full institution name (not abbreviation); keep fiscal years 1985–present.
- No results → broaden years, check spelling, try alternate institution names.
- Web research fails → proceed with the PubMed + NIH data you have.

## Verification
The output dir exists with `publications.json`, `grants.json`, and `investigator_summary.md`; every
listed publication/grant traces to a verified record (no fabricated entries); counts and totals in
the summary match the JSON.
