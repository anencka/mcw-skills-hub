---
name: data-processing
description: Build reproducible data pipelines — load, clean, transform, and validate datasets — with sanity checks at every step and no silent data loss.
version: 1.0.0
metadata:
  hermes:
    tags: [data, pipeline, cleaning, pandas, reproducibility]
    category: data
---
# Data Processing & Pipelines

## When to Use
Loading, cleaning, merging, transforming, or validating datasets; building reusable, reproducible
processing steps from raw inputs to analysis-ready outputs.

## First-use setup (read the profile; fill if thin)
Read `~/work-profile/tools-and-systems.md` (preferred libraries, compute limits, where raw vs.
derived data live) and `~/work-profile/domain-knowledge.md` (data formats and domain norms). If
either is still mostly `*(to capture)*`, offer **once** to fill it — a few questions (hand to
`onboarding-interview`, e.g. "let's do tools-and-systems") or the operator edits it in the Files
tab — then proceed; if they skip, note that in memory and don't re-ask. **Read these fresh each
use; never cache their contents — the file is the source of truth.**
- **Sensitivity (hard rule):** confirm no PHI/identifiers in what you'll touch; if present, stop and flag.

## Procedure
1. **Inspect first.** Look at the raw data — shape, dtypes, ranges, missingness, a few real rows —
   before transforming. State what you observe.
2. **Plan the pipeline** as discrete, named steps (load → clean → transform → validate → write);
   keep raw data immutable and write derived outputs separately.
3. **Clean explicitly:** handle missing/duplicate/outlier values deliberately and **log row counts
   before/after each step** — never drop data silently.
4. **Validate** with assertions/sanity checks (expected ranges, key uniqueness, no unexpected
   NaNs, row-count reconciliation). Fail loudly on violations.
5. **Make it reproducible:** deterministic, parameterized, re-runnable; record inputs/outputs and
   any seeds. Prefer a script/function over one-off cells.
6. **Report** what changed (counts, decisions, assumptions) so results are auditable.

## Pitfalls
- Silent row drops / type coercions that lose data — always log deltas.
- Mutating raw data in place; non-reproducible one-off steps.
- Trusting a transform without validating the output.
- Processing identifiable/PHI data — out of scope; stop and flag.

## Verification
Each step's row/column deltas are logged and reconcile; validation checks pass; the pipeline
re-runs to the same result; raw data is untouched and outputs are written separately.
