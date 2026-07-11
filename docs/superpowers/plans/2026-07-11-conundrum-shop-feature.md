# Conundrum by Este Shop Feature — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Feature the Conundrum by Este Etsy shop on 626labs.dev: a product card in the index grid + a dedicated `conundrum.html` page with a performance-ordered, renderer-owned product gallery and a repo CTA that lights up when the POD pipeline goes public.

**Architecture:** Hand-authored PB-treated static page with two `SITE_JSON:` zones (`conundrum-products`, `conundrum-repo`) filled by new functions in `scripts/render-hub.py` from a new top-level `conundrum` key in `content/site.json`. Gallery images are Printify mockups harvested via the POD_Pipeline's existing secrets (secrets never enter this repo). Spec: `docs/superpowers/specs/2026-07-11-conundrum-shop-feature-design.md`.

**Tech Stack:** Python 3.11 (renderer + pytest), hand-written HTML/CSS/vanilla JS, PIL for the card thumb, GoatCounter events.

## Global Constraints

- **Branch:** all work on `feat/conundrum-shop`, branched from a fresh `origin/main` (`git fetch origin && git checkout -b feat/conundrum-shop origin/main`). Daily bots churn main — never branch from a stale local main.
- **Working dir:** every command runs from `C:\Users\estev\Projects\626labs-hub` unless stated. Use `git -C` if cwd is uncertain.
- **Commit trailer (every commit):** `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
- **No emoji** anywhere in page copy, code, or commits.
- **No counts in copy:** never "9 products" / "12 sold". Chips are labels ("recently sold", "most viewed"), never numbers.
- **No secrets in this repo:** Printify access happens by importing `pod_secrets` from `C:\Users\estev\Projects\POD_Pipeline` in throwaway scratchpad scripts only. Nothing containing a token is ever written under the repo.
- **Never hand-edit inside `SITE_JSON:` zone markers** once the renderer owns them. Zone content comes from site.json via `scripts/render-hub.py`.
- **Don't write to `assets/brand/`** (script-owned). New assets go to `assets/` root and `assets/screenshots/conundrum/`.
- **Voice:** Conundrum streetwear voice in the page hero + gallery zone copy; 626 builder-to-builder voice in the machine section and the index card description.
- **PB raster rules:** blueprint grid OK on the card thumb; NO scanlines baked into any raster.
- **Verification command note:** `site-doctor.py --check` exits 1 silently — always use `--report` when a human reads the output.

## File map

| File | Action | Responsibility |
|---|---|---|
| `assets/conundrum-logo.png` | Create (copy) | Hero logo + nav mark on the page |
| `assets/thumb-conundrum.png` | Create (PIL) | Index card banner + og:image, 620x620 |
| `assets/screenshots/conundrum/*.jpg` | Create (harvest) | Gallery mockups |
| `scripts/render-hub.py` | Modify | `render_conundrum_products()`, `render_conundrum_repo()`, `CONUNDRUM_HTML`, main() wiring + `--check` |
| `tests/test_render_hub.py` | Modify | Unit tests for both render functions |
| `conundrum.html` | Create | The page: PB shell, zones, crisp-lift, GoatCounter events |
| `content/site.json` | Modify | New `conundrum` key + new `products[]` card entry |
| `index.html`, `sitemap.xml` | Regenerated | By `scripts/render-hub.py` — never hand-edited |

---

### Task 1: Brand + gallery assets

**Files:**
- Create: `assets/conundrum-logo.png`
- Create: `assets/thumb-conundrum.png`
- Create: `assets/screenshots/conundrum/<slug>.jpg` (6-9 files)
- Scratch (NOT committed): `<scratchpad>/harvest_mockups.py`, `<scratchpad>/make_thumb.py`

**Interfaces:**
- Produces: asset paths that Task 5's site.json references must match exactly. Record the final filename list; Task 5 consumes it.

- [ ] **Step 1: Copy the Conundrum logo cut into assets**

```powershell
Copy-Item "C:\Users\estev\Projects\POD_Pipeline\conundrum_logo_transparent.png" "assets\conundrum-logo.png"
```

Open it and confirm it is transparent-background RGBA. If it is not transparent, run the repo's cutter first: `python tools/bgremove/bgremove.py "C:\Users\estev\Projects\POD_Pipeline\conundrum_logo_transparent.png" -o assets/conundrum-logo.png --mode auto`.

- [ ] **Step 2: Compose the 620x620 card thumb (PB field + logo)**

Write to the scratchpad (throwaway — do not commit) and run. Matches sibling thumbs (`thumb-rororo.png` is 620x620). Blueprint grid yes, scanlines no (raster rule).

```python
# <scratchpad>/make_thumb.py
from PIL import Image, ImageDraw

SIZE = 620
FINE, COARSE = 56, 280                      # two-scale drafting grid
CY = (23, 212, 250)

img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255))       # --pb-field
d = ImageDraw.Draw(img, "RGBA")
for x in range(0, SIZE, FINE):
    d.line([(x, 0), (x, SIZE)], fill=CY + (13,), width=1)   # ~.05 alpha
    d.line([(0, x), (SIZE, x)], fill=CY + (13,), width=1)
for x in range(0, SIZE, COARSE):
    d.line([(x, 0), (x, SIZE)], fill=CY + (28,), width=1)   # ~.11 alpha
    d.line([(0, x), (SIZE, x)], fill=CY + (28,), width=1)

logo = Image.open(r"assets/conundrum-logo.png").convert("RGBA")
w = int(SIZE * 0.72)
logo = logo.resize((w, int(logo.height * w / logo.width)), Image.LANCZOS)
img.alpha_composite(logo, ((SIZE - logo.width) // 2, (SIZE - logo.height) // 2))
img.convert("RGB").save("assets/thumb-conundrum.png")
print("wrote assets/thumb-conundrum.png")
```

Run: `python <scratchpad>/make_thumb.py` (from the repo root).
Expected: `wrote assets/thumb-conundrum.png`. Open the PNG — logo centered, faint cyan grid, black field.

- [ ] **Step 3: Harvest product mockups from Printify (pipeline-side secrets)**

The Printify products endpoint returns, per product: `title`, `images[]` (mockups, one with `is_default: true`), and `external.handle` (the live Etsy listing URL). `pod_secrets` exposes `printify_headers()` and `SHOP_ID` (documented in POD_Pipeline/CLAUDE.md).

```python
# <scratchpad>/harvest_mockups.py
import json, pathlib, re, sys

import requests

sys.path.insert(0, r"C:\Users\estev\Projects\POD_Pipeline")
from pod_secrets import printify_headers, SHOP_ID

OUT = pathlib.Path("assets/screenshots/conundrum")
OUT.mkdir(parents=True, exist_ok=True)

products, page = [], 1
while True:
    r = requests.get(
        f"https://api.printify.com/v1/shops/{SHOP_ID}/products.json?page={page}",
        headers=printify_headers(), timeout=30,
    )
    r.raise_for_status()
    d = r.json()
    products += d["data"]
    if page >= d.get("last_page", 1):
        break
    page += 1

visible = [p for p in products if p.get("visible")]
print(f"{len(visible)} visible products:\n")
for p in visible:
    handle = (p.get("external") or {}).get("handle", "")
    print(f"- {p['title']}\n    {handle}")

# Candidate slate: June reassessment keepers. Substring-match titles.
SLATE = [
    "Fire & Ice Spider Monster Joggers",
    "Watercolor x Neon Spider Monster",
    "Fire & Ice Spider Monster Shorts",
    "Not My Problem Penguin",
    # extend to 6-9 after reading the visible-products list above
]

manifest = []
for want in SLATE:
    match = next((p for p in visible if want.lower() in p["title"].lower()), None)
    if not match:
        print(f"!! no visible product matches: {want}")
        continue
    img = next((i for i in match["images"] if i.get("is_default")), match["images"][0])
    slug = re.sub(r"[^a-z0-9]+", "-", match["title"].split("|")[0].lower()).strip("-")
    dest = OUT / f"{slug}.jpg"
    dest.write_bytes(requests.get(img["src"], timeout=60).content)
    manifest.append({
        "title": match["title"].split("|")[0].strip(),
        "image": f"assets/screenshots/conundrum/{dest.name}",
        "etsyListing": (match.get("external") or {}).get("handle", ""),
    })
    print(f"saved {dest}")

MANIFEST = pathlib.Path(r"<scratchpad>/manifest_conundrum.json")  # controller supplies the real scratchpad path
MANIFEST.write_text(json.dumps(manifest, indent=2))
print(f"\nmanifest written to the session scratchpad (never the repo or Projects root): {MANIFEST}")
```

Run: `python <scratchpad>/harvest_mockups.py` from the repo root.
Expected: the visible-product list prints; extend `SLATE` to 6-9 picks using that list (favor reassessment keepers: the three spider items + best meme socks); re-run; 6-9 JPGs land in `assets/screenshots/conundrum/` and the manifest (titles, image paths, listing URLs) is written to the session scratchpad for Task 5 to consume.

If Printify auth fails (token missing/rotated): STOP and flag to Este — do not fall back to scraping Etsy.

- [ ] **Step 4: Sanity-check image sizes**

Run: `python -c "from PIL import Image; from pathlib import Path; [print(p.name, Image.open(p).size) for p in Path('assets/screenshots/conundrum').glob('*.jpg')]"`
Expected: every mockup at least 800px on the short edge. Printify default mockups are typically 3000+ px — if any file is tiny or zero-byte, re-download it.

- [ ] **Step 5: Commit**

```bash
git add assets/conundrum-logo.png assets/thumb-conundrum.png assets/screenshots/conundrum/
git commit -m "feat(assets): Conundrum brand cut, card thumb, gallery mockups

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Renderer functions (TDD)

**Files:**
- Modify: `scripts/render-hub.py` (add two functions near `render_product_foot`, ~line 550 region)
- Test: `tests/test_render_hub.py` (append)

**Interfaces:**
- Consumes: `esc()` / `attr()` helpers already in render-hub.py (lines 70-77).
- Produces: `render_conundrum_products(conundrum: dict) -> str` and `render_conundrum_repo(conundrum: dict) -> str`. Task 4's main() wiring calls both with `content["conundrum"]`. Card markup contract for Task 3's CSS: classes `merch-card`, `merch-img`, `merch-chip`, `merch-meta`, `merch-title`, `merch-price`; every card is an `<a>` with `data-etsy="<slug>"`. Repo CTA: class `repo-cta`, also carries `data-etsy="repo"`. Empty string when `repoUrl` is falsy.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_render_hub.py`:

```python
# ─── conundrum shop page zones ──────────────────────────────────────

def _conundrum(**over):
    base = {
        "etsyUrl": "https://www.etsy.com/shop/ConundrumByEste",
        "repoUrl": None,
        "products": [
            {
                "title": "Fire & Ice Spider Monster Joggers",
                "price": "$46.99",
                "image": "assets/screenshots/conundrum/fire-ice-spider-monster-joggers.jpg",
                "etsyListing": "https://www.etsy.com/listing/111",
                "chip": "recently sold",
            },
            {
                "title": "Not My Problem Penguin Crew Socks",
                "price": "$21.99",
                "image": "assets/screenshots/conundrum/not-my-problem-penguin-crew-socks.jpg",
                "etsyListing": "https://www.etsy.com/listing/222",
            },
        ],
    }
    base.update(over)
    return base


def test_conundrum_products_renders_cards_in_array_order():
    html = render_hub.render_conundrum_products(_conundrum())
    assert html.count('class="merch-card"') == 2
    assert html.index("Fire &amp; Ice") < html.index("Penguin")
    assert 'href="https://www.etsy.com/listing/111"' in html
    assert 'src="assets/screenshots/conundrum/fire-ice-spider-monster-joggers.jpg"' in html
    assert "$46.99" in html


def test_conundrum_products_chip_is_optional():
    html = render_hub.render_conundrum_products(_conundrum())
    assert html.count('class="merch-chip"') == 1
    assert "recently sold" in html


def test_conundrum_products_slugs_data_etsy():
    html = render_hub.render_conundrum_products(_conundrum())
    assert 'data-etsy="fire-ice-spider-monster-joggers"' in html


def test_conundrum_products_empty_list_renders_nothing():
    assert render_hub.render_conundrum_products(_conundrum(products=[])) == ""


def test_conundrum_repo_collapses_when_null():
    assert render_hub.render_conundrum_repo(_conundrum()) == ""
    assert render_hub.render_conundrum_repo(_conundrum(repoUrl="")) == ""


def test_conundrum_repo_renders_when_set():
    html = render_hub.render_conundrum_repo(
        _conundrum(repoUrl="https://github.com/626Labs-LLC/pod-pipeline")
    )
    assert 'href="https://github.com/626Labs-LLC/pod-pipeline"' in html
    assert 'class="repo-cta"' in html
    assert "Read the code" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_render_hub.py -k conundrum -v`
Expected: 6 FAILED with `AttributeError: module 'render_hub' has no attribute 'render_conundrum_products'`

- [ ] **Step 3: Implement both functions**

Add to `scripts/render-hub.py` after the products-section renderers (near `render_product_foot`):

```python
# ─── conundrum shop page (conundrum.html zones) ─────────────────────
def _etsy_slug(title: str) -> str:
    """Stable slug for GoatCounter etsy-click event paths."""
    return re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")


def render_conundrum_products(conundrum: dict) -> str:
    """Gallery cards for the SITE_JSON:conundrum-products zone.

    Array order IS display order (performance-ranked upstream). Chips are
    optional labels, never numbers.
    """
    cards = []
    for p in conundrum.get("products") or []:
        chip = (
            f'\n  <span class="merch-chip">{esc(p.get("chip"))}</span>'
            if p.get("chip")
            else ""
        )
        cards.append(
            f'<a class="merch-card" href="{attr(p.get("etsyListing"))}" '
            f'target="_blank" rel="noopener" '
            f'data-etsy="{attr(_etsy_slug(p.get("title")))}">\n'
            f'  <img class="merch-img" src="{attr(p.get("image"))}" '
            f'alt="{attr(p.get("title"))}" loading="lazy" />{chip}\n'
            f'  <div class="merch-meta">\n'
            f'    <div class="merch-title">{esc(p.get("title"))}</div>\n'
            f'    <div class="merch-price">{esc(p.get("price"))}</div>\n'
            f"  </div>\n"
            f"</a>"
        )
    return "\n".join(cards)


def render_conundrum_repo(conundrum: dict) -> str:
    """Repo CTA for the SITE_JSON:conundrum-repo zone.

    Collapses to nothing while repoUrl is unset — no placeholder ships.
    """
    repo = (conundrum.get("repoUrl") or "").strip()
    if not repo:
        return ""
    return (
        f'<a class="repo-cta" href="{attr(repo)}" target="_blank" '
        f'rel="noopener" data-etsy="repo">Read the code '
        '<svg class="ic arrow" viewBox="0 0 24 24">'
        '<path d="M5 12h14M13 5l7 7-7 7"/></svg></a>'
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_render_hub.py -v`
Expected: all tests PASS (the 6 new ones plus the existing sitemap suite).

- [ ] **Step 5: Commit**

```bash
git add scripts/render-hub.py tests/test_render_hub.py
git commit -m "feat(render): conundrum gallery + repo-CTA zone renderers

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: The page — conundrum.html

**Files:**
- Create: `conundrum.html`

**Interfaces:**
- Consumes: card markup classes from Task 2 (`merch-card`, `merch-img`, `merch-chip`, `merch-meta`, `merch-title`, `merch-price`, `repo-cta`, `data-etsy`).
- Produces: zone markers `SITE_JSON:conundrum-products` and `SITE_JSON:conundrum-repo` that Task 4's wiring fills. Page must be valid and presentable with both zones EMPTY (gallery grid collapses, repo CTA absent).

- [ ] **Step 1: Author the page**

Model: `mod-launcher-games.html` (freshest standalone page — same head pattern, brand tokens, grid-bg, topnav, PB override block appended at the end of `<style>`). Full page:

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Conundrum by Este · merch built by a machine · 626 Labs</title>
<meta name="description" content="Conundrum by Este is the 626 Labs merch shop — streetwear-grade prints designed by an AI pipeline and shipped print-on-demand. Socks, joggers, totes, hats. Every design AI-generated, human-approved." />
<meta property="og:title" content="Conundrum by Este — merch built by a machine" />
<meta property="og:description" content="The 626 Labs merch shop. AI-designed, human-approved, print-on-demand. See what's selling and the nine-stage pipeline behind it." />
<meta property="og:type" content="website" />
<meta property="og:url" content="https://626labs.dev/conundrum.html" />
<meta property="og:image" content="https://626labs.dev/assets/thumb-conundrum.png" />
<meta name="twitter:card" content="summary_large_image" />
<link rel="icon" type="image/png" href="favicon-626.png" />

<style>
  /* ---------- Web fonts ---------- */
  @import url('/fonts/fonts.css');

  /* ---------- Brand tokens (subset of Design/colors_and_type.css used here) ---------- */
  :root {
    --brand-navy:        #192e44;
    --brand-navy-deep:   #0f1f31;
    --brand-cyan:        #17d4fa;
    --brand-cyan-bright: #5ce6ff;
    --brand-magenta:     #f22f89;

    --brand-gradient: linear-gradient(135deg, var(--brand-cyan) 0%, var(--brand-magenta) 100%);

    --ink-0:   #ffffff;
    --ink-200: #c4cdda;
    --ink-300: #a4aebd;
    --ink-400: #99a4b4;

    --fg-1: var(--ink-0);
    --fg-2: var(--ink-200);
    --fg-3: var(--ink-300);
    --fg-muted: var(--ink-400);

    --bg-0: var(--brand-navy-deep);

    --border-1: rgba(255,255,255,.08);
    --border-2: rgba(255,255,255,.14);

    --r-md: 10px;
    --r-lg: 14px;

    --font-display: 'Space Grotesk', 'Inter', system-ui, sans-serif;
    --font-body:    'Inter', system-ui, -apple-system, sans-serif;
    --font-mono:    'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, monospace;

    --ease-out: cubic-bezier(.2,.7,.2,1);
    --dur-fast: 120ms;
    --dur-med: 220ms;
  }

  html, body { margin:0; padding:0; min-height:100vh; }
  body{
    background: var(--bg-0);
    color:var(--fg-1);
    font-family:var(--font-body);
    overflow-x:hidden;
    -webkit-font-smoothing: antialiased;
  }
  *{ box-sizing:border-box; }
  a{ color:var(--brand-cyan); }

  .grid-bg{
    position:fixed; inset:0; pointer-events:none; z-index:0;
  }

  /* ---------- Top nav ---------- */
  .topnav{
    position:sticky; top:0; z-index:50;
    backdrop-filter: blur(16px) saturate(140%);
    -webkit-backdrop-filter: blur(16px) saturate(140%);
    border-bottom: 1px solid var(--border-1);
  }
  .topnav-inner{
    max-width: 1180px; margin: 0 auto; padding: 14px 32px;
    display:flex; justify-content:space-between; align-items:center; gap:24px;
    font-family: var(--font-mono); font-size: 11px; letter-spacing:.1em;
  }
  .brand{
    display:inline-flex; align-items:center; gap:10px;
    color: var(--fg-1); text-decoration:none;
    text-transform: uppercase; font-weight:600; letter-spacing:.18em;
  }
  .brand .mark{ width:20px; height:20px; display:block; }
  .topnav .links{ display:flex; gap:22px; color: var(--fg-3); text-transform: uppercase; align-items:center; }
  .topnav .links a{ color:var(--fg-3); text-decoration:none; transition: color var(--dur-fast); }
  .topnav .links a:hover{ color: var(--brand-cyan); }
  .topnav .links a.cta{ color: var(--brand-cyan); }

  /* ---------- Layout ---------- */
  .wrap{ position:relative; z-index:1; max-width:1180px; margin:0 auto; padding: 56px 32px 72px; }

  /* ---------- Hero ---------- */
  .hero{ display:flex; flex-wrap:wrap; align-items:center; gap:28px 48px; margin-bottom:56px; }
  .hero .logo{ width:min(220px, 40vw); height:auto; }
  .hero h1{
    font-family:var(--font-display); font-weight:700;
    font-size: clamp(30px, 4.5vw, 46px); line-height:1.08; margin:0 0 12px;
  }
  .hero h1 em{ font-style:normal; background:var(--brand-gradient); -webkit-background-clip:text; background-clip:text; color:transparent; }
  .hero .house{ font-family:var(--font-mono); font-size:11px; letter-spacing:.14em; text-transform:uppercase; color:var(--fg-muted); margin:0 0 14px; }
  .hero p.dek{ max-width:640px; color:var(--fg-2); font-size:16px; line-height:1.65; margin:0 0 22px; }
  .shop-cta{
    display:inline-flex; align-items:center; gap:10px;
    font-family:var(--font-mono); font-size:13px; letter-spacing:.08em; text-transform:uppercase;
    color:#04121b; background:var(--brand-cyan); text-decoration:none;
    padding:12px 22px; border-radius:var(--r-md); font-weight:600;
    transition: box-shadow var(--dur-med) var(--ease-out), transform var(--dur-fast);
  }
  .shop-cta:hover{ transform: translateY(-1px); }

  /* ---------- Gallery ---------- */
  .section-eyebrow{
    font-family:var(--font-mono); font-size:11px; letter-spacing:.14em;
    text-transform:uppercase; color:var(--brand-cyan); margin:0 0 8px;
  }
  h2{ font-family:var(--font-display); font-weight:700; font-size:clamp(22px,3vw,30px); margin:0 0 10px; }
  .section-lead{ color:var(--fg-2); max-width:640px; line-height:1.65; margin:0 0 26px; }

  .merch-grid{
    display:grid; grid-template-columns:repeat(auto-fill, minmax(240px, 1fr));
    gap:22px; margin-bottom:64px;
  }
  .merch-card{
    position:relative; display:block; text-decoration:none;
    border:1px solid var(--border-1); border-radius:var(--r-lg);
    overflow:hidden; background:#0b1622;
    transition: transform var(--dur-med) var(--ease-out), border-color var(--dur-med);
  }
  .merch-card:hover{ transform:translateY(-3px); border-color:var(--brand-cyan); }
  .merch-img{ width:100%; aspect-ratio:1/1; object-fit:cover; display:block; }
  .merch-chip{
    position:absolute; top:12px; left:12px;
    font-family:var(--font-mono); font-size:10px; letter-spacing:.12em; text-transform:uppercase;
    color:#04121b; background:var(--brand-cyan);
    padding:4px 9px; border-radius:999px; font-weight:600;
  }
  .merch-meta{ display:flex; justify-content:space-between; align-items:baseline; gap:12px; padding:14px 16px; }
  .merch-title{ color:var(--fg-1); font-size:14px; font-weight:600; line-height:1.35; }
  .merch-price{ font-family:var(--font-mono); color:var(--brand-magenta); font-size:13px; white-space:nowrap; }

  /* ---------- The machine ---------- */
  .machine{ border-top:1px solid var(--border-1); padding-top:48px; }
  .stages{
    display:flex; flex-wrap:wrap; gap:10px; margin:22px 0 26px; padding:0; list-style:none;
    font-family:var(--font-mono); font-size:12px; letter-spacing:.06em;
  }
  .stages li{
    color:var(--fg-2); border:1px solid var(--border-2); border-radius:999px;
    padding:7px 14px; background:rgba(25,46,68,.5);
  }
  .stages li b{ color:var(--brand-cyan); font-weight:500; margin-right:6px; }
  .pull{
    border-left:2px solid var(--brand-magenta); margin:26px 0; padding:6px 0 6px 18px;
    font-family:var(--font-display); font-size:18px; color:var(--fg-1); max-width:560px; line-height:1.5;
  }
  .machine p{ color:var(--fg-2); max-width:680px; line-height:1.7; }
  .repo-cta{
    display:inline-flex; align-items:center; gap:10px; margin-top:18px;
    font-family:var(--font-mono); font-size:13px; letter-spacing:.08em; text-transform:uppercase;
    color:var(--brand-cyan); text-decoration:none;
    border:1px solid var(--brand-cyan); padding:11px 20px; border-radius:var(--r-md);
    transition: box-shadow var(--dur-med) var(--ease-out);
  }
  .repo-cta .ic{ width:16px; height:16px; stroke:currentColor; stroke-width:2; fill:none; }

  /* ---------- Footer ---------- */
  footer{
    border-top:1px solid var(--border-1); margin-top:72px; padding:26px 32px;
    font-family:var(--font-mono); font-size:11px; letter-spacing:.1em; text-transform:uppercase;
    color:var(--fg-muted); display:flex; justify-content:space-between; flex-wrap:wrap; gap:12px;
    max-width:1180px; margin-left:auto; margin-right:auto;
  }
  footer a{ color:var(--fg-3); text-decoration:none; }
  footer a:hover{ color:var(--brand-cyan); }

  @media (max-width:640px){
    .topnav-inner{ padding:12px 18px; }
    .wrap{ padding:40px 18px 56px; }
    .hero{ gap:20px; }
  }

  /* ==================================================================
     Phosphor Blueprint treatment — the drawing is the monitor.
     Same override-block pattern as mod-launcher-games.html.
     ================================================================== */
  :root {
    --pb-field: rgb(0,0,0);
    --pb-grid-fine: rgba(23,212,250,.05);
    --pb-grid-coarse: rgba(23,212,250,.11);
    --pb-scanline: rgba(0,0,0,.42);
    --pb-panel: rgba(0,0,0,.72);
    --pb-panel-border: rgba(23,212,250,.25);
    --pb-bloom-cyan: 0 0 14px rgba(23,212,250,.5);
    --pb-trail: 0 0 6px rgba(23,212,250,.9), 0 0 28px rgba(23,212,250,.5), 12px 0 24px rgba(23,212,250,.25);

    --bg-0: var(--pb-field);
    --border-1: rgba(23,212,250,.14);
    --border-2: rgba(23,212,250,.25);
  }

  .pb-scanlines {
    position: fixed; inset: 0; pointer-events: none; z-index: 60;
    background: repeating-linear-gradient(0deg, var(--pb-scanline) 0 1px, transparent 1px 3px);
  }

  body {
    background:
      linear-gradient(90deg, var(--pb-grid-fine) 1px, transparent 1px),
      linear-gradient(0deg,  var(--pb-grid-fine) 1px, transparent 1px),
      linear-gradient(90deg, var(--pb-grid-coarse) 1px, transparent 1px),
      linear-gradient(0deg,  var(--pb-grid-coarse) 1px, transparent 1px),
      var(--pb-field);
    background-size: 56px 56px, 56px 56px, 280px 280px, 280px 280px, auto;
  }

  .topnav { background: rgba(0,0,0,.72); border-bottom-color: var(--pb-panel-border); }
  .stages li, .merch-card { background: var(--pb-panel); }
  h1 { text-shadow: var(--pb-bloom-cyan); }
  .shop-cta:hover, .repo-cta:hover { box-shadow: var(--pb-trail); }

  /* Crisp-lift: product photography plays scanline-free (overlay is 60);
     the nav rides at 70 and carries its own scanlines so it still reads
     CRT while covering the lifted gallery on scroll. Same pattern as the
     Bacon Trail quiz (PR #78). */
  .merch-grid { position: relative; z-index: 61; }
  .topnav { z-index: 70; }
  .topnav::after {
    content: ''; position: absolute; inset: 0; pointer-events: none;
    background: repeating-linear-gradient(0deg, var(--pb-scanline) 0 1px, transparent 1px 3px);
  }
