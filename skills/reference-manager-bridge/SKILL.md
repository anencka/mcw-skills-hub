---
name: reference-manager-bridge
description: Move references between the agent and the operator's reference manager — EndNote (RIS/XML round-trip), Zotero (API), Mendeley, ReadCube/Papers — so literature work lands in the library they actually use.
version: 1.0.0
metadata:
  hermes:
    tags: [reference, endnote, zotero, mendeley, ris, bibtex]
    category: reference
    related_skills: [reference-management, literature-research, literature-alerts]
---
# Reference-Manager Bridge

## When to Use
The operator wants found papers pushed into their reference manager, wants their library
(or a group library) available to a writing task, or needs a bibliography converted
between manager formats. `reference-management` owns citation *hygiene*; this skill owns
the *transport*.

## First-use setup (read the profile; fill if thin)
`~/work-profile/tools-and-systems.md` should say which manager they use and, for Zotero,
their user/group ID and where the API key lives. Ask once and record it. At MCW, EndNote
is the common default — assume it when unstated, and confirm.

## Mechanics by manager

**EndNote (no API — file round-trip, the reliable path):**
- **Into EndNote:** write an `.ris` file (one reference per record, `TY` first, `ER  -`
  last; include DOI in `DO`, PMID in `AN` or `U1`). Save it in the workspace and tell the
  operator: *File → Import → Options: Reference Manager (RIS)*. Verify tags against 2-3
  records by eye before handing it over — malformed RIS imports silently wrong.
- **Out of EndNote:** ask the operator to export (*File → Export → Output style: RefMan
  (RIS)* or XML) and drop the file in the workspace (Files tab / terminal drop-box). Parse
  RIS or EndNote XML — never guess at fields the export doesn't contain.

**Zotero (real API, works today):**
- Key: the operator creates one at zotero.org/settings/keys; store per their
  `tools-and-systems.md` convention. User ID is on the same page.
- Read: `curl -s -H "Zotero-API-Key: $KEY" "https://api.zotero.org/users/<id>/items?limit=50&format=json"`
  (also `/collections`, `/items?q=<term>`; group libraries via `/groups/<id>/...`).
- Write: POST the same endpoint with a JSON array of item objects; fetch a template first
  (`/items/new?itemType=journalArticle`) rather than hand-building the schema. Respect the
  `Zotero-Write-Token`/version headers on writes.
- 100-item page cap; iterate with `start=` for full-library pulls.

**Mendeley / ReadCube (Papers):** both support RIS import/export — use the EndNote-style
file round-trip by default. Mendeley's API requires an OAuth app registration (not just a
key); treat API wiring as a separate setup task the operator opts into.

**Everything ↔ BibTeX/CSL:** for LaTeX/pandoc work, convert via RIS→BibTeX with pandoc
(`pandoc refs.ris -t biblatex`) or write BibTeX directly — then hand to
`reference-management` for key/style hygiene.

## Procedure
1. Identify manager + direction + which references (from a `literature-research` brief,
   a `literature-alerts` digest, or an operator list).
2. Build the transfer artifact (RIS file or API payload) **from verified metadata only** —
   DOI/PMID-resolved records, never reconstructed citations.
3. Validate before handoff: spot-check records, count in = count out, DOIs resolve.
4. Deliver: file path + the exact import clicks, or the API result summary (created keys,
   failures listed individually).
5. Record the manager/IDs learned in `tools-and-systems.md` for next time.

## Pitfalls
- Fabricating metadata to fill an RIS field — leave a field empty rather than invent it.
- Assuming a Zotero key has write scope (keys are scoped at creation; read-only is common).
- Dumping 500 references into the operator's library without asking — propose, then push.
- Mangling authors: RIS wants one `AU  - Last, First` per author, not a semicolon blob.

## Verification
Record counts match end to end; a spot-checked sample imports with correct
authors/year/DOI; API writes report their created item keys; nothing in the transfer was
invented.
