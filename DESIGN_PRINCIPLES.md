# Skill Design Principles

How to build a skill that behaves the same way every time it runs, leaves an auditable record,
and fails loudly instead of quietly. These principles apply to every skill in the hub, new or
revised. They exist because an agent following prose instructions improvises, and improvisation is
where reliability goes to die: guessed API fields, files written wherever seemed convenient, state
edited by hand, and "verified" meaning "I looked and it seemed fine."

The reference implementation is `grants/funding-opportunity-digest` 2.0.0 (bundled collector,
fail-closed validation, canonical run directory, tests). Where it does not yet meet a principle
below, that is called out as an open gap rather than papered over.

Principles are numbered so reviews and pull requests can cite them (`P5`, `P9`).

---

## Part 1 — Division of labor

### P1. Code for determinism, prose for judgment
**Rule.** Any step whose correct result is fully determined by its inputs belongs in a bundled,
tested script. Prose instructions are reserved for steps that need judgment.

| Belongs in a script | Belongs in prose |
|---|---|
| API calls and response parsing | Ranking by fit, relevance, or priority |
| File creation, placement, and naming | Writing and rewriting in the operator's voice |
| Deduplication and state updates | Critique, review, and scoring against a rubric |
| Date and time arithmetic, counting, scoring formulas | Deciding what to ask the operator |
| Format conversion, validation, schema checks | Explaining trade-offs and uncertainty |

**Why.** The old digest told the agent to run `curl` and read "`oppNum`" from the response. The
real field is `number`, nested under `data.oppHits`. Nothing noticed, because nothing checked.
A script with a tested normalizer would have failed the first time it ran.

**How.** If a SKILL.md contains a `curl` line, a hand-written file path pattern, or "compute X",
that step is a candidate for the skill's script. Readability scores, deadline arithmetic, and
dedup are all deterministic even though they feel like part of a writing or planning task.

### P2. One CLI per skill, with a stable interface
**Rule.** A scripted skill exposes one command-line entry point with subcommands, and the SKILL.md
tells the agent to call that entry point and nothing else for deterministic work.

**How.**
- Subcommands name the operation: `refresh`, `add`, `due`, `verify`, `migrate`.
- Output is one JSON object on stdout. Human-readable progress goes to stderr.
- Exit codes are fixed across the library:

  | Code | Meaning |
  |---|---|
  | `0` | Success, every step succeeded |
  | `1` | Partial: the run completed but at least one source or step failed and is recorded |
  | `2` | Usage or configuration error: nothing was done |

- Common flags: `--project-root` (defaulting to the skill's designated root, P5) and `--run-id`
  (defaulting per P7). No interactive prompts, ever. Scheduled runs have no one to answer.
- Stdlib only, unless the dependency is baked into the image's venv and the SKILL.md says which
  interpreter to use.
- Invoke with `PYTHONDONTWRITEBYTECODE=1` so bytecode never lands in a skill or project directory.

**Anti-pattern.** Several skills document raw `curl` calls for the agent to assemble at runtime.
Each run is a fresh improvisation of the request, the parse, and the error handling.

### P3. The code is the contract; the SKILL.md describes it
**Rule.** Request payloads, response shapes, and file formats are defined once, in code, and
pinned by tests. The SKILL.md explains what the script does and what its output means. It never
re-specifies a request the agent should construct by hand.

**How.** Put each source's request contract in a function the tests can call (the digest's
`source_calls()`), and assert the payload fields in a test. When the SKILL.md mentions a field
name, it is describing code that already uses that name.

---

## Part 2 — Where things live

### P4. Every file has a designated location
**Rule.** A skill declares exactly where it reads and writes, and writes nowhere else. The script
enforces this; the prose only reminds.

**How — two kinds of root:**
- **Skill-owned root** for skills that keep state or run on a schedule: a fixed directory
  `~/work/<skill-area>/`, for example `~/work/funding-digest/`, `~/work/lit-alerts/`,
  `~/work/tasks/`. One skill owns it.
- **Project deliverable root** for request-driven work: `~/work/<project>/<skill-output>/<slug>/`,
  for example `~/work/<project>/investigator-profiles/<name_slug>/`. Ask which project, or
  propose one. Never write loose into `~/work/`.

**Enforcement.** Scripts resolve every output path under the root and refuse anything that
escapes it, including via `..` or symlinks (`skillkit.contained()`, P15). System paths
(`/opt/...`) are read-only; a skill never edits the application, the runtime, or another skill.

