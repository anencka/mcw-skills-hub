"""Fail-closed tests for the investigator search scripts (no network).

An outage, an error envelope, or a dropped batch must produce status failed/partial and
exit 1 — never an empty "ok" result that reads as "no grants" / "no publications".

    python3 -m unittest discover -s <skill>/tests
"""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.error

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NIH = load("nih_reporter_search")
PUBMED = load("pubmed_search")


class FakeResponse:
    def __init__(self, body):
        self.body = body if isinstance(body, bytes) else body.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


def run_main(module, argv, opener):
    with tempfile.TemporaryDirectory() as directory:
        out_path = Path(directory) / "out.json"
        with mock.patch.object(module.urllib.request, "urlopen", opener), \
                mock.patch("sys.argv", [module.__name__] + argv + ["--output", str(out_path)]), \
                mock.patch.object(module.time if hasattr(module, "time") else mock.MagicMock(),
                                  "sleep", lambda *_: None), \
                contextlib.redirect_stderr(io.StringIO()):
            rc = module.main()
        return rc, json.loads(out_path.read_text())


NIH_ARGV = ["Jane Doe", "Example University", "2020", "2024"]
PUBMED_ARGV = ["Jane Doe", "Example University", "2020-01-01", "2024-12-31"]

NIH_RECORD = {
    "appl_id": 1, "project_num": "1R01EB000001-01", "core_project_num": "R01EB000001",
    "project_title": "Test grant", "fiscal_year": 2023, "award_amount": 100000,
    "pi_names": [{"first_name": "Jane", "last_name": "Doe", "is_contact_pi": True}],
    "organization": {"org_name": "EXAMPLE UNIVERSITY"},
    "activity_code": "R01", "agency_ic_admin": {"abbreviation": "NIBIB", "name": "NIBIB"},
}

ARTICLE = """<PubmedArticle><MedlineCitation><PMID>{pmid}</PMID><Article>
<ArticleTitle>Paper {pmid}</ArticleTitle><Journal><Title>J Test</Title>
<JournalIssue><PubDate><Year>2022</Year></PubDate></JournalIssue></Journal>
<AuthorList><Author><LastName>Doe</LastName><ForeName>Jane</ForeName></Author></AuthorList>
</Article></MedlineCitation></PubmedArticle>"""


def pubmed_opener(pmids, count=None, efetch_fails=False):
    def opener(req, timeout=None):
        url = req if isinstance(req, str) else req.full_url
        if "esearch" in url:
            return FakeResponse(json.dumps({"esearchresult": {
                "count": str(count if count is not None else len(pmids)), "idlist": pmids}}))
        if efetch_fails:
            raise urllib.error.URLError("efetch down")
        body = "<PubmedArticleSet>" + "".join(ARTICLE.format(pmid=p) for p in pmids) + "</PubmedArticleSet>"
        return FakeResponse(body)
    return opener


