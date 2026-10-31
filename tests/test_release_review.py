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


def test_the_marked_pages_carry_a_marker():
    pages = {page for page, _, _ in rr.find_markers()}
    assert {"sanduhr/index.html", "sanduhr/windows/index.html", "rororo.html", "mod-launcher-games.html"} <= pages


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


# Two pages can mark one repo (Sanduhr's Mac page at v2.x-mac, its Windows
# page at bare v3.x). A marker's tag suffix is its family; it sees only that.
FAMILIES = [
    rel("v3.5.0", "2026-10-19T12:00:00Z"),  # a Windows release newer than every Mac one
    rel("v2.27.0-mac", "2026-10-18T00:41:16Z"),
    rel("v2.26.1-mac", "2026-10-17T12:00:00Z"),
    rel("v2.26.0-mac", "2026-10-16T12:00:00Z"),
    rel("v3.4.3", "2026-10-11T15:36:06Z"),
    rel("v3.4.2", "2026-09-14T12:00:00Z"),
    rel("v3.3.0.0", "2026-07-19T12:00:00Z"),
    rel("v2.3.0-windows", "2026-05-06T12:00:00Z"),
    rel("legacy/python-v2.3.0", "2026-09-13T12:00:00Z"),
]


@pytest.mark.parametrize("tag,family", [
    ("v2.27.0-mac", "mac"), ("v2.3.0-windows", "windows"), ("v3.4.3", ""),
    ("v3.3.0.0", ""), ("3.4.3", ""), ("v1", None), ("legacy/python-v2.3.0", None),
    ("untagged-c6478f02e761a516871a", None),
])
def test_tag_family(tag, family):
    assert rr.tag_family(tag) == family


def test_a_suffixed_marker_sees_only_its_own_family():
    # The Mac page must not be flagged by v3.4.3.
    assert [r["tag_name"] for r in rr.releases_after("v2.26.0-mac", FAMILIES)] == ["v2.27.0-mac", "v2.26.1-mac"]


def test_a_bare_marker_sees_bare_and_four_part_tags_only():
    assert [r["tag_name"] for r in rr.releases_after("v3.4.2", FAMILIES)] == ["v3.5.0", "v3.4.3"]
    # v3.3.0.0 is the same family, older by date, so absent for the right reason.
    assert [r["tag_name"] for r in rr.releases_after("v3.3.0.0", FAMILIES)] == ["v3.5.0", "v3.4.3", "v3.4.2"]


def test_a_marker_outside_the_pattern_keeps_date_only_behavior():
    assert [r["tag_name"] for r in rr.releases_after("legacy/python-v2.3.0", FAMILIES)] == [
        "v3.5.0", "v2.27.0-mac", "v2.26.1-mac", "v2.26.0-mac", "v3.4.3", "v3.4.2"]


def test_releases_in_a_family_no_page_watches_are_reported():
    # Sanduhr's Windows tags went bare in June; if one came back as -windows,
    # neither marker's family would see it and the page would go stale with
    # no signal. The bot names such releases instead of ignoring them.
    stray = rel("v3.5.0-windows", "2026-10-20T00:00:00Z")
    out = rr.unwatched_releases(["v2.26.0-mac", "v3.4.2"], FAMILIES + [stray])
    assert [r["tag_name"] for r in out] == ["v3.5.0-windows"]
    # v2.3.0-windows predates every marker: history, not a stray.
    assert rr.unwatched_releases(["v2.26.0-mac", "v3.4.2"], FAMILIES) == []
    # A marker outside the version pattern watches every family.
    assert rr.unwatched_releases(["legacy/python-v2.3.0"], FAMILIES + [stray]) == []


def test_body_names_the_unwatched_family():
    strays = [{"repo": "o/r", "watched": ["mac", ""], "releases": [rel("v3.5.0-windows", "2026-10-20T00:00:00Z")]}]
    body = rr.render_body([], generated=set(), strays=strays)
    assert body.startswith("1 release landed")
    assert "no page watches" in body and "`v3.5.0-windows`" in body and "o/r" in body


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


