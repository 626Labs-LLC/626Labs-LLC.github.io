#!/usr/bin/env python3
"""Which hand-authored product pages are behind their repo's releases?

A page that describes an app carries one marker per repo it was last checked
against:

    <meta name="release-reviewed" content="owner/repo@tag">

The tag is the newest release the page's claims were read against. Every
published, non-prerelease release of that repo that came out after the tag is
a release nobody has read the page against yet. Draft releases never count.
A tag's suffix is its family: a page marked `@v2.27.0-mac` sees only `-mac`
releases and a page marked `@v3.4.3` only unsuffixed ones, so two pages can
review one repo (Sanduhr's Mac and Windows pages).

The release notes are the feature log: this script only notices that a
release landed and points at its notes. Updating a page means reading those
notes, fixing any claim that changed, and moving the tag forward in the same
commit.

    python scripts/release-review.py              # report to stdout
    python scripts/release-review.py --out body.md  # also write the issue body

Prints `BEHIND=<n>` as its last line (the number of unread releases across
all pages). Exit 0 on a completed check, behind or not; 2 when the check
could not be made (a marker naming a tag the repo doesn't have, the API
failing). The daily workflow (`release-review.yml`) keeps one rolling issue
from the body, and closes it when nothing is behind.

`GITHUB_TOKEN` in the environment raises the API rate limit; public repos
need nothing more.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MARKER_RE = re.compile(
    r'<meta\s+name="release-reviewed"\s+content="([^"@\s]+/[^"@\s]+)@([^"\s]+)"\s*/?>'
)

# Release-note headings that say nothing about what the app does.
BOILERPLATE_HEADING_RE = re.compile(
    r"install|download|checksum|requirement|upgrad|known issue", re.I
)
FIX_HEADING_RE = re.compile(r"\bfix", re.I)

# Directories that hold no maintained page: frozen archives, design sheets,
# harvested assets, bundles.
SKIP_DIRS = {"themes", "Design", "assets", "node_modules", "apps", "docs", ".git"}


def find_markers(root: Path = ROOT) -> list[tuple[str, str, str]]:
    """Every (page, repo, tag) marker in the site's public pages."""
    found = []
    for path in sorted(root.rglob("*.html")):
        rel = path.relative_to(root)
        if rel.parts[0] in SKIP_DIRS:
            continue
        for repo, tag in MARKER_RE.findall(path.read_text(encoding="utf-8")):
            found.append((rel.as_posix(), repo, tag))
    return found


def is_fixes_only(body: str | None) -> bool:
    """True when the notes' only substantive headings are about fixes.

    A heuristic for priority, never for skipping: a fixes-only release is
    still listed, just marked as unlikely to change what a page claims. Notes
    with no headings at all are not fixes-only; nothing says they are.
    """
    headings = [
        h.strip()
        for h in re.findall(r"^#{1,6}\s+(.+)$", body or "", re.M)
        if not BOILERPLATE_HEADING_RE.search(h)
    ]
    return bool(headings) and all(FIX_HEADING_RE.search(h) for h in headings)


TAG_FAMILY_RE = re.compile(r"^v?\d+(?:\.\d+)+(?:-([A-Za-z][A-Za-z0-9]*))?$")


def tag_family(tag: str) -> str | None:
    """The tag's family: its suffix ("mac"), "" for a bare numeric tag, None
    when the tag is not a version at all. Two pages can mark one repo (the
    Sanduhr Mac and Windows pages); each sees only its own family."""
    m = TAG_FAMILY_RE.match(tag)
    if not m:
        return None
    return m.group(1) or ""


def releases_after(marker_tag: str, releases: list[dict]) -> list[dict]:
    """Published, non-prerelease releases newer than the marker's, newest first,
    in the marker's tag family when it has one (a marker outside the version
    pattern sees every family, as before).

    Raises KeyError when the marker's tag is not among the published
    releases: a typo'd or deleted tag must fail loudly, not read as
    "nothing behind".
    """
    published = [
        r for r in releases
        if not r.get("draft") and not r.get("prerelease") and r.get("published_at")
    ]
    by_tag = {r["tag_name"]: r for r in published}
    if marker_tag not in by_tag:
        raise KeyError(marker_tag)
    cutoff = by_tag[marker_tag]["published_at"]
    newer = [r for r in published if r["published_at"] > cutoff]
    family = tag_family(marker_tag)
    if family is not None:
        newer = [r for r in newer if tag_family(r["tag_name"]) == family]
    return sorted(newer, key=lambda r: r["published_at"], reverse=True)


def unwatched_releases(marker_tags: list[str], releases: list[dict]) -> list[dict]:
    """Published releases of one repo in a tag family none of its markers
    watch, newer than every marker, newest first. A page can only go stale
    silently when a release lands in a family no page reads; this names it.
    A marker outside the version pattern watches every family, so it has no
    strays; releases older than the newest marker are history."""
    families = {tag_family(t) for t in marker_tags}
    if None in families:
        return []
    published = [
        r for r in releases
        if not r.get("draft") and not r.get("prerelease") and r.get("published_at")
    ]
    by_tag = {r["tag_name"]: r for r in published}
    dates = [by_tag[t]["published_at"] for t in marker_tags if t in by_tag]
    if not dates:
        return []
    cutoff = max(dates)
    strays = [
        r for r in published
        if r["published_at"] > cutoff
        and tag_family(r["tag_name"]) is not None
        and tag_family(r["tag_name"]) not in families
    ]
    return sorted(strays, key=lambda r: r["published_at"], reverse=True)