</style>
</head>
<body>

<div class="pb-scanlines" aria-hidden="true"></div>
<div class="grid-bg" aria-hidden="true"></div>

<nav class="topnav">
  <div class="topnav-inner">
    <a class="brand" href="index.html"><img class="mark" src="assets/conundrum-logo.png" alt="" />626 Labs</a>
    <div class="links">
      <a href="index.html#work">Products</a>
      <a href="index.html#thinking">Field Notes</a>
      <a class="cta" href="#" id="nav-shop" data-etsy="shop">Shop on Etsy</a>
    </div>
  </div>
</nav>

<main class="wrap">

  <!-- Hero: Conundrum voice -->
  <section class="hero">
    <img class="logo" src="assets/conundrum-logo.png" alt="Conundrum by Este logo" />
    <div>
      <p class="house">626 Labs presents</p>
      <h1>Conundrum <em>by Este</em></h1>
      <p class="dek">Merch with a plot twist: every design here came out of a machine
        that was taught taste. Bold prints, zero clip-art energy, socks that go
        harder than they need to. AI-generated, human-approved, printed on demand.</p>
      <a class="shop-cta" href="#" id="hero-shop" data-etsy="shop">Shop on Etsy</a>
    </div>
  </section>

  <!-- Gallery: Conundrum voice, renderer-owned -->
  <section>
    <p class="section-eyebrow">The lineup</p>
    <h2>What's moving</h2>
    <p class="section-lead">Ordered by what actually sells and gets seen — not by
      what we're precious about. Tap through to the listing.</p>
    <div class="merch-grid">
      <!-- SITE_JSON:conundrum-products:start -->
      <!-- SITE_JSON:conundrum-products:end -->
    </div>
  </section>

  <!-- The machine: 626 voice -->
  <section class="machine">
    <p class="section-eyebrow">The machine behind it</p>
    <h2>Nine stages, concept to listing</h2>
    <p>Every product in the shop rode the same pipeline: a Python script library
      that takes a concept to a live Etsy listing with a human approval gate at
      the end. Gemini generates the art, a QA pass filters the AI slop, classical
      CV cuts the background, PIL composites the type, and one base artwork fans
      out into a full variant matrix before anything uploads.</p>
    <ul class="stages">
      <li><b>01</b>concept</li>
      <li><b>02</b>generate — textless, always</li>
      <li><b>03</b>QA — the AI-slop filter</li>
      <li><b>04</b>background removal</li>
      <li><b>05</b>text composite</li>
      <li><b>06</b>variant matrix</li>
      <li><b>07</b>upload</li>
      <li><b>08</b>create product</li>
      <li><b>09</b>publish — human go required</li>
    </ul>
    <p class="pull">The model never writes the words. Art generates textless;
      type gets composited after — so the lettering is always real.</p>
    <p>The pipeline is being cleaned up for a public release. When it ships,
      the code lands here.</p>
    <!-- SITE_JSON:conundrum-repo:start -->
    <!-- SITE_JSON:conundrum-repo:end -->
  </section>

