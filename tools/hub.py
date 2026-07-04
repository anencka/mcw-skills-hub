#!/usr/bin/env python3
"""MCW Skills Hub maintenance tool.

  python3 tools/hub.py sync      # mirror baseline skills from ../deploy/hermes-skills
                                 # into the hub's flat skills/ layout
  python3 tools/hub.py catalog   # regenerate catalog.json from skills/

Run from the skills-hub directory (or pass --hub). Sync flattens the baseline's
<category>/<name>/ layout to the tap-convention skills/<name>/ (category is preserved in
each skill's frontmatter, and re-derived from the source directory when absent there).
Hub-only (community) skills — anything in skills/ that has no baseline counterpart — are
left untouched by sync.
"""

import argparse
import json
import os
import re
import shutil
import sys

import yaml

VALID_NAME = re.compile(r'^[a-z0-9][a-z0-9._-]{0,63}$')
MAX_DESCRIPTION = 1024

# The hub publishes to a PUBLIC repo — only benign skills belong in it. Skills carrying
# institutional branding, licensed templates, or otherwise protected material stay out:
# list them here OR mark them `metadata.hermes.internal: true` in their frontmatter.
# They remain fully available in-container via the baked-in baseline dir.
EXCLUDE_SKILLS = {
    'brand-guidelines',   # MCW logos + official Office templates — protected assets
}
# Never ship build/backup cruft inside a skill directory.
COPY_IGNORE = shutil.ignore_patterns('__pycache__', '*.pyc', '*.backup', '.DS_Store')


def is_internal(fm):
    hermes = ((fm.get('metadata') or {}).get('hermes')
              if isinstance(fm.get('metadata'), dict) else None) or {}
    return bool(hermes.get('internal', False)) if isinstance(hermes, dict) else False


def read_front_matter(skill_md):
    with open(skill_md, 'r', encoding='utf-8') as f:
        text = f.read()
    if not text.startswith('---'):
        raise ValueError('frontmatter must start at byte 0')
    end = text.find('\n---', 3)
    if end == -1:
        raise ValueError('unterminated frontmatter')
    fm = yaml.safe_load(text[3:end])
    if not isinstance(fm, dict):
        raise ValueError('frontmatter is not a mapping')
    if not text[end + 4:].strip():
        raise ValueError('empty skill body')
    return fm


def iter_skill_dirs(root):
    """Yield (dirpath, depth-relative-path) for every directory holding a SKILL.md."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        if 'SKILL.md' in filenames:
            dirnames[:] = []          # skill dirs are leaves (references/ etc. inside)
            yield dirpath


def validate(fm, dir_name, where):
    name = str(fm.get('name') or '')
    desc = str(fm.get('description') or '')
    errors = []
    if not VALID_NAME.match(name):
        errors.append(f'invalid name {name!r}')
    if name != dir_name:
        errors.append(f'name {name!r} != directory {dir_name!r}')
    if not desc or len(desc) > MAX_DESCRIPTION:
        errors.append('missing/overlong description')
    if errors:
        raise ValueError(f'{where}: ' + '; '.join(errors))


def cmd_sync(hub, baseline):
    if not os.path.isdir(baseline):
        sys.exit(f'baseline dir not found: {baseline}')
    dest_root = os.path.join(hub, 'skills')
    os.makedirs(dest_root, exist_ok=True)
    synced = 0
    skipped = 0
    for src in iter_skill_dirs(baseline):
        dir_name = os.path.basename(src)
        fm = read_front_matter(os.path.join(src, 'SKILL.md'))
        validate(fm, dir_name, src)
        dest = os.path.join(dest_root, dir_name)
        if dir_name in EXCLUDE_SKILLS or is_internal(fm):
            if os.path.isdir(dest):
                shutil.rmtree(dest)   # enforce exclusion on re-sync, not just first sync
            skipped += 1
            print(f'  SKIPPED {dir_name} (internal/protected — not for the public hub)')
            continue
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        shutil.copytree(src, dest, ignore=COPY_IGNORE)
        synced += 1
        print(f'  synced {dir_name}')
    print(f'sync: {synced} skill(s) mirrored into {dest_root}, {skipped} excluded')


def cmd_catalog(hub):
    skills_root = os.path.join(hub, 'skills')
    entries = []
    for skill_dir in sorted(iter_skill_dirs(skills_root)):
        dir_name = os.path.basename(skill_dir)
        where = os.path.relpath(skill_dir, hub)
        fm = read_front_matter(os.path.join(skill_dir, 'SKILL.md'))
        validate(fm, dir_name, where)
        if dir_name in EXCLUDE_SKILLS or is_internal(fm):
            print(f'  catalog: skipping internal/protected skill {dir_name}')
            continue
        hermes = ((fm.get('metadata') or {}).get('hermes')
                  if isinstance(fm.get('metadata'), dict) else None) or {}
        entries.append({
            'name': str(fm['name']),
            'description': str(fm['description']),
            'version': str(fm.get('version') or ''),
            'category': str(hermes.get('category') or ''),
            'tags': [str(t) for t in (hermes.get('tags') or []) if str(t)][:12],
            'curated': bool(hermes.get('curated', False)),
            'has_blueprint': isinstance(hermes.get('blueprint'), dict),
            'path': f'skills/{dir_name}',
        })
    catalog = {'schema': 1, 'count': len(entries), 'entries': entries}
    out = os.path.join(hub, 'catalog.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2)
        f.write('\n')
    print(f'catalog: wrote {len(entries)} entrie(s) to {out}')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['sync', 'catalog'])
    ap.add_argument('--hub', default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument('--baseline', default=None,
                    help='baseline skills dir (default: <hub>/../deploy/hermes-skills)')
    args = ap.parse_args()
    baseline = args.baseline or os.path.join(os.path.dirname(args.hub), 'deploy', 'hermes-skills')
    if args.command == 'sync':
        cmd_sync(args.hub, baseline)
    else:
        cmd_catalog(args.hub)


if __name__ == '__main__':
    main()
