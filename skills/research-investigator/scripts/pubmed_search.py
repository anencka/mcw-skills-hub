#!/usr/bin/env python3
"""
PubMed Search Script for Academic Investigator Research

Searches PubMed for publications by a specific author, accounting for name
variations (full first name, first initial, middle initials) and institution
affiliation.

Usage:
    python pubmed_search.py "Kevin Koch" "Medical College of Wisconsin" "2020-01-01" "2024-12-31"
    python pubmed_search.py --first "Kevin" --last "Koch" --middle "M" --institution "MCW" --start "2020-01-01" --end "2024-12-31"

Output:
    JSON file with bibliographic information and abstracts
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
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


def generate_author_variants(first: str, last: str, middle: str = "") -> list:
    """
    Generate author name variants for PubMed search.

    PubMed author search format: "LastName FirstInitial" or "LastName FirstName"

    Note: PubMed's [AU] field does prefix matching, so "McCrea M[AU]" will also
    match papers by "McCrea MA" (with middle initial). We don't need to generate
    all possible middle initial combinations explicitly.
    """
    variants = []
    last = last.strip()
    first = first.strip()
    middle = middle.strip() if middle else ""

    if not last:
        return variants

    # Full last name is always included
    # Variant 1: Last, First (full first name)
    if first:
        variants.append(f"{last} {first}")

        # Variant 2: Last, F (first initial only)
        first_initial = first[0]
        variants.append(f"{last} {first_initial}")

        # Variants with middle initial/name if provided
        if middle:
            middle_initial = middle[0]
            # Variant 3: Last FM (first initial + middle initial)
            variants.append(f"{last} {first_initial}{middle_initial}")
            # Variant 4: Last, First M (full first + middle initial)
            variants.append(f"{last} {first} {middle_initial}")
            # Variant 5: Last, First Middle (full names)
            variants.append(f"{last} {first} {middle}")
    else:
        # Just last name
        variants.append(last)

    return list(set(variants))  # Remove duplicates


def generate_institution_variants(institution: str) -> list:
    """Generate institution name variants for affiliation search."""
    variants = [institution]

    # Common abbreviation mappings
    abbreviations = {
        "medical college of wisconsin": ["MCW", "Med Coll Wisconsin", "Med Coll Wis"],
        "university of wisconsin": ["UW", "Univ Wisconsin", "U Wisconsin", "UW-Madison", "UW Madison"],
        "university of": ["Univ", "U"],
        "medical college": ["Med Coll", "Med College"],
        "medical center": ["Med Ctr", "Med Center"],
        "hospital": ["Hosp"],
        "institute": ["Inst"],
        "department": ["Dept"],
        "national institutes of health": ["NIH"],
        "centers for disease control": ["CDC"],
    }

    institution_lower = institution.lower()

    # Add known abbreviations
    for full, abbrevs in abbreviations.items():
        if full in institution_lower:
            variants.extend(abbrevs)

    return list(set(variants))


def build_pubmed_query(author_variants: list, institution_variants: list,
                       start_date: str, end_date: str) -> str:
    """
    Build a PubMed search query.

    Query structure:
    (author1[AU] OR author2[AU] OR ...) AND
    (institution1[AD] OR institution2[AD] OR ...) AND
    (start_date:end_date[PDAT])
    """
    # Author query - use [AU] field
    # Note: Don't use quotes around author names - PubMed's [AU] field is structured
    # and works better with unquoted "LastName FirstInitial" format
    author_queries = [f'{v}[AU]' for v in author_variants]
    author_part = "(" + " OR ".join(author_queries) + ")"

    # Institution query - use [AD] (affiliation) field
    institution_queries = [f'"{v}"[AD]' for v in institution_variants]
    institution_part = "(" + " OR ".join(institution_queries) + ")"

    # Date range query - format: YYYY/MM/DD
    start_formatted = start_date.replace("-", "/")
    end_formatted = end_date.replace("-", "/")
    date_part = f'("{start_formatted}"[PDAT] : "{end_formatted}"[PDAT])'

    # Combine all parts
    query = f"{author_part} AND {institution_part} AND {date_part}"

    return query


def search_pubmed(query: str, max_results: int = 1000) -> list:
    """
    Search PubMed and return list of PMIDs.

    Uses E-utilities esearch endpoint.
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "usehistory": "y"
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())

        result = data.get("esearchresult", {})
        pmids = result.get("idlist", [])
        count = int(result.get("count", 0))

        print(f"Found {count} results, retrieved {len(pmids)} PMIDs", file=sys.stderr)

        return pmids

    except Exception as e:
        print(f"Error searching PubMed: {e}", file=sys.stderr)
        return []


