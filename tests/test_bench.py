"""On the bench: the homepage strip of public repos ranked by recent commits.

Este's direction (2026-11-17): when a public repo is catching heat, build
heat included, the site should feature it. What these pin: the ranking is
commits first (bots already excluded upstream), visitors only break ties; an
excluded or too-quiet repo never appears; a repo the site already shows
links to its page and one it does not is marked as such; the renderer emits
an EMPTY element (the bot's daily write must never dirty --check); the
stylesheet reads contract tokens only, so every theme dresses it.
"""
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import archetypes  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


render_hub = _load("render_hub_bench", ROOT / "scripts" / "render-hub.py")

BENCH_CSS = ROOT / "repo-meter" / "bench.css"
BENCH_JS = ROOT / "repo-meter" / "bench.js"
DATA = ROOT / "data" / "bench.json"
WORKFLOW = ROOT / ".github" / "workflows" / "refresh-repo-activity.yml"

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def rank(args):
    js = (
        "import {rankBench} from './scripts/refresh-repo-activity.mjs';"
        f"console.log(JSON.stringify(rankBench({json.dumps(args)})))"
    )
    out = subprocess.run(["node", "--input-type=module", "-e", js], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def _args(**over):
    base = {
        "today": "2026-11-17",
        "config": {"count": 3, "windowDays": 14, "minCommits": 3, "exclude": []},
        "activity": {},
        "visitors": {},
        "catalog": {},
    }
    base.update(over)
    return base


# ── ranking ───────────────────────────────────────────────────────────────

@needs_node
def test_ranks_by_commits_inside_the_window_only():
    out = rank(_args(activity={
        "o/quiet": {"2026-11-16": 4},
        "o/busy": {"2026-11-10": 20, "2026-11-04": 5},
        # 40 commits, all before the window opens on 2026-11-04
        "o/old": {"2026-11-03": 40},
    }))
    assert [i["repo"] for i in out] == ["o/busy", "o/quiet"]
    assert out[0]["commits"] == 25 and out[0]["lastCommit"] == "2026-11-10"


@needs_node
def test_visitors_break_a_tie_and_never_outrank_commits():
    out = rank(_args(
        activity={"o/a": {"2026-11-16": 5}, "o/b": {"2026-11-16": 5}, "o/c": {"2026-11-16": 6}},
        visitors={"o/a": 1, "o/b": 90, "o/c": 0},
    ))
    assert [i["repo"] for i in out] == ["o/c", "o/b", "o/a"]


@needs_node
def test_a_repo_under_the_floor_or_excluded_never_appears():
    out = rank(_args(
        config={"count": 5, "windowDays": 14, "minCommits": 3, "exclude": ["O/Site"]},
        activity={"o/site": {"2026-11-16": 99}, "o/typo": {"2026-11-16": 2}, "o/real": {"2026-11-16": 3}},
    ))
    assert [i["repo"] for i in out] == ["o/real"]


@needs_node
def test_a_repo_outside_the_public_list_never_ranks():
    """A maintainer's own token reads private repos (Celestia3 is private by
    design) that the CI token 404s. The first local run of this bot put the
    flagship's private commit count in the strip. The public list decides,
    not what the token happened to see."""
    out = rank(_args(
        activity={"o/private": {"2026-11-16": 50}, "o/open": {"2026-11-16": 5}},
        publicRepos=["O/Open"],
    ))
    assert [i["repo"] for i in out] == ["o/open"]


@needs_node
def test_count_caps_the_list():
    act = {f"o/r{n}": {"2026-11-16": 10 + n} for n in range(6)}
    assert len(rank(_args(activity=act))) == 3


@needs_node
def test_a_featured_repo_takes_its_site_title_and_page_and_an_unknown_one_is_marked():
    out = rank(_args(
        activity={"o/app": {"2026-11-16": 9}, "o/new": {"2026-11-16": 8}},
        catalog={
            "o/app": {"title": "The App", "href": "/app.html", "blurb": "Does a thing.", "featured": True},
            "o/new": {"title": "new", "href": "https://github.com/o/new", "blurb": "Fresh.", "featured": False},
        },
    ))
    assert out[0] == {"repo": "o/app", "title": "The App", "href": "/app.html",
                      "blurb": "Does a thing.", "featured": True, "commits": 9,
                      "lastCommit": "2026-11-16"}
    assert out[1]["featured"] is False and out[1]["href"] == "https://github.com/o/new"


@needs_node
def test_a_repo_with_no_catalog_entry_falls_back_to_its_name_and_github():
    out = rank(_args(activity={"o/bare": {"2026-11-16": 4}}))
    assert out[0]["title"] == "bare"
    assert out[0]["href"] == "https://github.com/o/bare"
    assert out[0]["featured"] is False and out[0]["blurb"] == ""


@needs_node
def test_a_workflow_committing_as_the_actions_org_is_not_a_person():
    """6deux6 (a release-feed bot) commits its own state file as `actions`,
    which GitHub links to an ORGANIZATION account, not a Bot one. The first
    bench ranked it at 27 commits; 3 were a person's."""
    commits = [
        {"author": {"login": "actions", "type": "Organization"},
         "commit": {"author": {"name": "6deux6", "date": "2026-11-16T19:11:43Z"},
                    "committer": {"name": "6deux6"}}},
        {"author": {"login": "someone", "type": "User"},
         "commit": {"author": {"name": "Someone", "date": "2026-11-14T10:00:00Z"},
                    "committer": {"name": "GitHub"}}},
        {"author": {"login": "dependabot[bot]", "type": "Bot"},
         "commit": {"author": {"name": "dependabot[bot]", "date": "2026-11-14T11:00:00Z"},
                    "committer": {"name": "GitHub"}}},
        {"author": None,
         "commit": {"author": {"name": "github-actions", "date": "2026-11-14T12:00:00Z"},
                    "committer": {"name": "github-actions"}}},
    ]
    js = (
        "import {bucket} from './scripts/refresh-repo-activity.mjs';"
        f"console.log(JSON.stringify(bucket({json.dumps(commits)})))"
    )
    out = subprocess.run(["node", "--input-type=module", "-e", js], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    assert json.loads(out.stdout) == {"2026-11-14": 1}


# ── the renderer emits the empty element, and only the element ───────────

BENCH = {"enabled": True, "eyebrow": "On the bench", "note": "Most commits, last 14 days."}


def _product(**over):
    base = {"id": "a", "title": "A", "description": "d", "tags": []}
    base.update(over)
    return base


def test_products_zone_opens_with_the_empty_bench_and_links_its_assets_once():
    html = render_hub.render_products([_product(), _product(id="b")], None, BENCH)
    assert re.search(r'<div class="bench" data-bench[^>]*></div>', html)
    assert html.index('class="bench"') < html.index("<article")
    assert html.count('href="/repo-meter/bench.css"') == 1
    assert html.count('src="/repo-meter/bench.js"') == 1
    assert 'data-eyebrow="On the bench"' in html
    assert 'data-note="Most commits, last 14 days."' in html


def test_no_bench_block_or_a_disabled_one_renders_nothing():
    for bench in (None, {}, {**BENCH, "enabled": False}):
        html = render_hub.render_products([_product()], None, bench)
        assert "bench" not in html


def test_bench_attributes_are_escaped():
    html = render_hub.render_products([_product()], None, {**BENCH, "eyebrow": 'x" onload="y'})
    assert 'onload="y' not in html


def test_the_home_page_bakes_no_bench_data():
    page = ROOT / "index.html"
    text = page.read_text(encoding="utf-8")
    assert "bench-item" not in text
    site = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
    if (site.get("bench") or {}).get("enabled"):
        assert re.search(r'<div class="bench" data-bench[^>]*></div>', text)


# ── the stylesheet and the script ─────────────────────────────────────────

def test_bench_css_reads_only_contract_tokens():
    css = re.sub(r"/\*.*?\*/", "", BENCH_CSS.read_text(encoding="utf-8"), flags=re.S)
    reads = set(re.findall(r"var\(\s*(--[\w-]+)", css))
    private = {"--bench-share"}  # set inline by bench.js on each bar
    foreign = reads - archetypes.REQUIRED_TOKENS - private
    assert not foreign, f"bench.css reads {sorted(foreign)}, which no theme is required to define"


def test_bench_css_declares_no_color_literal():
    css = re.sub(r"/\*.*?\*/", "", BENCH_CSS.read_text(encoding="utf-8"), flags=re.S)
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(", css)


def test_bench_js_fetches_its_file_and_never_writes_html_from_it():
    """Titles and blurbs come from GitHub repo descriptions: text, not markup."""
    js = BENCH_JS.read_text(encoding="utf-8")
    assert "/data/bench.json" in js
    assert ".bench[data-bench]" in js
    assert "innerHTML" not in js
    assert "textContent" in js


# ── the data file and the bot ─────────────────────────────────────────────

def test_bench_data_has_the_shape_bench_js_reads():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    assert set(d) == {"generatedAt", "windowDays", "minCommits", "items"}
    commits = [i["commits"] for i in d["items"]]
    assert commits == sorted(commits, reverse=True)
    site = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
    cfg = site["bench"]
    assert len(d["items"]) <= cfg["count"]
    excluded = {r.lower() for r in cfg["exclude"]}
    for i in d["items"]:
        assert set(i) == {"repo", "title", "href", "blurb", "featured", "commits", "lastCommit"}
        assert re.fullmatch(r"[\w.-]+/[\w.-]+", i["repo"]), i
        assert i["repo"].lower() not in excluded
        assert i["commits"] >= d["minCommits"]
        assert i["href"].startswith(("/", "https://")), i


def test_bot_workflow_commits_the_bench_file_too_and_still_renders_nothing():
    yml = WORKFLOW.read_text(encoding="utf-8")
    assert "git add data/repo-activity.json data/bench.json" in yml
    assert "render-hub.py" not in yml
