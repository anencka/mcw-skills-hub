"""Unit tests for the bundled funding-digest collector (no network).

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

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "refresh.py"
SPEC = importlib.util.spec_from_file_location("funding_refresh", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

FORBIDDEN_KEYS = {"token", "access_token", "api_key", "password", "secret"}


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def empty_ok_opener(req, timeout):
    url = req.full_url
    if "reporter.nih.gov" in url:
        return FakeResponse({"results": []})
    if "grants.gov" in url:
        return FakeResponse({"errorcode": 0, "data": {"oppHits": []}})
    return FakeResponse({"response": {"award": []}})


def json_keys(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from json_keys(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from json_keys(item)


class RefreshTests(unittest.TestCase):
    def test_parse_keywords_reads_only_target_section(self):
        text = "# Config\n## Search Keywords\n- MRI reconstruction\n- low-field MRI\n## Funders\n- NIH\n"
        self.assertEqual(MODULE.parse_keywords(text), ["MRI reconstruction", "low-field MRI"])
        with self.assertRaises(ValueError):
            MODULE.parse_keywords("## Funders\n- NIH\n")

    def test_grantsgov_normalization_excludes_envelope_token(self):
        payload = {
            "token": "must-not-survive",
            "data": {
                "oppHits": [
                    {
                        "id": "123",
                        "number": "RFA-TEST-1",
                        "title": "Test",
                        "agency": "NIH",
                        "agencyCode": "HHS-NIH11",
                        "openDate": "01/01/2026",
                        "closeDate": "02/01/2026",
                        "oppStatus": "posted",
                    }
                ]
            },
        }
        records = MODULE.normalize_grantsgov(payload)
        self.assertEqual(records[0]["identifier"], "RFA-TEST-1")
        self.assertEqual(records[0]["record_type"], "opportunity")
        self.assertEqual(records[0]["use"], "discovery")
        self.assertEqual(records[0]["close_date"], "02/01/2026")
        self.assertFalse(FORBIDDEN_KEYS & set(json_keys(records)))
        self.assertEqual(records[0]["link"], "https://www.grants.gov/search-results-detail/123")

    def test_grantsgov_api_error_indicator_is_a_failure(self):
        with self.assertRaises(ValueError):
            MODULE.normalize_grantsgov({"errorcode": 1, "msg": "bad request", "data": {"oppHits": []}})

    def test_atomic_writer_creates_parent_and_valid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runs" / "2026-01-01" / "sources.json"
            MODULE.write_json_atomic(path, {"ok": True})
            self.assertEqual(json.loads(path.read_text()), {"ok": True})
            MODULE.write_json_atomic(path, {"ok": 2})  # same-date rewrite is idempotent
            self.assertEqual(json.loads(path.read_text()), {"ok": 2})
            self.assertEqual([p.name for p in path.parent.iterdir()], ["sources.json"])

    def test_missing_result_envelopes_are_errors(self):
        with self.assertRaises(ValueError):
            MODULE.normalize_grantsgov({"errorcode": 0, "data": {}})
        with self.assertRaises(ValueError):
            MODULE.normalize_grantsgov({"errorcode": 0, "oppHits": []})  # top-level, not under data
        with self.assertRaises(ValueError):
            MODULE.normalize_reporter({"meta": {"total": 0}})
        with self.assertRaises(ValueError):
            MODULE.normalize_nsf({"response": {"notification": [{"type": "ERROR"}]}})

    def test_legitimate_zero_results_are_accepted(self):
        self.assertEqual(MODULE.normalize_grantsgov({"errorcode": 0, "data": {"oppHits": []}}), [])
        self.assertEqual(MODULE.normalize_reporter({"results": []}), [])
        self.assertEqual(MODULE.normalize_nsf({"response": {"award": []}}), [])

    def test_award_sources_are_explicitly_labeled_and_linked(self):
        reporter = MODULE.normalize_reporter(
            {"results": [{"project_num": "1R01TEST", "project_title": "Test", "appl_id": 99,
                          "agency_ic_admin": {"name": "NIBIB"}}]}
        )
        nsf = MODULE.normalize_nsf(
            {"response": {"award": [{"id": "123", "title": "Test", "fundsObligatedAmt": "5"}]}}
        )
        for record in reporter + nsf:
            self.assertEqual(record["record_type"], "award")
            self.assertEqual(record["use"], "calibration")
        self.assertEqual(reporter[0]["agency"], "NIBIB")
        self.assertEqual(reporter[0]["link"], "https://reporter.nih.gov/project-details/99")
        self.assertEqual(nsf[0]["award_amount"], "5")
        self.assertEqual(nsf[0]["link"], "https://www.nsf.gov/awardsearch/showAward?AWD_ID=123")

    def test_normalizers_reject_missing_identifiers(self):
        with self.assertRaises(ValueError):
            MODULE.normalize_grantsgov({"data": {"oppHits": [{"id": "1", "number": " "}]}})
        with self.assertRaises(ValueError):
            MODULE.normalize_reporter({"results": [{"project_num": None}]})
        with self.assertRaises(ValueError):
            MODULE.normalize_nsf({"response": {"award": [{"id": ""}]}})

    def test_normalizers_reject_non_object_records(self):
        with self.assertRaises(ValueError):
            MODULE.normalize_grantsgov({"data": {"oppHits": ["not-an-object"]}})
        with self.assertRaises(ValueError):
            MODULE.normalize_reporter({"results": ["not-an-object"]})
        with self.assertRaises(ValueError):
            MODULE.normalize_nsf({"response": {"award": ["not-an-object"]}})

    def test_request_contracts(self):
        seen = {}

        def opener(req, timeout):
            url = req.full_url
            if "reporter.nih.gov" in url:
                seen["reporter"] = json.loads(req.data.decode("utf-8"))
            elif "grants.gov" in url:
                seen["grantsgov"] = json.loads(req.data.decode("utf-8"))
            else:
                seen["nsf"] = url
            return empty_ok_opener(req, timeout)

        MODULE.collect_term("MRI reconstruction", opener=opener)
        advanced = seen["reporter"]["criteria"]["advanced_text_search"]
        self.assertEqual(advanced["search_text"], "MRI reconstruction")
        self.assertEqual(advanced["search_field"], "all")
        self.assertEqual(advanced["operator"], "and")
        self.assertIn("ProjectNum", seen["reporter"]["include_fields"])
        self.assertIn("ApplId", seen["reporter"]["include_fields"])
        self.assertEqual(seen["grantsgov"]["oppStatuses"], "posted")
        self.assertEqual(seen["grantsgov"]["keyword"], "MRI reconstruction")
        self.assertIn("keyword=MRI+reconstruction", seen["nsf"])

    def test_output_path_is_inside_project_root_and_rejects_invalid_dates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = MODULE.run_output_path(root, "2026-01-02")
            self.assertEqual(path, root.resolve() / "runs" / "2026-01-02" / "sources.json")
            with self.assertRaises(ValueError):
                MODULE.run_output_path(root, "../../outside")
            with self.assertRaises(ValueError):
                MODULE.run_output_path(root, "2026-13-40")

    def _project(self, directory):
        root = Path(directory)
        config = root / "config" / "funding-watch.md"
        config.parent.mkdir(parents=True)
        config.write_text("## Search Keywords\n- MRI\n")
        return root

    def test_main_writes_artifact_under_project_root_and_returns_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._project(directory)
            with mock.patch.object(MODULE.request, "urlopen", empty_ok_opener):
                rc = MODULE.main(["--project-root", str(root), "--run-date", "2026-01-02"])
            self.assertEqual(rc, 0)
            artifact = json.loads((root / "runs" / "2026-01-02" / "sources.json").read_text())
            self.assertEqual(artifact["retrieved_on"], "2026-01-02")
            self.assertEqual(set(artifact["terms"][0]["sources"]), {"grantsgov", "reporter", "nsf"})
            self.assertFalse(FORBIDDEN_KEYS & set(json_keys(artifact)))

    def test_main_returns_nonzero_for_source_failure(self):
        def failing_opener(req, timeout):
            raise TimeoutError("simulated")

        with tempfile.TemporaryDirectory() as directory:
            root = self._project(directory)
            with mock.patch.object(MODULE.request, "urlopen", failing_opener):
                rc = MODULE.main(["--project-root", str(root), "--run-date", "2026-01-02"])
            self.assertEqual(rc, 1)
            artifact = json.loads((root / "runs" / "2026-01-02" / "sources.json").read_text())
            sources = artifact["terms"][0]["sources"]
            self.assertTrue(all(s["status"] == "error" for s in sources.values()))
            self.assertEqual(sources["grantsgov"]["error_type"], "TimeoutError")

    def test_main_fails_cleanly_without_config(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SystemExit):
                MODULE.main(["--project-root", directory, "--run-date", "2026-01-02"])



def grants_opener(numbers):
    """Grants.gov returns `numbers` for every term; RePORTER and NSF return empty lists."""
    def opener(req, timeout):
        url = req.full_url
        if "grants.gov" in url:
            hits = [{"id": str(i), "number": n, "title": n} for i, n in enumerate(numbers)]
            return FakeResponse({"errorcode": 0, "data": {"oppHits": hits}})
        return empty_ok_opener(req, timeout)
    return opener


LEGACY_CONFIG = """# Funding Watch Configuration
## Search Keywords
- MRI
- low-field MRI
## Delivery
- recipient: someone@example.org
## Reviewed/Seen (do not re-surface)
<!-- Format: oppNum | date-seen -->

