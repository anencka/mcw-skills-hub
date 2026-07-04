---
name: data-visualization
description: Produce clear, honest, publication-quality figures — right chart for the data, accurate encodings, readable labels — in the operator's preferred plotting stack.
version: 1.0.0
metadata:
  hermes:
    tags: [visualization, plots, figures, matplotlib]
    category: data
---
# Data Visualization

## When to Use
Creating plots/figures for exploration, analysis, papers, slides, or grants — and improving the
clarity and correctness of existing figures.

## First-use setup (read the profile; fill if thin)
Read `~/work-profile/tools-and-systems.md` (preferred plotting libraries, output formats, where
figures are saved/embedded) and `~/work-profile/communication-style.md` (figure conventions:
fonts, color palette incl. colorblind-safe needs, style). If either is still mostly
`*(to capture)*`, offer **once** to fill it — a few questions (hand to `onboarding-interview`,
e.g. "let's do tools-and-systems") or the operator edits it in the Files tab — then proceed; if
they skip, note that in memory and don't re-ask. **Read these fresh each use; never cache their
contents — the file is the source of truth.**

## Procedure
1. **Match chart to question and data type.** Distribution → hist/violin/ECDF; comparison → bar
   with error/dot; relationship → scatter; trend → line; composition → stacked/area (sparingly).
   Avoid chart types that distort (e.g., dual y-axes, 3D, truncated bars).
2. **Encode honestly:** zero baselines for bars; show uncertainty (error bars/CI/n) when relevant;
   don't imply precision the data lacks.
3. **Make it readable:** descriptive title, labeled axes **with units**, legible font sizes,
   minimal clutter, colorblind-safe palette, direct labels over dense legends when possible.
4. **Produce reproducibly:** a parameterized script that regenerates the figure from data; save
   to the operator's format/DPI; vector (SVG/PDF) for publication where possible.
5. **Review** the rendered image — actually look at it — for overlap, clipping, misleading scales,
   and that it answers the intended question.

## Pitfalls
- Misleading encodings (truncated axes, bad aspect ratio, rainbow colormaps for quantitative data).
- Unlabeled axes/units, tiny fonts, overplotting, non-colorblind-safe colors.
- Hand-tweaking a figure that can't be regenerated from code.
- Claiming a figure is correct without viewing the rendered output.

## Verification
The figure renders correctly (viewed, not assumed), uses an honest encoding with labeled axes/
units and uncertainty where relevant, regenerates from the script, and is saved in the requested
format/quality.
