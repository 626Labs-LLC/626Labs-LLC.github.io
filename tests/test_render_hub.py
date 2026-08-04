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
    assert m[render_hub.THESIS_HTML] == "archetypes/reading.css"
    assert m[render_hub.WORKFLOW_HTML] == "archetypes/reading.css"
    # the pre-existing three are unchanged by the rename
    assert m[render_hub.PRESS_HTML] == "archetypes/utility.css"
    assert m[render_hub.PRIVACY_HTML] == "archetypes/utility.css"
    assert m[render_hub.THEMES_HTML] == "tokens.css"


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
        set(render_hub.THEME_CSS_HREFS) - {render_hub.THEMES_HTML}
        == set(render_hub.THEME_CSS_ONLY_PAGES)
    )
    # themes.html is the one deliberate exclusion — main() handles it next
    # to its gallery zone, not in this loop.
    assert render_hub.THEMES_HTML not in render_hub.THEME_CSS_ONLY_PAGES
    assert render_hub.THEMES_HTML in render_hub.THEME_CSS_HREFS


def test_reading_pages_href_follows_the_active_slug_not_a_hardcoded_theme():
    for slug in ("phosphor-blueprint", "some-future-theme"):
        for page in (render_hub.THESIS_HTML, render_hub.WORKFLOW_HTML):
            link = render_hub.render_theme_css_link(
                slug, render_hub.THEME_CSS_HREFS[page]
            )
            assert link == (
                f'<link rel="stylesheet" href="/themes/{slug}/archetypes/reading.css">'
            )


def test_reading_pages_carry_the_zone_and_track_the_registry_on_disk():
    slug = render_hub.theme_registry.load()["active"]
    expected = render_hub.render_theme_css_link(slug, "archetypes/reading.css")
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
        render_hub.ROOT / "themes" / slug / "archetypes" / "reading.css"
    ).read_text(encoding="utf-8")
    defined = set(re.findall(r"(--[\w-]+)\s*:", css))
    for page in (render_hub.THESIS_HTML, render_hub.WORKFLOW_HTML):
        used = set(re.findall(r"var\(\s*(--[\w-]+)", page.read_text(encoding="utf-8")))
        assert not used - defined, (
            f"{page.name} reads {sorted(used - defined)}, undefined in "
            f"themes/{slug}/archetypes/reading.css"
        )


def test_preview_mode_emits_the_theme_css_pages_too(tmp_path):
    # --theme/--out used to write index.html and nothing else, which left a
    # queued theme's effect on the hand-authored pages impossible to see or
    # gate before the 1st: their only theme-derived seam is the theme-css
    # <link>, and preview mode skipped the loop that rewrites it. Now every
    # THEME_CSS_ONLY_PAGES member lands in out_dir with its zone repointed.
    slug = render_hub.theme_registry.active_slug(render_hub.theme_registry.load())

    # Snapshot the LIVE pages before the run. Preview writes copies into
    # out_dir; if it ever also writes through to the repo tree, a preview of
    # a QUEUED theme would stamp that theme's slug into the live thesis.html
    # — shipping an unrotated dress from a command whose whole contract is
    # "touches nothing." Comparing bytes is the only assertion that catches
    # it; checking out_dir's contents cannot, and neither can the absence of
    # feed.xml/sitemap.xml below.
    before = {p: p.read_bytes() for p in render_hub.THEME_CSS_ONLY_PAGES}
    before[render_hub.INDEX_HTML] = render_hub.INDEX_HTML.read_bytes()

    rc = render_hub.main(["--theme", slug, "--out", str(tmp_path)])
    assert rc == 0
    assert (tmp_path / "index.html").exists()
    for page in render_hub.THEME_CSS_ONLY_PAGES:
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
