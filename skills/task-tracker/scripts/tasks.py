#!/usr/bin/env python3
"""Task/deadline registry CLI — the ONLY way skills read or write the registry.

Registry: ~/work/tasks/tasks.json (created on first use). All date arithmetic happens
here, in code — never in a model's head. Output is JSON on stdout for easy agent parsing.

  tasks.py add --title T --due YYYY-MM-DD [--lead N] [--project P] [--notes N] [--source S]
  tasks.py list [--all]              # open tasks (or everything) sorted by due date
  tasks.py due [--horizon N]         # buckets: overdue / due_soon (within lead) / upcoming
  tasks.py done ID | reopen ID
  tasks.py edit ID [--title T] [--due D] [--lead N] [--project P] [--notes N]
  tasks.py remove ID
"""

import argparse
import datetime
import json
import os
import re
import sys
import tempfile

REGISTRY = os.path.expanduser(os.environ.get('TASKS_FILE', '~/work/tasks/tasks.json'))
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
DEFAULT_LEAD = 7


def load():
    try:
        with open(REGISTRY, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict) or not isinstance(data.get('tasks'), list):
            sys.exit(f'error: {REGISTRY} is not a valid registry')
        return data
    except FileNotFoundError:
        return {'tasks': [], 'next_id': 1}
    except json.JSONDecodeError as e:
        sys.exit(f'error: {REGISTRY} is corrupt ({e}) — fix or move it aside; refusing to overwrite')


def save(data):
    os.makedirs(os.path.dirname(REGISTRY), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(REGISTRY), suffix='.tmp')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    os.replace(tmp, REGISTRY)


def parse_date(s, label='--due'):
    if not DATE_RE.match(s or ''):
        sys.exit(f'error: {label} must be YYYY-MM-DD')
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        sys.exit(f'error: {label} is not a real date')


def find(data, task_id):
    for t in data['tasks']:
        if t['id'] == task_id:
            return t
    sys.exit(f'error: no task {task_id!r} (use `tasks.py list --all`)')


def out(obj):
    json.dump(obj, sys.stdout, indent=2)
    print()


def cmd_add(a):
    data = load()
    parse_date(a.due)
    task = {
        'id': f't{data.get("next_id", len(data["tasks"]) + 1)}',
        'title': a.title.strip(),
        'due': a.due,
        'lead_days': a.lead,
        'project': (a.project or '').strip(),
        'notes': (a.notes or '').strip(),
        'source': (a.source or 'manual').strip(),
        'status': 'open',
        'created': datetime.date.today().isoformat(),
    }
    if not task['title']:
        sys.exit('error: --title is required')
    dup = [t for t in data['tasks'] if t['status'] == 'open'
           and t['title'].lower() == task['title'].lower() and t['due'] == task['due']]
    if dup:
        sys.exit(f'error: duplicate of open task {dup[0]["id"]} — edit that instead')
    data['tasks'].append(task)
    data['next_id'] = data.get('next_id', len(data['tasks'])) + 1
    save(data)
    out(task)


def cmd_list(a):
    data = load()
    tasks = [t for t in data['tasks'] if a.all or t['status'] == 'open']
    out(sorted(tasks, key=lambda t: (t['due'], t['id'])))


def cmd_due(a):
    today = datetime.date.today()
    buckets = {'today': today.isoformat(), 'overdue': [], 'due_soon': [], 'upcoming': []}
    for t in load()['tasks']:
        if t['status'] != 'open':
            continue
        due = parse_date(t['due'], f'task {t["id"]} due')
        days = (due - today).days
        entry = dict(t, days_until_due=days)
        if days < 0:
            buckets['overdue'].append(entry)
        elif days <= int(t.get('lead_days', DEFAULT_LEAD)):
            buckets['due_soon'].append(entry)
        elif days <= a.horizon:
            buckets['upcoming'].append(entry)
    for k in ('overdue', 'due_soon', 'upcoming'):
        buckets[k].sort(key=lambda t: t['due'])
    out(buckets)


def _set_status(task_id, status):
    data = load()
    task = find(data, task_id)
    task['status'] = status
    task['completed'] = datetime.date.today().isoformat() if status == 'done' else None
    save(data)
    out(task)


def cmd_edit(a):
    data = load()
    task = find(data, a.id)
    if a.title:
        task['title'] = a.title.strip()
    if a.due:
        parse_date(a.due)
        task['due'] = a.due
    if a.lead is not None:
        task['lead_days'] = a.lead
    if a.project is not None:
        task['project'] = a.project.strip()
    if a.notes is not None:
        task['notes'] = a.notes.strip()
    save(data)
    out(task)


def cmd_remove(a):
    data = load()
    task = find(data, a.id)
    data['tasks'] = [t for t in data['tasks'] if t['id'] != a.id]
    save(data)
    out({'removed': task})


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('add')
    p.add_argument('--title', required=True)
    p.add_argument('--due', required=True)
    p.add_argument('--lead', type=int, default=DEFAULT_LEAD,
                   help=f'nag lead time in days (default {DEFAULT_LEAD})')
    p.add_argument('--project')
    p.add_argument('--notes')
    p.add_argument('--source')
    p.set_defaults(fn=cmd_add)

    p = sub.add_parser('list')
    p.add_argument('--all', action='store_true')
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser('due')
    p.add_argument('--horizon', type=int, default=30)
    p.set_defaults(fn=cmd_due)

    for name, status in (('done', 'done'), ('reopen', 'open')):
        p = sub.add_parser(name)
        p.add_argument('id')
        p.set_defaults(fn=lambda a, s=status: _set_status(a.id, s))

    p = sub.add_parser('edit')
    p.add_argument('id')
    p.add_argument('--title')
    p.add_argument('--due')
    p.add_argument('--lead', type=int)
    p.add_argument('--project')
    p.add_argument('--notes')
    p.set_defaults(fn=cmd_edit)

    p = sub.add_parser('remove')
    p.add_argument('id')
    p.set_defaults(fn=cmd_remove)

    args = ap.parse_args()
    args.fn(args)


if __name__ == '__main__':
    main()