</main>

<footer>
  <span>Conundrum by Este x 626 Labs</span>
  <span><a href="index.html">626labs.dev</a> · Imagine Something Else.</span>
</footer>

<script>
(function () {
  // The shop URL lives in one place: swap SHOP_URL at Task 5 render time is NOT
  // needed — it is baked here once, from site.json's conundrum.etsyUrl.
  var SHOP_URL = 'ETSY_SHOP_URL_PLACEHOLDER';
  document.getElementById('hero-shop').href = SHOP_URL;
  document.getElementById('nav-shop').href = SHOP_URL;

  // Outbound Etsy click events -> GoatCounter (event paths: etsy-click/<slug>).
  document.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a[data-etsy]') : null;
    if (!a || !window.goatcounter || !window.goatcounter.count) return;
    window.goatcounter.count({
      path: 'etsy-click/' + a.getAttribute('data-etsy'),
      title: 'Etsy click: ' + a.getAttribute('data-etsy'),
      event: true,
    });
  });
})();
</script>

<!-- GoatCounter — privacy-friendly, cookieless analytics. See goatcounter.com. -->
<script data-goatcounter="https://626labs.goatcounter.com/count"
        async src="//gc.zgo.at/count.js"></script>

</body>
</html>
```

**IMPORTANT — one real placeholder exists on purpose:** `ETSY_SHOP_URL_PLACEHOLDER` is replaced with the confirmed shop URL in Task 5, Step 2 (it cannot be known before the shop URL is derived there). It must NOT survive Task 5 — Task 5 Step 6 greps for it.

- [ ] **Step 2: Eyeball the page with empty zones**

Run: `python -m http.server 8631` (repo root), open `http://localhost:8631/conundrum.html`.
Expected: PB-treated page renders; gallery section shows heading + lead with an empty grid; no repo CTA; no JS console errors. Stop the server after.

