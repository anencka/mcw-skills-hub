#!/usr/bin/env python3
"""
NIH Reporter Search Script for Academic Investigator Research

Searches NIH Reporter for grants where a specific individual is a named
investigator, filtering by institution and date range.

Usage:
    python nih_reporter_search.py "Kevin Koch" "Medical College of Wisconsin" "2020" "2024"
    python nih_reporter_search.py --first "Kevin" --last "Koch" --institution "MCW" --start-year 2020 --end-year 2024

Output:
    JSON file with grant details including title, funding, dates, and abstracts
"""

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional


def parse_name(full_name: str) -> dict:
    """Parse a full name into components."""
    parts = full_name.strip().split()
    if len(parts) == 1:
        return {"first": "", "middle": "", "last": parts[0]}
    elif len(parts) == 2:
        return {"first": parts[0], "middle": "", "last": parts[1]}
    else:
        return {"first": parts[0], "middle": " ".join(parts[1:-1]), "last": parts[-1]}


def generate_pi_name_variants(first: str, last: str, middle: str = "") -> list:
    """
    Generate PI name search variants for NIH Reporter.

    NIH Reporter uses full name searches but may have variations in how
    names are stored.
    """
    variants = []
    last = last.strip()
    first = first.strip()
    middle = middle.strip() if middle else ""

    if not last:
        return variants

    # Primary variant: standard format
    if first:
        variants.append({"first_name": first, "last_name": last})

        # First initial only
        variants.append({"first_name": first[0], "last_name": last})

        if middle:
            # With middle initial
            middle_initial = middle[0]
            variants.append({
                "first_name": f"{first} {middle_initial}",
                "last_name": last
            })
            variants.append({
                "first_name": f"{first} {middle}",
                "last_name": last
            })
    else:
        variants.append({"last_name": last})

    return variants


def generate_institution_variants(institution: str) -> list:
    """Generate institution name variants for organization search."""
    variants = [institution]

    # Common abbreviation mappings
    abbreviations = {
        "medical college of wisconsin": ["MCW", "Med Coll Wisconsin"],
        "university of wisconsin": ["UW-Madison", "UW Madison", "Univ Wisconsin Madison"],
        "university of": ["Univ"],
        "medical college": ["Med Coll"],
        "medical center": ["Med Ctr"],
        "hospital": ["Hosp"],
        "institute": ["Inst"],
        "national institutes of health": ["NIH"],
    }

    institution_lower = institution.lower()

    for full, abbrevs in abbreviations.items():
        if full in institution_lower:
            variants.extend(abbrevs)
        # Also check if abbreviation was provided and add full name
        for abbrev in abbrevs:
            if abbrev.lower() == institution_lower:
                # Map MCW -> Medical College of Wisconsin, etc.
                if abbrev.lower() == "mcw":
                    variants.append("Medical College of Wisconsin")

    return list(set(variants))


def search_nih_reporter(pi_names: list, institutions: list,
                        start_year: int, end_year: int,
                        limit: int = 500, offset: int = 0) -> dict:
    """
    Search NIH Reporter API for grants.

    Uses the v2 projects search endpoint.
    """
    url = "https://api.reporter.nih.gov/v2/projects/search"

    # Build fiscal years list
    fiscal_years = list(range(start_year, end_year + 1))

    # Build PI name criteria - search using any_name for flexibility
    # NIH Reporter API uses pi_names with first_name and last_name fields
    pi_criteria = []
    for name in pi_names:
        pi_criteria.append({
            "first_name": name.get("first_name", ""),
            "last_name": name.get("last_name", "")
        })

    # Build request body
    request_body = {
        "criteria": {
            "pi_names": pi_criteria,
            "fiscal_years": fiscal_years,
            "org_names": institutions
        },
        "include_fields": [
            "ProjectNum",
            "ProjectNumSplit",
            "ContactPiName",
            "AllText",
            "FullStudySection",
            "SubprojectId",
            "FiscalYear",
            "Organization",
            "ProjectTitle",
            "AbstractText",
            "PhrProjectNum",
            "PiNames",
            "ProjectStartDate",
            "ProjectEndDate",
            "AwardAmount",
            "AgencyIcAdmin",
            "AgencyIcFundings",
            "CongDist",
            "CovidResponse",
            "DirectCostAmt",
            "IndirectCostAmt",
            "OrgCity",
            "OrgCountry",
            "OrgDept",
            "OrgDistrict",
            "OrgDuns",
            "OrgFips",
            "OrgName",
            "OrgState",
            "OrgZipcode",
            "ProgramOfficers",
            "ProjectDetailUrl",
            "AwardNoticeDate",
            "IsActive",
            "AwardType",
            "NciDivisionProgram",
            "ArraFunded",
            "BudgetStart",
            "BudgetEnd"
        ],
        "offset": offset,
        "limit": limit,
        "sort_field": "fiscal_year",
        "sort_order": "desc"
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        request_data = json.dumps(request_body).encode("utf-8")
        req = urllib.request.Request(url, data=request_data, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode())

        return result

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"HTTP Error {e.code}: {error_body}", file=sys.stderr)
        return {"meta": {"total": 0}, "results": []}
    except Exception as e:
        print(f"Error searching NIH Reporter: {e}", file=sys.stderr)
        return {"meta": {"total": 0}, "results": []}


