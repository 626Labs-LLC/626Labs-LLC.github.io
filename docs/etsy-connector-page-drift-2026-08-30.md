# Etsy connector page — drift audit, 2026-08-30

`/etsy-mcp.html` shipped 2026-08-11 (PR #99) on one premise: everything on it is
literally true today. Nineteen days later the product moved and the page did not.
This is the claim-by-claim check against what is now live at
`etsy-agentic-connector.web.app`, which serves a home page, `privacy.html`
(last updated 12 August 2026) and `docs.html` — all three returning 200.

## The headline: the product renamed itself

Everywhere it speaks for itself, the product is now **"626Labs Agentic Sales
Connector."** The hub page calls it **"626Labs Etsy Agentic Connector"** in the
`<title>`, the `<h1>`, `og:title`, the meta description, the footer, and
`content/site.json`'s product title.

Recommend keeping the `etsy-mcp.html` slug regardless of the rename. It is
indexed, it is in `sitemap.xml`, and the page is still the Etsy connector's
page. Renaming the file costs an indexed URL and buys nothing.

## Claims that are still exactly true

No change needed. Verified line by line against the live privacy and docs pages:

- Read-only posture, and the sentence **"Zero tools modify your Etsy shop"** —
  which is now verbatim what the product's own home page says.
- All four scopes, unchanged: `listings_r`, `shops_r`, `transactions_r`,
  `feedback_r`. The live glosses are slightly richer but say the same thing.
- Credentials typed only on etsy.com's own consent screen, never seen by the
  service.
- **AES-256-GCM** at rest.
- Full **CSV export** anytime.
- **No scraping** — official API plus a seller-exported CSV, labeled as
  supplemental.
- Etsy Open API v3 as the data source; MCP as the protocol; Claude as the
  reference client.

## Claims that have gone stale

| On the page | What is live now |
|---|---|
| Product name "Etsy Agentic Connector" | "626Labs Agentic Sales Connector" |
| Privacy + Docs URLs as text, "coming online with the beta" | Both live, 200 |
| "Read-only in v1" | The product says "read-focused" — see below |
| Contact `estevan@626labs.dev` | Privacy page lists `estevan.hernandez@gmail.com` |
| Deletion: "immediate on request; automatic purge 30 days after disconnect" | Split: **tokens deleted immediately** on disconnect; snapshots and imported CSV get the 30-day grace, then purge |

**"Read-only" vs "read-focused."** The distinction is real and the product now
makes it deliberately. Nine tools ship; seven are read-only against Etsy. Two
write, but never to Etsy: `importSupplementCsv` writes to the connector's own
store, and `deleteMyData` destroys data there. So "zero tools modify your Etsy
shop" stays exactly true while "read-only in v1" is now imprecise about the
connector's own storage. Mirroring the product's own word is both more accurate
and more honest.

## Missing from the page entirely

1. **The affiliation disclaimer.** Every page on the connector's own site carries
   *"Not affiliated with or endorsed by Etsy, Inc."* The hub page uses the Etsy
   name throughout and carries no such line. The repo has precedent for exactly
   this — RORORO's copy runs *"Independent third-party tool — not affiliated
   with Roblox Corporation."* This is the most important omission on the list.

2. **"Runs without you."** Snapshots happen server-side on a schedule; the
   seller's machine does not need to be on. It is the product's strongest
   differentiator and the page does not mention it.

3. **Why day-over-day movement is hard at all.** Etsy's API reports lifetime
   counters only. Storing daily snapshots is what makes movement exist as data.
   The page says movers are "computed from snapshot history" without saying why
   that is the whole trick.

4. **Honest numbers.** Every response is stamped with `data_as_of` and a source;
   an unreadable number comes back as `unknown` with a reason, never as zero; a
   broken connection returns a reconnect link rather than stale figures. This is
   trust-section material and belongs on a page whose center of gravity is trust.

5. **The tool list.** Nine named tools, each labeled for whether it touches the
   shop. The page describes capabilities in prose and names nothing.

## The open question — status

The page says: *in active development, private testing with Conundrum by Este,
public availability planned after Etsy's Commercial Access and Anthropic's
Connectors Directory.*

What is observable: a public "Connect your Etsy shop" CTA, a published MCP
server URL (`https://etsy-agentic-connector.web.app/mcp`), and public docs
telling any reader how to add it to their client.

What is **not** observable, and must not be inferred: whether either review has
actually completed. Etsy permits a personal app to reach the owner's own shop
without commercial access, so a live connect page is not evidence of approval.
The status paragraph cannot be rewritten from the outside — it needs Este's
answer on where those two reviews actually stand.

## Not drift, but worth recording

- **Traffic: zero.** GoatCounter's 30-day window (2026-07-31 to 2026-08-30)
  records 422 hits across 8 paths. `/etsy-mcp.html` is not among them. Expected
  rather than alarming: the product is unannounced, and the only inbound path is
  a homepage card on a page that itself drew 31 hits. `/rororo.html` took 360 of
  the 422.
- **Rotation untested in production.** `content/themes.json` still has an empty
  queue, so the 2026-09-01 run will open a "queue is empty" issue and change
  nothing. The page's rotation wiring stays test-gated rather than exercised.
- **`rebuild-hub.yml` is healthy** — green on its one run since the 2026-08-12
  fix. It has not fired since because nothing touched its trigger paths.
