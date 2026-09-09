---
name: firecrawl-research
description: Research a life-sciences topic or author against Firecrawl's Research Index (41M+ paper abstracts from PubMed, bioRxiv, medRxiv, and arXiv, refreshed daily) — ranked semantic search, full-text passage reading, and citation-graph exploration. Uses the Firecrawl API (FIRECRAWL_API_KEY from Settings → Integrations; works keyless at lower rate limits).
version: 1.0.0
metadata:
  hermes:
    tags: [research, firecrawl, literature, papers, pubmed, biorxiv, medrxiv, arxiv, life-sciences]
    category: research
    related_skills: [literature-research, research-investigator, reference-management]
---
# Firecrawl Research (Papers Index)

Search Firecrawl's **Research Index** — one semantic index over ~41M+ paper abstracts covering the
drug-discovery, clinical-trial, and biology literature (PubMed, bioRxiv, medRxiv) plus arXiv —
by **topic** or by **author**, then read full-text passages and walk the citation graph. Everything
goes through the bundled script; results are real indexed records, never reconstructed from memory.

**How this differs from neighbors:** `research-investigator` builds an investigator *dossier*
(PubMed + NIH Reporter grants, false-positive review); `literature-research` is the general
source-agnostic synthesis procedure. This skill is the **Firecrawl-specific search engine** — one
ranked semantic query across biomedical + preprint sources at once, with passage-level reading.
Use it alone for quick topic/author sweeps, or as the search step inside `literature-research`.

## API key
The script reads `FIRECRAWL_API_KEY` from the environment — the same key the operator enters at
**Settings → Integrations → Firecrawl** (it lands in the agent's `.env`). The paper endpoints also
work **keyless at lower rate limits**, so never block on a missing key: proceed, and if you hit
HTTP 429 tell the operator that adding a Firecrawl key in Settings raises the limits.

## Paths (this container)
- **Script:** `/opt/mcwagent/hermes-skills/research/firecrawl-research/scripts/firecrawl_research.py`
- **Project:** all work lives under a project folder — `~/work/<project>/` (never write loose in
  `~/work/`). Ask the operator which project this is for, or propose one.
- **Output:** `~/work/<project>/firecrawl-research/<slug>/` where `<slug>` is a short lowercase
  underscore name for the topic or author (e.g. `psma_radioligand`, `okafor_dwi`).

## Script commands (exact)
```bash
SCRIPT=/opt/mcwagent/hermes-skills/research/firecrawl-research/scripts/firecrawl_research.py

# 1. Topic search — ranked abstracts. Optional: --authors <substring>, --from/--to YYYY-MM-DD, -k N (default 20)
python3 $SCRIPT search "PSMA radioligand therapy response rates" -k 20 --output search.json

# 2. Paper metadata — title, authors, dates, ids (search results do NOT include authors; this does)
python3 $SCRIPT paper pmid:38570288 --output paper_38570288.json

# 3. Read full-text passages answering a question (empty passages = full text not indexed)
python3 $SCRIPT read pmid:38570288 "what response rates were reported" -k 5 --output read_38570288.json

# 4. Related papers via citation graph: --mode similar (co-citation, default) | citers | references
python3 $SCRIPT similar pmid:38570288 --intent "other PSMA radioligand trials" --mode citers -k 10 --output similar.json
```
Paper ids: canonical `paperId` from results, or `pmid:`, `pmcid:`, `arxiv:`, `doi:` forms.
Search returns `{success, results: [{paperId, primaryId, ids{doi,pmid,pmcid,arxiv}, title, abstract, score}]}`.

## Workflow — topic mode
1. Ask for the topic (and optional date range) if not given; set up the output dir.
2. Turn the topic into 2–4 **distinct natural-language queries** (different phrasings/subaspects —
   the index is semantic, and phrasing changes results). Run each `search` to its own
   `search_<n>.json`, pacing ~1 s between calls.
3. Deduplicate by `paperId` across the runs. Keep on-topic hits (read the abstracts — drop
   coincidental semantic matches).
4. For the **3–8 most load-bearing papers**, run `paper` (to get authors + dates) and `read` with
   the operator's actual question. If `passages` is empty, use the abstract and say so — do not
   paraphrase full text you never retrieved.
5. Optionally expand from the 1–2 best papers with `similar` (`citers` for follow-on work,
   `references` for foundations).
6. Write `topic_summary.md`: header (topic, queries used, date range, generated date); findings by
   theme with per-claim citations (title, authors when fetched, year, DOI/PMID); a "coverage &
   gaps" note (what the queries did/didn't reach; abstracts-only vs full-text-read); and a full
   deduplicated paper list. Point to the raw JSON files.

## Workflow — author mode
1. Get author name (and optional topic focus / date range). Note: `--authors` is a **substring
   match on the author string** — use the last name (`--authors "Okafor"`), not "First Last".
2. The API requires a topic query even in author mode, and results are phrasing-sensitive. Run
   **2–3 broad queries** covering the author's likely areas with `--authors <lastname>` (ask the
   operator for areas, or take them from `~/work-profile/domain-knowledge.md` — read fresh).
   An empty `results` array means *that query* found nothing — try another phrasing before
   concluding the author has no indexed papers.
3. **Verify authorship:** search hits don't list authors. For every hit, run `paper` (pace ~1 s)
   and confirm the target appears in `paper.authors`; drop non-matches. Same-surname collisions
   exist — flag "uncertain" rather than guessing when initials/fields don't line up.
4. Write `author_summary.md`: verified papers (numbered: authors, title, year, DOI/PMID), themes
   across them, and an explicit note that this reflects **index coverage under the queries used**,
   not a complete bibliography — for that, `research-investigator` (PubMed + grants) is the tool.

## Error handling
- **HTTP 429** → keyless rate limit; tell the operator a Firecrawl key in Settings → Integrations
  raises limits. Wait 30 s and retry once; if still limited, deliver what you have and say so.
- **Empty results** → rephrase the query (semantic index); for authors, try more/broader topic
  queries. Report empty only after ≥3 phrasings.
- **Empty `passages`** → full text isn't indexed for that paper (common for abstract-only PubMed
  records); fall back to the abstract and cite the DOI for the operator to read the source.
- **Network failure** → the script retries once itself; report the stderr message, don't loop.

## No fabrication
Every paper in a summary traces to a record in the saved JSON (`paperId` + title match). Never
invent or "complete" citations, author lists, or findings; never cite full text when only the
abstract was retrieved. If the offline model is unsure whether two hits are the same paper,
compare `ids` (DOI/PMID) — don't merge on title similarity alone.

## Verification
Output dir contains the raw `*.json` files and the summary; every cited paper appears in a JSON
file; author-mode papers each have a `paper_*.json` proving the author match; limitations
(rate-limited, abstracts-only, queries used) are stated in the summary.