def parse_grant_record(record: dict) -> dict:
    """Parse a NIH Reporter grant record into a structured format."""

    # Extract PI information
    pi_names = record.get("pi_names", []) or []
    contact_pi = record.get("contact_pi_name", "")

    pis = []
    for pi in pi_names:
        pis.append({
            "name": pi.get("full_name", ""),
            "first_name": pi.get("first_name", ""),
            "last_name": pi.get("last_name", ""),
            "is_contact_pi": pi.get("is_contact_pi", False)
        })

    # Extract organization info
    org = {
        "name": record.get("org_name", ""),
        "city": record.get("org_city", ""),
        "state": record.get("org_state", ""),
        "country": record.get("org_country", ""),
        "department": record.get("org_dept", ""),
        "zip": record.get("org_zipcode", "")
    }

    # Extract funding info
    agency_fundings = record.get("agency_ic_fundings", []) or []
    funding_breakdown = []
    for funding in agency_fundings:
        funding_breakdown.append({
            "agency": funding.get("name", ""),
            "abbreviation": funding.get("abbreviation", ""),
            "total_cost": funding.get("total_cost", 0)
        })

    # Extract dates
    project_start = record.get("project_start_date", "")
    project_end = record.get("project_end_date", "")
    budget_start = record.get("budget_start", "")
    budget_end = record.get("budget_end", "")

    # Parse project number components
    project_num_split = record.get("project_num_split", {}) or {}

    # Determine mechanism from project number
    project_num = record.get("project_num", "")
    mechanism = project_num_split.get("activity_code", "")
    if not mechanism and project_num:
        # Try to extract from full project number (e.g., R01, K08, etc.)
        match = re.match(r'^([A-Z]\d{2})', project_num)
        if match:
            mechanism = match.group(1)

    return {
        "project_number": project_num,
        "project_number_components": {
            "activity_code": project_num_split.get("activity_code", ""),
            "administering_ic": project_num_split.get("administering_ic", ""),
            "application_type": project_num_split.get("appl_type_code", ""),
            "serial_number": project_num_split.get("serial_num", ""),
            "support_year": project_num_split.get("support_year", ""),
            "suffix": project_num_split.get("suffix_code", "")
        },
        "title": record.get("project_title", ""),
        "abstract": record.get("abstract_text", ""),
        "principal_investigators": pis,
        "contact_pi": contact_pi,
        "organization": org,
        "fiscal_year": record.get("fiscal_year", ""),
        "dates": {
            "project_start": project_start,
            "project_end": project_end,
            "budget_start": budget_start,
            "budget_end": budget_end
        },
        "funding": {
            "award_amount": record.get("award_amount", 0),
            "direct_cost": record.get("direct_cost_amt", 0),
            "indirect_cost": record.get("indirect_cost_amt", 0),
            "funding_breakdown": funding_breakdown
        },
        "mechanism": mechanism,
        "funding_institute": record.get("agency_ic_admin", {}).get("abbreviation", "") if record.get("agency_ic_admin") else "",
        "funding_institute_name": record.get("agency_ic_admin", {}).get("name", "") if record.get("agency_ic_admin") else "",
        "is_active": record.get("is_active", False),
        "covid_response": record.get("covid_response", []),
        "arra_funded": record.get("arra_funded", ""),
        "study_section": record.get("full_study_section", {}).get("name", "") if record.get("full_study_section") else "",
        "program_officers": record.get("program_officers", []) or [],
        "award_type": record.get("award_type", ""),
        "project_detail_url": record.get("project_detail_url", "") or f"https://reporter.nih.gov/project-details/{project_num}"
    }