**Anti-pattern.** The old digest kept its watch file loose at `~/work/funding-watch.md`, and a
later run scattered scripts and reports across `~/work/` until a manual cleanup.

### P5. Standard layout inside a skill-owned root
```
~/work/<skill-area>/
├── config/        # operator-editable inputs: queries, preferences, delivery settings
├── state/         # machine-owned state: seen lists, registries, cursors — scripts only
├── runs/
│   └── <run-id>/  # one directory per run: manifest, evidence, deliverable (P7)
└── README.md      # what this directory is, generated or maintained by the skill
```
- **`config/`** is for the operator. Markdown with fixed `##` headings, or YAML. Scripts may read
  it and must tolerate the operator's edits. The agent edits it only with the operator's consent.
- **`state/`** is for the machine. JSON or JSONL, written only by the skill's script, never by
  hand and never by the agent's own file edits (the task-tracker rule: "never edit tasks.json by
  hand").
- **`runs/`** accumulates. Old runs are evidence; they are not rewritten.

**Anti-pattern.** Mixing operator config and machine state in one hand-edited markdown file. An
agent appending identifiers to a file the operator also edits invites merge damage and parse
drift. (Open gap in the reference implementation: the digest's seen list still lives in
`config/funding-watch.md`.)

### P6. State changes are atomic, idempotent, and append-preferring
**Rule.** Every write to state is atomic (write a temp file in the same directory, then rename),
safe to repeat, and preserves history.

**How.**
- Re-running the same logical run produces the same state, not duplicates. Compute
  `new = current − historical` before appending.
- Prefer append-only logs (`state/seen.jsonl` with one record per identifier and the run that
  first saw it) over rewriting a list.
- Report pre-existing inconsistencies as data-quality notes. Do not silently rewrite history
  during a routine run.
- Order state commits after the artifact that justifies them exists. Mark an item "seen" only
  after the run's deliverable recording it has been written, so a crashed run can be re-run
  without losing items.
- One owner per state file. Other skills read it through the owner's CLI (the deadline-sentinel
  reads tasks through `tasks.py due`, never by parsing `tasks.json`).

---

## Part 3 — Reliability

### P7. Every scripted run leaves a manifest
**Rule.** Any run that executes a skill script writes `runs/<run-id>/run.json` describing what
happened. Pure-judgment skills without scripts record their sources and scope inside the
deliverable instead (P12).

**Run id.** Scheduled skills use the local date (`2026-09-28`) so a same-day re-run replaces its
own run idempotently. On-demand skills that can run several times a day use a local timestamp
(`2026-09-28T101500`).

**Schema (`skill-run/1`).**
```json
{
  "schema": "skill-run/1",
  "skill": "funding-opportunity-digest",
  "skill_version": "2.0.0",
  "run_id": "2026-09-28",
  "started_at": "2026-09-28T06:00:04-05:00",
  "finished_at": "2026-09-28T06:02:51-05:00",
  "trigger": "cron | operator",
  "argv": ["refresh", "--project-root", "."],
  "status": "ok | partial | failed",
  "inputs":  [{"path": "config/funding-watch.md", "sha256": "…"}],
  "outputs": [{"path": "runs/2026-09-28/sources.json", "sha256": "…", "kind": "evidence"},
              {"path": "runs/2026-09-28/digest.txt",  "sha256": "…", "kind": "deliverable"}],
  "steps":   [{"name": "grantsgov:MRI reconstruction", "status": "ok", "records": 25},
              {"name": "nsf:MRI reconstruction", "status": "error",
               "error_type": "TimeoutError", "message": "timed out after 90s"}],
  "side_effects": [{"kind": "email", "mode": "queued-for-approval", "to_tier": "external"}],
  "notes": []
}
```
- Paths are relative to the skill root. Timestamps carry the local offset.
- `status` is computed, never asserted: `failed` if nothing usable was produced, `partial` if any
  step failed, `ok` otherwise. It matches the exit code (P2).
- The agent's judgment steps (ranking, writing the digest) append their outputs and side effects
  to the manifest through the CLI, for example `cli record-output` and `cli record-effect`, so
  the manifest covers the whole run and not only the scripted half.

### P8. Fail closed, disclose partial coverage
**Rule.** Malformed input is an error, not an empty result. Failure of one source does not abort
the others, and does not go unreported.