def fetch_pubmed_details(pmids: list, batch_size: int = 100) -> list:
    """
    Fetch detailed records for PMIDs.

    Uses E-utilities efetch endpoint with XML format.
    """
    if not pmids:
        return []

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    all_records = []

    # Process in batches
    for i in range(0, len(pmids), batch_size):
        batch = pmids[i:i + batch_size]
        print(f"Fetching records {i+1}-{i+len(batch)} of {len(pmids)}...", file=sys.stderr)

        params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "rettype": "xml",
            "retmode": "xml"
        }

        url = f"{base_url}?{urllib.parse.urlencode(params)}"

        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                xml_data = response.read().decode()

            records = parse_pubmed_xml(xml_data)
            all_records.extend(records)

            # Be nice to NCBI servers
            if i + batch_size < len(pmids):
                time.sleep(0.5)

        except Exception as e:
            print(f"Error fetching batch: {e}", file=sys.stderr)

    return all_records


def parse_pubmed_xml(xml_data: str) -> list:
    """Parse PubMed XML response into structured records."""
    records = []

    try:
        root = ET.fromstring(xml_data)

        for article in root.findall(".//PubmedArticle"):
            record = parse_article(article)
            if record:
                records.append(record)

    except ET.ParseError as e:
        print(f"XML parsing error: {e}", file=sys.stderr)

    return records


def parse_article(article: ET.Element) -> Optional[dict]:
    """Parse a single PubMed article element."""
    try:
        medline = article.find(".//MedlineCitation")
        if medline is None:
            return None

        pmid_elem = medline.find(".//PMID")
        pmid = pmid_elem.text if pmid_elem is not None else ""

        article_elem = medline.find(".//Article")
        if article_elem is None:
            return None

        # Title
        title_elem = article_elem.find(".//ArticleTitle")
        title = "".join(title_elem.itertext()) if title_elem is not None else ""

        # Abstract
        abstract_elem = article_elem.find(".//Abstract")
        abstract = ""
        if abstract_elem is not None:
            abstract_texts = []
            for text in abstract_elem.findall(".//AbstractText"):
                label = text.get("Label", "")
                content = "".join(text.itertext())
                if label:
                    abstract_texts.append(f"{label}: {content}")
                else:
                    abstract_texts.append(content)
            abstract = " ".join(abstract_texts)

        # Authors
        authors = []
        author_list = article_elem.find(".//AuthorList")
        if author_list is not None:
            for author in author_list.findall(".//Author"):
                last_name = author.findtext("LastName", "")
                fore_name = author.findtext("ForeName", "")
                initials = author.findtext("Initials", "")

                # Get affiliations
                affiliations = []
                for aff in author.findall(".//AffiliationInfo/Affiliation"):
                    if aff.text:
                        affiliations.append(aff.text)

                authors.append({
                    "last_name": last_name,
                    "fore_name": fore_name,
                    "initials": initials,
                    "affiliations": affiliations
                })

        # Journal info
        journal = article_elem.find(".//Journal")
        journal_title = ""
        journal_abbrev = ""
        volume = ""
        issue = ""
        pages = ""
        pub_year = ""
        pub_month = ""

        if journal is not None:
            journal_title = journal.findtext(".//Title", "")
            journal_abbrev = journal.findtext(".//ISOAbbreviation", "")

            ji = journal.find(".//JournalIssue")
            if ji is not None:
                volume = ji.findtext("Volume", "")
                issue = ji.findtext("Issue", "")

                pub_date = ji.find(".//PubDate")
                if pub_date is not None:
                    pub_year = pub_date.findtext("Year", "")
                    pub_month = pub_date.findtext("Month", "")
                    if not pub_year:
                        medline_date = pub_date.findtext("MedlineDate", "")
                        if medline_date:
                            year_match = re.search(r'\d{4}', medline_date)
                            if year_match:
                                pub_year = year_match.group()

        # Pagination
        pagination = article_elem.find(".//Pagination")
        if pagination is not None:
            pages = pagination.findtext("MedlinePgn", "")

        # DOI and other IDs
        doi = ""
        pmc = ""
        for id_elem in article.findall(".//ArticleIdList/ArticleId"):
            id_type = id_elem.get("IdType", "")
            if id_type == "doi":
                doi = id_elem.text or ""
            elif id_type == "pmc":
                pmc = id_elem.text or ""

        # MeSH terms
        mesh_terms = []
        mesh_list = medline.find(".//MeshHeadingList")
        if mesh_list is not None:
            for mesh in mesh_list.findall(".//MeshHeading"):
                descriptor = mesh.find("DescriptorName")
                if descriptor is not None and descriptor.text:
                    mesh_terms.append(descriptor.text)

        # Keywords
        keywords = []
        keyword_list = medline.find(".//KeywordList")
        if keyword_list is not None:
            for kw in keyword_list.findall("Keyword"):
                if kw.text:
                    keywords.append(kw.text)

        # Publication types
        pub_types = []
        for pt in article_elem.findall(".//PublicationTypeList/PublicationType"):
            if pt.text:
                pub_types.append(pt.text)

        return {
            "pmid": pmid,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "journal": {
                "title": journal_title,
                "abbreviation": journal_abbrev,
                "volume": volume,
                "issue": issue,
                "pages": pages
            },
            "publication_date": {
                "year": pub_year,
                "month": pub_month
            },
            "doi": doi,
            "pmc_id": pmc,
            "mesh_terms": mesh_terms,
            "keywords": keywords,
            "publication_types": pub_types,
            "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""
        }

    except Exception as e:
        print(f"Error parsing article: {e}", file=sys.stderr)
        return None


