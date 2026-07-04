---
name: note-taker
description: Capture, list, search, and tag timestamped markdown notes in ~/notes/. Use to jot something down, find a past note, or review recent notes/tags.
version: 1.0.0
metadata:
  hermes:
    tags: [notes, capture, tags, search]
    category: notes
---
# Note Taker

Lightweight capture of timestamped, taggable markdown notes. Notes live in **`~/notes/`**
(`/home/agent/workspace/notes/`) — plain files, visible and editable in the Files tab. Create the
directory if it doesn't exist (`mkdir -p ~/notes`).

## Add a note
1. Filename: `note_YYYYMMDD_HHMMSS.md` (use the real current time from `date +%Y%m%d_%H%M%S`).
2. Write this structure (tags optional, comma-separated):
   ```markdown
   # Note - YYYY-MM-DD HH:MM:SS

   **Tags:** tag1, tag2

   <note content>
   ```
3. Save to `~/notes/` and confirm the filename + path back to the operator.

## List notes
List `~/notes/*.md` newest-first (e.g. `ls -t ~/notes/*.md`); for each, show filename, time, and its
`**Tags:**` line if present.

## Search notes
Grep `~/notes/*.md` case-insensitively for the term; show each matching file with a short preview
snippet drawn from the **content** (skip the header, the `**Tags:**` line, and `---` separators).

## Recent notes
Show the newest N (default 5): filename, time, and a ~150-char preview of the actual content.

## List tags
Pull every `**Tags:**` line across `~/notes/`, split on commas, and show the unique tags sorted.

## Notes
- Always operate inside `~/notes/`. No PHI, no secrets in notes.
- When building previews, skip headers/tags/separators so the snippet is meaningful.
- Be brief and confirm what you did.

## Verification
The note file exists under `~/notes/` with the timestamped name, header, any tags, and the content;
list/search/recent reflect the files actually present.
