import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

# render-hub.py has a hyphen (matches site-doctor.py convention) — load by path.
_spec = importlib.util.spec_from_file_location(
    "render_hub", ROOT / "scripts" / "render-hub.py"
)
render_hub = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(render_hub)


def _make_site(tmp_path):
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    for name in ("vibe-walk", "editorial", "bacon-trail"):
        d = tmp_path / name
        d.mkdir()
        (d / "index.html").write_text("<html></html>", encoding="utf-8")


def test_sitemap_includes_home_and_subpages(tmp_path):
    _make_site(tmp_path)
    xml = render_hub.render_sitemap(root=tmp_path)
    assert xml.startswith('<?xml version="1.0" encoding="utf-8"?>')
    assert "<urlset" in xml and "</urlset>" in xml
    assert "<loc>https://626labs.dev/</loc>" in xml
    assert "<loc>https://626labs.dev/vibe-walk/</loc>" in xml
    assert "<loc>https://626labs.dev/editorial/</loc>" in xml
    assert "<loc>https://626labs.dev/bacon-trail/</loc>" in xml


def test_sitemap_is_deterministic(tmp_path):
    _make_site(tmp_path)
    assert render_hub.render_sitemap(root=tmp_path) == render_hub.render_sitemap(root=tmp_path)


def test_sitemap_home_listed_first_with_top_priority(tmp_path):
    _make_site(tmp_path)
    xml = render_hub.render_sitemap(root=tmp_path)
    assert xml.index("<loc>https://626labs.dev/</loc>") < xml.index(
        "<loc>https://626labs.dev/bacon-trail/</loc>"
    )
    assert "<priority>1.0</priority>" in xml
    assert "<priority>0.8</priority>" in xml


def test_sitemap_subpages_sorted_alphabetically(tmp_path):
    _make_site(tmp_path)
    xml = render_hub.render_sitemap(root=tmp_path)
    order = [
        xml.index(f"<loc>https://626labs.dev/{name}/</loc>")
        for name in ("bacon-trail", "editorial", "vibe-walk")
    ]
    assert order == sorted(order)


