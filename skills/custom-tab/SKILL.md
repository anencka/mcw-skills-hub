---
name: custom-tab
description: Build or update the operator's "Custom" tab — a private web surface (HTML/CSS/JS) served from ~/custom/, with a bridge for server-side save/load, multi-panel layouts, and panel-to-panel broadcast. Use when asked to make a custom page, dashboard, mini-app, viewer, planner, or anything that should show up under the Custom tab.
version: 2.0.0
metadata:
  hermes:
    category: coding
    tags: [web, html, dashboard, custom-tab, ui]
---

# Custom Tab

## When to Use
The operator wants a small web page, dashboard, report viewer, calculator, or interactive mini-app
that appears in the web interface's **Custom** tab. This is the operator-owned UI surface — full
HTML/CSS/JS, no image rebuild needed. Multi-view apps (a selector page plus several live panels)
are supported — see "Multi-panel layouts" below.

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

## The sandbox and the bridge
Your pages run in **sandboxed iframes with an opaque (null) origin**. They cannot read the app's
session cookie or CSRF token and cannot call `/api/*` or `/custom/app/save` directly — a fetch from
a null origin carries no credentials. Everything privileged goes through a narrow **postMessage
bridge** exposed by the Custom-tab shell. Include this helper in every page (put it in a shared
`~/custom/hermes.js` and `<script src="hermes.js">` it — adjust the relative path from subfolders,
e.g. `src="../hermes.js"` from `views/`):

```js
const hermes = {
  _n: 0, _wait: {}, _onb: null,
  _call(op, payload, timeoutMs) {
    return new Promise((res, rej) => {
      const id = ++this._n;
      const t = setTimeout(() => { delete this._wait[id]; rej(new Error('bridge timeout')); }, timeoutMs || 3000);
      this._wait[id] = { res: v => { clearTimeout(t); res(v); }, rej: e => { clearTimeout(t); rej(e); } };
      parent.postMessage({ type: 'hermes-bridge', id, op, payload }, '*');
    });
  },
  save(filename, content) { return this._call('save', { filename, content }); },
  async load(filename) {            // retry: on a cold load our first message can beat the bridge
    for (let i = 0; i < 5; i++) {
      try { return await this._call('load', { filename }, 2000); }
      catch (e) { await new Promise(r => setTimeout(r, 300)); }
    }
    return { ok: false, error: 'bridge unavailable' };
  },
  setLayout(panels) { return this._call('setLayout', { panels }); },  // main page only
  broadcast(data)   { return this._call('broadcast', data); },        // notify sibling panels
  onBroadcast(fn)   { this._onb = fn; },                              // fn(data, from)
};
addEventListener('message', (e) => {
  if (e.source !== parent) return;
  const m = e.data; if (!m) return;
  if (m.type === 'hermes-broadcast') { if (hermes._onb) hermes._onb(m.data, m.from); return; }
  if (m.type !== 'hermes-bridge-reply') return;
  const w = hermes._wait[m.id]; if (!w) return; delete hermes._wait[m.id];
  m.ok ? w.res(m.result) : w.rej(new Error(m.error));
});
```

Do **not** try the old approach of fetching `/custom/app/csrf` and calling `save` directly — that
route no longer exists and the sandboxed page has no credentials. The bridge is the only path.

