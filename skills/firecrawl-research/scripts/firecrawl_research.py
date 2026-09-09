#!/usr/bin/env python3
"""
Firecrawl Research Index client — search life-sciences / arXiv papers by topic or author.

Wraps the four Firecrawl Research Index endpoints (https://docs.firecrawl.dev/features/research):
  search   GET /v2/search/research/papers?query=...&authors=...&from=...&to=...&k=N
  paper    GET /v2/search/research/papers/{id}                (metadata incl. authors)
  read     GET /v2/search/research/papers/{id}?query=...&k=N  (full-text passages)
  similar  GET /v2/search/research/papers/{id}/similar?intent=...&mode=...&k=N

Index: ~41M+ abstracts across PubMed, bioRxiv, medRxiv (life sciences) and arXiv.
Auth: reads FIRECRAWL_API_KEY from the environment. Works keyless at lower rate
limits; the key raises them. Paper ids accept canonical paperId or a source id
(pmid:38570288, pmcid:PMC12296053, arxiv:2004.05211, doi:10.1053/...).

Usage:
    python3 firecrawl_research.py search "PSMA radioligand therapy" -k 20 --output results.json
    python3 firecrawl_research.py search "simultaneous multislice MRI" --authors "Okafor" --from 2015-01-01
    python3 firecrawl_research.py paper pmid:38570288
    python3 firecrawl_research.py read pmid:38570288 "what response rates were reported" -k 5
    python3 firecrawl_research.py similar pmid:38570288 --intent "other PSMA therapy trials" --mode citers

Output: JSON to --output file (default stdout). Exit 0 on success, 1 on API/network error.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://api.firecrawl.dev/v2/search/research/papers"


def api_get(path: str, params: dict) -> dict:
    """GET a Research Index endpoint, with one retry on 429/5xx."""
    qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{BASE_URL}{path}" + (f"?{qs}" if qs else "")
    headers = {"Accept": "application/json"}
    api_key = os.environ.get("FIRECRAWL_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    last_err = None
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:500]}"
            if e.code == 429 and not api_key:
                last_err += " (keyless rate limit — set FIRECRAWL_API_KEY for higher limits)"
            if e.code not in (429, 500, 502, 503) or attempt == 1:
                break
            time.sleep(5)
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = f"network error: {e}"
            if attempt == 1:
                break
            time.sleep(5)
    raise RuntimeError(f"Firecrawl API request failed: {url}\n{last_err}")


def quote_id(paper_id: str) -> str:
    return urllib.parse.quote(paper_id, safe="")


def cmd_search(args) -> dict:
    return api_get("", {
        "query": args.query,
        "authors": args.authors,
        "categories": args.categories,
        "from": args.from_date,
        "to": args.to_date,
        "k": args.k,
    })


def cmd_paper(args) -> dict:
    return api_get(f"/{quote_id(args.id)}", {})


def cmd_read(args) -> dict:
    return api_get(f"/{quote_id(args.id)}", {"query": args.query, "k": args.k})


def cmd_similar(args) -> dict:
    return api_get(f"/{quote_id(args.id)}/similar", {
        "intent": args.intent,
        "mode": args.mode,
        "k": args.k,
    })


def main() -> int:
    parser = argparse.ArgumentParser(description="Query the Firecrawl Research Index")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--output", help="write JSON here instead of stdout")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("search", parents=[common],
                       help="search paper abstracts by topic (optionally filter by author)")
    p.add_argument("query", help="natural-language topic query")
    p.add_argument("--authors", help="author substring filter, e.g. 'Okafor'")
    p.add_argument("--categories", help="category filter, e.g. 'cs.LG' (arXiv) — omit for life sciences")
    p.add_argument("--from", dest="from_date", help="inclusive lower date bound, YYYY-MM-DD")
    p.add_argument("--to", dest="to_date", help="inclusive upper date bound, YYYY-MM-DD")
    p.add_argument("-k", type=int, default=20, help="number of results (default 20)")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("paper", parents=[common],
                       help="fetch one paper's metadata (title, authors, dates, ids)")
    p.add_argument("id", help="paperId or pmid:/pmcid:/arxiv:/doi: id")
    p.set_defaults(func=cmd_paper)

    p = sub.add_parser("read", parents=[common],
                       help="retrieve top full-text passages answering a question")
    p.add_argument("id", help="paperId or pmid:/pmcid:/arxiv:/doi: id")
    p.add_argument("query", help="question about the paper's content")
    p.add_argument("-k", type=int, default=5, help="number of passages (default 5)")
    p.set_defaults(func=cmd_read)

    p = sub.add_parser("similar", parents=[common],
                       help="find related papers (co-citation, citers, or references)")
    p.add_argument("id", help="paperId or pmid:/pmcid:/arxiv:/doi: id")
    p.add_argument("--intent", required=True, help="natural-language intent for ranking")
    p.add_argument("--mode", choices=["similar", "citers", "references"], default="similar")
    p.add_argument("-k", type=int, default=10, help="number of results (default 10)")
    p.set_defaults(func=cmd_similar)

    args = parser.parse_args()
    try:
        result = args.func(args)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        if isinstance(result, dict) and "results" in result:
            summary = f"{len(result['results'])} results"
        elif isinstance(result, dict) and "passages" in result:
            summary = f"{len(result['passages'])} passages"
            if not result["passages"]:
                summary += " (no full text indexed for this paper — use its abstract/DOI)"
        elif isinstance(result, dict) and "paper" in result:
            summary = f"paper: {result['paper'].get('title', '?')}"
        else:
            summary = "response"
        print(f"Wrote {summary} to {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
