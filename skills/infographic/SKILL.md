---
name: infographic
description: Turn a markdown brief or a topic into a single-image infographic using the native image generation tool (Nano Banana Pro via OpenRouter), with strong in-image text.
version: 1.0.0
metadata:
  hermes:
    tags: [infographic, image, visual, nano-banana, presentations]
    category: presentations
---
# Infographic

Produce a polished single-image infographic from a markdown file, notes, or a topic. This skill is
**prompt-craft** — the actual rendering is done by the **native image generation tool**, which is
configured to use **Nano Banana Pro** (`google/gemini-3-pro-image-preview`) through the operator's
existing OpenRouter key. Nano Banana Pro has unusually strong in-image text rendering, which is what
makes infographics work.

## First-use setup (read the profile; fill if thin)
Skim `~/work-profile/communication-style.md` (visual tone, palette, formality) and
`~/work-profile/identity.md` (who/what it represents). If thin, offer **once** to fill them or skip
and note it in memory. **Read fresh each use; never cache — the file is the source of truth.**
Confirm image generation is configured: it's on by default (`image_gen.provider: openrouter`);
if a call returns `auth_required`, the OpenRouter key isn't set — point the operator to the Settings tab.

## Procedure
1. **Get the content.** From a given markdown file/notes or a topic. Extract the **title**, the 3–6
   **key points/sections**, any **numbers/stats** worth featuring, and the intended **audience**.
   Don't invent facts or figures — use only what the source provides (or ask).
2. **Write a tight image prompt** describing the infographic as a finished design, not a request.
   Include, concretely:
   - Title text (exact words) and each section's heading + 1 short line, **spelled exactly** as they
     must appear (the model renders your literal text).
   - Layout (e.g. "header band, then a 3-column row of icon + stat + caption, footer with source").
   - Visual style: palette, simple flat icons, clean sans-serif, generous whitespace; match the
     operator's style preferences. Keep it legible — few words per block. **For MCW-branded
     infographics, consult the `brand-guidelines` skill** for the palette (lead with MCW Green
     `#006f66`) and fonts — and do **not** ask the model to render the MCW logo; composite the real
     approved logo file on afterward.
   - Any real numbers to feature, verbatim.
3. **Render** by calling the **image generation tool** with that prompt and an `aspect_ratio`
   (`landscape` for slides/handouts, `portrait` for posters, `square` for social). The default model
   is `nano-banana-pro`; for a faster/cheaper draft pass `model: nano-banana-2`.
4. **Place the output.** The tool saves to `$HERMES_HOME/cache/images/`. **Copy it into the active
   project** so it's visible in the Files tab — `~/work/<project>/figures/<slug>.png` (ask which
   project this infographic is for, or propose a name to create; never write loose in `~/work/`).
   Report that path.
5. **Proof and iterate.** Open/inspect the result and check the **text is spelled correctly and
   readable** (the most common failure). If a label is wrong or cramped, refine the prompt (tighten
   wording, fewer elements, bump to `nano-banana-pro` if you drafted on flash) and regenerate.

## Pitfalls
- Misspelled or garbled in-image text — proof every label; simplify if the model struggles.
- Cramming too much in — infographics fail when dense; fewer, larger blocks read better.
- Inventing stats/figures to fill the design — only feature real numbers from the source.
- Leaving the image only in the cache dir — always copy it into `~/work/<project>/figures/` so the operator can see it.
- No PHI / no secrets in the graphic.

## Verification
A PNG exists under `~/work/<project>/figures/`, its title and section text are spelled correctly and
legible, every featured number traces to the source, and the layout/aspect match the request.
