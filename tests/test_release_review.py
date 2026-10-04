"""Release review: product pages carry the release they were last checked against.

What these pin: the marker parses and every marker names a repo its own page
links to; a typo'd tag fails loudly instead of reading as "nothing behind";
drafts and prereleases never count; the fixes-only flag only lowers priority
(the release is still listed); and the workflow never commits.
"""
import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location("release_review", ROOT / "scripts" / "release-review.py")
rr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rr)

WORKFLOW = ROOT / ".github" / "workflows" / "release-review.yml"


def rel(tag, when, draft=False, prerelease=False, body=""):
    return {
        "tag_name": tag, "name": tag, "published_at": when, "draft": draft,
        "prerelease": prerelease, "body": body,
        "html_url": f"https://github.com/o/r/releases/tag/{tag}",
    }


RELEASES = [
    rel("v3", "2026-10-03T00:00:00Z"),
    rel("v2", "2026-10-02T00:00:00Z"),
    rel("v1", "2026-10-01T00:00:00Z"),
    rel("v4-rc", "2026-10-04T00:00:00Z", prerelease=True),
    rel("v5", None, draft=True),
]


def test_the_three_pages_carry_a_marker():
    pages = {page for page, _, _ in rr.find_markers()}
    assert {"sanduhr/index.html", "rororo.html", "mod-launcher-games.html"} <= pages


@pytest.mark.parametrize("page,repo,tag", rr.find_markers())
def test_each_marker_names_a_repo_its_page_links(page, repo, tag):
    html = (ROOT / page).read_text(encoding="utf-8")
    assert f"github.com/{repo}" in html or f'data-repo="{repo}"' in html, (
        f"{page} is marked against {repo} but never links it"
    )
    assert re.fullmatch(r"[\w.\-]+", tag), tag


def test_releases_after_lists_newer_published_ones_newest_first():
    assert [r["tag_name"] for r in rr.releases_after("v1", RELEASES)] == ["v3", "v2"]
    assert rr.releases_after("v3", RELEASES) == []


def test_a_marker_tag_the_repo_lacks_fails_loudly():
    with pytest.raises(KeyError):
        rr.releases_after("v9", RELEASES)
    # A draft or prerelease tag is not a published release either.
    with pytest.raises(KeyError):
        rr.releases_after("v4-rc", RELEASES)


@pytest.mark.parametrize("body,expected", [
    ("## Fixes\n- a\n\n## Install\nget it", True),
    ("## Bug fixes\n- a", True),
    ("## Sign out\nnew\n\n## Fixes\n- a", False),
    ("Just prose, no headings.", False),
    ("", False),
    (None, False),
])
def test_fixes_only(body, expected):
    assert rr.is_fixes_only(body) is expected


def test_body_lists_every_unread_release_and_flags_fixes_only():
    results = [
        {"page": "a.html", "repo": "o/r", "tag": "v1",
         "releases": [rel("v3", "2026-10-03T00:00:00Z", body="## Fixes\n- x"),
                      rel("v2", "2026-10-02T00:00:00Z", body="## New\n- y")]},
        {"page": "b.html", "repo": "o/s", "tag": "v1", "releases": []},
    ]
    body = rr.render_body(results)
    assert body.startswith("2 releases landed since 1 page was last checked.")
    assert "`v3`, 2026-10-03 (fixes only)" in body
    assert "`v2`, 2026-10-02\n" in body
    assert "b.html" not in body


def test_workflow_never_commits_and_never_runs_on_pull_requests():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "git push" not in text and "git commit" not in text
    assert "pull_request" not in text
    assert "contents: read" in text