def aggregate_grants(grants: list) -> list:
    """
    Aggregate multi-year grant records into single grant entries.

    NIH Reporter returns one record per fiscal year, so we consolidate
    to show unique grants with their full date range and total funding.
    """
    # Group by core project number (without year suffix)
    grant_map = {}

    for grant in grants:
        # Use the core project number (activity code + IC + serial number)
        components = grant.get("project_number_components", {})
        core_num = f"{components.get('activity_code', '')}{components.get('administering_ic', '')}{components.get('serial_num', '')}"

        if not core_num:
            # Fall back to full project number
            core_num = grant.get("project_number", "unknown")

        if core_num not in grant_map:
            grant_map[core_num] = {
                "core_project_number": core_num,
                "project_numbers": [],
                "title": grant.get("title", ""),
                "abstract": grant.get("abstract", ""),
                "principal_investigators": grant.get("principal_investigators", []),
                "contact_pi": grant.get("contact_pi", ""),
                "organization": grant.get("organization", {}),
                "mechanism": grant.get("mechanism", ""),
                "funding_institute": grant.get("funding_institute", ""),
                "funding_institute_name": grant.get("funding_institute_name", ""),
                "earliest_start": grant.get("dates", {}).get("project_start", ""),
                "latest_end": grant.get("dates", {}).get("project_end", ""),
                "fiscal_years": [],
                "total_award_amount": 0,
                "total_direct_cost": 0,
                "total_indirect_cost": 0,
                "is_active": False,
                "study_section": grant.get("study_section", ""),
                "project_detail_url": grant.get("project_detail_url", ""),
                "yearly_records": []
            }

        entry = grant_map[core_num]

        # Add project number if not already present
        project_num = grant.get("project_number", "")
        if project_num and project_num not in entry["project_numbers"]:
            entry["project_numbers"].append(project_num)

        # Track fiscal years
        fy = grant.get("fiscal_year")
        if fy and fy not in entry["fiscal_years"]:
            entry["fiscal_years"].append(fy)

        # Update date range
        start = grant.get("dates", {}).get("project_start", "")
        end = grant.get("dates", {}).get("project_end", "")
        if start and (not entry["earliest_start"] or start < entry["earliest_start"]):
            entry["earliest_start"] = start
        if end and (not entry["latest_end"] or end > entry["latest_end"]):
            entry["latest_end"] = end

        # Accumulate funding
        funding = grant.get("funding", {})
        entry["total_award_amount"] += funding.get("award_amount", 0) or 0
        entry["total_direct_cost"] += funding.get("direct_cost", 0) or 0
        entry["total_indirect_cost"] += funding.get("indirect_cost", 0) or 0

        # Track active status
        if grant.get("is_active"):
            entry["is_active"] = True

        # Keep best abstract (longest non-empty)
        if grant.get("abstract") and len(grant.get("abstract", "")) > len(entry.get("abstract", "") or ""):
            entry["abstract"] = grant.get("abstract")

        # Store yearly record
        entry["yearly_records"].append({
            "fiscal_year": fy,
            "project_number": project_num,
            "award_amount": funding.get("award_amount", 0),
            "budget_start": grant.get("dates", {}).get("budget_start", ""),
            "budget_end": grant.get("dates", {}).get("budget_end", "")
        })

    # Convert to list and sort
    aggregated = list(grant_map.values())

    # Sort fiscal years and yearly records
    for grant in aggregated:
        grant["fiscal_years"].sort(reverse=True)
        grant["yearly_records"].sort(key=lambda x: x.get("fiscal_year", 0), reverse=True)

    # Sort grants by most recent fiscal year
    aggregated.sort(key=lambda x: max(x.get("fiscal_years", [0])), reverse=True)

    return aggregated


def format_grant_reference(grant: dict) -> str:
    """Format a grant as a reference string."""
    title = grant.get("title", "Untitled")
    project_nums = grant.get("project_numbers", [])
    project_num = project_nums[0] if project_nums else grant.get("core_project_number", "Unknown")

    start = grant.get("earliest_start", "")[:10] if grant.get("earliest_start") else ""
    end = grant.get("latest_end", "")[:10] if grant.get("latest_end") else ""
    date_range = f"{start} to {end}" if start and end else ""

    total = grant.get("total_award_amount", 0)
    amount = f"${total:,.0f}" if total else ""

    return f"{project_num}: {title} ({date_range}). {amount}"


