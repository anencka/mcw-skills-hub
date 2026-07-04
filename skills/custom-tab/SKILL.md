---
name: custom-tab
description: Build or update the operator's "Custom" tab — a private web surface (HTML/CSS/JS) served from ~/custom/, with server-side save/load so pages can persist data. Use when asked to make a custom page, dashboard, mini-app, viewer, planner, or anything that should show up under the Custom tab.
version: 1.1.0
metadata:
  hermes:
    category: coding
    tags: [web, html, dashboard, custom-tab, ui]
---

# Custom Tab

## When to Use
The operator wants a small web page, dashboard, report viewer, calculator, or interactive mini-app
that appears in the web interface's **Custom** tab. This is the operator-owned UI surface — full
HTML/CSS/JS, no image rebuild needed.

## Where the content lives
- All Custom-tab content lives in **`~/custom/`** (`/home/agent/workspace/custom/`), on the data
  volume. This is the *only* place that drives the Custom tab.
- The tab serves **`~/custom/index.html`** as the entry point. Add more files under `~/custom/`
  (CSS, JS, images, data) and reference them **relatively** (`<link href="style.css">`,
  `<script src="app.js">`, `<img src="chart.png">`). Subfolders work too.
- It is served at `/custom/app/…` behind login; you don't configure routes or restart anything —
  saving a file makes it live on the next page load.

## Hard boundary
**Never edit the base web application to change this tab.** The app code (`/opt/webapp`), the Hermes
runtime (`/opt/hermes`), and the baseline skills (`/opt/mcwagent`) are system-owned and read-only to
you — and editing them is the wrong fix anyway. Everything the Custom tab shows is controlled by
`~/custom/`. If you ever feel the need to touch `app.py` or a template to change the tab, stop:
the answer is a file under `~/custom/`.

## Missing a backend endpoint? Don't sidecar it — flag it.
If the page needs a backend route that doesn't exist (e.g. an LLM-chat panel calling `/api/...`),
do **not** stand up your own server, proxy, daemon, or port listener under `~/custom/` to fake it.
That workaround is wrong on every axis:
- **It's broken anyway.** A browser `fetch('http://127.0.0.1:PORT')` resolves to the *operator's*
  machine, not this container — and an HTTPS page can't call a plain-HTTP local port (mixed content).
  It only ever "works" when you test it with `curl` from inside the container.
- **It's unmanaged.** A hand-started process isn't under supervisord, so it dies on the next restart
  and never comes back — the feature silently breaks.
- **It's unauthenticated.** It bypasses the app's login + CSRF, and can spend the operator's
  credentials with no gate.
- **It hardcodes a provider.** Never call a model provider's REST API directly (OpenRouter, Bedrock,
  Azure, …). The system is provider-agnostic — model calls route through Hermes (`hermes chat -q`),
  so a provider switch is a config change, not a code change. A direct provider call re-introduces
  exactly the lock-in the operator is avoiding.

Instead: build only what works as **static files served by the tab**, and **tell the operator which
endpoint the app is missing** so they can add it properly (authenticated, supervised, provider-neutral).
Propose the fix; don't sidecar it.

## Persisting data (server-side save/load)
Static pages can't write to disk from the browser, so for tools that must **keep state across
browser/device/reboot** (planners, dashboards, note editors, config), use the built-in persistence
endpoints — files are stored under `~/custom/`, authenticated, sandboxed, and atomic. Do NOT fall
back to localStorage for anything that matters (it's lost on a browser/device/origin change), and do
NOT sidecar your own server (see the section above).

The write is CSRF-protected like the rest of the app. Because the page is static (no Jinja token to
embed), fetch the token first, then send it as `X-CSRF-Token`:

```js
// relative URLs resolve from /custom/app/ (the index page). From a sub-page use /custom/app/save etc.

// load (returns {ok, content} or {error}; 404 if absent)
async function loadState() {
  const r = await fetch('save?filename=planner-state.json');
  if (r.ok) return JSON.parse((await r.json()).content);
  return null;                       // first run / not saved yet
}

// save (POST needs the CSRF token)
async function saveState(state) {
  const { csrf_token } = await (await fetch('csrf')).json();
  await fetch('save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf_token },
    body: JSON.stringify({ filename: 'planner-state.json', content: JSON.stringify(state) })
  });
}
```
- `filename` may include subdirs (`data/config.json`, `notes/project.md`); parent dirs are created.
- Confined to `~/custom/` — `../` escapes are rejected. Any text format is fine (.json/.md/.csv/.yaml).
- These files also appear in the Files tab and can be read/edited by the agent, so saved state is
  inspectable and portable.

## Procedure
1. `mkdir -p ~/custom` if it doesn't exist.
2. Write `~/custom/index.html` (a complete HTML document). Keep it self-contained or split into
   sibling files referenced relatively.
3. For data the page needs, write it alongside (e.g. `~/custom/data.json`) and `fetch('data.json')`,
   or inline small data directly into the HTML.
4. Save. There's no build step and no restart — reload the Custom tab to see it.

## Pitfalls
- **Absolute paths break.** Use relative URLs for assets — the page is served under a `/custom/app/`
  prefix, so `/style.css` won't resolve but `style.css` will.
- **Don't write outside `~/custom/`** for tab content, and don't try to wire it up by editing the
  Flask app — there's nothing to wire; the folder is the contract.
- Large/binary assets belong in `~/custom/` too; keep the page fast.

## Verification
- Confirm `~/custom/index.html` exists and that any referenced assets resolve (relative paths,
  correct filenames).
- Tell the operator to open the **Custom** tab (or reload it) to view the result; describe what they
  should see.