class NihReporterTests(unittest.TestCase):
    def test_outage_is_failed_not_empty_success(self):
        def opener(req, timeout=None):
            raise TimeoutError("timed out")
        rc, out = run_main(NIH, NIH_ARGV, opener)
        self.assertEqual(rc, NIH.EXIT_PARTIAL)
        self.assertEqual(out["status"], "failed")
        self.assertEqual(out["grants"], [])
        self.assertIn("TimeoutError", out["errors"][0]["message"])

    def test_http_error_is_failed(self):
        def opener(req, timeout=None):
            raise urllib.error.HTTPError(req.full_url, 503, "unavailable", {}, None)
        rc, out = run_main(NIH, NIH_ARGV, opener)
        self.assertEqual((rc, out["status"]), (NIH.EXIT_PARTIAL, "failed"))
        self.assertIn("503", out["errors"][0]["message"])

    def test_envelope_without_results_is_failed(self):
        rc, out = run_main(NIH, NIH_ARGV, lambda req, timeout=None: FakeResponse('{"meta": {"total": 0}}'))
        self.assertEqual((rc, out["status"]), (NIH.EXIT_PARTIAL, "failed"))

    def test_legitimate_zero_results_is_ok(self):
        rc, out = run_main(NIH, NIH_ARGV,
                           lambda req, timeout=None: FakeResponse('{"meta": {"total": 0}, "results": []}'))
        self.assertEqual((rc, out["status"], out["errors"]), (NIH.EXIT_OK, "ok", []))

    def test_success_is_ok(self):
        body = json.dumps({"meta": {"total": 1}, "results": [NIH_RECORD]})
        rc, out = run_main(NIH, NIH_ARGV, lambda req, timeout=None: FakeResponse(body))
        self.assertEqual((rc, out["status"]), (NIH.EXIT_OK, "ok"))
        self.assertEqual(out["summary"]["total_records"], 1)

    def test_truncation_at_max_results_is_partial(self):
        body = json.dumps({"meta": {"total": 900}, "results": [NIH_RECORD]})
        rc, out = run_main(NIH, NIH_ARGV + ["--max-results", "1"], lambda req, timeout=None: FakeResponse(body))
        self.assertEqual((rc, out["status"]), (NIH.EXIT_PARTIAL, "partial"))
        self.assertIn("incomplete", out["errors"][0]["message"])

    def test_three_r01s_stay_three_grants_with_their_organization_and_pis(self):
        """Yearly records group by core project number. The old key read a component under
        the wrong name, so every R01 of one investigator merged into a single "R01" grant,
        and the organization and PIs came back empty (requested under names the API ignores)."""
        def record(project_num, fy, amount, co_pi=False):
            appl, rest = project_num[0], project_num[1:]
            core, year = rest.split("-")
            pis = [{"full_name": "Jane Q Doe", "first_name": "Jane", "last_name": "Doe", "is_contact_pi": True}]
            if co_pi:
                pis.append({"full_name": "Sam Roe", "first_name": "Sam", "last_name": "Roe", "is_contact_pi": False})
            return {
                "project_num": project_num, "core_project_num": core, "fiscal_year": fy,
                "award_amount": amount, "project_title": f"Grant {core}", "contact_pi_name": "DOE, JANE Q",
                "principal_investigators": pis,
                "organization": {"org_name": "EXAMPLE UNIVERSITY", "org_city": "SPRINGFIELD",
                                 "org_state": "ZZ", "dept_type": "RADIOLOGY"},
                "project_num_split": {"appl_type_code": appl, "activity_code": "R01", "ic_code": core[3:5],
                                      "serial_num": core[5:], "support_year": year[:2], "suffix_code": year[2:]},
                "agency_ic_admin": {"code": core[3:5], "abbreviation": "NIBIB", "name": "Institute"},
            }
        records = [
            record("5R01EB000003-02", 2024, 300, co_pi=True), record("1R01EB000003-01A1", 2023, 310, co_pi=True),
            record("5R01EB000002-03", 2023, 200), record("5R01EB000002-02", 2022, 200),
            record("1R01EB000002-01A1", 2021, 210),
            record("5R01EB000001-02", 2021, 100), record("3R01EB000001-01S1", 2020, 50),
            record("1R01EB000001-01", 2020, 100),
        ]
        sent = []

        def opener(req, timeout=None):
            sent.append(json.loads(req.data))
            return FakeResponse(json.dumps({"meta": {"total": len(records)}, "results": records}))
        rc, out = run_main(NIH, NIH_ARGV, opener)
        self.assertEqual((rc, out["status"]), (NIH.EXIT_OK, "ok"))
        for name in ("CoreProjectNum", "PrincipalInvestigators", "Organization", "ProjectNumSplit"):
            self.assertIn(name, sent[0]["include_fields"])
        self.assertEqual(out["summary"]["unique_grants"], 3)
        self.assertEqual(out["summary"]["total_funding"], 1470)
        by_core = {g["core_project_number"]: g for g in out["grants"]}
        self.assertEqual({k: g["total_award_amount"] for k, g in by_core.items()},
                         {"R01EB000003": 610, "R01EB000002": 610, "R01EB000001": 250})
        self.assertEqual(len(by_core["R01EB000001"]["project_numbers"]), 3)   # the supplement stays in
        for grant in out["grants"]:
            self.assertEqual(grant["organization"]["name"], "EXAMPLE UNIVERSITY")
            self.assertEqual(grant["organization"]["department"], "RADIOLOGY")
            self.assertEqual(grant["contact_pi"], "DOE, JANE Q")
            self.assertEqual(grant["funding_institute"], "NIBIB")
        self.assertEqual([p["name"] for p in by_core["R01EB000003"]["principal_investigators"]],
                         ["Jane Q Doe", "Sam Roe"])

        # Without core_project_num the key is activity + IC + serial; a partial key never merges.
        for r in records:
            del r["core_project_num"]
        rc, out = run_main(NIH, NIH_ARGV, opener)
        self.assertEqual(sorted(g["core_project_number"] for g in out["grants"]),
                         ["R01EB000001", "R01EB000002", "R01EB000003"])
        for r in records:
            r["project_num_split"]["ic_code"] = ""
            r["agency_ic_admin"] = None
        rc, out = run_main(NIH, NIH_ARGV, opener)
        self.assertEqual(out["summary"]["unique_grants"], len(records))