def main():
    parser = argparse.ArgumentParser(
        description="Search NIH Reporter for grants by an academic investigator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Kevin Koch" "Medical College of Wisconsin" 2020 2024
  %(prog)s --first Kevin --last Koch --institution MCW --start-year 2020 --end-year 2024
  %(prog)s "Jane Doe" "Harvard" 2019 2024 --output jane_doe_grants.json
        """
    )

    # Positional arguments (simple usage)
    parser.add_argument("name", nargs="?", help="Full name of investigator (e.g., 'Kevin Koch')")
    parser.add_argument("institution", nargs="?", help="Institution name or abbreviation")
    parser.add_argument("start_year", nargs="?", type=int, help="Start fiscal year (e.g., 2020)")
    parser.add_argument("end_year", nargs="?", type=int, help="End fiscal year (e.g., 2024)")

    # Named arguments (advanced usage)
    parser.add_argument("--first", help="First name")
    parser.add_argument("--last", help="Last name")
    parser.add_argument("--middle", help="Middle name or initial", default="")
    parser.add_argument("--institution-name", dest="inst", help="Institution (alternative to positional)")
    parser.add_argument("--start-year", dest="start_yr", type=int, help="Start year (alternative)")
    parser.add_argument("--end-year", dest="end_yr", type=int, help="End year (alternative)")

    # Output options
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--max-results", type=int, default=500, help="Maximum results to fetch")
    parser.add_argument("--no-aggregate", action="store_true", help="Don't aggregate multi-year records")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--raw", action="store_true", help="Output raw API response")

    args = parser.parse_args()

    # Resolve arguments
    if args.first and args.last:
        first_name = args.first
        last_name = args.last
        middle_name = args.middle or ""
    elif args.name:
        name_parts = parse_name(args.name)
        first_name = name_parts["first"]
        last_name = name_parts["last"]
        middle_name = name_parts["middle"]
    else:
        parser.error("Must provide either 'name' or --first/--last arguments")

    institution = args.inst or args.institution
    if not institution:
        parser.error("Must provide institution")

    start_year = args.start_yr or args.start_year
    end_year = args.end_yr or args.end_year
    if not start_year or not end_year:
        parser.error("Must provide start and end years")

    # Generate search variants
    pi_names = generate_pi_name_variants(first_name, last_name, middle_name)
    institution_variants = generate_institution_variants(institution)

    if args.verbose:
        print(f"PI name variants: {pi_names}", file=sys.stderr)
        print(f"Institution variants: {institution_variants}", file=sys.stderr)

    # Search NIH Reporter
    print(f"Searching NIH Reporter for {first_name} {last_name} ({start_year}-{end_year})...", file=sys.stderr)

    all_results = []
    offset = 0
    limit = min(args.max_results, 500)
    total = None

    while True:
        response = search_nih_reporter(pi_names, institution_variants, start_year, end_year, limit=limit, offset=offset)

        if args.raw:
            print(json.dumps(response, indent=2))
            return

        meta = response.get("meta", {})
        if total is None:
            total = meta.get("total", 0)
            print(f"Found {total} grant records", file=sys.stderr)

        results = response.get("results", [])
        if not results:
            break

        all_results.extend(results)
        offset += len(results)

        if offset >= total or offset >= args.max_results:
            break

        print(f"  Fetched {offset}/{total}...", file=sys.stderr)

    # Parse records
    print(f"Processing {len(all_results)} grant records...", file=sys.stderr)
    grants = [parse_grant_record(r) for r in all_results]

    # Aggregate multi-year records
    if not args.no_aggregate:
        aggregated_grants = aggregate_grants(grants)
        print(f"Aggregated into {len(aggregated_grants)} unique grants", file=sys.stderr)
    else:
        aggregated_grants = grants

    # Add references
    for grant in aggregated_grants:
        grant["reference"] = format_grant_reference(grant)

    # Build output
    result = {
        "query": {
            "investigator": f"{first_name} {middle_name} {last_name}".strip(),
            "pi_name_variants": pi_names,
            "institution": institution,
            "institution_variants": institution_variants,
            "start_year": start_year,
            "end_year": end_year
        },
        "summary": {
            "total_records": len(all_results),
            "unique_grants": len(aggregated_grants),
            "active_grants": len([g for g in aggregated_grants if g.get("is_active")]),
            "total_funding": sum(g.get("total_award_amount", 0) for g in aggregated_grants)
        },
        "grants": aggregated_grants
    }

    # Output
    output_json = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_json)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