- [ ] **Step 3: Commit**

```bash
git add conundrum.html
git commit -m "feat(site): conundrum.html — shop page shell, PB treatment, crisp-lift gallery

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Renderer wiring — main() owns the conundrum zones

**Files:**
- Modify: `scripts/render-hub.py` — path constant near line 48 (`INDEX_HTML = ...`), wiring inside `main()` (~line 1675), `--check` list (~line 1723), write block (~line 1742)

**Interfaces:**
- Consumes: `render_conundrum_products` / `render_conundrum_repo` (Task 2), zone markers in `conundrum.html` (Task 3).
- Produces: `main()` renders/checks conundrum.html whenever site.json has a `conundrum` key. Task 5 relies on this: adding the key + running the renderer fills the page.

- [ ] **Step 1: Add the path constant**

After `INDEX_HTML = ROOT / "index.html"` (line 48):

```python
CONUNDRUM_HTML = ROOT / "conundrum.html"
```

- [ ] **Step 2: Wire into main()**

In `main()`, after the `out = apply_section_toggles(...)` line and before the feed block:

```python
    # conundrum.html — shop page zones (gallery + repo CTA). Only when the
    # conundrum key exists; the page and key ship together.
    conundrum_new = conundrum_old = None
    if "conundrum" in content:
        conundrum_old = CONUNDRUM_HTML.read_text(encoding="utf-8")
        conundrum_new = substitute_zone(
            conundrum_old, "conundrum-products",
            render_conundrum_products(content["conundrum"]),
        )
        conundrum_new = substitute_zone(
            conundrum_new, "conundrum-repo",
            render_conundrum_repo(content["conundrum"]),
        )
    conundrum_changed = conundrum_new is not None and conundrum_new != conundrum_old
