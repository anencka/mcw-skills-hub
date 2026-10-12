#!/usr/bin/env python3
"""Collect and normalize funding-watch source data into a canonical run directory.

Bundled with the funding-opportunity-digest skill. Queries Grants.gov (discovery),
NIH RePORTER and NSF Awards (calibration) for every keyword in the watch config and
writes one sanitized, normalized artifact:

    <project-root>/runs/<YYYY-MM-DD>/sources.json

Envelope-level fields (Grants.gov's response `token`, pagination metadata, etc.) are
never written. Any source whose response is missing its documented record key, whose
records are not objects, or whose records lack a source identifier is recorded as a
failure — never as a silent zero-result run. Exit status is nonzero when any source
failed so a scheduled job can disclose missing coverage.

Subcommands (all take --project-root, default ~/work/funding-digest):

    refresh   [--run-date D]   collect + normalize; marks each Grants.gov record `seen` and
                               lists `new_candidates` (not in the seen log or Do Not Surface)
    mark-seen --run-date D     append D's screened identifiers to state/seen.jsonl — refuses
                               until runs/D/digest.txt or runs/D/run-summary.md exists
    migrate                    one-time move of a legacy `## Reviewed/Seen` config list into
                               state/seen.jsonl (idempotent)

    python3 refresh.py refresh --project-root ~/work/my-digest --run-date 2026-01-05
    python3 refresh.py --project-root . --run-date 2026-01-05     # same as `refresh`

Exit codes: 0 ok; 1 at least one source failed (recorded in sources.json); 2 usage or
configuration error, nothing written.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Callable
from urllib import parse, request

DEFAULT_PROJECT_ROOT = Path("~/work/funding-digest")
CONFIG_RELPATH = Path("config") / "funding-watch.md"
SEEN_RELPATH = Path("state") / "seen.jsonl"
USER_AGENT = "Hermes funding-opportunity-digest/3.0"
EXIT_OK, EXIT_PARTIAL, EXIT_USAGE = 0, 1, 2
SUBCOMMANDS = ("refresh", "mark-seen", "migrate")
# The operator's manual never-surface list. The legacy heading held the machine seen list
# before 3.0.0; `migrate` moves those entries to state/seen.jsonl and renames the heading.
OVERRIDE_HEADING = "## Do Not Surface"
LEGACY_HEADING_PREFIX = "## reviewed/seen"
GRANTSGOV_ROWS = 25
CALIBRATION_LIMIT = 20


def required_identifier(value: Any, source: str) -> str:
    """Return a nonblank source identifier or reject the record."""
    if value is None or not str(value).strip():
        raise ValueError(f"{source} record is missing its required identifier")
    return str(value).strip()


def parse_keywords(config_text: str) -> list[str]:
    """Return bullet items under the '## Search Keywords' section of the watch config."""
    keywords: list[str] = []
    in_section = False
    for raw_line in config_text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            in_section = line.casefold() == "## search keywords"
            continue
        if in_section and line.startswith("- "):
            value = line[2:].strip()
            if value:
                keywords.append(value)
    if not keywords:
        raise ValueError("No entries found under '## Search Keywords'")
    return keywords


def _fetch_json(
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout: int = 90,
    opener: Callable[..., Any] = request.urlopen,
) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=body, headers=headers, method="POST" if body else "GET")
    with opener(req, timeout=timeout) as response:
        decoded = json.loads(response.read().decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("API response must be a JSON object")
    return decoded


def normalize_grantsgov(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Grants.gov search2: records live under data.oppHits; the opportunity number is `number`."""
    if data.get("errorcode") not in (None, 0):
        raise ValueError(f"Grants.gov API error: {data.get('msg', data.get('errorcode'))}")
    envelope = data.get("data")
    if not isinstance(envelope, dict) or "oppHits" not in envelope:
        raise ValueError("Grants.gov response is missing data.oppHits")
    hits = envelope["oppHits"]
    if not isinstance(hits, list):
        raise ValueError("Grants.gov response is missing data.oppHits")
    records = []
    for hit in hits:
        if not isinstance(hit, dict):
            raise ValueError("Grants.gov oppHits entries must be objects")
        detail_id = hit.get("id")
        records.append(
            {
                "record_type": "opportunity",
                "use": "discovery",
                "identifier": required_identifier(hit.get("number"), "Grants.gov"),
                "title": hit.get("title"),
                "agency": hit.get("agency"),
                "agency_code": hit.get("agencyCode"),
                "open_date": hit.get("openDate"),
                "close_date": hit.get("closeDate"),
                "status": hit.get("oppStatus"),
                "link": f"https://www.grants.gov/search-results-detail/{detail_id}" if detail_id else None,
            }
        )
    return records