def test_a_generated_page_is_told_where_its_edits_go():
    # sanduhr/ has been generated since 2026-10-17: a reviewer who edits its
    # HTML loses the edit on the next render, so the issue says where to go.
    results = [
        {"page": "sanduhr/index.html", "repo": "o/s", "tag": "v1",
         "releases": [{"tag_name": "v2", "name": "v2", "published_at": "2026-10-16T00:00:00Z", "html_url": "u", "body": "x"}]},
        {"page": "rororo.html", "repo": "o/r", "tag": "v1",
         "releases": [{"tag_name": "v2", "name": "v2", "published_at": "2026-10-16T00:00:00Z", "html_url": "u", "body": "x"}]},
    ]
    body = rr.render_body(results, generated={"sanduhr/index.html"})
    sanduhr, rororo = body.split("## `rororo.html`")
    assert "Generated page" in sanduhr and "pageSpec" in sanduhr
    assert "Generated page" not in rororo
    assert "sanduhr/index.html" in rr.generated_pages()


def test_a_tag_with_no_release_above_the_marker_is_listed():
    # Sanduhr v4.0.0 was tagged and shipped with no GitHub release; the
    # Windows page was checked through v3.9.1 and the bot listed only 4.0.1.
    releases = [rel("v4.0.1", "2026-10-29T00:00:00Z"), rel("v3.9.1", "2026-10-24T00:00:00Z"),
                rel("v2.37.0-mac", "2026-10-29T00:00:00Z"),
                rel("v4.1.0", "2026-10-30T00:00:00Z", prerelease=True),
                rel("v4.2.0", None, draft=True)]
    tags = ["v4.2.0", "v4.1.0", "v4.0.1", "v4.0.0", "v3.9.1", "v3.8.5", "v2.38.0-mac",
            "untagged-c6478f02e761a516871a", "legacy/python-v2.3.0"]
    # A draft counts as unreleased; a prerelease is deliberate; v3.8.5 is
    # below the marker; the -mac tag is another family; non-versions skip.
    assert rr.unreleased_tags("v3.9.1", tags, releases) == ["v4.2.0", "v4.0.0"]
    assert rr.unreleased_tags("v4.0.1", tags, releases) == ["v4.2.0"]
    assert rr.unreleased_tags("v2.37.0-mac", tags, releases) == ["v2.38.0-mac"]
    assert rr.unreleased_tags("legacy/python-v2.3.0", tags, releases) == []


def test_body_lists_an_unreleased_tag_and_counts_it():
    results = [{"page": "w.html", "repo": "o/s", "tag": "v3.9.1",
                "releases": [rel("v4.0.1", "2026-10-29T00:00:00Z")], "unreleased": ["v4.0.0"]},
               {"page": "x.html", "repo": "o/t", "tag": "v1", "releases": [], "unreleased": ["v2.0.0"]}]
    body = rr.render_body(results, generated=set())
    assert body.startswith("3 releases landed since 2 pages were last checked.")
    assert "`v4.0.0`, tagged with no GitHub release" in body and "o/s/tree/v4.0.0" in body
    assert "x.html" in body


@pytest.mark.parametrize("page,repo,tag", rr.find_markers())
def test_a_release_search_link_tracks_its_markers_major(page, repo, tag):
    # The Sanduhr Windows page links releases?q=v4 because the repo's latest
    # release is the Mac build. A hardcoded major hides every 5.x build the
    # day it ships; moving the marker to 5.x without the link fails here.
    html = (ROOT / page).read_text(encoding="utf-8")
    majors = set(re.findall(rf"github\.com/{re.escape(repo)}/releases\?q=v(\d+)\b", html))
    if not majors or rr.tag_family(tag) is None:
        return
    assert majors == {str(rr.version_key(tag)[0])}, (
        f"{page} searches releases for v{sorted(majors)} but is marked {tag}")
