"""The repo meter: a 26-week commit grid on every showcased project.

Spec: docs/superpowers/specs/2026-10-01-repo-meter-design.md. What these pin:
the renderers emit the EMPTY element exactly when a repo is known (never any
data, so the daily bot write cannot dirty --check); the meter's stylesheet
reads contract tokens only (so every theme dresses it without knowing it
exists); the data file keeps the shape meter.js reads; the bot workflow runs
the script and commits only the data file.
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import archetypes  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


render_hub = _load("render_hub_meter", ROOT / "scripts" / "render-hub.py")
plugin_pages = _load("render_plugin_pages_meter", ROOT / "scripts" / "render-plugin-pages.py")

METER_CSS = ROOT / "repo-meter" / "meter.css"
METER_JS = ROOT / "repo-meter" / "meter.js"
DATA = ROOT / "data" / "repo-activity.json"
WORKFLOW = ROOT / ".github" / "workflows" / "refresh-repo-activity.yml"


def _product(**over):
    base = {"id": "vibe-test", "title": "Vibe Test", "description": "d", "tags": []}
    base.update(over)
    return base


# ── renderers emit the empty element, and only the element ───────────────

def test_product_row_carries_a_meter_when_it_names_a_repo():
    html = render_hub.render_product(_product(repo="estevanhernandez-stack-ed/vibe-test"))
    assert 'class="repo-meter" data-repo="estevanhernandez-stack-ed/vibe-test"' in html
    assert 'aria-label="Commit activity for Vibe Test"' in html
    # empty: the browser fills it; nothing from the data file is rendered
    assert re.search(r'<div class="repo-meter"[^>]*></div>', html)


def test_product_row_without_a_repo_carries_no_meter():
    html = render_hub.render_product(_product())
    assert "repo-meter" not in html


def test_products_zone_links_the_meter_assets_once_and_only_with_a_repo():
    with_repo = render_hub.render_products([
        _product(id="a", repo="o/a"), _product(id="b", repo="o/b"),
    ])
    assert with_repo.count('href="/repo-meter/meter.css"') == 1
    assert with_repo.count('src="/repo-meter/meter.js"') == 1
    assert with_repo.index("repo-meter/meter.css") > with_repo.rindex("</article>")
    without = render_hub.render_products([_product(id="a"), _product(id="b")])
    assert "repo-meter" not in without


def test_product_row_escapes_the_repo_attribute():
    html = render_hub.render_product(_product(repo='o/a" onload="x'))
    assert 'onload="x' not in html
    assert "&quot;" in html


def test_plugin_page_hero_carries_the_meter_and_the_head_links_its_assets():
    data = json.loads((ROOT / "content" / "plugin-pages.json").read_text(encoding="utf-8"))
    pid, p = next(iter(data["plugins"].items()))
    p = dict(p, id=pid)
    hero = plugin_pages.render_hero(p)
    assert 'class="repo-meter" data-repo="' in hero
    assert re.search(r'<div class="repo-meter"[^>]*></div>', hero)
    head = plugin_pages.render_head(p)
    assert 'href="/repo-meter/meter.css"' in head and 'src="/repo-meter/meter.js"' in head


def test_plugin_meter_prefers_site_json_repo_over_plugin_repos():
    """vibe-keystone's commits land in the vibe-plugins monorepo (site.json);
    plugin-repos.json names the solo shipping repo. The meter is about
    activity, so site.json wins."""
    site = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
    products = site["products"]
    if isinstance(products, dict):
        products = products.get("items") or list(products.values())
    by_id = {p["id"]: p.get("repo") for p in products if isinstance(p, dict) and p.get("id")}
    for pid, repo in by_id.items():
        if repo and pid in plugin_pages.PLUGIN_METER_REPOS:
            assert plugin_pages.PLUGIN_METER_REPOS[pid] == repo


def test_no_rendered_page_bakes_activity_data():
    """The whole point of fetching at runtime: a bot write cannot dirty a
    render. A rendered meter is an empty div; no page carries an rm-grid."""
    for page in (ROOT / "index.html", ROOT / "vibe-cartographer" / "index.html"):
        if page.exists():
            assert "rm-grid" not in page.read_text(encoding="utf-8")


# ── the stylesheet reads contract tokens only ─────────────────────────────

def test_meter_css_reads_only_contract_tokens():
    css = re.sub(r"/\*.*?\*/", "", METER_CSS.read_text(encoding="utf-8"), flags=re.S)
    reads = set(re.findall(r"var\(\s*(--[\w-]+)", css))
    private = {"--rm-weeks"}  # set inline by meter.js on the grid itself
    foreign = reads - archetypes.REQUIRED_TOKENS - private
    assert not foreign, (
        f"meter.css reads {sorted(foreign)}, which no theme is required to define; "
        "the meter must dress itself from archetypes.REQUIRED_TOKENS only"
    )


def test_meter_css_declares_no_color_literal():
    css = re.sub(r"/\*.*?\*/", "", METER_CSS.read_text(encoding="utf-8"), flags=re.S)
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(", css)


def test_meter_js_fetches_the_data_file_and_fills_the_element():
    js = METER_JS.read_text(encoding="utf-8")
    assert "/data/repo-activity.json" in js
    assert ".repo-meter[data-repo]" in js
    assert "rm-grid" in js and "rm-sum" in js


def test_meter_js_leaves_an_unreadable_repo_empty():
    """Celestia3 is private: the runner's token 404s it and the bot lists it
    under `missing`. The first cut rendered 'no public activity in 26
    weeks' for it, which reads as a dead flagship. A repo the bot could not
    read renders NOTHING (the :empty element takes no height)."""
    js = METER_JS.read_text(encoding="utf-8")
    assert "no public activity" not in js
    assert 'setAttribute("data-filled", "skip")' in js


# ── the data file and the bot ─────────────────────────────────────────────

def test_activity_data_has_the_shape_meter_js_reads():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    assert set(d) >= {"fetchedAt", "windowDays", "repos", "missing"}
    assert d["windowDays"] == 182
    assert isinstance(d["missing"], list)
    for repo, rec in d["repos"].items():
        assert re.fullmatch(r"[\w.-]+/[\w.-]+", repo), repo
        assert set(rec) == {"days", "total", "lastCommit", "truncated"}, repo
        assert rec["total"] == sum(rec["days"].values()), repo
        for day, n in rec["days"].items():
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", day) and n > 0, (repo, day)
        assert rec["lastCommit"] == (max(rec["days"]) if rec["days"] else None), repo


def test_every_showcased_repo_is_in_the_data_file_or_listed_missing():
    """The bot derives its repo set from site.json, plugin-repos.json and the
    data-repo attributes in the root HTML; a renderer emitting a meter for a
    repo the bot never fetches would render 'no public activity' forever."""
    d = json.loads(DATA.read_text(encoding="utf-8"))
    known = set(d["repos"]) | set(d["missing"])
    site = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
    products = site["products"]
    if isinstance(products, dict):
        products = products.get("items") or list(products.values())
    wanted = {p["repo"] for p in products if isinstance(p, dict) and p.get("repo")}
    wanted |= set(plugin_pages.PLUGIN_METER_REPOS.values())
    for page in ROOT.glob("*.html"):
        wanted |= set(re.findall(r'data-repo="([^"\s]+/[^"\s]+)"', page.read_text(encoding="utf-8")))
    assert wanted <= known, sorted(wanted - known)


def test_bot_workflow_runs_the_script_and_commits_only_the_data_file():
    yml = WORKFLOW.read_text(encoding="utf-8")
    assert "node scripts/refresh-repo-activity.mjs" in yml
    assert "git add data/repo-activity.json" in yml
    assert "render-hub.py" not in yml and "render-plugin-pages.py" not in yml
    assert "git pull --rebase origin main" in yml
