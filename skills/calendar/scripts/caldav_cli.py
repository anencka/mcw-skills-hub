#!/usr/bin/env python3
"""Minimal CalDAV calendar CLI for the Hermes agent.

Run with the bundled-scripts venv: /opt/mcwagent/.venv/bin/python3 (has `caldav` + `icalendar`).
Credentials are read from $HERMES_HOME/.env (default /opt/data/.env):
    CALDAV_URL, CALDAV_USERNAME, CALDAV_PASSWORD

Subcommands:
    test                       connect and list calendars
    agenda [--days N] [--calendar NAME]   upcoming events (default 7 days)
    freebusy [--days N]        busy time blocks in the window
    events-json --start ISO --end ISO [--calendar NAME]
                               events in the window as a JSON array on stdout (machine
                               consumer: the webapp Calendar tab — COMMS_SURFACES_PLAN B1)
    ics-json --start ISO --end ISO
                               same JSON shape from the EXTERNAL_ICS_URL feed in .env
                               (read-only overlay of the user's own calendar — B2/T8)
    create --summary --start --end [--desc] [--calendar NAME]
                               create an event (ISO datetimes, e.g. 2026-06-12T14:00)

Creating an event is an outbound change — the agent must get explicit approval first.
"""
import argparse
import datetime as dt
import os
import sys
import uuid

def _caldav():
    """Lazy import: only the subcommands that actually talk CalDAV need the lib, and the
    outbox policy shim in `create` must work (queue/refuse) even without it — e.g. in the
    committed shim tests, which run with a bare python3."""
    try:
        import caldav
        return caldav
    except ImportError:
        sys.exit("error: caldav library not available — run with /opt/mcwagent/.venv/bin/python3")


KEYS = ("CALDAV_URL", "CALDAV_USERNAME", "CALDAV_PASSWORD")


def load_env():
    """Resolve CalDAV creds, returning (env, sources) so a caller can see where each
    value came from.

    Precedence, highest first:
      1. CALDAV_TEST_* — the explicit "validate before save" channel used by the Settings
         UI to check candidate creds WITHOUT first writing them to .env. Only ever set
         deliberately by that flow.
      2. The .env FILE. It is read AFTER the inherited process env so the file always wins:
         a long-lived parent (app/agent) loads .env once via load_dotenv and hands its
         os.environ down to subprocesses; if .env is later corrected, that stale copy must
         NOT shadow the fixed file. Making the file authoritative is the fix for exactly the
         http://:2079 vs https://:2080 mix-up that motivated this.
      3. Inherited process env (lowest) — only used to seed a key the file doesn't define.
    """
    home = os.environ.get("HERMES_HOME", "/opt/data")
    path = os.path.join(home, ".env")
    env, sources = {}, {}

    # 1. explicit validation channel wins outright when fully supplied
    if all(os.environ.get("CALDAV_TEST_" + k.split("_", 1)[1]) for k in KEYS):
        for k in KEYS:
            env[k] = os.environ["CALDAV_TEST_" + k.split("_", 1)[1]]
            sources[k] = "validation request (CALDAV_TEST_*)"
        return env, sources

    # 3. seed from inherited process env (lowest priority)
    for k in KEYS:
        if os.environ.get(k):
            env[k] = os.environ[k]
            sources[k] = "process env"

    # 2. .env file overwrites — read last so it is authoritative over stale inherited env
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if s and not s.startswith("#") and "=" in s:
                    k, _, v = s.partition("=")
                    k = k.strip()
                    if k in KEYS:
                        env[k] = v.strip()
                        sources[k] = path
    return env, sources


def client(env):
    url, user, pw = env.get("CALDAV_URL"), env.get("CALDAV_USERNAME"), env.get("CALDAV_PASSWORD")
    if not (url and user and pw):
        sys.exit("error: missing config: CALDAV_URL / CALDAV_USERNAME / CALDAV_PASSWORD "
                 "(set them via the Settings tab)")
    return _caldav().DAVClient(url=url, username=user, password=pw)


def _calendars(env, name=None):
    cals = client(env).principal().calendars()
    if name:
        cals = [c for c in cals if (c.name or "").lower() == name.lower()] or cals
    return cals


def _comp_dt(component, field):
    v = component.get(field)
    return v.dt if v is not None else None


def cmd_test(env, _):
    cals = _calendars(env)
    print("ok: connected. calendars: " + ", ".join((c.name or "(unnamed)") for c in cals))


def _gather(env, days, name=None):
    now = dt.datetime.now()
    end = now + dt.timedelta(days=days)
    events = []
    for cal in _calendars(env, name):
        try:
            for ev in cal.search(start=now, end=end, event=True, expand=True):
                c = ev.icalendar_component
                events.append({
                    "calendar": cal.name or "",
                    "summary": str(c.get("summary", "(no title)")),
                    "start": _comp_dt(c, "dtstart"),
                    "end": _comp_dt(c, "dtend"),
                })
        except Exception as e:  # one bad calendar shouldn't kill the agenda
            print(f"# warning: calendar '{cal.name}' search failed: {e}", file=sys.stderr)
    events.sort(key=lambda x: str(x["start"]))
    return events


