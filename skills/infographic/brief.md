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
> **Layout:** <header band with title and subtitle; N cards in a row/column, each with a
> picture box <w>x<h> above/left of a heading and M bullets; a row of K figures; a footer strip>.
> **Order and emphasis:** <what the eye should meet first, second, third; which number is biggest>.
> **Each block, with its lines of `words.txt`:** <card 1 = lines 3–6; card 2 = …>.
> **Pictures:** <background.png behind everything under the veil; panel1.png in card 1 …; or
> "none: icons">. Each picture box has the shape its picture was asked for in.
> **Colour and type:** <the `:root` values as they are | changes, and who asked for them>.
> **Constraints:** every word is HTML text typed exactly as in `words.txt`; body text no
> smaller than <24px landscape / 26px portrait>; text only on a card or the header band, never
> straight on a picture; nothing outside the canvas; no remote files; no words in CSS.

## 4. The art prompts
One shared style line, so the pictures look like a set; then one prompt per picture. Each
prompt describes a picture and nothing else. Leave this section as "none" when there is no
image backend, or the operator wants none.

- **Style line (ends every prompt):** <flat vector illustration, simple shapes, soft shadows,
  deep teal-green and white with pale green accents, plain light background, subject centred
  with clear space around it, no text or lettering anywhere>
- **background** — `aspect_ratio: <landscape>` — <a soft abstract background of …, very pale, low contrast>
- **panel1** — `aspect_ratio: <landscape>` — <ONE subject, concrete: "a wristwatch, a ring and a set of keys in a small tray">
- **panel2** — …

## 5. Checks and fixes
One entry per round. A round is: render, read `render-html`'s lines, look at the PNG, fix.

| Round | What the checks found | What was changed (which prompt, which rule in the page) |
|---|---|---|
| 1 | | |

**Left as it is, and why:** <anything not fixed after the last round>
