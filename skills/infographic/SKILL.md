---
name: infographic
description: Turn a markdown brief, notes or a topic into a single-image infographic that follows the institution's brand. You plan it in a written brief, write every word as HTML, ask the image model only for art without words, combine the two, check the result with a program and by eye, and fix what the checks find.
version: 3.0.0
metadata:
  hermes:
    tags: [infographic, image, visual, html, brand, presentations]
    category: presentations
---
# Infographic

Produce a polished single-image infographic from a markdown file, notes, or a topic.

**How it is built, and why.** Image models misspell words they draw — a stray letter in a
heading, a garbled number; every model tried here did. So the work is split:

| Part | Made by | Checked by |
|---|---|---|
| The words, numbers and layout | **code**: an HTML page you write, drawn by `render-html` | `render-html` itself, against the source — exact, not a judgement |
| The pictures (optional) | **the image model** (`image_generate`), asked for art with **no words** | you, with `vision_analyze` |
| The whole picture | the two combined in the page | both |

You write two prompts before you make anything: one for the code and one set for the art.
Then you make, check, and repeat until the checks pass.

## Before you start
1. Skim `~/work-profile/communication-style.md` and `~/work-profile/identity.md`. If thin,
   offer **once** to fill them or skip. **Read fresh each use; never cache.**
2. `render-html --help` must run. If the command is missing, this container's image predates
   it: tell the operator the image needs updating, and stop.
3. Find out what art you can get — `image_gen.provider` in `$HERMES_HOME/config.yaml`:
   - `image-local` — the image model on this server. Prompts stay on the server. About half
     a minute a picture, one at a time.
   - `mcw` — the image model of the institution's own inference gateway. Prompts go to that
     gateway and no further; each picture is billed to the gateway key.
   - `openrouter` (or another vendor) — prompts are sent to that vendor.
   - unset, or `image_generate` answers with an error — **no art.** Use the template's tinted
     boxes and icons. Do not stop, and do not ask for a backend to be set up unless the
     operator wants illustrations.

## Brand — the default look
Every infographic follows the institution's brand in **colour and type** unless the operator
asks for something else. Each time:
- Read the `brand-guidelines` skill, and `~/work/brand-kit/style-notes.md` if it exists (the
  kit wins where they differ). `template.html` already carries that palette and font stack in
  `:root`; change `:root` only to match what you read, or what the operator asks for.
- Use the palette's colours only. Lead with the primary colour; the accents are for rules,
  icons and markers, not for small text.
- **No logo by default.** A logo makes the piece speak for the institution. Add it only when
  the operator asks for an official or branded piece — then place the approved file (from
  `~/work/brand-kit/logos/`, else the `brand-guidelines` assets) with `<img class="logo">`,
  follow that skill's logo rules, and tell the operator it may need Communications review.
  If no approved file is installed, say so; never draw, redraw or generate a logo.
- If the operator wants a different look, do that, and say in your report that the piece is
  off-brand at their request.

## The stages
Work in `~/work/<project>/figures/<slug>/` (ask which project, or propose one; never write
loose in `~/work/`). The finished picture goes one level up: `~/work/<project>/figures/<slug>.png`.

### 1. The words → `words.txt`
From the source, write every piece of text the picture will show, one per line, **exactly as
it should read**: the title, each heading, each bullet, each number with its label, the
footer. Lines starting with `#` are notes. This file is the contract, and `render-html`
holds you to it twice: every line must be in the picture, and every line must be in the source.
- Only what the source says. No slogans, captions, credits or "Source:" lines of your own.
  If the source has no footer, there is no footer.
- The source must be a text file `render-html` can read. If it is a PDF or a Word file,
  convert it to text first and keep that copy in the folder. If the operator gave the content
  in chat, save what they wrote as `source.md` in the folder, unchanged.
- Words the operator asks for that are not in their source (a title they dictate, a credit
  line) go, exactly as they gave them, in `asked.txt` in the folder — and in `words.txt`.
- A topic with no source at all ("make an infographic about hand hygiene"): write the content
  first as `source.md`, show it to the operator, and get their agreement before designing.
- Numbers verbatim, with the source's own units and labels. Do not turn a label into a unit
  or shorten it ("Minutes" stays "Minutes", not "min").
- Keep what gives a number its meaning: a table keeps its title and its column labels (the
  template has a table slot); a list keeps its heading.
- Cut for length here, not later — an infographic holds a title, 3–6 blocks of a few short
  lines, and a handful of numbers. Tell the operator what you left out.

### 2. The brief → `brief.md`
Copy `brief.md` (beside this file) and fill it in. It contains the two prompts:
- **The code prompt** (section 3 of the brief): the layout, written as if for a developer
  who has not seen the source — canvas, blocks and their order, which lines of `words.txt` go
  in which block, which picture goes where and at what shape, colours and type, the
  constraints. See "Writing the code prompt".
