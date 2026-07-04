# MCW Skills Hub

The institution's shared library of agent skills. Anyone's agent can **browse** this
catalog, **install** a skill with one click (or one command), and **modify** their local
copy freely — installs are copies, never links. Improvements flow back as pull requests.

This directory is designed to be published as its own repository (e.g.
`mcw/skills-hub` on the institution's GitHub/Forgejo). Until then it lives inside the
main project repo and works the same way.

## Layout (tap-compatible)

```
skills-hub/
├── README.md
├── catalog.json          # generated — do not edit by hand (tools/hub.py catalog)
├── tools/hub.py          # sync + catalog generator
└── skills/
    └── <skill-name>/     # FLAT — one dir per skill, category lives in frontmatter
        ├── SKILL.md      # required; YAML frontmatter (name, description, metadata.hermes.*)
        └── references/ scripts/ templates/   # optional
```

The flat `skills/<name>/` layout matches the Hermes Agent **tap** convention, so once
published the whole hub can be registered on any instance:

```bash
hermes skills tap add <owner>/<repo>     # browse/search/install everything in the hub
hermes skills install <owner>/<repo>/skills/<name>   # or install one directly
```

Single-file skills also install from a raw URL: `hermes skills install https://…/SKILL.md`.
Every install goes through the agent's quarantine + security scan before it is enabled.

## Where skills come from

- **Baseline skills** are maintained in `../deploy/hermes-skills/<category>/<name>/`
  (the source of truth — they ship baked into the container image) and are mirrored here
  by `tools/hub.py sync` so the hub catalog shows everything available.
- **Community skills** live only here, under `skills/`, added by pull request.

## Contributing a skill

1. Copy an existing skill as a starting point, or scaffold one from the Skills tab
   ("New skill") and refine it with your agent.
2. Frontmatter must have `name` (lowercase/digits/hyphens, ≤64 chars, matching the
   directory name) and a trigger-phrased `description` (≤1024 chars). Put tags/category/
   related_skills under `metadata.hermes`. A skill that should run on a schedule can
   declare `metadata.hermes.blueprint: {schedule, prompt}` — it then appears as a
   one-click suggestion in the Automations tab.
3. House rules: write for the *operator*; read `~/work-profile/*` fresh, never cache it;
   spell out exact commands/API calls so an open-weight model doesn't guess; **no
   fabrication** — citations, deadlines, and records come from a source or the operator.
4. Run `python3 tools/hub.py catalog` and include the regenerated `catalog.json`.
5. Open a pull request. A maintainer review marks the skill `curated: true` in its
   frontmatter (`metadata.hermes.curated`) before merge — the catalog badge users see.

## Regenerating

```bash
python3 tools/hub.py sync      # mirror baseline skills from ../deploy/hermes-skills
python3 tools/hub.py catalog   # rebuild catalog.json from skills/
```

`catalog.json` is what the web dashboard's "Browse catalog" reads (via
`SKILLS_HUB_CATALOG_URL` or `SKILLS_HUB_CATALOG_FILE`), with `SKILLS_HUB_REPO` naming
the published `owner/repo` so the UI can build install identifiers.