```

- [ ] **Step 3: Extend --check and the write block**

In the `--check` branch, extend the stale tuple list:

```python
        stale = [name for name, drifted in
                 (("index.html", index_changed), ("feed.xml", feed_changed),
                  ("sitemap.xml", sitemap_changed),
                  ("conundrum.html", conundrum_changed)) if drifted]
```

In the write section (after the index write block):

```python
    if conundrum_changed:
        CONUNDRUM_HTML.write_text(conundrum_new, encoding="utf-8")
        print("conundrum.html zones rebuilt from content/site.json")
```

- [ ] **Step 4: Verify no-op behavior (key absent)**

Run: `python scripts/render-hub.py --check`
Expected: exit 0, "up to date" — site.json has no `conundrum` key yet, so the wiring is a no-op and nothing regressed. Then run `python -m pytest tests/ -v` — all PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/render-hub.py
git commit -m "feat(render): wire conundrum.html zones into main() + --check

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Data — site.json conundrum key + index card, first real render

**Files:**
- Modify: `content/site.json` (new top-level `conundrum` key; new entry in `products[]`)
- Modify: `conundrum.html` (bake the confirmed shop URL over the placeholder)
- Regenerated: `index.html`, `sitemap.xml`, `conundrum.html` zones (by the renderer)

**Interfaces:**
- Consumes: Task 1's asset filenames + the harvest manifest (`<scratchpad>/manifest_conundrum.json`); Task 4's wiring.
- Produces: the live data other surfaces read. Phase 2 contract: setting `conundrum.repoUrl` to the public repo URL is the ONLY edit needed to light the repo CTA.

- [ ] **Step 1: Derive the shop URL**

Fetch any harvested `etsyListing` URL (plain GET, no auth) and extract the shop link:

```python
# <scratchpad>/shop_url.py
import re, requests, json, pathlib
manifest = json.loads(pathlib.Path(r"<scratchpad>/manifest_conundrum.json").read_text())
r = requests.get(manifest[0]["etsyListing"], timeout=30,
                 headers={"User-Agent": "Mozilla/5.0"})
