---
name: site-access
description: What to do when a website or API can't be reached because the institutional egress allowlist blocked it (DNS NXDOMAIN / "could not resolve host" / connection refused to a new site). Generates the approval link the user clicks to allow the site once or always.
version: 1.0.0
metadata:
  hermes:
    tags: [network, egress, allowlist, approval, blocked]
    category: productivity
---
# Site access (egress allowlist)

This deployment restricts the agent's outbound network to an **allowlist of approved
sites** (a security measure against prompt-injection exfiltration). When you try to reach
a site that isn't on the list, DNS fails — typically `NXDOMAIN`, `could not resolve
host`, `getaddrinfo ENOTFOUND`, or `Name or service not known`.

## Recognize it

A *blocked* site fails DNS resolution entirely. (If DNS resolves but the connection times
out, that's a normal network problem, not the allowlist.) Widely-used research sites,
publishers, PubMed/NIH, GitHub, PyPI etc. are pre-approved — blocks usually happen on
less common domains.

## What to do

1. Extract the blocked **domain** (e.g. `data.somejournal.org`). Registrable domain is
   enough — approval covers subdomains.
2. Read `HERMES_PUBLIC_FQDN` from the environment (also in `$HERMES_HOME/.env`).
3. Give the user this link **in whatever channel you're talking on** (terminal, Signal,
   web chat) and explain in one sentence why you need the site:

   ```
   https://<HERMES_PUBLIC_FQDN>/egress/approve?domain=<blocked-domain>
   ```

   Example message: *"I can't reach `data.somejournal.org` — it's not on the approved
   site list. If you want me to use it, approve it here (choose 'allow for 8 hours', or
   'always allow' — note that 'always' applies to everyone's agents on this server):
   https://<your-instance-host>/egress/approve?domain=data.somejournal.org"*

4. Wait for the user to say they approved it, then **retry** the original request. New
   DNS lookups succeed immediately after approval.
5. If `HERMES_PUBLIC_FQDN` is not set, tell the user to ask their administrator to add
   the domain to the allowlist (`allowlist-local.conf` on the host).

## Fallback without approval

If the user prefers not to approve the site, try to get the content another way: the
Firecrawl web tools (search/scrape) are pre-approved and can often fetch what a direct
request to the blocked domain would have.

## Rules

- **Never try to work around the allowlist** (alternate resolvers, IP literals, open
  proxies). The point of the gate is that a person — not you — decides.
- Only ask for domains you actually need for the user's current task, one at a time,
  and always say *why*. The approval page warns users about look-alike domains; make
  your reason easy to verify.
