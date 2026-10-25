---
name: infographic
description: Turn a markdown brief, notes or a topic into a single-image infographic that follows the institution's brand. You plan it in a written brief, write every word as HTML, ask the image model only for art without words, combine the two, check the result with a program and by eye, and fix what the checks find.
version: 3.5.0
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
     boxes, icons and its own soft background shading. Do not stop, and do not ask for a backend to be set up unless the
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
- When you cut the start of a source line, begin what is left with a capital.
- **Cut for length here, not later.** An infographic is read at a glance, not studied. It
  holds:
  - a title, and one subtitle line (14 words at most);
  - 3 or 4 blocks, each one heading and at most 3 lines of about 8 words — **no
    sub-headings inside a block**;
  - up to 4 big numbers, each with a label of 6 words at most (no grant numbers, no lists of
    names, no "|"-joined details);
  - about one word per 11,000 square pixels in all: ~130 on a landscape or portrait page,
    ~105 on a square one. `render-html` counts.
  Pick what matters most to the reader; leave the rest out. A long source (a CV, a dossier,
  a report) gives an infographic of its headlines — the detail goes in your report, where you
  tell the operator what you left out.

### 2. The brief → `brief.md`
Copy `brief.md` (beside this file) and fill it in. It contains the two prompts:
- **The code prompt** (section 3 of the brief): the layout, written as if for a developer
  who has not seen the source — canvas, blocks and their order, which lines of `words.txt` go
  in which block, which picture goes where and at what shape, colours and type, the
  constraints. See "Writing the code prompt".
- **The art prompts** (section 4): one shared style line, a background, and one picture per
  card. See "Writing art prompts". The background is part of the look, not an extra: leave
  it out only when the operator asks for a plain page.

Decide the canvas here: landscape `1600x900` (slides, handouts), portrait `1080x1350`
(posters, hallway screens), square `1080x1080`. And the layout:
- **Numbers first** — **always** when the source is about a person, a team, a programme or a
  year (a profile, a CV, a dossier, an annual summary, a report card): move the numbers
  section above the cards and give it `class="stats lead"`; then three cards.
- **Steps or sections first** (the template as it is) otherwise: cards across, then a table
  or a row of numbers directly under them. For instructions, a process, "before / during /
  after".
In both, the rows follow one another with the template's spacing: no row is pushed to the
bottom of the page, and spare height goes to the cards' pictures (the picture row grows by
itself), not to a gap.

### 3. The art (skip when there is no backend)
For each art prompt, call `image_generate` with the prompt and its `aspect_ratio`
(`landscape`, `square` or `portrait`). Copy the result from `$HERMES_HOME/cache/images/` into
the folder under the name the brief gives it, keeping its extension (`background.png`,
`panel1-raw.png`, …).

**Card pictures are tinted panels** (the default). Each is drawn on a pale mint background
and shown whole in a box of the same tint (`class="art boxed"`), so the join does not show.
As each one arrives:
1. **Even its background first** — a measured check, cheaper than a look:

       art-tint panel1-raw.png panel1.png

   It moves the picture's plain background to the card tint, so every picture in the set
   matches its box and the others. **Exit 2** (*the background is not plain*) means the
   model drew a wall, a floor or a room: change the prompt (the table in stage 6) and ask
   again. A `LOOK` means it moved almost nothing or almost everything: look at the result.
2. **Then look at it** with `vision_analyze`. Ask, in these words: *"Describe the main
   subject in one sentence. Then list any letters, numbers, words, logos or watermarks you can
   see, and any smeared, duplicated or distorted parts."* Accept it only if the subject is
   the one asked for, there is no lettering (labels, marked buttons and dials count), and
   nothing is distorted. (Whether the background is plain is `art-tint`'s to decide, not the
   vision model's — its judgement of backgrounds is unreliable.)

(No `art-tint` command on this system: use the raw picture in a box, as it is.)

Otherwise **rewrite the prompt** — say what to change, not the same words again (see the
table in stage 6) — and ask again. If the second try still misses, **change the subject,
not just the words**: take a simpler stand-in from the card's own words (an object instead
of a person doing something — "a handheld ultrasound probe beside a simple heart shape"
instead of "a clinician scanning a patient") and ask once more. Large equipment (scanners,
machines, beds with devices) starts with the stand-in on the first retry, not the second:
it comes with a wall most often. **Pictures in all the cards or in none:** only if that
simpler subject fails too does every card in the row get an icon instead (the background
stays). **Never put one picture in two cards**, and never reuse a picture to fill a gap —
`render-html` reports the same picture twice. A failed background gives way to the
template's own shading. At most six pictures in an infographic, the background among them.

