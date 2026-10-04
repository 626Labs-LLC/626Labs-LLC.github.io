#!/usr/bin/env python3
"""Which hand-authored product pages are behind their repo's releases?

A page that describes an app carries one marker per repo it was last checked
against:

    <meta name="release-reviewed" content="owner/repo@tag">

The tag is the newest release the page's claims were read against. Every
published, non-prerelease release of that repo that came out after the tag is
a release nobody has read the page against yet. Draft releases never count.

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


def releases_after(marker_tag: str, releases: list[dict]) -> list[dict]:
    """Published, non-prerelease releases newer than the marker's, newest first.

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
    return sorted(newer, key=lambda r: r["published_at"], reverse=True)


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


def render_body(results: list[dict]) -> str:
    behind = [r for r in results if r["releases"]]
    total = sum(len(r["releases"]) for r in behind)
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
        for rel in r["releases"]:
            flag = " (fixes only)" if is_fixes_only(rel.get("body")) else ""
            date = rel["published_at"][:10]
            name = rel.get("name") or rel["tag_name"]
            lines.append(f"- [{name}]({rel['html_url']}), `{rel['tag_name']}`, {date}{flag}")
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

    total = sum(len(r["releases"]) for r in results)
    if args.out:
        args.out.write_text(render_body(results), encoding="utf-8")
    print(f"BEHIND={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