class PubMedTests(unittest.TestCase):
    def test_outage_is_failed_not_empty_success(self):
        def opener(req, timeout=None):
            raise urllib.error.URLError("dns failure")
        rc, out = run_main(PUBMED, PUBMED_ARGV, opener)
        self.assertEqual((rc, out["status"]), (PUBMED.EXIT_PARTIAL, "failed"))
        self.assertEqual(out["publications"], [])

    def test_esearch_error_field_is_failed(self):
        rc, out = run_main(PUBMED, PUBMED_ARGV, lambda req, timeout=None: FakeResponse(
            json.dumps({"esearchresult": {"ERROR": "Invalid query"}})))
        self.assertEqual((rc, out["status"]), (PUBMED.EXIT_PARTIAL, "failed"))
        self.assertIn("Invalid query", out["errors"][0]["message"])

    def test_failed_detail_batch_is_recorded_with_its_pmids(self):
        rc, out = run_main(PUBMED, PUBMED_ARGV, pubmed_opener(["111", "222"], efetch_fails=True))
        self.assertEqual((rc, out["status"]), (PUBMED.EXIT_PARTIAL, "failed"))
        self.assertEqual(out["errors"][0]["pmids"], ["111", "222"])

    def test_retrieval_cap_is_partial(self):
        rc, out = run_main(PUBMED, PUBMED_ARGV, pubmed_opener(["111"], count=50))
        self.assertEqual((rc, out["status"]), (PUBMED.EXIT_PARTIAL, "partial"))
        self.assertEqual(out["matches_available"], 50)

    def test_legitimate_zero_results_is_ok(self):
        rc, out = run_main(PUBMED, PUBMED_ARGV, pubmed_opener([]))
        self.assertEqual((rc, out["status"], out["publications"]), (PUBMED.EXIT_OK, "ok", []))

    def test_success_is_ok(self):
        rc, out = run_main(PUBMED, PUBMED_ARGV, pubmed_opener(["111", "222"]))
        self.assertEqual((rc, out["status"], out["total_results"]), (PUBMED.EXIT_OK, "ok", 2))

    def test_doi_and_pmc_are_the_articles_own_not_a_cited_papers(self):
        """The reference list carries ArticleIdLists too; a search over all of them returned
        a cited paper's DOI for a 2026 Nature article."""
        def xml(elocation):
            return f"""<PubmedArticleSet><PubmedArticle>
  <MedlineCitation><PMID>42875489</PMID><Article>
    <ArticleTitle>An article</ArticleTitle>{elocation}
  </Article></MedlineCitation>
  <PubmedData>
    <ArticleIdList><ArticleId IdType="pubmed">42875489</ArticleId>
      <ArticleId IdType="doi">10.1038/s41586-026-00001-x</ArticleId>
      <ArticleId IdType="pmc">PMC1000001</ArticleId></ArticleIdList>
    <ReferenceList><Reference><Citation>A cited paper</Citation>
      <ArticleIdList><ArticleId IdType="doi">10.1093/bioinformatics/bty388</ArticleId>
        <ArticleId IdType="pmc">PMC6000002</ArticleId></ArticleIdList></Reference></ReferenceList>
  </PubmedData></PubmedArticle></PubmedArticleSet>"""
        own = '<ELocationID EIdType="doi" ValidYN="Y">10.1038/s41586-026-00001-x</ELocationID>'
        for elocation in (own, ""):            # from ELocationID, and from PubmedData alone
            [rec] = PUBMED.parse_pubmed_xml(xml(elocation))
            self.assertEqual((rec["doi"], rec["pmc_id"]), ("10.1038/s41586-026-00001-x", "PMC1000001"))


if __name__ == "__main__":
    unittest.main()