- **The art prompts** (section 4): one shared style line and one prompt per picture. See
  "Writing art prompts".

Decide the canvas here: landscape `1600x900` (slides, handouts), portrait `1080x1350`
(posters, hallway screens), square `1080x1080`.

### 3. The art (skip when there is no backend)
For each art prompt, call `image_generate` with the prompt and its `aspect_ratio`
(`landscape`, `square` or `portrait`). Copy the result from `$HERMES_HOME/cache/images/` into
the folder under the name the brief gives it (`background.png`, `panel1.png`, …).
**Check each picture as it arrives** with `vision_analyze`. Ask, in these words: *"Describe
the main subject in one sentence. Then list any letters, numbers, words, logos or
watermarks you can see, any smeared, duplicated or distorted parts, and the main colours."*
Accept it only if the subject is the one asked for, there is no lettering, and nothing is
distorted. Otherwise **rewrite the prompt** — say what to change, not the same words again
(see the table in stage 6) — and ask again. At most two more tries per picture; then use the
icon for that box. At most five pictures in an infographic.

### 4. The code → `page.html`
Copy `template.html` (beside this file) to `page.html` and build what the code prompt
describes. Type each word from `words.txt`; delete every slot you have no words for.
- `body` has a fixed `width`/`height` equal to the canvas (`<body class="portrait">` for
  1080x1350, `<body class="portrait square">` for 1080x1080).
- A box without a picture gets a simple line icon that suits its block — replace the
  template's placeholder icons (inline SVG, a few strokes, no words).
- Words are HTML text. None in a picture, none in CSS `content:`.
- Only files in the folder and fonts installed here. No web fonts, no remote images.

### 5. Combine and render
Put the accepted pictures in: un-comment each `<img>` (and the backdrop with its veil).
Keep text on a card or the header band, never straight on a picture. If a picture's colours
fight the palette, add `class="tinted"` to its box rather than accepting a clash. Then:

    render-html page.html ../<slug>.png --size 1600x900 --source <the source file>

`words.txt` in the folder is picked up by itself; add `--source asked.txt` if there is one.
The picture is saved at twice the canvas size, sharp enough to print.

### 6. Check — this stage is not optional
**a. Read every line `render-html` printed.** `RESULT: clean` is required. Each `PROBLEM`
line is a defect in the picture: text cut off, outside the canvas, out of its box or over
other text; pictures or headings in a row that are not level; a picture that did not load;
faint text; a word missing from the picture, a word in it that is not in `words.txt`, or a
line of `words.txt` that is not in the source. `LOOK` lines name what a program cannot judge.
The run must include `--source`: without it the last of those is not checked.

**b. Look at the PNG** with `vision_analyze`. Ask, in these words: *"This is an infographic.
List every defect you can see: text that is cut off, overlaps something, touches an edge or
is hard to read against what is behind it; boxes that are uneven or misaligned; empty areas
that look unfinished; pictures that are distorted, noisy, off-subject, or contain letters;
pictures that do not look like one set. Then say what a reader's eye meets first, second
and third."* Compare the reading order with the brief. **Do not ask it to proof-read**: the
words were checked exactly in (a), and a vision model misreads small text.

**c. Check the numbers** in `words.txt` against the source, one by one.

**d. Fix and repeat.** Go back to the stage the defect comes from:

| What the check found | Go back to | What to change |
|---|---|---|
| A word missing, extra or different | stage 4 | Retype it from `words.txt`. If `words.txt` itself is wrong, fix that from the source first. |
| A line that is not in the source | stage 1 | Replace it with the source's own wording, or delete it. It stays only if the operator asked for it — then it belongs in `asked.txt`. Never add it to the source file. |
| Text cut off, out of its box, outside the canvas | stage 2, then 4 | Change the layout in the code prompt: fewer columns, smaller picture boxes, less padding, smaller type (not below the brief's minimum). Still too long → ask the operator which lines to drop. **Never reword to make it fit.** |
| Text overlapping, pictures or headings not level, uneven boxes | stage 4 | Fix the CSS; if the plan itself is the cause, fix the code prompt first. Boxes in a row start at the top and share one layout — never centre the content of some. |
| Empty areas that look unfinished | stage 2, then 4 | Give the room to something: taller picture boxes (the template's grow by themselves), larger type, or one block fewer. Do not spread content out or centre it to hide the gap. |
| Faint text | stage 4 | Use the palette's dark colour on light, white on the lead colour. |
| Text hard to read over a picture | stage 5 | Put it on a card, or strengthen the veil. |
| A picture with letters in it, distorted, or off-subject | stage 2, then 3 | Rewrite that art prompt: name the subject more plainly, remove anything that carries writing (signs, screens, papers, charts), simplify. Then generate again. |
| Pictures that do not look like one set, or clash with the palette | stage 2, then 3 | Tighten the shared style line and regenerate the odd one; or add `class="tinted"`. |
| The eye lands on the wrong thing | stage 2, then 4 | Change sizes and order in the code prompt. |

A fix is not finished until it has been rendered and checked again — both (a) and (b): a
change that cures one defect often causes another. Do not wave a finding away because a
measurement disagrees with it; look at the place it names.

Write each round in section 5 of the brief: what was found, what you changed. **At most
three rounds of fixing.** If something is still wrong after the third, stop: deliver the
best version and list what is not right. If `vision_analyze` is not available, say so in
your report — the picture was then checked by the program only; do not call it looked at.

### 7. Report
The path of the PNG; the last `RESULT` line; what you looked at and what you could not;
what you left out of the source; anything dropped (a picture replaced by an icon) or still
wrong; and that the folder holds `page.html`, `words.txt` and `brief.md` for later edits.
If you placed a logo: which approved file, and that an official piece may need review by
Communications before it is used.

## Writing the code prompt
It must let someone build the page without seeing the source, and let you check the page
against it afterwards. It names:
- the canvas, and the blocks from top to bottom with rough sizes;
- which lines of `words.txt` go in each block — every line placed exactly once;
- the hierarchy: the largest thing on the page, and the order the eye should follow;
- each picture: its file, its box, and the shape it was asked for in (a `landscape` picture
  in a wide box, a `square` one in a square box — a picture is cropped to fill its box, so
  the subject must be in the middle);
- colour and type: "as `:root`", or the changes and who asked for them;
- the constraints, including the smallest body text (24px on a 1600 px canvas, 26px on 1080).

Few words per block. If the plan needs more than six blocks, propose two infographics.

## Writing art prompts
A prompt describes **one picture** — never the infographic.
- **One subject, concrete and nameable:** "a wristwatch, a ring and a set of keys in a small
  tray", not "preparation".
- **Where it sits:** subject centred, clear space around it, plain background — the box
  crops the edges.
- **The shared style line**, word for word on every prompt: the kind of drawing, the
  palette in plain words (image models do not follow hex codes: say "deep teal-green and
  white with pale green accents"), the background.
- **End with "no text or lettering anywhere".** And leave out anything that carries
  writing: signs, documents, screens showing an interface, calendars, name badges, charts
  with axes, book covers. If one is needed, say it is blank ("a blank clipboard").
- **Never** ask for words, labels, numbers, a logo, a real person, or anything from a
  patient's record. Small, simplified figures draw better than close-up faces and hands.
- **A background** is its own kind: "a soft abstract background, pale, low contrast", with
  nothing that could be mistaken for content.
- Two or three sentences. Longer prompts get partly ignored.

Example — style line: *"Flat vector illustration, simple shapes, soft shadows, deep
teal-green and white with pale green accents, plain white background, subject centred with
clear space around it, no text or lettering anywhere."* Prompt: *"A patient lying on the
table of an MRI scanner, seen from the side, a technologist standing beside it."* + the
style line.

## A fully model-drawn infographic (only on request)
If the operator asks for an infographic drawn entirely by the image model **and**
`image_gen.provider` is `openrouter` (Nano Banana Pro, which renders lettering well): write one
prompt that describes the finished design with every title and label spelled exactly, call
`image_generate` with `model: nano-banana-pro`, and proof every word against `words.txt` by
eye. Never do this with `image-local` or `mcw` — their lettering comes out wrong.

## Pitfalls
- Asking the image model for words, labels, numbers or a logo — they come out misspelled.
- Sending the same art prompt again and hoping — change the prompt, and write down what changed.
- Rewording the source to make a line fit, or filling an empty slot with a phrase of your own.
- Reporting a picture as checked when only the file was written.
- Asking `vision_analyze` whether the spelling is right — it is the wrong tool for that.
- Web fonts or remote images in the page — they are not loaded, on purpose.
- Cramming too much in — fewer, larger blocks read better.
- Leaving the result only in a cache or temp folder — the PNG belongs in `~/work/<project>/figures/`.
- Keep secrets out of the graphic. PHI and other protected information too, unless the operator
  asks for it. An art prompt is sent to the image backend: with `image-local` it stays on this
  server; with any other backend it is a disclosure to that vendor (SOUL, rule 2) — and art
  prompts should describe pictures, not people or cases, either way.

## Verification
`~/work/<project>/figures/<slug>.png` exists, rendered from `page.html` in the folder beside
`words.txt` and a filled-in `brief.md`; the last `render-html` run was given `--source` and
ended `RESULT: clean`, with the words and source checks counted in; you looked at the PNG and at each picture in it (or said
that you could not); every number traces to the source; the colours and type are the brand's
(or the operator asked otherwise); there is no logo unless the operator asked for one; and
your report says what was checked, fixed, dropped or left.