def cmd_agenda(env, args):
    events = _gather(env, args.days, args.calendar)
    if not events:
        print(f"(no events in the next {args.days} days)")
        return
    for e in events:
        print(f"{e['start']}  →  {e['end']}   {e['summary']}   [{e['calendar']}]")


def cmd_freebusy(env, args):
    events = _gather(env, args.days)
    if not events:
        print(f"(no busy blocks in the next {args.days} days)")
        return
    print("Busy:")
    for e in events:
        print(f"  {e['start']} – {e['end']}")


def cmd_events_json(env, args):
    """Window query for the webapp Calendar tab: JSON on stdout, nothing else (stderr is
    for humans/diagnostics). Values are plain text fields — the caller renders them as
    text, never HTML (G1). Malformed events in a calendar are skipped, not fatal."""
    import json
    start = dt.datetime.fromisoformat(args.start)
    end = dt.datetime.fromisoformat(args.end)
    out = []
    for cal in _calendars(env, args.calendar):
        try:
            found = cal.search(start=start, end=end, event=True, expand=True)
        except Exception as e:
            print(f"# warning: calendar '{cal.name}' search failed: {e}", file=sys.stderr)
            continue
        for ev in found:
            try:
                c = ev.icalendar_component
                s, e_ = _comp_dt(c, "dtstart"), _comp_dt(c, "dtend")
                all_day = s is not None and not isinstance(s, dt.datetime)
                out.append({
                    "calendar": str(cal.name or ""),
                    "summary": str(c.get("summary", "(no title)")),
                    "description": str(c.get("description", "")),
                    "location": str(c.get("location", "")),
                    "start": s.isoformat() if s is not None else "",
                    "end": e_.isoformat() if e_ is not None else "",
                    "all_day": all_day,
                    "uid": str(c.get("uid", "")),
                })
            except Exception as e:
                print(f"# warning: skipping malformed event: {e}", file=sys.stderr)
    out.sort(key=lambda x: x["start"])
    print(json.dumps(out))


def cmd_ics_json(env, args):
    """B2 overlay: fetch the user's external ICS feed (URL-as-capability, e.g. an O365
    'publish calendar' link) and emit the same JSON shape as events-json. Read-only by
    construction — we only ever GET the feed. Recurrences are expanded with
    recurring_ical_events (a caldav dependency, so always present in this venv)."""
    import json
    import urllib.request

    import icalendar
    import recurring_ical_events

    # EXTERNAL_ICS_URL_TEST is the webapp's validate-before-save channel (same pattern as
    # CALDAV_TEST_*); otherwise the .env FILE is authoritative (stale-env rationale above).
    url = os.environ.get("EXTERNAL_ICS_URL_TEST", "")
    if not url:
        home = os.environ.get("HERMES_HOME", "/opt/data")
        path = os.path.join(home, ".env")
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s.startswith("EXTERNAL_ICS_URL="):
                        url = s.partition("=")[2].strip()
    if not url:
        print("[]")
        return
    # Query bounds MUST be timezone-aware: real feeds (O365/Google) carry tz-aware event
    # times, and recurring_ical_events.between() raises TypeError comparing naive-vs-aware.
    # args.start/end are date-only strings -> naive midnight -> stamp UTC.
    start = dt.datetime.fromisoformat(args.start)
    end = dt.datetime.fromisoformat(args.end)
    if start.tzinfo is None:
        start = start.replace(tzinfo=dt.timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=dt.timezone.utc)
    with urllib.request.urlopen(url, timeout=20) as r:
        body = r.read()
    cal = icalendar.Calendar.from_ical(body)
    out = []
    # Expansion itself can raise on a quirky feed; degrade to empty rather than crash the
    # whole command (the webapp then shows an empty overlay, not a 500).
    try:
        occurrences = recurring_ical_events.of(cal).between(start, end)
    except Exception as e:
        print(f"# warning: ICS recurrence expansion failed: {e}", file=sys.stderr)
        occurrences = []
    for c in occurrences:
        try:
            s, e_ = _comp_dt(c, "dtstart"), _comp_dt(c, "dtend")
            all_day = s is not None and not isinstance(s, dt.datetime)
            out.append({
                "calendar": "external",
                "summary": str(c.get("summary", "(no title)")),
                "description": str(c.get("description", "")),
                "location": str(c.get("location", "")),
                "start": s.isoformat() if s is not None else "",
                "end": e_.isoformat() if e_ is not None else "",
                "all_day": all_day,
                "uid": str(c.get("uid", "")),
            })
        except Exception as e:
            print(f"# warning: skipping malformed event: {e}", file=sys.stderr)
    out.sort(key=lambda x: x["start"])
    print(json.dumps(out))