**How.**
- Assert the documented envelope before reading records: the record key exists and holds a list,
  even an empty one. A missing key, wrong type, API error indicator, non-object record, or blank
  identifier marks that source as failed.
- Record per-source status in the evidence artifact and the manifest; continue with the rest;
  exit `1`.
- The deliverable states coverage plainly: which sources and terms ran, which failed, with the
  actual error text.
- Never fill a gap with remembered or plausible data. "The NSF source timed out" is a correct
  deliverable. An invented NSF award is not.
- Network calls always carry a timeout. A retry, if any, happens once, inside the script.

### P9. Time is local, explicit, and computed
**Rule.** Dates come from the container's configured timezone, are written as ISO 8601, and all
arithmetic happens in code.

**How.** Scripts use `datetime.now().astimezone()` rather than a hard-coded zone. Skills never
tell the model to work out "days until" or "next Friday" in its head; they call the script, or
resolve the date out loud and confirm it with the operator. Keep the source's own date string
verbatim for display, and normalize separately for comparison.

---

## Part 4 — Verification and provenance

### P10. Controlled verification: tests, then a verify command
**Rule.** A skill proves its work mechanically before the agent claims success.

**Two layers.**
1. **Unit tests** in `tests/test_*.py`, stdlib `unittest`, no network. Inject the opener or
   client so tests never reach a live API. They run in the library gate
   (`deploy/tests/skill-scripts-test.sh`) on every base bump. Minimum coverage for a scripted
   skill:
   - request contract for each external source (P3);
   - missing, malformed, and legitimately empty envelopes (P8);
   - missing identifiers and non-object records;
   - path containment and rejection of escaping paths (P4);
   - idempotent re-run of the same run id (P6);
   - exit codes for success, partial failure, and bad configuration (P2);
   - the `verify` subcommand passing on a good run and failing on a bad one.
2. **A `verify` subcommand** the agent runs at the end of every stateful or scheduled run:
   `cli verify --run-id <id>`. It checks, and exits nonzero on any failure:
   - the manifest exists, parses, and its status matches the step results;
   - every listed output exists inside the root and matches its recorded hash;
   - no retained JSON contains a forbidden key (P13);
   - skill-specific invariants, for example every candidate named in the digest appears in
     `sources.json`, or every state append is unique.

**The agent's final response** quotes the verify result and names the exact artifact paths.
A check the agent improvised outside the skill's tooling is labeled "ad-hoc verification", never
"tests passed".

**Prose checklists remain** for judgment the machine cannot check: tone, argument quality,
whether a critique is fair. They are not a substitute for layer 2 wherever layer 2 is possible.

**Anti-pattern.** "Verification: the file exists and looks right" as the only check. It is
unfalsifiable and the model always reports that it passed.

### P11. A subagent's or tool's summary is a claim, not proof
**Rule.** Before reporting that something happened, check the artifact, not the message
that says it happened. (From `delegate-to-specialist`: read the reply, then verify the
deliverable exists at the output path.) This applies equally to a script's stdout, a specialist's
reply, and the agent's own earlier turn.

### P12. Every claim traces to a record
**Rule.** Each factual line in a deliverable can be traced to a specific record in the run's
evidence, by identifier.

**How.**
- Keep a normalized evidence artifact (`sources.json` or equivalent) for every run that
  consumes external data. The deliverable cites identifiers from it: opportunity numbers, PMIDs,
  DOIs, award numbers, transcript anchor phrases.
- Label the role of each record in the artifact itself, not only in prose: the digest's
  `use: discovery` versus `use: calibration`.
- Use the library's grading vocabulary consistently: `CONFIRMED`, `PLAUSIBLE`, `NOT ASSESSED`
  (with the reason), and for citations `SUPPORTS`, `PARTIAL`, `DOES NOT SUPPORT`, `NOT FOUND`.
- State coverage: "checked 34 of 41 citations", "6 terms × 3 sources, 1 failed". A partial pass
  says so. A passed check is information too; list it.
- For pure-judgment skills without an evidence artifact, the deliverable ends with a short
  sources-and-scope block: inputs read (paths), rules applied (with the source and version
  fetched), and what was not assessed.

---

## Part 5 — Safety and boundaries

### P13. Minimize data; keep secrets out of everything
**Rule.** Artifacts retain only what provenance needs.

**How.**
- Normalize instead of storing raw API envelopes. Strip response-generated tokens and unrelated
  metadata.
