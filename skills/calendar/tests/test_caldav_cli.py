"""Unit tests for the calendar CLI's agent-facing partial-failure reporting (no CalDAV
server, no caldav library). events-json keeps its webapp contract and is pinned too.

    python3 -m unittest discover -s <skill>/tests
"""

import argparse
import contextlib
import datetime as dt
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "caldav_cli.py"
SPEC = importlib.util.spec_from_file_location("caldav_cli", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Field:
    def __init__(self, value):
        self.dt = value


class FakeEvent:
    def __init__(self, summary, start):
        self.icalendar_component = {
            "summary": summary,
            "dtstart": Field(start),
            "dtend": Field(start + dt.timedelta(hours=1)),
            "uid": summary,
        }


class FakeCalendar:
    def __init__(self, name, events=(), error=None):
        self.name, self._events, self._error = name, list(events), error

    def search(self, **_):
        if self._error:
            raise self._error
        return self._events


def run(cmd, calendars, **kw):
    args = argparse.Namespace(days=7, calendar=None, **kw)
    out = io.StringIO()
    with mock.patch.object(MODULE, "_calendars", return_value=calendars), \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        rc = cmd({}, args)
    return rc, out.getvalue()


SOON = dt.datetime.now() + dt.timedelta(days=1)


class AgendaTests(unittest.TestCase):
    def test_all_calendars_ok_is_exit_zero_without_banner(self):
        rc, out = run(MODULE.cmd_agenda, [FakeCalendar("Work", [FakeEvent("Lab meeting", SOON)])])
        self.assertEqual(rc, MODULE.EXIT_OK)
        self.assertNotIn("INCOMPLETE", out)
        self.assertIn("Lab meeting", out)

    def test_one_failed_calendar_is_partial_and_named_first(self):
        rc, out = run(MODULE.cmd_agenda, [
            FakeCalendar("Work", [FakeEvent("Lab meeting", SOON)]),
            FakeCalendar("Clinic", error=TimeoutError("read timed out")),
        ])
        self.assertEqual(rc, MODULE.EXIT_PARTIAL)
        first = out.splitlines()[0]
        self.assertTrue(first.startswith("INCOMPLETE: 1 calendar(s)"), first)
        self.assertIn("'Clinic'", first)
        self.assertIn("TimeoutError", first)
        self.assertIn("Lab meeting", out)

    def test_every_calendar_failed_never_reads_as_an_empty_agenda(self):
        rc, out = run(MODULE.cmd_agenda, [FakeCalendar("Work", error=ConnectionError("refused"))])
        self.assertEqual(rc, MODULE.EXIT_PARTIAL)
        self.assertIn("INCOMPLETE", out)
        self.assertIn("from the calendars that could be read", out)

    def test_freebusy_reports_partial_the_same_way(self):
        rc, out = run(MODULE.cmd_freebusy, [
            FakeCalendar("Work", [FakeEvent("x", SOON)]),
            FakeCalendar("Clinic", error=TimeoutError("t")),
        ])
        self.assertEqual(rc, MODULE.EXIT_PARTIAL)
        self.assertTrue(out.startswith("INCOMPLETE"))
        self.assertIn("Busy:", out)


class ContractTests(unittest.TestCase):
    def test_events_json_keeps_webapp_contract_on_partial_failure(self):
        # Bare JSON list on stdout and no nonzero return: the webapp discards everything on rc != 0.
        args = argparse.Namespace(start=SOON.date().isoformat(),
                                  end=(SOON + dt.timedelta(days=2)).date().isoformat(), calendar=None)
        out = io.StringIO()
        with mock.patch.object(MODULE, "_calendars", return_value=[
                FakeCalendar("Work", [FakeEvent("Lab meeting", SOON)]),
                FakeCalendar("Clinic", error=TimeoutError("t"))]), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            rc = MODULE.cmd_events_json({}, args)
        self.assertIn(rc, (None, 0))
        events = json.loads(out.getvalue())
        self.assertIsInstance(events, list)
        self.assertEqual([e["summary"] for e in events], ["Lab meeting"])

    def test_missing_config_is_exit_two(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
            MODULE.client({})
        self.assertEqual(cm.exception.code, MODULE.EXIT_USAGE)


if __name__ == "__main__":
    unittest.main()
