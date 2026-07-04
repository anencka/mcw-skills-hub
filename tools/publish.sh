#!/usr/bin/env bash
# Publish the skills hub to its public GitHub repo.
#
#   tools/publish.sh [owner/repo]     # default: anencka/mcw-skills-hub
#
# The hub's working copy lives in the main project repo (this directory); the public repo
# is a publish target, refreshed wholesale on every run. Safe to re-run (idempotent).
#
# PUBLIC REPO RULE: only benign skills — no institutional branding, licensed templates, or
# protected material. Enforced by tools/hub.py (EXCLUDE_SKILLS / metadata.hermes.internal);
# this script re-runs sync + catalog first so an out-of-date working copy can't leak.
set -euo pipefail

REPO="${1:-anencka/mcw-skills-hub}"
HUB="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-python3}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

cd "$HUB"
"$PY" tools/hub.py sync
"$PY" tools/hub.py catalog

# Belt-and-braces: refuse to publish if protected content slipped through anyway.
if [ -d skills/brand-guidelines ] || grep -rqiE 'asn-lab|nencka' skills 2>/dev/null; then
    echo "ABORT: protected/personal content detected in skills/ — fix before publishing." >&2
    exit 1
fi

if git ls-remote "git@github.com:$REPO.git" >/dev/null 2>&1; then
    git clone --depth 1 "git@github.com:$REPO.git" "$WORK/repo"
elif command -v gh >/dev/null 2>&1; then
    echo "Creating public repo $REPO"
    gh repo create "$REPO" --public \
        --description "Shared agent skills library for academic knowledge work (SKILL.md format — Hermes Agent / Claude Code compatible)"
    git clone "git@github.com:$REPO.git" "$WORK/repo"
else
    echo "ABORT: repo $REPO does not exist and gh is not installed — create it on GitHub first." >&2
    exit 1
fi

rsync -a --delete --exclude '.git' "$HUB/" "$WORK/repo/"
cd "$WORK/repo"
git add -A
if git diff --cached --quiet; then
    echo "Public hub already up to date."
    exit 0
fi
git commit -m "Publish skills hub ($(git -C "$HUB" rev-parse --short HEAD 2>/dev/null || echo local))"
git push origin HEAD
echo "Published to https://github.com/$REPO"