def test_sitemap_honors_exclude(tmp_path, monkeypatch):
    _make_site(tmp_path)
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    (drafts / "index.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.setattr(render_hub, "SITEMAP_EXCLUDE", frozenset({"drafts"}))
    xml = render_hub.render_sitemap(root=tmp_path)
    assert "drafts" not in xml


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


# ─── plugin-family grouping ─────────────────────────────────────────

def _products():
    mk = lambda i: {"id": i, "title": i, "description": "d", "tags": [], "status": "live"}
    return [mk("celestia-3"), mk("vibe-cartographer"), mk("vibe-doc"),
            mk("rororo"), mk("vibe-test"), mk("conundrum")]


def _family():
    return {
        "memberIds": ["vibe-cartographer", "vibe-doc", "vibe-test"],
        "card": {"id": "vibe-family", "title": "The Vibe Plugin Family",
                 "description": "One playbook.", "tags": [], "status": "live",
                 "flagship": True, "repo": "estevanhernandez-stack-ed/vibe-plugins",
                 "productPage": "plugins/", "productPageLabel": "Meet the family"},
    }


def test_family_grouping_collapses_members_in_place():
    html = render_hub.render_products(_products(), _family())
    assert html.count('<article class="product') == 4  # 3 non-members + 1 family card
    assert "The Vibe Plugin Family" in html
    assert html.index("celestia-3") < html.index("The Vibe Plugin Family") < html.index("rororo")
    for member in ("vibe-doc", "vibe-test"):
        assert f"<h3>{member}</h3>" not in html


def test_family_grouping_absent_config_is_identity():
    prods = _products()
    assert render_hub.render_products(prods) == render_hub.render_products(prods, None)
    assert render_hub.render_products(prods).count('<article class="product') == 6


def test_family_flagship_head_links_product_page():
    html = render_hub.render_products(_products(), _family())
    assert 'href="plugins/"' in html
    assert "Meet the family" in html


# ─── founding (section 02) ───────────────────────────────────────────

def _founding():
    return {"eyebrow": "02 · The founding", "headline": "It started with a Nintendo",
            "quote": "I build tools, because care doesn't always scale",
            "paragraphs": ["<strong>First</strong> para.", "Second para."],
            "door": {"label": "Read the whole story", "href": "about.html"}}


def test_founding_renders_section_with_door():
    html = render_hub.render_founding(_founding())
    assert 'id="founding"' in html and 'href="about.html"' in html
    assert "Read the whole story" in html and "care doesn" in html


def test_founding_paragraphs_render_raw_html():
    assert "<strong>First</strong>" in render_hub.render_founding(_founding())


# ─── themes gallery (themes.html zone) ───────────────────────────────

def _make_theme(tmp_path, slug, **meta):
    d = tmp_path / "themes" / slug
    d.mkdir(parents=True)
    # render_themes_gallery only reads theme.json — tokens.css/archetypes/
    # completeness is theme_registry/theme-doctor's job, exercised in their
    # own test modules, not here.
    (d / "tokens.css").write_text("x", encoding="utf-8")
    base = {"name": slug.title(), "slug": slug, "thesis": f"{slug} thesis.", "month": "2026-08"}
    base.update(meta)
    (d / "theme.json").write_text(json.dumps(base), encoding="utf-8")


def test_themes_gallery_active_only_renders_one_live_card_linking_root(tmp_path):
    _make_theme(tmp_path, "phosphor-blueprint", name="Phosphor Blueprint",
                thesis="CRT phosphor kit.", month="2026-08")
    reg = {"active": "phosphor-blueprint", "queue": [], "archive": []}
    html = render_hub.render_themes_gallery(reg, root=tmp_path)
    assert html.count('class="theme-card ') == 1
    assert '<a class="theme-card live" href="/">' in html
    assert '<span class="theme-status live">Live</span>' in html
    assert "Phosphor Blueprint" in html and "CRT phosphor kit." in html
    assert "August 2026" in html


def test_themes_gallery_queued_theme_has_no_link_and_queued_chip(tmp_path):
    _make_theme(tmp_path, "phosphor-blueprint")
    _make_theme(tmp_path, "next-up", name="Next Up", thesis="Coming soon.")
    reg = {"active": "phosphor-blueprint", "queue": ["next-up"], "archive": []}
    html = render_hub.render_themes_gallery(reg, root=tmp_path)
    assert '<div class="theme-card queued">' in html
    assert '<span class="theme-status queued">Queued</span>' in html
    assert "Next Up" in html
    # No href anywhere pointing at a queued theme — it isn't live yet.
    assert 'href="/next-up' not in html


def test_themes_gallery_archived_theme_links_registry_url_and_month(tmp_path):
    _make_theme(tmp_path, "phosphor-blueprint")
    _make_theme(tmp_path, "old-look", name="Old Look", thesis="Retired now.", month="2026-07")
    reg = {
        "active": "phosphor-blueprint",
        "queue": [],
        "archive": [{"slug": "old-look", "month": "2026-08", "url": "/themes/archive/2026-08/"}],
    }
    html = render_hub.render_themes_gallery(reg, root=tmp_path)
    assert '<a class="theme-card archived" href="/themes/archive/2026-08/">' in html
    assert '<span class="theme-status archived">Archived</span>' in html
    # Registry month (when it was actually retired) wins over theme.json's
    # original month — the registry is the authoritative record.
    assert "August 2026" in html


def test_themes_gallery_archive_renders_newest_first(tmp_path):
    _make_theme(tmp_path, "phosphor-blueprint")
    _make_theme(tmp_path, "first-out", name="First Out")
    _make_theme(tmp_path, "second-out", name="Second Out")
    reg = {
        "active": "phosphor-blueprint",
        "queue": [],
        "archive": [
            {"slug": "first-out", "month": "2026-06", "url": "/themes/archive/2026-06/"},
            {"slug": "second-out", "month": "2026-07", "url": "/themes/archive/2026-07/"},
        ],
    }
    html = render_hub.render_themes_gallery(reg, root=tmp_path)
    assert html.index("Second Out") < html.index("First Out")


def test_themes_gallery_missing_theme_json_falls_back_to_slug_name(tmp_path):
    # Active theme dir exists (with theme.json) so the registry stays valid,
    # but an archived slug's source dir is gone entirely.
    _make_theme(tmp_path, "phosphor-blueprint")
    reg = {
        "active": "phosphor-blueprint",
        "queue": [],
        "archive": [{"slug": "long-gone", "month": "2026-05", "url": "/themes/archive/2026-05/"}],
    }
    html = render_hub.render_themes_gallery(reg, root=tmp_path)
    assert "Long Gone" in html


def test_themes_gallery_always_has_at_least_the_active_card(tmp_path):
    _make_theme(tmp_path, "phosphor-blueprint")
    reg = {"active": "phosphor-blueprint", "queue": [], "archive": []}
    html = render_hub.render_themes_gallery(reg, root=tmp_path)
    assert html.count('class="theme-card ') == 1


def test_real_themes_registry_renders_at_least_one_card():
    html = render_hub.render_themes_gallery(render_hub.theme_registry.load())
    assert html.count('class="theme-card ') >= 1
    assert '<span class="theme-status live">Live</span>' in html


def test_themes_gallery_card_has_no_thumbnail_when_none_captured(tmp_path):
    # capture_theme_screenshot (scripts/freeze-theme.py) is the only writer
    # of assets/themes/<slug>.png — a theme that hasn't been through a live
    # rotation yet has no file there, and the card must render cleanly
    # without an <img>, not a broken one.
    _make_theme(tmp_path, "phosphor-blueprint")
    reg = {"active": "phosphor-blueprint", "queue": [], "archive": []}
    html = render_hub.render_themes_gallery(reg, root=tmp_path)
    assert "<img" not in html


def test_themes_gallery_card_has_thumbnail_when_captured(tmp_path):
    _make_theme(tmp_path, "phosphor-blueprint", name="Phosphor Blueprint")
    thumbs = tmp_path / "assets" / "themes"
    thumbs.mkdir(parents=True)
    (thumbs / "phosphor-blueprint.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    reg = {"active": "phosphor-blueprint", "queue": [], "archive": []}
    html = render_hub.render_themes_gallery(reg, root=tmp_path)
    assert (
        '<img class="theme-thumb" src="/assets/themes/phosphor-blueprint.png" '
        'alt="Phosphor Blueprint thumbnail" loading="lazy" width="1440" height="900">'
    ) in html
    # The thumbnail is the first thing inside the card, before the head chips.
    assert html.index("theme-thumb") < html.index("theme-card-head")


def test_theme_thumbnail_href_none_when_missing(tmp_path):
    assert render_hub._theme_thumbnail_href("nope", tmp_path) is None


def test_theme_thumbnail_href_present_when_captured(tmp_path):
    thumbs = tmp_path / "assets" / "themes"
    thumbs.mkdir(parents=True)
    (thumbs / "phosphor-blueprint.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    assert (
        render_hub._theme_thumbnail_href("phosphor-blueprint", tmp_path)
        == "/assets/themes/phosphor-blueprint.png"
    )


# ─── About easter-egg theme registry (about.html "about-theme-toggle" zone) ─
#
# render_about_theme_dresses is the render-time source of truth A7's
# client-side toggle reads (about.html's own JSON <script id=
# "about-theme-registry">) -- it has to stay in lockstep with
# content/themes.json the same way render_themes_gallery already does for
# themes.html's cards, so it gets the same kind of pure-function coverage.


def _parse_about_dresses(payload: str) -> list[dict]:
    inner = payload.split(">", 1)[1].rsplit("<", 1)[0]
    return json.loads(inner)


def test_about_theme_dresses_default_is_always_first_with_no_css(tmp_path):
    _make_theme(tmp_path, "phosphor-blueprint")
    reg = {"active": "phosphor-blueprint", "queue": [], "archive": []}
    dresses = _parse_about_dresses(render_hub.render_about_theme_dresses(reg, root=tmp_path))
    assert dresses[0] == {"slug": "default", "label": "Long Now Terminal", "css": None}


def test_about_theme_dresses_includes_live_theme_with_reading_css_url(tmp_path):
    _make_theme(tmp_path, "phosphor-blueprint", name="Phosphor Blueprint")
    reg = {"active": "phosphor-blueprint", "queue": [], "archive": []}
    dresses = _parse_about_dresses(render_hub.render_about_theme_dresses(reg, root=tmp_path))
    assert dresses[1]["slug"] == "phosphor-blueprint"
    assert dresses[1]["label"] == "Phosphor Blueprint"
    assert dresses[1]["css"] == "/themes/phosphor-blueprint/archetypes/reading.css"


def test_about_theme_dresses_archive_newest_first(tmp_path):
    _make_theme(tmp_path, "phosphor-blueprint")
    _make_theme(tmp_path, "first-out", name="First Out")
    _make_theme(tmp_path, "second-out", name="Second Out")
    reg = {
        "active": "phosphor-blueprint",
        "queue": [],
        "archive": [
            {"slug": "first-out", "month": "2026-06", "url": "/themes/archive/2026-06/"},
            {"slug": "second-out", "month": "2026-07", "url": "/themes/archive/2026-07/"},
        ],
    }
    dresses = _parse_about_dresses(render_hub.render_about_theme_dresses(reg, root=tmp_path))
    assert [d["slug"] for d in dresses] == ["default", "phosphor-blueprint", "second-out", "first-out"]


def test_about_theme_dresses_queue_is_not_offered(tmp_path):
    # The brief is explicit: archived months, the live theme, and About's
    # own default -- approved-but-not-yet-live themes aren't offered for
    # public preview ahead of their own rotation.
    _make_theme(tmp_path, "phosphor-blueprint")
    _make_theme(tmp_path, "next-up", name="Next Up")
    reg = {"active": "phosphor-blueprint", "queue": ["next-up"], "archive": []}
    dresses = _parse_about_dresses(render_hub.render_about_theme_dresses(reg, root=tmp_path))
    slugs = [d["slug"] for d in dresses]
    assert slugs == ["default", "phosphor-blueprint"]
    assert "next-up" not in slugs


def test_about_theme_dresses_payload_is_a_self_contained_script_tag():
    payload = render_hub.render_about_theme_dresses(render_hub.theme_registry.load())
    assert payload.startswith('<script type="application/json" id="about-theme-registry">')
    assert payload.endswith("</script>")
    _parse_about_dresses(payload)  # raises if the embedded JSON is malformed


def test_real_about_theme_registry_offers_default_and_the_live_theme():
    reg = render_hub.theme_registry.load()
    dresses = _parse_about_dresses(render_hub.render_about_theme_dresses(reg))
    assert dresses[0]["slug"] == "default"
    assert any(d["slug"] == render_hub.theme_registry.active_slug(reg) for d in dresses)


# ─── main() guardrails (Fix 5) ─────────────────────────────────────────────
#
# Two failure-shaped bugs the whole-branch review caught: a missing theme
# shell used to fall back to reading the LIVE index.html as its own source
# (so `--check` would compare that file against itself and stay green
# forever, and a genuinely broken theme would render as a silent no-op
# instead of an error); and `--theme` without `--out` had no guard at all,
# so a typo'd invocation would render an arbitrary theme straight over the
# live site and every other surface it touches (feed, sitemap, story pages,
# themes.html).


def test_theme_without_out_is_a_usage_error(capsys):
    # This guard fires before anything touches the registry or the
    # filesystem, so it's safe to exercise against the real repo state.
    rc = render_hub.main(["--theme", "phosphor-blueprint"])
    assert rc != 0
    err = capsys.readouterr().err
    assert "--out" in err


def test_missing_archetype_fails_loudly_instead_of_falling_back_to_live_index(tmp_path, capsys):
    # A slug with no themes/<slug>/ directory at all under the real ROOT.
    # theme+out are paired (clears the first guard above) so this isolates
    # the missing-archetype guard; nothing is written since it errors first.
    # No shell.html fallback either (A4) — a missing archetype file is
    # always a loud error, never a silent render-around.
    rc = render_hub.main([
        "--theme", "definitely-not-a-real-theme-slug",
        "--out", str(tmp_path),
    ])
    assert rc != 0
    err = capsys.readouterr().err
    assert "archetype" in err.lower()
    assert "archetypes/home.html" in err
    assert "definitely-not-a-real-theme-slug" in err
    assert not (tmp_path / "index.html").exists()


# ─── theme-css zone: the hand-authored pages' stylesheet <link> ───────────
#
# thesis.html and workflow.html used to carry a private :root token block
# and a private copy of the theme's treatment layer, so a rotation could
# not reach them — they'd have kept July's colors into September while
# every other reading page moved on. They now resolve their stylesheet the
# same renderer-owned way press.html/privacy.html/themes.html do. These
# tests pin the wiring itself: the href has to be DERIVED from whatever
# content/themes.json currently says is active, never a literal slug.


def test_theme_css_map_covers_the_converted_reading_pages():
    m = render_hub.THEME_CSS_HREFS
    # The TOKEN half, never archetypes/reading.css. That file is the Long
    # Now Terminal dress about.html's theme picker wears; a page that links
    # a dress for its palette alone inherits every element rule the dress
    # ever grows. Split before it cost anything, unlike the product pair.
    assert m[render_hub.THESIS_HTML] == "archetypes/reading-tokens.css"
    assert m[render_hub.WORKFLOW_HTML] == "archetypes/reading-tokens.css"
    assert "archetypes/reading.css" not in m.values(), (
        "no page may link the reading DRESS; about.html reaches it through "
        "its own theme picker, which is not this map"
    )
    # the pre-existing three are unchanged by the rename
    assert m[render_hub.PRESS_HTML] == "archetypes/utility.css"
    assert m[render_hub.PRIVACY_HTML] == "archetypes/utility.css"
    assert m[render_hub.THEMES_HTML] == "tokens.css"


def _page_style(page):
    """Every <style> block on `page`, joined. Reading only the first one is a
    silent hole: three of these pages declare their treatment in a later
    block than their base rules."""
    import re

    return "\n".join(
        re.findall(r"<style[^>]*>(.*?)</style>", page.read_text(encoding="utf-8"), re.S)
    )


def _var_reads(css):
    """(name, has_fallback) for every var() in `css`, parens balanced so
    `var(--a, var(--b))` reports --a with a fallback AND --b without one."""
    import re

    out = []
    for m in re.finditer(r"var\(\s*(--[\w-]+)", css):
        depth, i, comma = 1, m.end(), False
        while i < len(css) and depth:
            if css[i] == "(":
                depth += 1
            elif css[i] == ")":
                depth -= 1
            elif css[i] == "," and depth == 1:
                comma = True
            i += 1
        out.append((m.group(1), comma))
    return out


# Every hand-authored page that resolves its palette from a theme file. Not
# just the product four: the C1 rule below is about the whole conversion.
CONVERTED_PAGES = (
    render_hub.PRESS_HTML, render_hub.PRIVACY_HTML,
    render_hub.THESIS_HTML, render_hub.WORKFLOW_HTML,
    render_hub.CONUNDRUM_HTML, render_hub.ROROROPLUGINS_HTML,
    render_hub.RORORO_HTML, render_hub.MODLAUNCHERGAMES_HTML,
    render_hub.ETSYMCP_HTML,
)


def test_no_converted_page_renders_broken_under_a_contract_satisfying_theme():
    """THE rule the whole conversion rests on: a theme that defines
    archetypes.REQUIRED_TOKENS exactly, and nothing else, must not break any
    page that gave up its private tokens.

    It could, and did. Every one of these pages had its --pb-* treatment
    tokens moved into the theme, where they are deliberately NOT part of the
    contract. A from-scratch theme satisfying all 47 required names passed
    theme-doctor --browser --require-browser — an unresolved var() logs no
    console error and causes no horizontal scroll — and would have rotated in
    unattended. Then `body { background: <gradients>, var(--pb-field) }` goes
    invalid-at-computed-value-time and resolves to TRANSPARENT, and five
    pages render light-grey text on browser-default white.

    So: every name a page reads must either be in the contract, be declared
    by the page itself, or carry a fallback. Checked by parsing rather than
    by rendering, so it is exhaustive rather than a spot check.
    """
    required = frozenset(render_hub.archetypes.REQUIRED_TOKENS)
    for page in CONVERTED_PAGES:
        style = _page_style(page)
        declared = {n for n, _ in
                    __import__("re").findall(r"(--[\w-]+)\s*:\s*([^;{}]+)", style)}
        unguarded = sorted({
            name for name, has_fallback in _var_reads(style)
            if not has_fallback and name not in required and name not in declared
        })
        assert not unguarded, (
            f"{page.name} reads {unguarded} with no fallback. None is in "
            f"REQUIRED_TOKENS, so a theme that satisfies the contract exactly "
            f"leaves the declaration invalid — transparent backgrounds, no "
            f"borders, unstyled text."
        )


def test_no_converted_page_overrides_a_contracted_token():
    """The other half of the same finding. A page that redefines --bg-0 or
    --border-1 after the theme's <link> is a page the rotation cannot reach:
    a new theme can define those names perfectly and still not touch it.
    That is the same "a copy no rotation can reach" defect the private :root
    blocks had, one indirection deeper.

    Page-local aliases are fine and are how the treatment survives — they
    just have to be page-local NAMES, not contracted ones.
    """
    import re

    required = frozenset(render_hub.archetypes.REQUIRED_TOKENS)
    for page in CONVERTED_PAGES:
        style = re.sub(r"/\*.*?\*/", "", _page_style(page), flags=re.S)
        shadowed = sorted({n for n, _ in re.findall(r"(--[\w-]+)\s*:\s*([^;{}]+)", style)
                           if n in required})
        assert not shadowed, (
            f"{page.name} redefines contracted token(s) {shadowed} after the "
            f"theme's stylesheet link — the rotation cannot reach them"
        )


def test_no_workflow_hand_enumerates_a_renderer_owned_page():
    """I1. render-hub.py rewrites ten hand-authored pages on every run, and
    both CI workflows have to name them to commit them. Those names were
    repeated in three places across two YAML files with nothing comparing
    them to THEME_CSS_HREFS — so adding an eleventh page meant the renderer
    rewrote it, --check passed because it WAS rendered, the commit step left
    it out, and the site moved to ten pages on the new theme and one on the
    old. A8 already found exactly that for press/privacy/about, after a
    rotation had run.

    Both lists come from `--list-renderer-owned-pages` now. This asserts the
    lists are DERIVED rather than merely correct-today: a page name appearing
    literally in either workflow's commands is the drift starting again.
    """
    import re

    owned = {p.name for p in render_hub.THEME_CSS_HREFS} | {render_hub.ABOUT_HTML.name}
    for wf in ("rebuild-hub.yml", "rotate-theme.yml"):
        text = (render_hub.ROOT / ".github" / "workflows" / wf).read_text(encoding="utf-8")
        # Comments explain; command lines act. Only the latter matter.
        commands = "\n".join(
            line for line in text.splitlines() if not line.lstrip().startswith("#")
        )
        assert "--list-renderer-owned-pages" in commands, (
            f"{wf} does not ask render-hub.py which pages it owns"
        )
        named = sorted(
            n for n in owned
            if re.search(r"(?<![\w/-])" + re.escape(n) + r"\b", commands)
        )
        assert not named, (
            f"{wf} hand-enumerates renderer-owned page(s) {named} — derive them "
            f"from `render-hub.py --list-renderer-owned-pages` instead"
        )


def test_list_renderer_owned_pages_is_every_page_the_renderer_rewrites(capsys):
    """...and the command has to actually emit them, or the workflows commit
    nothing. Posix paths, LF-terminated: a trailing CR reaches git as a
    different pathspec and `git add` dies with "did not match any files"."""
    rc = render_hub.main(["--list-renderer-owned-pages"])
    assert rc == 0
    out = capsys.readouterr().out
    listed = [line for line in out.split("\n") if line]
    expected = sorted(
        {p.relative_to(render_hub.ROOT).as_posix() for p in render_hub.THEME_CSS_HREFS}
        | {render_hub.ABOUT_HTML.relative_to(render_hub.ROOT).as_posix()}
    )
    assert listed == expected
    assert "\r" not in out


def test_browser_gate_serves_the_game_feed_from_a_committed_fixture():
    """mod-launcher-games.html renders its whole body from an off-origin
    manifest, so under third-party isolation the browser gate would grade
    only its fetch-failed fallback — the page with the most complex layout of
    the six, checked in its emptiest state. One fixture buys the populated
    layout back without reopening the network dependency.

    Pins that the fixture exists, parses, and is shaped like what the page
    validates (`schemaVersion === 1` and an array of games), because a
    fixture that silently stops matching leaves the gate quietly back where
    it started.
    """
    import importlib.util
    import json

    spec = importlib.util.spec_from_file_location(
        "theme_doctor_for_fixture_test", render_hub.ROOT / "scripts" / "theme-doctor.py"
    )
    td = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(td)

    assert "626-game-manifest" in td._OFF_ORIGIN_FIXTURES
    content_type, body = td._OFF_ORIGIN_FIXTURES["626-game-manifest"]
    assert content_type == "application/json"
    data = json.loads(body)
    assert data["schemaVersion"] == 1
    assert isinstance(data["games"], list) and data["games"]
    tiers = {g["tier"] for g in data["games"]}
    assert {"engine-curated", "nexus-only"} <= tiers, (
        "the fixture must exercise both game-row lists, not just one"
    )
    assert any(isinstance(g.get("featured"), int) for g in data["games"]), (
        "the fixture must populate the featured cover rail too"
    )


def test_every_stylesheet_a_page_links_is_one_the_doctor_token_checks():
    """The load-bearing invariant of the whole branch, and nothing asserted
    it. render-hub.py decides which stylesheet each bespoke page LINKS;
    theme-doctor.py decides which stylesheets get checked for token
    completeness. If those two sets ever drift apart, a page links a file
    the gate never grades and ships with unresolved var()s — green suite,
    broken page. Point one page at archetypes/reading.css by mistake and
    that is exactly what happens.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "theme_doctor_for_render_hub_test", render_hub.ROOT / "scripts" / "theme-doctor.py"
    )
    td = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(td)

    assert set(render_hub.THEME_CSS_HREFS.values()) == set(td.REQUIRED_TOKEN_CSS), (
        "the stylesheets bespoke pages link and the stylesheets the doctor "
        "checks for token completeness have drifted apart"
    )


# The bespoke product pages: hand-authored, each keeping its own layout,
# each linking the theme's product TOKEN file for its palette and nothing
# else. Kept as one list so a fifth page joins every test below at once
# instead of joining whichever ones someone remembered.
PRODUCT_TOKEN_PAGES = (
    render_hub.CONUNDRUM_HTML,
    render_hub.ROROROPLUGINS_HTML,
    render_hub.RORORO_HTML,
    render_hub.MODLAUNCHERGAMES_HTML,
)


def test_theme_css_map_covers_the_converted_product_pages():
    m = render_hub.THEME_CSS_HREFS
    # The TOKEN half, never archetypes/product.css. That file is the element
    # dress render-plugin-pages.py inlines into its own 15 generated pages;
    # its bare `body`/`a:hover`/`section.hero`/`.card`/`.btn` selectors land
    # on bespoke markup they were never written for. Pointing either page at
    # it once shipped a magenta hover underline onto 11 links across the two
    # pages that no resting-state gate could see. Measured again for the
    # second pair against their live DOM: the dress is 158 style rules
    # carrying 180 selectors, of which 31 match rororo.html and 20 match
    # mod-launcher-games.html — one `:root` (the vocabulary they want) plus
    # 30 and 19 dress selectors they do not.
    for page in PRODUCT_TOKEN_PAGES:
        assert m[page] == "archetypes/product-tokens.css"
    assert "archetypes/product.css" not in m.values(), (
        "no page may link the product DRESS; the dress is inlined by "
        "render-plugin-pages.py into markup it was written for"
    )


def test_theme_css_constants_agree_in_both_directions():
    # Only one direction of this pairing fails loudly. A page in
    # THEME_CSS_ONLY_PAGES but not in THEME_CSS_HREFS is a KeyError the
    # first time main() runs. The other direction is SILENT and is the one
    # that actually costs something: add a page to THEME_CSS_HREFS, forget
    # THEME_CSS_ONLY_PAGES, and main() never touches the page, --check never
    # reports it (the stale list is built from theme_css_pages, which is
    # built from THEME_CSS_ONLY_PAGES), and the page keeps whatever slug was
    # last hand-committed — the exact bug this whole zone exists to kill,
    # reintroduced by an omission no test would catch. So: set equality,
    # not membership.
    assert (
        set(render_hub.THEME_CSS_HREFS) - set(render_hub.THEME_CSS_MULTI_ZONE_PAGES)
        == set(render_hub.THEME_CSS_ONLY_PAGES)
    )
    # The exclusions are deliberate and are exactly the pages main() renders
    # in their own block, beside their other zones. A page listed in BOTH
    # tuples gets read from disk and written back by the theme-css loop
    # AFTER its own block wrote its other zones, silently reverting them —
    # so the two sets must not overlap either.
    assert not (
        set(render_hub.THEME_CSS_MULTI_ZONE_PAGES)
        & set(render_hub.THEME_CSS_ONLY_PAGES)
    )
    for page in render_hub.THEME_CSS_MULTI_ZONE_PAGES:
        assert page in render_hub.THEME_CSS_HREFS
    # Membership, not just consistency. Every assertion above stays true if
    # THESIS_HTML is moved into THEME_CSS_MULTI_ZONE_PAGES — and main()
    # then stops rendering its theme-css zone entirely, because that tuple
    # is the EXCLUSION list and thesis.html has no block of its own. The
    # exclusions are exactly the two pages main() renders in their own
    # block, and that is a fact worth stating rather than deriving.
    assert render_hub.THEME_CSS_MULTI_ZONE_PAGES == (
        render_hub.THEMES_HTML, render_hub.CONUNDRUM_HTML,
    )


def test_conundrum_keeps_its_gallery_zones_when_the_theme_css_zone_renders():
    # conundrum.html is the first page to carry the theme-css zone AND
    # renderer-owned content zones. main() renders it once, in its own
    # block; this pins that a full render leaves BOTH intact rather than
    # one overwriting the other.
    slug = render_hub.theme_registry.active_slug(render_hub.theme_registry.load())
    html = render_hub.CONUNDRUM_HTML.read_text(encoding="utf-8")
    assert (
        render_hub.render_theme_css_link(slug, "archetypes/product-tokens.css") in html
    )
    assert "<!-- SITE_JSON:conundrum-products:start -->" in html
    assert "<!-- SITE_JSON:conundrum-repo:start -->" in html
    assert 'class="merch-card"' in html


def test_preview_covers_every_theme_css_page_except_themes_html():
    # Derived, not enumerated — so a page added to THEME_CSS_HREFS is
    # previewable in the same commit rather than silently un-gateable
    # against a queued theme.
    assert (
        set(render_hub.PREVIEWABLE_THEME_CSS_PAGES)
        == set(render_hub.THEME_CSS_HREFS) - {render_hub.THEMES_HTML}
    )


def test_reading_pages_href_follows_the_active_slug_not_a_hardcoded_theme():
    for slug in ("phosphor-blueprint", "some-future-theme"):
        for page in (render_hub.THESIS_HTML, render_hub.WORKFLOW_HTML):
            link = render_hub.render_theme_css_link(
                slug, render_hub.THEME_CSS_HREFS[page]
            )
            assert link == (
                f'<link rel="stylesheet" '
                f'href="/themes/{slug}/archetypes/reading-tokens.css">'
            )


def test_reading_pages_carry_the_zone_and_track_the_registry_on_disk():
    slug = render_hub.theme_registry.load()["active"]
    expected = render_hub.render_theme_css_link(slug, "archetypes/reading-tokens.css")
    for page in (render_hub.THESIS_HTML, render_hub.WORKFLOW_HTML):
        html = page.read_text(encoding="utf-8")
        assert "<!-- SITE_JSON:theme-css:start -->" in html
        assert "<!-- SITE_JSON:theme-css:end -->" in html
        assert expected in html
        # substitute_zone is what main() runs; on a rendered tree it is a
        # no-op, which is exactly what render-hub.py --check asserts.
        assert render_hub.substitute_zone(html, "theme-css", expected) == html


def test_reading_pages_define_no_tokens_of_their_own():
    # The point of the conversion: the dress comes from the theme file, so
    # a page re-growing a private :root would silently opt back out of the
    # rotation while still passing every other check.
    import re

    for page in (render_hub.THESIS_HTML, render_hub.WORKFLOW_HTML):
        style = "\n".join(
            re.findall(r"<style[^>]*>(.*?)</style>", page.read_text(encoding="utf-8"), re.S)
        )
        assert not re.search(r":root\s*\{", style), f"{page.name} re-grew a :root block"


def test_reading_pages_own_their_scanline_overlay_rule():
    # The one rule the reading split handed back to the pages. Both carry a
    # .pb-scanlines element; the rule used to live in reading.css, which
    # they no longer link. A page with the element and no rule renders no
    # overlay at all — invisible to a token-completeness gate, and a real
    # pixel change. conundrum.html has always had it this way.
    #
    # Scanned as a RULE, not as a substring of raw markup — the same two
    # holes its product twin had: a plain substring check passes on
    # `/* .pb-scanlines lives in the theme now */`, which is exactly the
    # comment someone leaves while deleting the rule, and reading only the
    # first <style> block misses a rule declared in a later one.
    import re

    for page in (render_hub.THESIS_HTML, render_hub.WORKFLOW_HTML):
        html = page.read_text(encoding="utf-8")
        assert 'class="pb-scanlines"' in html, f"{page.name} lost the element"
        style = re.sub(r"/\*.*?\*/", "", _page_style(page), flags=re.S)
        assert re.search(r"(^|[\s,}])\.pb-scanlines\s*[,{]", style), (
            f"{page.name} carries a .pb-scanlines element but declares no rule "
            "for it — the theme no longer supplies one"
        )


def _unguarded_reads(text: str) -> set:
    """Every `var(--x)` in `text` that carries NO fallback.

    A read with a fallback cannot break a page: that is the whole point of the
    page-scoped `--page-*` aliases, which are written `var(--pb-x,
    var(--contracted))` so a theme without the private name still renders.
    Requiring those to resolve made both callers fail any theme whose private
    namespace was spelled differently — `--sx-*` instead of `--pb-*` — which
    is a taste in prefixes, not a defect, and pytest is a rotation gate.

    Balanced-paren scan, matching `check_theme_reads_only_what_it_defines`'s
    semantics in scripts/theme-doctor.py so the two cannot drift apart.
    """
    import re as _re

    body = _re.sub(r"/\*.*?\*/", "", text, flags=_re.S)
    out = set()
    for m in _re.finditer(r"var\(\s*(--[\w-]+)", body):
        depth, i, has_fallback = 1, m.end(), False
        while i < len(body) and depth:
            if body[i] == "(":
                depth += 1
            elif body[i] == ")":
                depth -= 1
            elif body[i] == "," and depth == 1:
                has_fallback = True
            i += 1
        if not has_fallback:
            out.add(m.group(1))
    return out



def test_a_guarded_var_read_is_not_required_to_resolve():
    """The property the two `resolve_every_var_they_read` tests rest on, tested
    directly — because against the LIVE theme those two pass either way. The
    mutation that matters (requiring guarded reads to resolve) only bites a
    theme whose private namespace is spelled differently, which is exactly the
    theme they were false-rejecting.

    `var(--a, var(--b))` guards `--a` and leaves `--b` unguarded in its own
    right; that is `check_theme_reads_only_what_it_defines`'s rule, mirrored
    here so the two cannot drift.
    """
    assert _unguarded_reads("x{color: var(--a, var(--b))}") == {"--b"}
    assert _unguarded_reads("x{color: var(--c)}") == {"--c"}
    assert _unguarded_reads("x{color: var(--d, #fff)}") == set()
    assert _unguarded_reads("/* var(--commented) */ x{color: var(--e)}") == {"--e"}

def test_reading_pages_resolve_every_var_they_read():
    # Their tokens now live in the theme, with no page-local fallback — so
    # an unresolved var() is a straight rendering break, not a stale value.
    #
    # The theme graded is whatever content/themes.json says is ACTIVE, never
    # a hardcoded slug. That is what makes this a rotation gate rather than
    # a museum piece: pytest runs inside rotate-theme.yml's gate stack AFTER
    # the registry flips to the incoming theme, so on the 1st this asserts
    # against the dress about to go live. Hardcoding "phosphor-blueprint"
    # would keep re-verifying the OUTGOING theme forever, passing happily
    # while the incoming one breaks both pages.
    import re

    slug = render_hub.theme_registry.active_slug(render_hub.theme_registry.load())
    css = (
        render_hub.ROOT / "themes" / slug / "archetypes" / "reading-tokens.css"
    ).read_text(encoding="utf-8")
    defined = set(re.findall(r"(--[\w-]+)\s*:", css))
    for page in (render_hub.THESIS_HTML, render_hub.WORKFLOW_HTML):
        # UNGUARDED reads only — a read with a fallback resolves by
        # construction. See _unguarded_reads.
        used = _unguarded_reads(page.read_text(encoding="utf-8"))
        assert not used - defined, (
            f"{page.name} reads {sorted(used - defined)}, undefined in "
            f"themes/{slug}/archetypes/reading-tokens.css"
        )


def test_product_pages_href_follows_the_active_slug_not_a_hardcoded_theme():
    for slug in ("phosphor-blueprint", "some-future-theme"):
        for page in PRODUCT_TOKEN_PAGES:
            link = render_hub.render_theme_css_link(
                slug, render_hub.THEME_CSS_HREFS[page]
            )
            assert link == (
                f'<link rel="stylesheet" '
                f'href="/themes/{slug}/archetypes/product-tokens.css">'
            )


def test_product_pages_carry_the_zone_and_track_the_registry_on_disk():
    slug = render_hub.theme_registry.load()["active"]
    expected = render_hub.render_theme_css_link(slug, "archetypes/product-tokens.css")
    for page in PRODUCT_TOKEN_PAGES:
        html = page.read_text(encoding="utf-8")
        assert "<!-- SITE_JSON:theme-css:start -->" in html
        assert "<!-- SITE_JSON:theme-css:end -->" in html
        assert expected in html
        assert render_hub.substitute_zone(html, "theme-css", expected) == html


def test_product_pages_define_no_token_of_their_own():
    # Same point as the reading pair, one shade weaker by necessity.
    # rororo-plugins.html defines no token at all. conundrum.html defines
    # three — the base tokens the Phosphor Blueprint treatment REPOINTS —
    # but every value has to resolve through a theme-owned name, never a
    # literal. A literal is a photocopy re-growing, and a photocopy is what
    # no rotation can reach.
    #
    # Scanned by DECLARATION, not by `:root {`. An earlier cut of this test
    # matched `:root\s*\{` alone, so a page re-growing its tokens under
    # `html {`, `body {`, or `[data-theme] {` passed clean while being just
    # as unreachable — a token is unreachable because it is page-local, not
    # because of which selector happens to hold it.
    import re

    def declarations(page):
        style = "\n".join(
            re.findall(r"<style[^>]*>(.*?)</style>", page.read_text(encoding="utf-8"), re.S)
        )
        style = re.sub(r"/\*.*?\*/", "", style, flags=re.S)
        return re.findall(r"(--[\w-]+)\s*:\s*([^;{}]+)", style)

    regrown = declarations(render_hub.ROROROPLUGINS_HTML)
    assert not regrown, (
        f"rororo-plugins.html re-grew page-local tokens: "
        f"{sorted(n for n, _ in regrown)}"
    )

    # The other three wear the Phosphor Blueprint treatment, so each keeps a
    # :root that REPOINTS --bg-0/--border-1/--border-2 at treatment names.
    # That is the page's own styling decision; a literal there would be the
    # photocopy growing back.
    for page in (render_hub.CONUNDRUM_HTML, render_hub.RORORO_HTML,
                 render_hub.MODLAUNCHERGAMES_HTML):
        for name, value in declarations(page):
            assert value.strip().startswith("var(--"), (
                f"{page.name} defines {name} as the literal {value.strip()!r} — "
                "a private copy the rotation cannot reach"
            )


def test_product_pages_own_their_scanline_overlay_rule():
    # The trap a token-completeness gate cannot see. archetypes/product.css
    # carries a `.pb-scanlines` rule, and every page here that shows the
    # overlay has an element with that class. None of them links the dress,
    # so the rule has to be the page's own — a page with the element and no
    # rule renders no overlay at all, and no token is missing to say so.
    # Same check the reading pair got after the split nearly deleted theirs.
    #
    # Scanned as a RULE, not as a substring of raw markup. A substring check
    # over un-stripped text passes on `/* .pb-scanlines lives in the theme
    # now */` — the exact comment someone would leave behind while deleting
    # the rule, which is the mutation this test exists to fail. It also has
    # to read every <style> block, not just the first: three of these four
    # pages declare the rule in a treatment section, and nothing guarantees
    # that section shares a block with the base styles forever.
    import re

    for page in PRODUCT_TOKEN_PAGES:
        html = page.read_text(encoding="utf-8")
        if 'class="pb-scanlines"' not in html:
            continue  # rororo-plugins.html is still on the pre-treatment dress
        style = re.sub(r"/\*.*?\*/", "", _page_style(page), flags=re.S)
        assert re.search(r"(^|[\s,}])\.pb-scanlines\s*[,{]", style), (
            f"{page.name} carries a .pb-scanlines element but declares no rule "
            "for it — the theme supplies tokens to these pages, not rules"
        )


def test_product_pages_resolve_every_var_they_read():
    # Their tokens now live in the theme, with no page-local fallback — so
    # an unresolved var() is a straight rendering break, not a stale value.
    # Graded against whatever content/themes.json says is ACTIVE, so inside
    # rotate-theme.yml's gate stack (which runs pytest AFTER the registry
    # flips) this asserts against the dress about to go live.
    import re

    slug = render_hub.theme_registry.active_slug(render_hub.theme_registry.load())
    css = (
        render_hub.ROOT / "themes" / slug / "archetypes" / "product-tokens.css"
    ).read_text(encoding="utf-8")
    defined = set(re.findall(r"(--[\w-]+)\s*:", css))
    for page in PRODUCT_TOKEN_PAGES:
        html = page.read_text(encoding="utf-8")
        used = _unguarded_reads(html)
        # A page may declare its own --page-* aliases (see the C1 fix); those
        # resolve locally by definition. Everything else has to come from the
        # theme.
        local = set(re.findall(r"(--[\w-]+)\s*:", _page_style(page)))
        assert not used - defined - local, (
            f"{page.name} reads {sorted(used - defined - local)}, undefined in "
            f"themes/{slug}/archetypes/product-tokens.css and not declared locally"
        )


def test_preview_mode_emits_the_theme_css_pages_too(tmp_path):
    # --theme/--out used to write index.html and nothing else, which left a
    # queued theme's effect on the hand-authored pages impossible to see or
    # gate before the 1st: their only theme-derived seam is the theme-css
    # <link>, and preview mode skipped the loop that rewrites it. Now every
    # PREVIEWABLE_THEME_CSS_PAGES member lands in out_dir with its zone
    # repointed — including conundrum.html, whose other zones preview mode
    # deliberately leaves alone (it previews a DRESS, not content).
    slug = render_hub.theme_registry.active_slug(render_hub.theme_registry.load())

    # Snapshot the LIVE pages before the run. Preview writes copies into
    # out_dir; if it ever also writes through to the repo tree, a preview of
    # a QUEUED theme would stamp that theme's slug into the live thesis.html
    # — shipping an unrotated dress from a command whose whole contract is
    # "touches nothing." Comparing bytes is the only assertion that catches
    # it; checking out_dir's contents cannot, and neither can the absence of
    # feed.xml/sitemap.xml below.
    before = {p: p.read_bytes() for p in render_hub.PREVIEWABLE_THEME_CSS_PAGES}
    before[render_hub.INDEX_HTML] = render_hub.INDEX_HTML.read_bytes()
    before[render_hub.THEMES_HTML] = render_hub.THEMES_HTML.read_bytes()

    rc = render_hub.main(["--theme", slug, "--out", str(tmp_path)])
    assert rc == 0
    assert (tmp_path / "index.html").exists()
    for page in render_hub.PREVIEWABLE_THEME_CSS_PAGES:
        written = tmp_path / page.name
        assert written.exists(), f"preview did not emit {page.name}"
        expected = render_hub.render_theme_css_link(
            slug, render_hub.THEME_CSS_HREFS[page]
        )
        assert expected in written.read_text(encoding="utf-8")

    for page, original in before.items():
        assert page.read_bytes() == original, (
            f"preview mode wrote back over the live {page.name} in the repo tree"
        )
    # And it renders only the page set, not the rest of the pipeline.
    assert not (tmp_path / "feed.xml").exists()
    assert not (tmp_path / "sitemap.xml").exists()


# ─── theme.json render opt-ins: railLimit + foundingBody ─────────────
# Both run unattended inside rotate-theme.yml on the 1st. The contract:
# a theme without the keys (phosphor-blueprint) renders exactly the
# pre-opt-in output; a theme with them gets the rail fold / body wrapper.

def _stories(n):
    return [{"title": f"Note {i}", "published": f"2026-0{1 + i // 9}-{1 + i % 9:02d}",
             "_filename": f"note-{i}.md"} for i in range(n)]


def test_render_opts_default_off_and_reject_bad_values(tmp_path):
    _make_theme(tmp_path, "plain")
    assert render_hub._theme_render_opts("plain", tmp_path) == {"railLimit": None, "foundingBody": False}
    _make_theme(tmp_path, "slate", railLimit=4, foundingBody=True)
    assert render_hub._theme_render_opts("slate", tmp_path) == {"railLimit": 4, "foundingBody": True}
    # bools, zero, negatives and strings are not a limit; a truthy non-True is not an opt-in
    for bad in (True, 0, -3, "4"):
        _make_theme(tmp_path, f"bad-{bad!r}".replace("'", ""), railLimit=bad, foundingBody="yes")
        opts = render_hub._theme_render_opts(f"bad-{bad!r}".replace("'", ""), tmp_path)
        assert opts == {"railLimit": None, "foundingBody": False}, bad
    assert render_hub._theme_render_opts("missing", tmp_path) == {"railLimit": None, "foundingBody": False}


def test_field_notes_rail_limit_folds_overflow_into_details_with_every_link():
    html = render_hub.render_field_notes(_stories(10), rail_limit=4)
    assert html.count('<article class="field-note">') == 10
    assert html.count('<details class="field-notes-more">') == 1
    assert "<summary>More Field Notes (6)</summary>" in html
    assert 'href="/editorial/"' not in html          # an expander, not a door out
    before, after = html.split("<details", 1)
    assert before.count('<article class="field-note">') == 4
    assert after.count('<article class="field-note">') == 6
    for i in range(10):
        assert f'href="https://626labs.dev/editorial/note-{i}/"' in html


def test_field_notes_without_rail_limit_emits_no_details():
    for html in (render_hub.render_field_notes(_stories(10)),
                 render_hub.render_field_notes(_stories(10), rail_limit=None),
                 render_hub.render_field_notes(_stories(3), rail_limit=4)):
        assert html.count('<article class="field-note">') in (10, 3)
        assert "<details" not in html and "More Field Notes" not in html


def test_founding_body_wrapper_is_opt_in():
    bare = render_hub.render_founding(_founding())
    assert "founding-body" not in bare
    assert bare == render_hub.render_founding(_founding(), {"foundingBody": False})
    wrapped = render_hub.render_founding(_founding(), {"foundingBody": True})
    assert '<div class="founding-body">' in wrapped
    assert wrapped.count("<p>") == bare.count("<p>") == 2
    assert wrapped.index("founding-body") < wrapped.index("<strong>First</strong>")
    assert wrapped.index("</div>") < wrapped.index('class="thinking-link"')
