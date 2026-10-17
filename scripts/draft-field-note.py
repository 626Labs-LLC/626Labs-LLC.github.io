"""Draft a Field Note from a product's newest release, through the Claude API.

    python scripts/draft-field-note.py <product-id>              # newest release
    python scripts/draft-field-note.py <product-id> --tag v1.2.0 # a specific one
    python scripts/draft-field-note.py <product-id> --dry-run    # show the prompt, no API call
    python scripts/draft-field-note.py sanduhr --since 2026-10-01 --match='-mac$'
                                     # every release since a date, one note
                                     # (`--match=`: a value starting with - needs the = form)

The API counterpart of the repo-local /announce skill, for the site Field Note
only. It reads the same sources so the two never drift: the product entry in
content/site.json, the release resolved through render-hub's SHIELDS_RELEASE
mapping (the badges' mapping), the Field Note template and per-channel voice in
.claude/skills/announce/references/, and the canonical banned list in
626labs-marketing/docs/banned.md.

Two differences from /announce, both on purpose:
- The draft is ALWAYS `draft: true`. Unreviewed model writing never publishes
  on a push; `site.py story publish <slug>` is the human step.
- The model returns only title / subtitle / tagline / body (structured output).
  The script writes the frontmatter itself, so the publishing fence and the
  date can't come back malformed.

Credentials: ANTHROPIC_API_KEY_SCRIPTS locally, a name Claude Code doesn't
read, so a machine-wide key can't switch Claude Code from the Max plan login
to per-use API billing. Without it, the SDK's own resolution (ANTHROPIC_API_KEY,
or Workload Identity Federation variables in CI). Needs `pip install anthropic` (not in
requirements.txt: CI never runs this). Prints no credential.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
STORIES = ROOT / "content" / "stories"
ANNOUNCE_REFS = ROOT / ".claude" / "skills" / "announce" / "references"
BANNED = ROOT.parent / "626labs-marketing" / "docs" / "banned.md"
# One published launch-shaped note, for register and HTML shape only.
EXEMPLAR = STORIES / "2026-07-03-rororo-grew-a-family.md"

MODEL = "claude-opus-5-5"

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Launch headline. Punchy, specific, sentence case."},
        "subtitle": {"type": "string", "description": "One sentence: what it does, for whom."},
        "tagline": {"type": "string", "description": "Short kicker."},
        "body_html": {
            "type": "string",
            "description": "The note body as HTML: <p>, <h2>, <strong>, <em>, <code>, <a href>. No <figure>, no <img>, no frontmatter.",
        },
    },
    "required": ["title", "subtitle", "tagline", "body_html"],
    "additionalProperties": False,
}


def _render_hub():
    """render-hub.py as a module, for SHIELDS_RELEASE. Its name has a hyphen,
    so it is loaded by path; scripts/ goes on sys.path for its sibling import."""
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("render_hub", SCRIPTS / "render-hub.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def find_product(pid: str) -> dict:
    site = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
    products = site.get("products", [])
    for p in products:
        if p.get("id") == pid:
            return p
    ids = ", ".join(p.get("id", "?") for p in products)
    sys.exit(f"no product '{pid}' in content/site.json. Known ids: {ids}")


def _gh_json(*args: str):
    out = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        return None
    return json.loads(out.stdout)


def _release_source(product: dict) -> tuple[str, str] | None:
    """(repo, tag prefix) by the /announce resolution order (SKILL.md step 2):
    SHIELDS_RELEASE entry, then the vibe-plugins monorepo prefix, then the
    product's own repo. None means no release to draft from, which is
    expected for some products."""
    pid = product["id"]
    entry = _render_hub().SHIELDS_RELEASE.get(pid, {})
    if entry.get("hide"):
        return None
    repo, prefix = entry.get("repo"), (entry.get("filter") or "").rstrip("*")
    if not repo:
        repo = product.get("repo")
        if repo == "estevanhernandez-stack-ed/vibe-plugins":
            prefix = f"{pid}-v"
    return (repo, prefix) if repo else None


def resolve_releases_since(product: dict, since: str, match: str | None) -> dict | None:
    """Every published, non-prerelease release on or after `since` (and whose
    tag matches the `match` regex, if given), folded into one release-shaped
    dict so the prompt and renderer stay single-path. None when nothing
    qualifies."""
    src = _release_source(product)
    if not src:
        return None
    repo, prefix = src
    listed = _gh_json("release", "list", "--repo", repo, "-L", "100",
                      "--json", "tagName,publishedAt,isPrerelease") or []
    tags = [r["tagName"] for r in listed
            if not r["isPrerelease"] and r["publishedAt"][:10] >= since
            and r["tagName"].startswith(prefix)
            and (not match or re.search(match, r["tagName"]))]
    releases = [rel for t in tags
                if (rel := _gh_json("release", "view", t, "--repo", repo,
                                    "--json", "tagName,name,body,publishedAt,url"))]
    if not releases:
        return None
    newest, oldest = releases[0], releases[-1]
    return {
        "repo": repo,
        "tagName": f"{oldest['tagName']}..{newest['tagName']}",
        "count": len(releases),
        "publishedAt": newest["publishedAt"],
        "url": f"https://github.com/{repo}/releases",
        "body": fold_release_notes(releases),
    }


_BOLD_LEAD = re.compile(r"^- \*\*(.+?)\*\*")


def _blocks(body: str) -> list[str]:
    """A release body as top-level bullet items and paragraphs. A bullet runs
    until the next top-level bullet or a blank line followed by a non-bullet."""
    blocks: list[str] = []
    for chunk in re.split(r"\n\s*\n", (body or "").replace("\r\n", "\n")):
        for item in re.split(r"\n(?=- )", chunk.strip()):
            if item.strip():
                blocks.append(item.strip())
    return blocks


def _block_key(block: str) -> str:
    m = _BOLD_LEAD.match(block)
    return (m.group(1) if m else " ".join(block.split())).lower()


def fold_release_notes(releases: list[dict]) -> str:
    """Releases newest first -> one notes body with each item once. Some repos
    write cumulative notes (Sanduhr's 2.24.1 repeats all of 2.24.0), so an
    item keyed by its bold lead (else its text) keeps its NEWEST wording but
    sits under the OLDEST release that carried it, which is when it shipped."""
    newest_text: dict[str, str] = {}
    first_seen: dict[str, int] = {}
    for i, rel in enumerate(releases):           # newest -> oldest
        for block in _blocks(rel.get("body", "")):
            key = _block_key(block)
            newest_text.setdefault(key, block)
            first_seen[key] = i                  # overwritten until the oldest
    sections = []
    for i, rel in enumerate(releases):
        items = [newest_text[k] for k in newest_text if first_seen[k] == i]
        if items:
            head = f"### {rel['tagName']} ({rel['publishedAt'][:10]})"
            sections.append(head + "\n\n" + "\n\n".join(items))
    return "\n\n".join(sections)


def resolve_release(product: dict, tag: str | None) -> dict | None:
    """One release: `tag`, else the newest under the product's release source."""
    src = _release_source(product)
    if not src:
        return None
    repo, prefix = src
    fields = "tagName,name,body,publishedAt,url"
    if not tag and prefix:
        listed = _gh_json("release", "list", "--repo", repo, "--json", "tagName,publishedAt", "-L", "30") or []
        tags = [r["tagName"] for r in listed if r["tagName"].startswith(prefix)]
        if not tags:
            return None
        tag = tags[0]
    args = ["release", "view", *([tag] if tag else []), "--repo", repo, "--json", fields]
    rel = _gh_json(*args)
    if rel:
        rel["repo"] = repo
    return rel


def _template_section() -> str:
    """templates.md section 1 only: the Field Note shape."""
    text = (ANNOUNCE_REFS / "templates.md").read_text(encoding="utf-8")
    m = re.search(r"^## 1\..*?(?=^## 2\.)", text, re.S | re.M)
    return m.group(0).strip() if m else text


def _body_of(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return re.sub(r"\A---\r?\n.*?\r?\n---\r?\n", "", text, count=1, flags=re.S).strip()


def build_prompt(product: dict, release: dict | None) -> tuple[str, str]:
    banned = BANNED.read_text(encoding="utf-8") if BANNED.exists() else ""
    if not banned:
        print(f"warning: {BANNED} not found; drafting without the banned list", file=sys.stderr)
    system = "\n\n".join([
        "You write first drafts of Field Notes for 626labs.dev, the site of 626 Labs, "
        "an independent software lab. A human edits every draft before it publishes.",
        "## Rules\n"
        "- Builder-to-builder, second person, sentence case. Punchline first: what shipped and why it matters.\n"
        "- Specific over generic: name the real change, the real number, the real command.\n"
        "- Only facts from the product entry and release notes below. Never invent features, numbers, "
        "dates, quotes or user reactions. If the notes are thin, write a shorter note.\n"
        "- Fold release highlights in as prose, never a changelog dump.\n"
        "- Em-dashes minimal: commas, periods and colons by default. No emoji. No ellipses for drama.\n"
        "- No self-reference (\"this post\", \"this article\"). Just say the thing.\n"
        "- Close with how to get it: the install command or link from the product entry. "
        "No sign-off or tagline line after it; the author adds their own.\n"
        "- 300 to 700 words. Body as HTML: <p>, <h2>, <strong>, <em>, <code>, <a href>.",
        "## Field Note template (from the /announce skill)\n" + _template_section(),
        "## Voice per channel (from the /announce skill)\n" + (ANNOUNCE_REFS / "voice.md").read_text(encoding="utf-8"),
        "## Banned words (canonical list; tiers A and B apply)\n" + banned,
        "## A published Field Note, for register and HTML shape only. Do not reuse its facts.\n"
        + _body_of(EXEMPLAR),
    ])
    keep = ("id", "title", "tagline", "description", "repo", "install", "productPage",
            "liveUrl", "storeUrl", "tags", "npm", "status")
    facts = {k: product[k] for k in keep if k in product}
    parts = ["## Product entry (content/site.json)\n" + json.dumps(facts, indent=2, ensure_ascii=False)]
    if release and release.get("count"):
        parts.append(
            f"## {release['count']} releases, {release['tagName']} ({release['repo']})\n"
            f"{release['url']}\n\n"
            "Write ONE note about the period, grouped by theme (what a user can now do), "
            "not a section per version. Name versions only where it helps the reader update.\n\n"
            + release["body"]
        )
    elif release:
        parts.append(
            f"## Release {release.get('tagName')} ({release.get('repo')}, published "
            f"{(release.get('publishedAt') or '')[:10]})\n{release.get('url', '')}\n\n"
            + (release.get("body") or "(no notes)")
        )
    else:
        parts.append("## Release\nNo published release. Draft from the product entry alone and keep it short.")
    parts.append("Write the Field Note.")
    return system, "\n\n".join(parts)


def draft(system: str, user: str, model: str, effort: str) -> dict:
    import anthropic

    # ANTHROPIC_API_KEY_SCRIPTS first (see the module docstring). With no key
    # at all, the SDK's own resolution runs, which is how CI federates.
    key = os.environ.get("ANTHROPIC_API_KEY_SCRIPTS")
    client = anthropic.Anthropic(api_key=key) if key else anthropic.Anthropic()
    resp = client.beta.messages.create(
        model=model,
        max_tokens=16000,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": SCHEMA}},
        # A safety-classifier decline is re-run on a fallback model chosen by
        # refusal category, inside the same call.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if resp.stop_reason != "end_turn":
        sys.exit(f"no draft: stop_reason={resp.stop_reason} (request {resp._request_id})")
    text = next((b.text for b in resp.content if b.type == "text"), "")
    u = resp.usage
    print(f"model {resp.model}: {u.input_tokens} in / {u.output_tokens} out", file=sys.stderr)
    return json.loads(text)


def _fm(value: str) -> str:
    """One-line, double-quoted frontmatter value. render-hub strips only the
    outer quotes, so inner quotes survive as written."""
    return '"' + " ".join(str(value).split()) + '"'


def render(fields: dict, release: dict | None, today: str) -> str:
    source = f"{release['repo']}@{release['tagName']}" if release else "site.json only"
    return (
        "---\n"
        f"title: {_fm(fields['title'])}\n"
        f"subtitle: {_fm(fields['subtitle'])}\n"
        f"tagline: {_fm(fields['tagline'])}\n"
        f"published: {today}\n"
        'author: "Este Hernandez"\n'
        "draft: true\n"
        "---\n\n"
        f"<!-- First draft by scripts/draft-field-note.py from {source}. Edit, then: "
        "python scripts/site.py story publish <slug> -->\n\n"
        + _one_block_per_line(fields["body_html"])
        + "\n"
    )


def _one_block_per_line(body: str) -> str:
    """The model tends to return the body as a single line. A blank line
    between block elements makes the draft editable by hand; markdown passes
    the blocks through unchanged."""
    body = re.sub(r"(</(?:p|h2|h3|ul|ol|blockquote)>)\s*(?=<)", r"\1\n\n", body.strip())
    return re.sub(r"\n{3,}", "\n\n", body)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("product", help="product id from content/site.json")
    ap.add_argument("--tag", help="release tag (default: newest)")
    ap.add_argument("--since", metavar="YYYY-MM-DD",
                    help="fold every release published on or after this date into one note")
    ap.add_argument("--match", metavar="REGEX",
                    help="with --since: only tags matching this regex (e.g. '-mac$')")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    ap.add_argument("--dry-run", action="store_true", help="print the prompt; no API call, nothing written")
    ap.add_argument("--force", action="store_true", help="overwrite an existing draft")
    args = ap.parse_args(argv)

    if args.match and not args.since:
        ap.error("--match needs --since")
    if args.since and args.tag:
        ap.error("--since and --tag are exclusive")
    if args.since and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.since):
        ap.error("--since takes YYYY-MM-DD")

    product = find_product(args.product)
    if args.since:
        release = resolve_releases_since(product, args.since, args.match)
        if not release:
            sys.exit(f"no published release since {args.since}"
                     + (f" matching {args.match!r}" if args.match else ""))
        print(f"releases: {release['count']}, {release['repo']}@{release['tagName']}", file=sys.stderr)
    else:
        release = resolve_release(product, args.tag)
        print(f"release: {release['repo']}@{release['tagName']}" if release else "release: none, drafting from site.json",
              file=sys.stderr)
    system, user = build_prompt(product, release)

    today = date.today().isoformat()
    if args.since:
        tag = f"since-{args.since}"
    else:
        tag = release["tagName"].lower().removeprefix(f"{product['id']}-") if release else "note"
    suffix = re.sub(r"[^a-z0-9.]+", "-", tag).strip("-")
    dest = STORIES / f"{today}-{product['id']}-{suffix}.md"

    if args.dry_run:
        print(f"would write {dest.relative_to(ROOT)}\nsystem: {len(system)} chars\n\n{user}")
        return 0
    if dest.exists() and not args.force:
        sys.exit(f"{dest.relative_to(ROOT)} exists; pass --force to overwrite")

    fields = draft(system, user, args.model, args.effort)
    dest.write_text(render(fields, release, today), encoding="utf-8", newline="\n")
    print(f"wrote {dest.relative_to(ROOT)} (draft: true). Review it, then: "
          f"python scripts/site.py story publish {dest.stem}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