def fetch_releases(repo: str) -> list[dict]:
    """The repo's 100 most recent releases (ample for a daily check)."""
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases?per_page=100",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "626labs-release-review"},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def generated_pages() -> set[str]:
    """Pages render-product-pages.py writes from content/site.json. Their
    claims and markers live in the entry's `pageSpec`; an edit to the HTML
    is overwritten by the next render, silently."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_release_review_product_pages", Path(__file__).resolve().parent / "render-product-pages.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return set(mod.generated_pages(ROOT))


def render_body(results: list[dict], generated: set[str] | None = None,
                strays: list[dict] | None = None) -> str:
    generated = generated_pages() if generated is None else generated
    behind = [r for r in results if r["releases"]]
    strays = [s for s in (strays or []) if s["releases"]]
    total = sum(len(r["releases"]) for r in behind) + sum(len(s["releases"]) for s in strays)
    lines = [
        f"{total} release{'s' if total != 1 else ''} landed since "
        f"{len(behind)} page{'s were' if len(behind) != 1 else ' was'} last checked.",
        "",
        "To clear a page: read each release's notes, fix any claim on the page that "
        "changed, and move its `release-reviewed` marker to the newest tag listed. "
        "Fixes-only releases rarely change a claim, but read the notes anyway.",
        "",
    ]
    for r in behind:
        lines.append(f"## `{r['page']}`, {r['repo']} (checked through `{r['tag']}`)")
        lines.append("")
        if r["page"] in generated:
            lines.append(
                "_Generated page: fix its claims and move its marker in `content/site.json` "
                "(the entry's `pageSpec`, marker under `releaseReviewed`), then run "
                "`scripts/render-product-pages.py`. A direct edit to the HTML is overwritten "
                "on the next render._"
            )
            lines.append("")
        for rel in r["releases"]:
            flag = " (fixes only)" if is_fixes_only(rel.get("body")) else ""
            date = rel["published_at"][:10]
            name = rel.get("name") or rel["tag_name"]
            lines.append(f"- [{name}]({rel['html_url']}), `{rel['tag_name']}`, {date}{flag}")
        lines.append("")
    for s in strays:
        watched = ", ".join(f"`-{f}`" if f else "bare `vX.Y.Z`" for f in s["watched"])
        lines.append(f"## {s['repo']}: releases in a tag family no page watches")
        lines.append("")
        lines.append(
            f"_This repo's pages watch {watched}. These landed in another family, so no page "
            "will ever list them as behind: either tag in a watched family, or move the "
            "marker of the page they belong to onto one of them in the same commit._"
        )
        lines.append("")
        for rel in s["releases"]:
            date = rel["published_at"][:10]
            name = rel.get("name") or rel["tag_name"]
            lines.append(f"- [{name}]({rel['html_url']}), `{rel['tag_name']}`, {date}")
        lines.append("")
    lines.append("_Maintained by `.github/workflows/release-review.yml`; closes itself when nothing is behind._")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, help="also write the issue body here")
    args = ap.parse_args(argv)

    markers = find_markers()
    if not markers:
        print("no release-reviewed markers found", file=sys.stderr)
        return 2

    cache: dict[str, list[dict]] = {}
    results = []
    for page, repo, tag in markers:
        try:
            if repo not in cache:
                cache[repo] = fetch_releases(repo)
            newer = releases_after(tag, cache[repo])
        except KeyError:
            print(f"{page}: {repo} has no published release tagged {tag}", file=sys.stderr)
            return 2
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"{page}: could not read {repo}'s releases: {exc}", file=sys.stderr)
            return 2
        results.append({"page": page, "repo": repo, "tag": tag, "releases": newer})
        state = f"{len(newer)} behind" if newer else "current"
        print(f"{page}  {repo}@{tag}  {state}")
        for rel in newer:
            flag = "  (fixes only)" if is_fixes_only(rel.get("body")) else ""
            print(f"    {rel['tag_name']}  {rel['published_at'][:10]}{flag}")

    # Releases in a tag family none of a repo's markers watch: the one way a
    # page goes stale with no signal under the family rule.
    by_repo: dict[str, list[str]] = {}
    for _, repo, tag in markers:
        by_repo.setdefault(repo, []).append(tag)
    strays = []
    for repo, tags in by_repo.items():
        unwatched = unwatched_releases(tags, cache[repo])
        if unwatched:
            watched = sorted({f for f in (tag_family(t) for t in tags) if f is not None})
            strays.append({"repo": repo, "watched": watched, "releases": unwatched})
            print(f"{repo}  {len(unwatched)} release(s) in a tag family no page watches (pages watch: {watched})")
            for rel in unwatched:
                print(f"    {rel['tag_name']}  {rel['published_at'][:10]}")

    total = sum(len(r["releases"]) for r in results) + sum(len(s["releases"]) for s in strays)
    if args.out:
        args.out.write_text(render_body(results, strays=strays), encoding="utf-8")
    print(f"BEHIND={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