- No keys named `token`, `access_token`, `api_key`, `password`, or `secret` in any retained JSON;
  `verify` scans for them recursively.
- Secrets come from the agent's `.env`, set through the Settings tab. They never appear on a
  command line, where process listings expose them, in a log, or in a config file the skill
  creates.
- No PHI in any artifact. Skills that could encounter it say so and stop to flag.
- No shell transcripts, temporary scripts, duplicate downloads, or `__pycache__` in a skill or
  project directory.

### P14. Side effects are declared, gated, and quiet by default
**Rule.** Every skill classifies what it does to the outside world, and outbound effects go only
through sanctioned, approval-gated channels.

| Class | Examples | Rule |
|---|---|---|
| Read-only | search, agenda, report | Free to run |
| Local write | files under the skill root or project | Only in designated locations (P4) |
| Outbound | email, calendar events, reference-library writes, posts | Sanctioned tool only (himalaya, the calendar CLI), approval-gated, recorded in the manifest |

- Unattended runs never use chat delivery; email goes through himalaya on the account matching
  the recipient's tier, with no hand-written `From:` header.
- **Quiet runs say nothing.** If there is nothing substantive, send nothing and write a run
  summary instead. A daily "all clear" trains the operator to ignore the skill.
- A skill that reports on state does not modify it. Reporters suggest; owners change.
- A refusal from a gate (egress block, `550 not authorized`, approval denial) is a signal, not a
  bug to route around. Never widen a credential, switch resolver, or build a sidecar service to
  get past it.

### P15. Configuration over customization; portable by default
**Rule.** A skill works for any operator without editing its SKILL.md or scripts.

**How.**
- Operator-specific values live in `config/` or `~/work-profile/`: recipients, keywords, IDs,
  preferences. Never names, addresses, or absolute home paths in the skill itself. The public
  publish gate rejects personal identifiers.
- Defaults are generic and safe: quiet when empty, approval-gated, local timezone.
- Installs are copies. A locally installed copy takes precedence over the baked baseline of the
  same name, and must point its script paths at itself.

---

## Part 6 — Maintenance

### P16. Shared helpers are vendored, not re-invented
**Rule.** Common mechanics come from one canonical module, `skillkit.py`, copied into each skill
that needs it at `scripts/skillkit.py`. A gate check fails if any copy differs from the canonical
file, so skills stay installable standalone and never drift.

**Canonical location:** `skills-hub/tools/skillkit.py`, checked by `tools/hub.py check` and by
`deploy/tests/skill-scripts-test.sh`. *(Not yet created; building it is the first enhancement
task.)*

**Contents (stdlib only):**

| Helper | Purpose |
|---|---|
| `contained(root, *parts)` | Resolve a path under the root; raise if it escapes (P4) |
| `atomic_write_text` / `atomic_write_json` | Temp file plus rename in the same directory (P6) |
| `append_jsonl_unique(path, records, key)` | Idempotent append-only state (P6) |
| `fetch_json(url, payload=None, timeout=90, opener=None)` | JSON over HTTP with a timeout, a user agent, and an injectable opener for tests (P8) |
| `require_list(obj, "data.oppHits")` / `require_id(value, source)` | Fail-closed envelope and identifier checks (P8) |
| `RunManifest` | Context manager that records inputs, outputs with hashes, steps, errors, and side effects, and writes `run.json` atomically (P7) |
| `verify_manifest(root, run_id)` | The generic half of every `verify` subcommand (P10) |
| `scan_forbidden_keys(obj)` | Recursive secret-key scan (P13) |
| `verify_quotes(source_text, quotes)` | Confirm each quoted anchor appears verbatim in its source, after whitespace normalization; returns the misses (P12). Catches invented quotes in reviews, minutes, and checklists |
| `queue_email(to, subject, body_path, manifest)` | The one sanctioned way a skill queues mail: picks the himalaya account by recipient tier, never writes a `From:` header, records the side effect (P14) |
| `local_now()` / `local_today()` | Timezone-aware time from the container (P9) |
| `EXIT_OK`, `EXIT_PARTIAL`, `EXIT_USAGE` | The library's exit codes (P2) |

### P17. Say it once
**Rule.** A convention shared by many skills is stated once and referenced, not pasted into
every SKILL.md.