**When the image service does not answer.** If `image_generate` returns `error_type:
api_error` with "did not answer" or a ConnectionError, the backend is loading or
restarting. Wait 60–90 seconds (one foreground `sleep 75`) and send the same prompt again.
This is not a failed try: do not change the prompt, and do not count it toward the
change-the-subject rule above. After three such failures in a row, tell the operator the
image service is down, and offer icons or a later retry.

#### Floating cut-outs (optional)
Only when the operator asks for floating pictures, or the backend is known to give pure
white. With `image-local`, expect near-white backgrounds and floor shadows; prefer the
tinted panel. Ask for the subject "isolated on a plain pure white background, with white
space on every side" instead of the mint background, then cut each card picture out:

    art-cutout panel1-raw.png panel1.png

It makes the plain white around the subject transparent, so the picture floats on the
see-through card, and crops it to the subject; remove `boxed` from its `.art`. If it says
*the background is not plain white*, ask again once; if that fails, use the tinted panel
for the whole row. A `LOOK` from `art-cutout` means it took almost nothing or almost
everything: look at the result.

### 4. The code → `page.html`
Copy `template.html` (beside this file) to `page.html` and build what the code prompt
describes. Type each word from `words.txt`; delete every slot you have no words for.
**Edit, don't splice:** change the slots in place, with targeted replacements of the
template's own example text. Never cut the file at the first `<body>`, `<main>` or similar
string and paste a new body in — the comments may name those tags too, and a cut there
leaves a comment open that hides the whole page. After editing, `render-html` must print
CHECK lines. `RESULT: not checked (the page could not be measured)` or `PROBLEM blank page`
means the page itself is broken (an unclosed comment, a stray tag): compare `page.html`
with `template.html` and fix that first.
- `body` has a fixed `width`/`height` equal to the canvas (`<body class="portrait">` for
  1080x1350, `<body class="portrait square">` for 1080x1080).
- A box without a picture gets a simple line icon that suits its block — replace the
  template's placeholder icons (inline SVG, a few strokes, no words).
- Words are HTML text. None in a picture, none in CSS `content:`.
- Only files in the folder and fonts installed here. No web fonts, no remote images.

### 5. Combine and render
Put the accepted pictures in: un-comment each `<img>` (the tinted `panelN.png`, its box
`class="art boxed"`), and the backdrop with its veil. The cards are frosted glass: the background is meant to be seen through
them. Do not thicken the cards or the veil to make a page look tidier; if `render-html`
finds text too faint, strengthen the veil a little (up to 0.3) and render again.
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
pictures that do not look like one set. Say whether the page looks finished and designed,
or plain, flat and empty. Then say what a reader's eye meets first, second and third."*
Compare the reading order with the brief. **Do not ask it to proof-read**: the words were
checked exactly in (a), and a vision model misreads small text.

The vision model's statements about **geometry** — boxes "uneven", "higher", "misaligned",
gaps "larger", an "empty strip" — vary from run to run and are often wrong. `render-html`
already measures alignment, empty bands and edges. When the vision model reports a geometry
defect that `render-html` did not, run `render-html --boxes page.html` (it prints where each
box is and `LEVEL ok` or `LEVEL off by N px` for each row) and act only on what it shows.
Use the vision model for what a program cannot judge: the pictures' subjects, lettering and
distortion, whether the pictures look like one set, the overall finish, the reading order.

**c. Check the numbers** in `words.txt` against the source, one by one.

**d. Fix and repeat.** Go back to the stage the defect comes from:

