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


if __name__ == "__main__":
    unittest.main()