## Persisting data (server-side save/load)
Static pages can't write to disk from the browser, so for tools that must **keep state across
browser/device/reboot** (planners, dashboards, note editors, config), use `hermes.save`/`hermes.load`.
Files are stored under `~/custom/`, authenticated, sandboxed, and written atomically. Do NOT fall
back to localStorage for anything that matters (sandboxed null-origin pages may not even have it,
and it's lost on a browser/device change), and do NOT sidecar your own server (see above).

```js
await hermes.save('data/planner.json', JSON.stringify(state));
const r = await hermes.load('data/planner.json');   // {ok, content} or rejects / {error}
const state = r.ok ? JSON.parse(r.content) : null;  // null → first run
```

- `filename` may include subdirs (`data/config.json`, `notes/project.md`); parent dirs are created.
- Confined to `~/custom/` — `../` escapes are rejected. Any text format is fine (.json/.md/.csv/.yaml).
- These files also appear in the Files tab and can be read/edited by the agent, so saved state is
  inspectable and portable.
- Writes are **last-write-wins** (no merging). With multiple panels, follow *one writer per file*,
  or read-modify-write immediately before saving.

## Multi-panel layouts (setLayout + broadcast)
The main page (`index.html`) can declare a stack of extra **panel iframes** rendered below it, each
an independently sandboxed page served from `~/custom/`. This is how to build a multi-view app: the
main page is the controller/selector; each panel is its own small HTML file.

```js
// From index.html only (panels get 'setLayout is main-page only' if they try):
await hermes.setLayout([
  { src: 'views/budget/chart.html', height: '400px', title: 'Spend by month' },
  { src: 'views/budget/table.html', height: '55vh',  title: 'Line items' },
]);
await hermes.setLayout([]);   // clear all panels (e.g. when switching views)
```

- `src` is a **relative path under `~/custom/`** (no leading `/`, no `..`, no URLs). Max 12 panels.
- `height` is optional (`px`/`vh`/`%`, default `400px`); each panel has a native resize handle.
- Calling `setLayout` again **replaces** the whole stack — re-declare the full layout per view.
- Every panel gets the same bridge (`hermes.save/load/broadcast`); copy/include the same helper.

**Shared data, different views** (the recommended pattern): keep one canonical data file, and let
each panel be a different lens over it. After any panel saves, it broadcasts; the others re-load:

```js
// In the panel that edits and saves:
await hermes.save('data/budget.json', JSON.stringify(model));
await hermes.broadcast({ type: 'data-changed', file: 'data/budget.json' });

// In every panel that displays the data:
hermes.onBroadcast(async (data) => {
  if (data && data.type === 'data-changed' && data.file === 'data/budget.json') await refresh();
});
```

`broadcast` delivers to all sibling frames (main + panels) except the sender; `from` is `'main'`
or the panel's `src`. It is fire-and-forget — don't build request/response protocols on it; for
state, the file is the source of truth.

## Procedure
1. `mkdir -p ~/custom` if it doesn't exist.
2. Write `~/custom/hermes.js` (the bridge helper above) and `~/custom/index.html` (a complete HTML
   document). Keep it self-contained or split into sibling files referenced relatively.
3. For a multi-view app: put each panel in its own file (e.g. `~/custom/views/<view>/<panel>.html`),
   have `index.html` render the view selector and call `hermes.setLayout(...)` on selection.
4. For data the app needs, save it under `~/custom/data/` via `hermes.save` (or write it directly
   as the agent) and load it with `hermes.load`.
5. Save. There's no build step and no restart — reload the Custom tab to see it.

## Pitfalls
- **Absolute paths break.** Use relative URLs for assets — pages are served under a `/custom/app/`
  prefix, so `/style.css` won't resolve but `style.css` will. From `views/x/panel.html`, the shared
  helper is `../../hermes.js`.
- **Don't write outside `~/custom/`** for tab content, and don't try to wire it up by editing the
  Flask app — there's nothing to wire; the folder is the contract.
- **Panels can't call `setLayout`** — only `index.html` can. Route layout changes through the main
  page (e.g. a panel broadcasts `{type:'switch-view', view:'budget'}` and main reacts).
- Large/binary assets belong in `~/custom/` too; keep the page fast.

## Verification
- Confirm `~/custom/index.html` exists and that any referenced assets resolve (relative paths,
  correct filenames — remember panels in subfolders need adjusted relative paths).
- Tell the operator to open the **Custom** tab (or reload it) to view the result; describe what they
  should see, including which panels appear for each view.