def _outbox(op, *op_args, stdin_text=None):
    """Talk to the outbox core (himalaya-shim contract, COMMS_SURFACES_PLAN.md A1.2/B3).
    Returns the subprocess stdout, or None when the outbox library isn't installed
    (non-container dev) — callers treat None as policy 'autonomous'."""
    import subprocess
    lib = os.environ.get("OUTBOX_LIB", "/usr/local/lib/outbox/outbox_queue.py")
    if not os.path.isfile(lib):
        return None
    r = subprocess.run(["python3", lib, op, *op_args], input=stdin_text,
                       capture_output=True, text=True, timeout=30)
    return (r.stdout or "").strip() if r.returncode == 0 else None


def cmd_create(env, args):
    start = dt.datetime.fromisoformat(args.start)
    end = dt.datetime.fromisoformat(args.end)
    # Calendar writes are an outbound class: consult the outbox policy unless this IS the
    # approved delivery pass (OUTBOX_DELIVER=1, set by the webapp's Approve action so the
    # approved and autonomous paths share this one code path). v1 behavioral, like email.
    if os.environ.get("OUTBOX_DELIVER") != "1":
        pol = _outbox("policy", "calendar-write") or "autonomous"
        if pol == "never":
            sys.exit("outbox: calendar writes are disabled by policy ('never'). "
                     "Nothing was created.")
        if pol == "queue":
            import json
            send_args = json.dumps({"summary": args.summary, "start": args.start,
                                    "end": args.end, "desc": args.desc or "",
                                    "calendar": args.calendar or ""})
            content = (f"Create event: {args.summary}\n{args.start} – {args.end}"
                       + (f"\n{args.desc}" if args.desc else ""))
            draft = _outbox("queue", "calendar-write",
                            "--origin", os.environ.get("HERMES_TURN_ORIGIN", "agent"),
                            "--subject", args.summary, "--args", send_args,
                            stdin_text=content)
            if not draft:
                # Fail CLOSED: policy said queue; if the queue write failed we must not
                # silently escalate to a direct write.
                sys.exit("outbox: queueing failed and policy is 'queue' — event NOT "
                         "created. Check the outbox volume/permissions.")
            print(f"outbox: draft {draft} queued for operator approval — the event "
                  "will be created once approved in the Outbox tab. Do NOT retry.")
            return
    cals = _calendars(env, args.calendar)
    if not cals:
        sys.exit("error: no calendar found")
    cal = cals[0]
    fmt = "%Y%m%dT%H%M%S"
    ical = (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Hermes//caldav_cli//EN\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uuid.uuid4()}@hermes\r\n"
        f"DTSTAMP:{dt.datetime.utcnow().strftime(fmt)}Z\r\n"
        f"DTSTART:{start.strftime(fmt)}\r\n"
        f"DTEND:{end.strftime(fmt)}\r\n"
        f"SUMMARY:{args.summary}\r\n"
        + (f"DESCRIPTION:{args.desc}\r\n" if args.desc else "")
        + "END:VEVENT\r\nEND:VCALENDAR\r\n"
    )
    cal.save_event(ical)
    print(f"ok: created '{args.summary}' {start} – {end} on calendar '{cal.name}'")


def main():
    p = argparse.ArgumentParser(description="Hermes CalDAV calendar CLI")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("test")
    a = sub.add_parser("agenda"); a.add_argument("--days", type=int, default=7); a.add_argument("--calendar")
    fb = sub.add_parser("freebusy"); fb.add_argument("--days", type=int, default=7)
    ej = sub.add_parser("events-json")
    ej.add_argument("--start", required=True); ej.add_argument("--end", required=True)
    ej.add_argument("--calendar")
    ij = sub.add_parser("ics-json")
    ij.add_argument("--start", required=True); ij.add_argument("--end", required=True)
    cr = sub.add_parser("create")
    cr.add_argument("--summary", required=True); cr.add_argument("--start", required=True)
    cr.add_argument("--end", required=True); cr.add_argument("--desc"); cr.add_argument("--calendar")
    args = p.parse_args()
    env, sources = load_env()
    # Surface where each value resolved from so a stale-env-vs-file mismatch is visible at a glance.
    for k in KEYS:
        if k in sources:
            shown = env[k] if k == "CALDAV_URL" else "(set)"
            print(f"# {k}={shown} from {sources[k]}", file=sys.stderr)
    try:
        {"test": cmd_test, "agenda": cmd_agenda, "freebusy": cmd_freebusy,
         "events-json": cmd_events_json, "ics-json": cmd_ics_json,
         "create": cmd_create}[args.cmd](env, args)
    except Exception as e:
        # caldav auth/connection errors all subclass Exception; SystemExit (missing-config) passes through.
        # Never swallow the URL or the underlying status/reason — a wrong scheme/port (the http://:2079
        # vs https://:2080 case) is only obvious if both are shown.
        name = e.__class__.__name__
        url = env.get("CALDAV_URL", "(unset)")
        detail = str(e).strip() or name
        if "Authoriz" in name or "Forbidden" in name or "Unauthorized" in detail:
            sys.exit(f"error: CalDAV auth failed — {detail} at {url} "
                     "(scheme/port likely wrong; cPanel CalDAV is https://<host>:2080/ — "
                     "otherwise check username / password)")
        sys.exit(f"error: {name}: {detail} (url={url})")


if __name__ == "__main__":
    main()