| What the check found | Go back to | What to change |
|---|---|---|
| A word missing, extra or different | stage 4 | Retype it from `words.txt`. If `words.txt` itself is wrong, fix that from the source first. |
| A line that is not in the source | stage 1 | Replace it with the source's own wording, or delete it. It stays only if the operator asked for it — then it belongs in `asked.txt`. Never add it to the source file. |
| Text cut off, out of its box, outside the canvas | stage 2, then 4 | Change the layout in the code prompt: fewer columns, smaller picture boxes, less padding, smaller type (not below the brief's minimum). Still too long → ask the operator which lines to drop. **Never reword to make it fit.** |
| Text overlapping, pictures or headings not level, uneven boxes | stage 4 | Fix the CSS; if the plan itself is the cause, fix the code prompt first. Boxes in a row start at the top and share one layout — never centre the content of some. |
| Empty areas that look unfinished | stage 2, then 4 | Give the room to something: taller picture boxes (the template's grow by themselves), larger type, or one block fewer. Do not spread content out or centre it to hide the gap. |
| Faint text | stage 4 | Use the palette's dark colour on light, white on the lead colour. On a see-through card (`against what is behind it in the picture`): strengthen the veil a little (up to 0.3), or move that text off the busiest part of the background. |
| Text hard to read over a picture | stage 5 | Put it on a card, or strengthen the veil. |
| A picture with letters in it, distorted, or off-subject | stage 2, then 3 | Change what caused the defect, and keep the subject and the style line. Letters or marks: remove the thing that carried them (a sign, a paper, a screen, a control panel), or say it is plain and unlabelled. Distorted: fewer objects or figures, or another view of the same subject. Off-subject: name the subject more concretely. Then generate again. |
| The page looks plain, flat or unfinished | stage 2, then 3 or 5 | No background picture → add one. Pictures small or cropped to strips → give them more of the card. Pictures lifeless → more soft shading, and deep navy on parts of the object — not more detail. A change of look is not a change of words: everything else stays as it is. |
| `blank page`, `blank render`, or `not checked (the page could not be measured)` | stage 4 | The page is broken, not the design: an unclosed `<!--` or a stray tag above the content. Compare `page.html` with `template.html`; never splice on a tag name. |
| `art-tint` exit 2 (background not plain) | stage 2, then 3 | The model drew a wall, a floor or a room. If the prompt is not already in the "flat 2D vector … no perspective, no horizon, no vignette" form of the style line, switch to it before changing the subject. Then, for a machine or large equipment, switch straight to an object stand-in (a patient table, a coil, a part of the machine) — they come with a wall most often. |
| A picture on a navy (dark) background | stage 2, then 3 | Navy with no stated place went into the background. Say "deep navy only on parts of the object". |
| Card pictures whose background tints differ | stage 3 | Run `art-tint` on each raw picture with the same `--tint`. Never edit the prompts to chase a matching colour. |
| `too many words`, `long`, or `wraps` | stage 1 | Cut lines from `words.txt` — fewer blocks, fewer lines, shorter labels — and tell the operator what you left out. Never shrink the type to fit. |
| `mixed`: some cards with a picture, some without | stage 3 | Generate the missing picture again with a simpler prompt; if it still fails, icons in every card of that row. |
| `empty`: a box with a large empty stretch | stage 2, then 4 | Boxes in a row share one height, so a short card is empty at the bottom: even out the content (move a line), drop the row to fewer cards, or let the picture take the room. Never fill it with words that are not in `words.txt`. |
| `edge`: a box against the edge of the canvas | stage 4 | Give it the same margin as the other boxes; take the room from the boxes above (smaller pictures, less padding), not from the margin. |
| `same picture` | stage 2, then 3 | Give that card its own subject (see "Each card's picture is about that card") and generate it. Never copy a picture into another card. |
| `empty band` across the page | stage 4 | Rows follow one another: remove the margin or `auto` spacing that pushed a row down; spare height goes to the cards' picture row. |
| `number label` | stage 1 | Six words at most: "publications", "peer-reviewed papers since 2016". Grant numbers, roles and names go in your report. |
| `subtitle` | stage 1 | One line under the title: who it is for, or the one-line summary. Not a list of roles. |
| `sub-heading` | stage 1, then 4 | One heading per block; its lines are plain text in the body style. Merge or drop the lines that were sub-headings. |
| `squeezed`: a picture shown as a strip | stage 4 | Give its box more height (at least 110 px, no wider than about 3 to 1) — take the room from words, not from the picture. |
| Pictures that do not look like one set, or clash with the palette | stage 2, then 3 | Tighten the shared style line and regenerate the odd one (after `art-tint`, the backgrounds already match); or add `class="tinted"`. |
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
  in a wide box, a `square` one in a square box — a tinted panel is shown whole on its tint,
  so a box of another shape leaves tint around the picture, not a cut-off subject);
- colour and type: "as `:root`", or the changes and who asked for them;
- the constraints, including the smallest body text (24px on a 1600 px canvas, 26px on 1080).

Few words per block. If the plan needs more than six blocks, propose two infographics.

## Writing art prompts
A prompt describes **one picture** — never the infographic. The look to aim for sits between
a line icon and a detailed scene: **a spot illustration** — one subject drawn in a few
simple shapes with soft shading, no setting around it, the kind of picture that reads at a
glance from across a room. Detail is what goes wrong: every extra object is a chance for
stray marks, labels and distortion.
- **One subject, concrete and nameable, with at most one or two things beside it:** "a
  wristwatch, a ring and a set of keys in a small tray", "a patient lying on an MRI table",
  not "preparation" and not a room.
- **Each card's picture is about that card, and no two are alike.** Read the card's heading
  and lines, then pick its subject; write the subjects side by side in the brief and change
  any that repeat an object or a view — three scanners are one picture three times. An
  abstract topic gets a concrete stand-in from its own words:
  - methods, techniques, software → the thing it acts on or makes: a brain made of simple
    shapes, a coil, a wave on a plain screen-less panel, a stack of image slices;
  - leadership, collaboration, teaching → people: two or three simplified figures around a
    table, a hand-off, a person at a whiteboard turned away from the viewer;
  - safety → a shield, a checklist on a blank clipboard; growth, funding → a seedling, steps;
  - clinical work → the patient side: a figure on a table, a hospital bed, a heart or a brain.
- **No setting, and no ground:** no room, no table, no floor, no horizon, no shadow under the
  object. The background is one uniform pale mint-green, "like a sticker on coloured paper" —
  `art-tint` evens it to the card tint. Image models fill an even colour more reliably than
  they give pure white (asked for white, they give near-white with a grey floor shadow), and
  "flat 2D … sticker on coloured paper, no perspective, no horizon" stops them drawing a
  ground plane under the subject.
- **Equipment plain and unbranded:** "a plain white MRI scanner with no labels, buttons or
  screens". Leave out anything that carries writing or marks: signs, documents, screens,
  monitors, control panels, dials, calendars, name badges, charts with axes, book covers.
  If one is needed, say it is blank ("a blank clipboard").
- **The shared style line**, word for word on every card prompt, with the card's subject in
  its `<subject>` slot: the kind of drawing, the palette in plain words (image models do not
  follow hex codes), the background. Say **where** the dark colour goes — "deep navy only on parts of the object":
  navy with no stated place goes into the background on large objects.
- **End with "no text or lettering anywhere".**
- **Never** ask for words, labels, numbers, a logo, a real person, or anything from a
  patient's record. One or two small, simplified figures at most; no close-up faces or hands.
- **The background** is its own kind, asked for in the canvas's shape and without the
  style line: *"A soft abstract background: a teal-green and white gradient with flowing
  curves and a few translucent circles, light but clearly visible, minimal, no text, no
  lettering, no people."* Nothing in it that could be mistaken for content.
- Two or three sentences. Longer prompts get partly ignored.

Example — style line: *"Flat 2D vector illustration of <subject>, teal-green and pale green with deep navy only
on parts of the object. Shading stays inside the object; the background is one single
uniform pale mint-green colour, identical in every corner and at the top and bottom, like a
sticker on coloured paper: no perspective, no table, no floor, no horizon, no shadow under
the object, no vignette, no gradient, no text or lettering anywhere."* Three cards — methods, clinical
studies, leadership — get three different subjects: *"a stylised brain built from a few
simple shapes, beside a small stack of image slices"* / *"a patient lying on a narrow
hospital table, seen from the side"* / *"three simplified figures around a small round
table, one pointing at a blank sheet"*. Each goes in the `<subject>` slot. Navy (the
palette's dark colour) on the object next to the lead colour gives the pictures depth; a
single hue looks flat.

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
- Asking an image model for "pure white": with `image-local` you get near-white plus a floor
  shadow. Use the tinted panel.
- Unplaced "navy" in a style line: it paints the background navy.
- Subjects that come with a ground or a device. In one run with `image-local`, a brain with
  glowing dots, a magnifying glass over a tissue section of cell dots, and figures around a
  networked globe passed; a microscope, a slide beside an MRI tile, and a prostate gland with
  slices (it read as a brain plus a device) kept failing. Guidance, not a list to copy.
- Splicing `page.html` on a tag name that also appears in the template's comments.
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
ended `RESULT: clean`, with the words and source checks counted in; each card picture
passed `art-tint` (or `art-cutout` on the floating path) and a vision check for subject,
lettering and distortion; the PNG is more than 200 KB at 2x for a page with pictures (a tiny
PNG means a blank render); you looked at the PNG (or said that you could not); every number traces to the source; the colours and type are the brand's
(or the operator asked otherwise); there is no logo unless the operator asked for one; and
your report says what was checked, fixed, dropped or left.
