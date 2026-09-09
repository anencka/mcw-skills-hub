---
name: review-security
description: Rubric pack for the reviewer specialist — security and safety review of code, configuration, scripts, or a skill before it is adopted. Use when a brief names the review-security rubric.
version: 1.0.0
metadata:
  hermes:
    tags: [review, security, code, configuration, rubric]
    category: review
---
# Security Review (rubric)

Adversarial read of code/config/skills the operator is about to run, adopt, or publish. Your
stance: *what could this do that its author didn't intend, and what could an attacker make it
do?* Findings only — you do not fix the artifact.

## Rubric (answer every applicable section)
1. **Secrets** — hardcoded credentials, tokens, keys; secrets flowing into logs, error messages,
   command lines (visible in process lists), or files with loose permissions.
2. **Input handling** — anything user- or file-derived reaching a shell (`os.system`, backticks,
   unquoted interpolation), SQL, `eval`/`exec`, YAML `load` vs `safe_load`, pickle; path
   traversal on file operations (`..`, absolute paths, symlinks).
3. **Network & egress** — what does it connect to, and is every destination expected? Downloads
   executed without checksum/pinning; http where https should be; credentials sent where they
   shouldn't go.
4. **Injection-by-content** (agent-era class): does the artifact feed retrieved text (web pages,
   emails, documents) anywhere it could be interpreted as instructions or commands? Prompt
   injection paths in skills — a SKILL.md that tells the agent to bypass policy is a CRITICAL
   finding.
5. **Privilege & blast radius** — runs as root when it needn't; writes outside its stated scope;
   deletes/overwrites without backup; `chmod`/`chown` looser than required; destructive commands
   reachable from normal flow.
6. **Dependencies** — unpinned installs, typosquat-adjacent package names, curl-pipe-to-shell.
7. **Failure honesty** — swallowed exceptions around security checks; TOCTOU races on
   check-then-use; timeouts absent on network calls.

## Output
Memo to the brief's output path: findings ordered CRITICAL/HIGH/MEDIUM/LOW, each with file:line,
a quoted snippet, the concrete attack or failure scenario, and CONFIRMED/PLAUSIBLE grade; then
the rubric table including clean sections (a passed section is information). ≤10-line summary
with an adopt / adopt-with-fixes / do-not-adopt recommendation, clearly labeled advisory.