**How.** The house rules (read `~/work-profile/*` fresh and never cache it, offer once to fill
thin files, no PHI, email only through himalaya) belong in one shared reference. Individual
skills name which profile files they read and link the rule. Pasted boilerplate diverges the
first time someone edits one copy.

### P18. Versions mean something
**Rule.** `version` in the frontmatter follows semver and changes whenever behavior changes.

**How.**
- Patch: wording, no behavior change. Minor: new capability, old runs and state still valid.
  Major: layout, state format, or interface change.
- Every behavior change gets a CHANGELOG entry.
- A layout or state change ships a `migrate` subcommand that moves old state idempotently and
  records what it did in a manifest. The SKILL.md tells the agent to run it once, not to move
  files by hand.
- The manifest records `skill_version`, so any run can be tied to the code that produced it.

### P19. Declare the contract in frontmatter
**Rule.** A skill's I/O contract is machine-readable, so tooling can check it.

```yaml
metadata:
  hermes:
    contract:
      root: ~/work/funding-digest          # or: project:<skill-output>
      cli: scripts/refresh.py
      verify: scripts/refresh.py verify
      state: [state/seen.jsonl]
      config: [config/funding-watch.md]
      network: [api.grants.gov, api.reporter.nih.gov, api.nsf.gov]
      side_effects: [email:approval-gated]
```
`hub.py check` can then confirm the CLI and tests exist, that declared network hosts are on the
egress allowlist, and that a skill with outbound side effects says how they are gated.
*(Proposed convention; tooling support follows the first skills that adopt it.)*

---

## Part 7 — Writing the SKILL.md itself

### P20. Instructions an open-weight model can follow without guessing
- **One path per task.** Give the exact command. Do not offer three ways to do it.
- **Explicit stop conditions and budgets.** "Fetch at most three pages; on a slow or failed fetch,
  skip it and move on." "Report empty only after three phrasings."
- **Fetch rules instead of remembering them.** Funder instructions, reporting checklists, and
  format limits change. Fetch the current version, cite it, and record the version in the
  deliverable.
- **Name the failure modes the model actually hits**, with the correct response to each, in an
  error-handling table.
- **Blank beats guessed.** `(unassigned)`, `*(to capture)*`, and `NOT ASSESSED` are correct
  outputs. A plausible guess gets trusted later and becomes an error.

### Section order
1. **When to Use**, including when to use a neighboring skill instead.
2. **Contract**: root, inputs, outputs, state, side effects, network. Mirrors P19.
3. **Setup**: profile files read, config created on first run with the operator's confirmation.
4. **Procedure**: numbered steps, each either a CLI call or a named judgment step.
5. **Failure handling**: table of symptom, meaning, and response.
6. **Pitfalls**.
7. **Verification**: the verify command, what it checks, and the remaining judgment checklist.

---

## Review checklist

Use this to review a new or revised skill. Cite the principle for each finding.

| # | Check | P |
|---|---|---|
| 1 | Every deterministic step is a CLI call; no curl, ad-hoc parsing, or in-head arithmetic in prose | P1, P2, P9 |
| 2 | Request and response contracts live in code and are pinned by tests | P3, P10 |
| 3 | Root and output paths are declared; the script enforces containment | P4 |
| 4 | Operator config and machine state are separated; state is written only by the script | P5 |
| 5 | State writes are atomic, idempotent, ordered after their justifying artifact | P6 |
| 6 | Scripted runs write a `skill-run/1` manifest whose status matches the exit code | P7, P2 |
| 7 | Malformed data fails closed; partial coverage is recorded and disclosed | P8 |
| 8 | Unit tests cover the minimum set and run in the gate with no network | P10 |
| 9 | Stateful and scheduled skills ship a `verify` subcommand the procedure runs | P10 |
| 10 | Every deliverable claim traces to an identified record; coverage is stated | P12 |
| 11 | No secrets, tokens, PHI, or temp files in artifacts; secrets come from `.env` | P13 |
| 12 | Side effects are classified, gated, recorded; quiet runs send nothing | P14 |
| 13 | No personal identifiers or absolute home paths; operator values come from config | P15 |
| 14 | Shared mechanics come from vendored `skillkit.py`; the copy matches canonical | P16 |
| 15 | Shared house rules are referenced, not pasted | P17 |
| 16 | Version bumped per semver; CHANGELOG entry; `migrate` for layout changes | P18 |
| 17 | Frontmatter declares the contract | P19 |
| 18 | Instructions give one path, budgets, stop conditions, and a failure table | P20 |
