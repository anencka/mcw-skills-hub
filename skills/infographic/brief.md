# Brief — <title of the infographic>

Fill this in BEFORE writing any code or asking for any picture. It holds the two prompts the
rest of the work follows (sections 3 and 4) and the record of what was checked and fixed
(section 5). Keep it beside `page.html`; it is how the infographic is edited later.

## 1. What it is for
- **Source:** <file, notes or topic it was made from>
- **Audience and where it will be seen:** <patients in a waiting room / a slide / a poster …>
- **The one thing a reader should take away:** <one sentence>
- **Canvas:** <landscape 1600x900 | portrait 1080x1350 | square 1080x1080>
- **Brand:** <default: the deployment's palette and fonts, no logo | official piece WITH the
  approved logo, asked for by the operator | another look, asked for by the operator: …>
- **Card pictures:** <tinted panels (default) | floating cut-outs (operator asked)>

## 2. The words
Every piece of text the picture will show is in `words.txt`, one per line, copied from the
source (`render-html --source` checks that). Nothing is added to it for the sake of the
design; words the operator asked for by hand are in `asked.txt`. Note here anything left out
and why:
- <e.g. "the source's third paragraph: background, not needed on a poster">

## 3. The code prompt
Written as if for a developer who has not seen the source. It is what `page.html` is built
from, and what it is checked against.

> Build one fixed-size HTML page, <W>x<H> px, from `template.html`.
> **Layout:** <steps first | numbers first>: <header band with title and subtitle; (numbers
> first: a band of K big numbers;) N cards in a row/column, each with a picture box <w>x<h>
> above/left of one heading and at most 3 lines; (steps first: a row of K figures or a table;)
> a footer strip>. About <W·H/11000> words in all.
> **Order and emphasis:** <what the eye should meet first, second, third; which number is biggest>.
> **Each block, with its lines of `words.txt`:** <card 1 = lines 3–6; card 2 = …>.
> **Pictures:** <background.png behind everything under the light veil, showing around the
> cards; panel1.png in card 1 …; or "none: icons and the page's own shading">. Each picture box has the shape its picture was asked for in.
> **Colour and type:** <the `:root` values as they are | changes, and who asked for them>.
> **Constraints:** every word is HTML text typed exactly as in `words.txt`; body text no
> smaller than <24px landscape / 26px portrait>; text only on a card or the header band, never
> straight on a picture; nothing outside the canvas; no remote files; no words in CSS.

## 4. The art prompts
One shared style line, so the pictures look like a set (each card's subject goes in its
`<subject>` slot); then the background, and one prompt per card picture. Each prompt describes a picture and nothing else. Leave this section as "none" when there is no
image backend, or the operator wants none.

- **Style line (every card prompt, the subject in its slot):** <Flat 2D vector illustration
  of <subject>, teal-green and pale green with deep navy only on parts of the object. Shading
  stays inside the object; the background is one single uniform pale mint-green colour,
  identical in every corner and at the top and bottom, like a sticker on coloured paper: no
  perspective, no table, no floor, no horizon, no shadow under the object, no vignette, no
  gradient, no text or lettering anywhere.>
- **Subjects side by side** (each from its own card; no object or view twice): card 1 =
  <…>; card 2 = <…>; card 3 = <…>
- **background** — `aspect_ratio: <the canvas's shape>` — no style line — <a soft abstract
  background: a teal-green and white gradient with flowing curves and a few translucent
  circles, light but clearly visible, minimal, no text, no lettering, no people>
- **panel1** — `aspect_ratio: <landscape>` — saved as `panel1-raw.<ext>`, tinted to
  `panel1.png` with `art-tint` — <ONE subject, concrete, at most one or two things beside it, no setting,
  equipment plain and unlabelled: "a wristwatch, a ring and a set of keys in a small tray">
- **panel2** — …

## 5. Checks and fixes
One entry per round. A round is: render, read `render-html`'s lines, look at the PNG, fix.

| Round | What the checks found | What was changed (which prompt, which rule in the page) |
|---|---|---|
| 1 | | |

**Left as it is, and why:** <anything not fixed after the last round>