def normalize_reporter(data: dict[str, Any]) -> list[dict[str, Any]]:
    """NIH RePORTER projects/search: records live under `results`."""
    if "results" not in data:
        raise ValueError("NIH RePORTER response is missing results")
    hits = data["results"]
    if not isinstance(hits, list):
        raise ValueError("NIH RePORTER response is missing results")
    records = []
    for hit in hits:
        if not isinstance(hit, dict):
            raise ValueError("NIH RePORTER results entries must be objects")
        agency = hit.get("agency_ic_admin")
        records.append(
            {
                "record_type": "award",
                "use": "calibration",
                "identifier": required_identifier(hit.get("project_num"), "NIH RePORTER"),
                "title": hit.get("project_title"),
                "agency": agency.get("name") if isinstance(agency, dict) else agency,
                "activity_code": hit.get("activity_code"),
                "fiscal_year": hit.get("fiscal_year"),
                "award_amount": hit.get("award_amount"),
                "link": f"https://reporter.nih.gov/project-details/{hit['appl_id']}"
                if hit.get("appl_id") else None,
            }
        )
    return records


def normalize_nsf(data: dict[str, Any]) -> list[dict[str, Any]]:
    """NSF Awards API: records live under response.award."""
    envelope = data.get("response")
    if not isinstance(envelope, dict) or "award" not in envelope:
        raise ValueError("NSF response is missing response.award")
    hits = envelope["award"]
    if not isinstance(hits, list):
        raise ValueError("NSF response is missing response.award")
    records = []
    for hit in hits:
        if not isinstance(hit, dict):
            raise ValueError("NSF response.award entries must be objects")
        identifier = required_identifier(hit.get("id"), "NSF")
        records.append(
            {
                "record_type": "award",
                "use": "calibration",
                "identifier": identifier,
                "title": hit.get("title"),
                "agency": "U.S. National Science Foundation",
                "awardee": hit.get("awardeeName"),
                "date": hit.get("date"),
                "award_amount": hit.get("fundsObligatedAmt"),
                "link": f"https://www.nsf.gov/awardsearch/showAward?AWD_ID={identifier}",
            }
        )
    return records


def source_calls(term: str) -> dict[str, tuple[str, dict[str, Any] | None, Callable[..., Any]]]:
    """The exact request contract for each source. Tests assert against this."""
    return {
        "grantsgov": (
            "https://api.grants.gov/v1/api/search2",
            {"keyword": term, "oppStatuses": "posted", "rows": GRANTSGOV_ROWS},
            normalize_grantsgov,
        ),
        "reporter": (
            "https://api.reporter.nih.gov/v2/projects/search",
            {
                "criteria": {
                    "advanced_text_search": {
                        "operator": "and",
                        "search_field": "all",
                        "search_text": term,
                    },
                    "use_relevance": True,
                },
                "limit": CALIBRATION_LIMIT,
                "include_fields": [
                    "ApplId",
                    "ProjectNum",
                    "ProjectTitle",
                    "AgencyIcAdmin",
                    "ActivityCode",
                    "FiscalYear",
                    "AwardAmount",
                ],
            },
            normalize_reporter,
        ),
        "nsf": (
            "https://api.nsf.gov/services/v1/awards.json?"
            + parse.urlencode({"keyword": term, "rpp": CALIBRATION_LIMIT}),
            None,
            normalize_nsf,
        ),
    }


def collect_term(term: str, opener: Callable[..., Any] | None = None) -> dict[str, Any]:
    opener = opener or request.urlopen  # resolved per call so tests can patch the module
    result: dict[str, Any] = {"term": term, "sources": {}}
    for source, (url, payload, normalizer) in source_calls(term).items():
        try:
            response = _fetch_json(url, payload=payload, opener=opener)
            records = normalizer(response)
            result["sources"][source] = {"status": "ok", "record_count": len(records), "records": records}
        except Exception as exc:  # Preserve per-source failures without aborting the full run.
            result["sources"][source] = {
                "status": "error",
                "error_type": type(exc).__name__,
                "message": str(exc),
                "record_count": 0,
                "records": [],
            }
    return result


