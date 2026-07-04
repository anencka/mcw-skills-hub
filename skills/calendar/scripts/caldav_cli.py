#!/usr/bin/env python3
"""Minimal CalDAV calendar CLI for the Hermes agent.

Run with the bundled-scripts venv: /opt/mcwagent/.venv/bin/python3 (has `caldav` + `icalendar`).
Credentials are read from $HERMES_HOME/.env (default /opt/data/.env):
    CALDAV_URL, CALDAV_USERNAME, CALDAV_PASSWORD

Subcommands:
    test                       connect and list calendars
    agenda [--days N] [--calendar NAME]   upcoming events (default 7 days)
    freebusy [--days N]        busy time blocks in the window
    create --summary --start --end [--desc] [--calendar NAME]
                               create an event (ISO datetimes, e.g. 2026-06-12T14:00)

Creating an event is an outbound change — the agent must get explicit approval first.
"""
import argparse
import datetime as dt
import os
import sys
import uuid

try:
    import caldav
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
    return caldav.DAVClient(url=url, username=user, password=pw)


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


def cmd_create(env, args):
    start = dt.datetime.fromisoformat(args.start)
    end = dt.datetime.fromisoformat(args.end)
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
        {"test": cmd_test, "agenda": cmd_agenda, "freebusy": cmd_freebusy, "create": cmd_create}[args.cmd](env, args)
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