m = re.search(r'https://www\.etsy\.com/shop/[A-Za-z0-9]+', r.text)
print(m.group(0) if m else "NOT FOUND — read the listing page manually")
```

Run: `python <scratchpad>/shop_url.py` (repo root). Expected: one shop URL (shape: `https://www.etsy.com/shop/<Name>`). If Etsy bot-blocks the fetch, open the listing in a browser and read the shop link by hand. **Record it — it is used in Steps 2 and 3 and confirmed with Este in the PR description.**

- [ ] **Step 2: Bake the shop URL into conundrum.html**

Replace `ETSY_SHOP_URL_PLACEHOLDER` in `conundrum.html` with the derived URL (one occurrence, in the `SHOP_URL` JS var).

- [ ] **Step 3: Add the conundrum key to site.json**

Top-level key (sibling of `products`, `lab`, `play`). Build `products[]` from the harvest manifest, **ordered by the performance defaults**: items with recent sales first (Printify orders — check Etsy Shop Manager or the pipeline's order data), then most-viewed (Etsy Shop Manager). Chips: `"recently sold"` on items with a sale in the last ~30 days, `"most viewed"` on the top-viewed item without a recent sale. Labels only, never numbers.

```json
"conundrum": {
  "etsyUrl": "<derived shop URL>",
  "repoUrl": null,
  "products": [
    {
      "title": "Fire & Ice Spider Monster Joggers",
      "price": "$46.99",
      "image": "assets/screenshots/conundrum/fire-ice-spider-monster-joggers.jpg",
      "etsyListing": "<from manifest>",
      "chip": "recently sold"
    }
  ]
}
```

(One entry shown; include every slate item from the manifest, real prices from the listings. 6-9 total.)

- [ ] **Step 4: Add the index card to products[]**

Insert into `products[]` directly after the `mod-launcher` entry (consumer-products cluster):

```json
{
  "id": "conundrum",
  "title": "Conundrum by Este",
  "description": "The 626 Labs merch shop — streetwear-grade prints designed by an AI pipeline and sold print-on-demand on Etsy. Gemini generates the art (always textless — type is composited after, so the lettering is real), a QA pass filters the AI slop, classical CV cuts the backgrounds, and one base artwork fans out into a full variant matrix before anything ships. Human approval gates every publish. Socks, joggers, totes, hats.",
  "tags": [
    { "label": "Merch", "tone": "magenta" },
    { "label": "Etsy", "tone": "cyan" },
    { "label": "AI pipeline", "tone": "magenta" },
    { "label": "Live", "tone": "live" }
  ],
  "status": "live",
  "repo": null,
  "npm": null,
  "install": null,
  "storeUrl": null,
  "productPage": "conundrum.html",
  "productPageLabel": "Visit the shop",
  "banner": "assets/thumb-conundrum.png",
  "meta": "POD merch · Etsy · AI-designed",
  "screenshots": []
}
```

- [ ] **Step 5: Render and verify**

```bash
python scripts/render-hub.py
python scripts/render-hub.py --check
python -m pytest tests/ -v
python scripts/site-doctor.py --report
```

Expected: first render reports `index.html rebuilt`, `sitemap.xml rebuilt from the page tree`, `conundrum.html zones rebuilt`; `--check` then exits 0 "up to date"; all tests PASS; doctor report shows **no dangling asset references** (its whole-JSON walk validates every gallery image path) and no prose-fact failures.

- [ ] **Step 6: Placeholder + sitemap assertions**

```bash
grep -c "ETSY_SHOP_URL_PLACEHOLDER" conundrum.html
grep -c "conundrum.html" sitemap.xml
grep -c 'merch-card' conundrum.html
```

Expected: `0` (placeholder gone), `1` (sitemap has the page), and N = the number of slate products (zones filled).

- [ ] **Step 7: Commit**

```bash
git add content/site.json conundrum.html index.html sitemap.xml
git commit -m "feat(site): Conundrum by Este — shop data, index card, first gallery render

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Browser verification + PR

**Files:** none new — verification and ship.

**Interfaces:**
- Consumes: everything above.
- Produces: the PR. Merge waits for Este (shop URL + slate order confirmation happen in PR review).

- [ ] **Step 1: Playwright pass**

Serve locally (`python -m http.server 8631`), then with the Playwright MCP tools against `http://localhost:8631/conundrum.html`:

1. Screenshot desktop (1280px) and mobile (390px) — gallery readable, no horizontal scroll.
2. Computed-style checks via evaluate: `.merch-grid` z-index is `61`; `.topnav` z-index is `70`; `.pb-scanlines` exists at z-index `60`.
3. Scroll the gallery under the nav — nav covers cards and still shows scanlines (screenshot).
4. Click a gallery card with the network tab traced — a request to `626labs.goatcounter.com/count` fires with `etsy-click/<slug>` (then block navigation or navigate back).
5. Hero + nav CTAs point at the confirmed shop URL.

If the browser shows stale CSS, cache-bust with `?v=2` — known local gotcha.

- [ ] **Step 2: Etsy links spot-check**

Run: for each `etsyListing` in site.json's conundrum key, `curl -s -o /dev/null -w "%{http_code} " -A "Mozilla/5.0" <url>`; expected `200` (or `403` if Etsy bot-blocks curl — then open one in a browser to confirm, and note that lychee may need an Etsy exclude later).

- [ ] **Step 3: Push and open the PR**

```bash
git push -u origin feat/conundrum-shop
gh pr create --title "feat(site): Conundrum by Este — shop card + page" --body "$(cat <<'EOF'
Features the Conundrum by Este Etsy shop: product card in the grid + conundrum.html
(PB shell, Conundrum core, crisp-lifted gallery). Gallery is renderer-owned from a new
site.json conundrum key, performance-ordered (recent sales first, views tiebreak).
Repo CTA collapses until conundrum.repoUrl is set — Phase 2 is a one-field edit when
the sanitized pipeline goes public. GoatCounter etsy-click events on all outbound links.

Spec: docs/superpowers/specs/2026-07-11-conundrum-shop-feature-design.md

**Este, confirm in review:**
- [ ] Shop URL: <derived URL here>
- [ ] Product slate + order (recent-sales-first — reorder the array if the ranking is off)
- [ ] Chips ("recently sold" / "most viewed") land on the right items

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 4: Watch CI**

Run: `gh pr checks --watch`. Expected: the doctor workflow (pytest + site-doctor + render --check) passes. Do NOT merge — Este confirms the three review items first.

---

## Self-review notes

- **Spec coverage:** page structure (T3), schema + card (T5), renderer + zones (T2/T4), crisp-lift (T3 CSS), performance ordering + chips (T5 S3), GoatCounter events (T3 JS, verified T6), count-free copy (all copy blocks), sitemap (free via renderer, asserted T5 S6), doctor/lychee guardrails (T5 S5, T6 S2), Phase 2 one-field contract (T4/T5). Pipeline-side `pod` ranking helper: deferred per spec ("can land with v1 or trail it") — not in this plan.
- **Known intentional placeholder:** `ETSY_SHOP_URL_PLACEHOLDER` (Task 3) — resolved and asserted-gone in Task 5.
- **Type consistency:** `render_conundrum_products(dict) -> str` / `render_conundrum_repo(dict) -> str` used identically in tests (T2), implementation (T2), and main() wiring (T4). CSS classes in T3 match the markup contract in T2.