def run_output_path(project_root: Path, run_date: str) -> Path:
    """Resolve a date-scoped output path and prove it stays inside the project root."""
    normalized = dt.date.fromisoformat(run_date).isoformat()
    root = project_root.expanduser().resolve()
    path = (root / "runs" / normalized / "sources.json").resolve()
    if root not in path.parents:
        raise ValueError("Output path escapes the project root")
    return path


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    write_text_atomic(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        temp_name = handle.name
    os.replace(temp_name, path)


# ---- seen log (machine state) and Do Not Surface (operator config) --------------------

def _is_override_heading(line: str) -> bool:
    folded = line.strip().casefold()
    return folded == OVERRIDE_HEADING.casefold() or folded.startswith(LEGACY_HEADING_PREFIX)


def parse_identifier_section(config_text: str) -> list[tuple[str, str | None]]:
    """Entries under the Do Not Surface (or legacy Reviewed/Seen) heading, in order.

    Accepts `identifier | YYYY-MM-DD`, `identifier`, and `- identifier`; skips blanks and
    HTML comments (single- or multi-line)."""
    entries: list[tuple[str, str | None]] = []
    in_section = in_comment = False
    for raw in config_text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            in_section = _is_override_heading(line)
            continue
        if not in_section:
            continue
        if in_comment:
            in_comment = "-->" not in line
            continue
        if line.startswith("<!--"):
            in_comment = "-->" not in line
            continue
        if not line:
            continue
        ident, _, date = line.lstrip("-* ").partition("|")
        ident, date = ident.strip(), date.strip() or None
        if ident:
            entries.append((ident, date))
    return entries


def load_seen(project_root: Path) -> dict[str, dict[str, Any]]:
    """identifier -> record from state/seen.jsonl (empty when the file does not exist)."""
    path = project_root / SEEN_RELPATH
    seen: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return seen
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        record = json.loads(raw)
        if not isinstance(record, dict) or not str(record.get("identifier", "")).strip():
            raise ValueError(f"{path}:{number} is not a seen record")
        seen.setdefault(record["identifier"], record)
    return seen


def append_seen(project_root: Path, records: list[dict[str, Any]]) -> None:
    """Append records to the seen log atomically (rewrite-and-rename; history preserved)."""
    path = project_root / SEEN_RELPATH
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    lines = "".join(json.dumps(r, sort_keys=True) + "\n" for r in records)
    write_text_atomic(path, existing + lines)


def legacy_seen_pending(project_root: Path, config_text: str) -> bool:
    """True when the config still holds a pre-3.0.0 seen list that was never migrated."""
    if (project_root / SEEN_RELPATH).exists():
        return False
    legacy = any(line.strip().casefold().startswith(LEGACY_HEADING_PREFIX)
                 for line in config_text.splitlines())
    return legacy and bool(parse_identifier_section(config_text))


def screened_identifiers(collected: dict[str, Any]) -> list[str]:
    """Unique Grants.gov identifiers in first-appearance order across all terms."""
    ordered: list[str] = []
    for term in collected.get("terms", []):
        source = term.get("sources", {}).get("grantsgov", {})
        for record in source.get("records", []):
            if record["identifier"] not in ordered:
                ordered.append(record["identifier"])
    return ordered


# ---- subcommands ------------------------------------------------------------------------

def cmd_refresh(project_root: Path, run_date: str) -> int:
    config_path = project_root / CONFIG_RELPATH
    config_text = config_path.read_text(encoding="utf-8")
    keywords = parse_keywords(config_text)
    if legacy_seen_pending(project_root, config_text):
        raise ValueError("config/funding-watch.md still holds a pre-3.0.0 `## Reviewed/Seen` "
                         "list and state/seen.jsonl does not exist — run `refresh.py migrate` once first")
    output_path = run_output_path(project_root, run_date)
    known = set(load_seen(project_root)) | {i for i, _ in parse_identifier_section(config_text)}

    collected = {
        "schema_version": 2,
        "retrieved_on": run_date,
        "config": str(config_path),
        "terms": [collect_term(term) for term in keywords],
    }
    for term in collected["terms"]:
        for record in term["sources"]["grantsgov"]["records"]:
            record["seen"] = record["identifier"] in known
    collected["new_candidates"] = [i for i in screened_identifiers(collected) if i not in known]
    write_json_atomic(output_path, collected)

    failures = sum(
        source["status"] != "ok"
        for term in collected["terms"]
        for source in term["sources"].values()
    )
    print(json.dumps({"output": str(output_path), "terms": len(keywords),
                      "source_failures": failures,
                      "new_candidates": len(collected["new_candidates"])}))
    return EXIT_PARTIAL if failures else EXIT_OK


def cmd_mark_seen(project_root: Path, run_date: str) -> int:
    sources_path = run_output_path(project_root, run_date)
    run_dir = sources_path.parent
    if not sources_path.exists():
        raise ValueError(f"no collector output for {run_date}: {sources_path} does not exist")
    if not ((run_dir / "digest.txt").exists() or (run_dir / "run-summary.md").exists()):
        raise ValueError(f"write runs/{run_date}/digest.txt or runs/{run_date}/run-summary.md "
                         "before marking this run's identifiers seen")
    collected = json.loads(sources_path.read_text(encoding="utf-8"))
    config_text = (project_root / CONFIG_RELPATH).read_text(encoding="utf-8")
    seen = load_seen(project_root)
    overrides = {i for i, _ in parse_identifier_section(config_text)}
    screened = screened_identifiers(collected)
    new = [i for i in screened if i not in seen and i not in overrides]
    append_seen(project_root, [{"identifier": i, "first_seen": run_date, "run_id": run_date} for i in new])
    print(json.dumps({"appended": len(new), "already_seen": len(screened) - len(new),
                      "seen_total": len(seen) + len(new),
                      "seen_log": str(project_root / SEEN_RELPATH)}))
    return EXIT_OK


def cmd_migrate(project_root: Path, today: str) -> int:
    config_path = project_root / CONFIG_RELPATH
    config_text = config_path.read_text(encoding="utf-8")
    has_legacy = any(line.strip().casefold().startswith(LEGACY_HEADING_PREFIX)
                     for line in config_text.splitlines())
    seen_path = project_root / SEEN_RELPATH
    if not has_legacy:
        if not seen_path.exists():
            write_text_atomic(seen_path, "")
        print(json.dumps({"migrated": 0, "duplicates": [], "note": "nothing to migrate"}))
        return EXIT_OK

    entries = parse_identifier_section(config_text)
    seen = load_seen(project_root)
    records, duplicates = [], []
    for ident, date in entries:
        if ident in seen or any(r["identifier"] == ident for r in records):
            duplicates.append(ident)
            continue
        records.append({"identifier": ident, "first_seen": date or today, "run_id": "migrated"})
    append_seen(project_root, records)

    # Rewrite only the legacy section: new heading, explanatory comment, no entries.
    out_lines, skipping = [], False
    for raw in config_text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("## "):
            if stripped.casefold().startswith(LEGACY_HEADING_PREFIX):
                out_lines += [
                    OVERRIDE_HEADING,
                    "<!-- Identifiers listed here are never reported, in addition to the machine seen log",
                    "     at state/seen.jsonl (written by `refresh.py mark-seen`; never edit it by hand).",
                    f"     One identifier per line. {len(records)} seen entries migrated on {today}. -->",
                    "",
                ]
                skipping = True
                continue
            skipping = False
        if not skipping:
            out_lines.append(raw)
    write_text_atomic(config_path, "\n".join(out_lines).rstrip("\n") + "\n")
    print(json.dumps({"migrated": len(records), "duplicates": duplicates,
                      "seen_log": str(seen_path), "config": str(config_path)}))
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in SUBCOMMANDS + ("-h", "--help"):
        argv = ["refresh"] + argv  # pre-3.0.0 invocation without a subcommand

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    today = dt.datetime.now().astimezone().date().isoformat()
    for name in SUBCOMMANDS:
        command = sub.add_parser(name)
        command.add_argument("--project-root", type=Path, default=DEFAULT_PROJECT_ROOT,
                             help=f"digest project directory (default {DEFAULT_PROJECT_ROOT})")
        if name == "refresh":
            command.add_argument("--run-date", default=today,
                                 help="ISO date for this run (default: today, local timezone)")
        elif name == "mark-seen":
            command.add_argument("--run-date", required=True, help="the run whose identifiers to mark")
    args = parser.parse_args(argv)

    project_root = args.project_root.expanduser()
    try:
        if args.command == "migrate":
            return cmd_migrate(project_root, today)
        run_date = dt.date.fromisoformat(args.run_date).isoformat()
        if args.command == "refresh":
            return cmd_refresh(project_root, run_date)
        return cmd_mark_seen(project_root, run_date)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))  # exit 2: nothing was written
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