def format_citation(record: dict) -> str:
    """Format a record as a bibliographic citation."""
    authors = record.get("authors", [])

    # Format authors
    if len(authors) == 0:
        author_str = "Unknown"
    elif len(authors) == 1:
        author_str = f"{authors[0]['last_name']} {authors[0]['initials']}"
    elif len(authors) <= 6:
        author_str = ", ".join(f"{a['last_name']} {a['initials']}" for a in authors)
    else:
        author_str = ", ".join(f"{a['last_name']} {a['initials']}" for a in authors[:6]) + ", et al"

    title = record.get("title", "Untitled")
    journal = record.get("journal", {})
    journal_abbrev = journal.get("abbreviation") or journal.get("title", "")
    year = record.get("publication_date", {}).get("year", "")
    volume = journal.get("volume", "")
    issue = journal.get("issue", "")
    pages = journal.get("pages", "")
    doi = record.get("doi", "")

    # Build citation
    citation = f"{author_str}. {title} {journal_abbrev}. {year}"
    if volume:
        citation += f";{volume}"
        if issue:
            citation += f"({issue})"
    if pages:
        citation += f":{pages}"
    citation += "."
    if doi:
        citation += f" doi:{doi}"

    return citation


def main():
    parser = argparse.ArgumentParser(
        description="Search PubMed for publications by an academic investigator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Kevin Koch" "Medical College of Wisconsin" "2020-01-01" "2024-12-31"
  %(prog)s --first Kevin --last Koch --institution MCW --start 2020-01-01 --end 2024-12-31
  %(prog)s "Jane Doe" "Harvard" "2019-01-01" "2024-12-31" --output jane_doe_pubs.json
        """
    )

    # Positional arguments (simple usage)
    parser.add_argument("name", nargs="?", help="Full name of investigator (e.g., 'Kevin Koch')")
    parser.add_argument("institution", nargs="?", help="Institution name or abbreviation")
    parser.add_argument("start_date", nargs="?", help="Start date (YYYY-MM-DD)")
    parser.add_argument("end_date", nargs="?", help="End date (YYYY-MM-DD)")

    # Named arguments (advanced usage)
    parser.add_argument("--first", help="First name")
    parser.add_argument("--last", help="Last name")
    parser.add_argument("--middle", help="Middle name or initial", default="")
    parser.add_argument("--institution-name", dest="inst", help="Institution (alternative to positional)")
    parser.add_argument("--start", help="Start date (alternative to positional)")
    parser.add_argument("--end", help="End date (alternative to positional)")

    # Output options
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--max-results", type=int, default=1000, help="Maximum results to fetch")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--query-only", action="store_true", help="Only print the query, don't search")

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

    start_date = args.start or args.start_date
    end_date = args.end or args.end_date
    if not start_date or not end_date:
        parser.error("Must provide start and end dates")

    # Generate search variants
    author_variants = generate_author_variants(first_name, last_name, middle_name)
    institution_variants = generate_institution_variants(institution)

    if args.verbose:
        print(f"Author variants: {author_variants}", file=sys.stderr)
        print(f"Institution variants: {institution_variants}", file=sys.stderr)

    # Build query
    query = build_pubmed_query(author_variants, institution_variants, start_date, end_date)

    if args.verbose or args.query_only:
        print(f"PubMed Query: {query}", file=sys.stderr)

    if args.query_only:
        print(query)
        return

    # Search PubMed
    print(f"Searching PubMed for {first_name} {last_name}...", file=sys.stderr)
    pmids = search_pubmed(query, args.max_results)

    if not pmids:
        print("No results found", file=sys.stderr)
        result = {
            "query": {
                "author": f"{first_name} {middle_name} {last_name}".strip(),
                "author_variants": author_variants,
                "institution": institution,
                "institution_variants": institution_variants,
                "start_date": start_date,
                "end_date": end_date,
                "pubmed_query": query
            },
            "total_results": 0,
            "publications": []
        }
    else:
        # Fetch details
        print(f"Fetching details for {len(pmids)} publications...", file=sys.stderr)
        records = fetch_pubmed_details(pmids)

        # Add citations to records
        for record in records:
            record["citation"] = format_citation(record)

        result = {
            "query": {
                "author": f"{first_name} {middle_name} {last_name}".strip(),
                "author_variants": author_variants,
                "institution": institution,
                "institution_variants": institution_variants,
                "start_date": start_date,
                "end_date": end_date,
                "pubmed_query": query
            },
            "total_results": len(records),
            "publications": records
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