PAR-1 | 2026-07-06
PAR-2 | 2026-07-13
PAR-1 | 2026-08-01
"""


class SeenLogTests(unittest.TestCase):
    def project(self, directory, config):
        root = Path(directory)
        (root / "config").mkdir(parents=True)
        (root / "config" / "funding-watch.md").write_text(config)
        return root

    def refresh(self, root, numbers, date="2026-01-05", argv_prefix=()):
        with mock.patch.object(MODULE.request, "urlopen", grants_opener(numbers)):
            rc = MODULE.main([*argv_prefix, "--project-root", str(root), "--run-date", date])
        return rc, json.loads((root / "runs" / date / "sources.json").read_text())

    def mark(self, root, date="2026-01-05"):
        return MODULE.main(["mark-seen", "--project-root", str(root), "--run-date", date])

    def seen_ids(self, root):
        return [json.loads(line)["identifier"]
                for line in (root / "state" / "seen.jsonl").read_text().splitlines() if line]

    def test_parse_identifier_section_formats(self):
        text = ("## Do Not Surface\n<!-- multi\nline -->\nA-1 | 2026-01-01\n- B-2\n\nC-3\n"
                "## Other\n- not-an-id\n")
        self.assertEqual(MODULE.parse_identifier_section(text),
                         [("A-1", "2026-01-01"), ("B-2", None), ("C-3", None)])

    def test_refresh_computes_new_candidates_against_log_and_overrides(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.project(d, "## Search Keywords\n- MRI\n- low-field MRI\n"
                                   "## Do Not Surface\nPAR-3\n")
            MODULE.append_seen(root, [{"identifier": "PAR-1", "first_seen": "2026-01-01", "run_id": "x"}])
            rc, out = self.refresh(root, ["PAR-1", "PAR-2", "PAR-3", "PAR-2"])
            self.assertEqual(rc, 0)
            self.assertEqual(out["new_candidates"], ["PAR-2"])  # deduplicated across both terms
            flags = {r["identifier"]: r["seen"] for r in out["terms"][0]["sources"]["grantsgov"]["records"]}
            self.assertEqual(flags, {"PAR-1": True, "PAR-2": False, "PAR-3": True})

    def test_explicit_refresh_subcommand_matches_legacy_invocation(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.project(d, "## Search Keywords\n- MRI\n")
            rc, out = self.refresh(root, ["PAR-9"], argv_prefix=("refresh",))
            self.assertEqual((rc, out["new_candidates"]), (0, ["PAR-9"]))

    def test_unmigrated_legacy_list_blocks_refresh_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.project(d, LEGACY_CONFIG)
            with contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit) as cm:
                self.refresh(root, ["PAR-9"])
            self.assertEqual(cm.exception.code, 2)
            self.assertIn("migrate", err.getvalue())
            self.assertFalse((root / "runs").exists())

    def test_migrate_moves_legacy_entries_once_and_keeps_other_sections(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.project(d, LEGACY_CONFIG)
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(MODULE.main(["migrate", "--project-root", str(root)]), 0)
            report = json.loads(out.getvalue())
            self.assertEqual((report["migrated"], report["duplicates"]), (2, ["PAR-1"]))
            records = [json.loads(l) for l in (root / "state" / "seen.jsonl").read_text().splitlines()]
            self.assertEqual([(r["identifier"], r["first_seen"]) for r in records],
                             [("PAR-1", "2026-07-06"), ("PAR-2", "2026-07-13")])
            config = (root / "config" / "funding-watch.md").read_text()
            self.assertIn("## Do Not Surface", config)
            self.assertNotIn("Reviewed/Seen", config)
            self.assertNotIn("PAR-1", config)
            self.assertIn("- recipient: someone@example.org", config)
            self.assertEqual(MODULE.parse_keywords(config), ["MRI", "low-field MRI"])
            self.assertEqual(MODULE.parse_identifier_section(config), [])
            # Second run is a no-op.
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(MODULE.main(["migrate", "--project-root", str(root)]), 0)
            self.assertEqual(self.seen_ids(root), ["PAR-1", "PAR-2"])
            # And refresh now runs, treating migrated ids as seen.
            rc, out = self.refresh(root, ["PAR-1", "PAR-7"])
            self.assertEqual((rc, out["new_candidates"]), (0, ["PAR-7"]))

    def test_migrate_without_legacy_creates_empty_log(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.project(d, "## Search Keywords\n- MRI\n")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(MODULE.main(["migrate", "--project-root", str(root)]), 0)
            self.assertEqual((root / "state" / "seen.jsonl").read_text(), "")

    def test_mark_seen_refuses_until_the_run_is_recorded(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.project(d, "## Search Keywords\n- MRI\n")
            self.refresh(root, ["PAR-1", "PAR-2"])
            with contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit) as cm:
                self.mark(root)
            self.assertEqual(cm.exception.code, 2)
            self.assertIn("digest.txt", err.getvalue())
            self.assertFalse((root / "state" / "seen.jsonl").exists())

    def test_mark_seen_appends_new_ids_once(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.project(d, "## Search Keywords\n- MRI\n## Do Not Surface\nPAR-3\n")
            self.refresh(root, ["PAR-1", "PAR-2", "PAR-3"])
            (root / "runs" / "2026-01-05" / "digest.txt").write_text("digest")
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(self.mark(root), 0)
            self.assertEqual(json.loads(out.getvalue())["appended"], 2)
            self.assertEqual(self.seen_ids(root), ["PAR-1", "PAR-2"])  # override not duplicated into state
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(self.mark(root), 0)
            self.assertEqual(json.loads(out.getvalue())["appended"], 0)
            self.assertEqual(self.seen_ids(root), ["PAR-1", "PAR-2"])

    def test_run_summary_also_satisfies_mark_seen(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.project(d, "## Search Keywords\n- MRI\n")
            self.refresh(root, ["PAR-4"])
            (root / "runs" / "2026-01-05" / "run-summary.md").write_text("nothing substantive")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(self.mark(root), 0)
            self.assertEqual(self.seen_ids(root), ["PAR-4"])


if __name__ == "__main__":
    unittest.main()
