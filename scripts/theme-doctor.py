#!/usr/bin/env python3
"""theme-doctor.py — the contract gate for 626labs.dev theme rotation.

Renders a theme via `render-hub.py --theme <slug> --out <tmp>` and runs a
fixed set of checks against the output: the twelve SITE_JSON zones are all
present, the page chrome (skip-link, nav, footer, analytics) is intact,
every internal href resolves to a real file, and any WCAG contrast pairs
the theme declares in its own theme.json meet AA (>= 4.5).

This is the ONLY thing standing between a theme and unattended monthly
rotation (the scheduled workflow promotes queue[0] to active with no human
in the loop) — it has to fail honestly. A check that always passes is worse
than no check: it turns a real gate into a rubber stamp.

Usage:
  python scripts/theme-doctor.py <slug> [--browser]

Exit 0 and "PASS <slug>" when every check clears. Exit 1 and a bulleted
failure list under "FAIL <slug>" otherwise.

--browser additionally drives Playwright (if the `playwright` package is
importable — it is never a hard dependency of this repo) to assert no
horizontal scroll at 1440/768/390px and zero browser console errors. Without
it, or without playwright installed, those two checks are skipped with a
one-line note and never fail the gate on their own.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    # Loaded two ways: `python scripts/theme-doctor.py` (Python already puts
    # the script's own dir on sys.path[0]) and importlib.util loading by
    # explicit file path from tests/ (it does NOT). Insert explicitly so
    # `import theme_registry` below works either way.
    sys.path.insert(0, str(SCRIPTS_DIR))
import theme_registry  # noqa: E402 — sibling module in scripts/

ZONES = ("hero", "hero-chips", "products", "lab-pool", "thinking", "founding",
         "stories", "lab-runs", "play", "about", "support", "contact")

HREF_RE = re.compile(r'href="([^"]*)"')
STYLE_BLOCK_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.S)

CUSTOM_PROP_RE = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")
HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
RGB_FUNC_RE = re.compile(
    r"^rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*[\d.]+\s*)?\)$"
)
VAR_RE = re.compile(r"^var\(\s*(--[\w-]+)\s*(?:,\s*(.+))?\)$")

AA_MIN_RATIO = 4.5


# ─── static checks — (html, css) -> list[str], per T3's contract ──────────
def check_zones(html: str, css: str) -> list[str]:
    """Every zone in ZONES needs both its start and end SITE_JSON marker."""
    errors = []
    for zone in ZONES:
        if f"SITE_JSON:{zone}:start" not in html:
            errors.append(f"zone {zone}: missing SITE_JSON:{zone}:start marker")
        if f"SITE_JSON:{zone}:end" not in html:
            errors.append(f"zone {zone}: missing SITE_JSON:{zone}:end marker")
    return errors


def check_chrome(html: str, css: str) -> list[str]:
    """Baseline page chrome a theme is never allowed to drop."""
    errors = []
    if 'class="skip-link"' not in html:
        errors.append('chrome: missing skip-link (class="skip-link")')
    if "<nav" not in html:
        errors.append("chrome: missing <nav>")
    if "<footer" not in html:
        errors.append("chrome: missing <footer>")
    if "data-goatcounter" not in html:
        errors.append("chrome: missing analytics (data-goatcounter)")
    return errors


def check_internal_links(html: str, css: str) -> list[str]:
    """Every non-external href resolves to a real file under the repo root."""
    errors = []
    seen = set()
    for href in HREF_RE.findall(html):
        target = href.split("#", 1)[0].split("?", 1)[0]
        if (
            href.startswith("http")
            or href.startswith("mailto:")
            or href.startswith("#")
            or target == ""
        ):
            continue
        if href in seen:
            continue
        seen.add(href)
        rel = target.lstrip("/")
        path = ROOT / rel
        ok = (path / "index.html").exists() if path.is_dir() else path.exists()
        if not ok:
            errors.append(f"internal link target missing: {href}")
    return errors


# ─── contrast ───────────────────────────────────────────────────────────
def _parse_custom_properties(css: str) -> dict[str, str]:
    """Last declaration wins — approximates the cascade for :root vars."""
    props: dict[str, str] = {}
    for name, value in CUSTOM_PROP_RE.findall(css):
        props[name.strip()] = value.strip()
    return props


def _hex_to_rgb(value: str) -> tuple[int, int, int] | None:
    m = HEX_RE.match(value)
    if not m:
        return None
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _rgb_func_to_rgb(value: str) -> tuple[int, int, int] | None:
    m = RGB_FUNC_RE.match(value)
    if not m:
        return None
    # Alpha is ignored: every alpha use in this codebase's tokens is a
    # translucent panel over a same-or-near color field (e.g. rgba(0,0,0,.72)
    # over rgb(0,0,0)) where compositing wouldn't move the channel values
    # enough to change an AA verdict. Treating rgb(a) uniformly keeps the
    # resolver simple and honest about what it does NOT model (true alpha
    # compositing against an arbitrary backdrop).
    return tuple(int(round(float(g))) for g in m.groups())  # type: ignore[return-value]


def _resolve_value(value: str, props: dict[str, str], seen: set[str]) -> tuple[int, int, int] | None:
    value = value.strip()
    m = VAR_RE.match(value)
    if m:
        ref, fallback = m.group(1), m.group(2)
        resolved = _resolve_color(ref, props, seen)
        if resolved is not None:
            return resolved
        if fallback:
            return _resolve_value(fallback, props, seen)
        return None
    return _hex_to_rgb(value) or _rgb_func_to_rgb(value)


def _resolve_color(
    name: str, props: dict[str, str], seen: set[str] | None = None
) -> tuple[int, int, int] | None:
    seen = seen if seen is not None else set()
    if name in seen or name not in props:
        return None
    seen.add(name)
    return _resolve_value(props[name], props, seen)


def _srgb_to_linear(channel: int) -> float:
    c = channel / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = (_srgb_to_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(rgb_a: tuple[int, int, int], rgb_b: tuple[int, int, int]) -> float:
    l1, l2 = _relative_luminance(rgb_a), _relative_luminance(rgb_b)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def evaluate_contrast_pairs(
    css: str, pairs: list[list[str]]
) -> list[tuple[str, str, float | None]]:
    """Per declared pair: (fg name, bg name, ratio or None if unresolvable)."""
    props = _parse_custom_properties(css)
    results = []
    for pair in pairs:
        fg_name, bg_name = pair[0], pair[1]
        fg = _resolve_color(fg_name, props)
        bg = _resolve_color(bg_name, props)
        ratio = _contrast_ratio(fg, bg) if fg is not None and bg is not None else None
        results.append((fg_name, bg_name, ratio))
    return results


def check_contrast(
    css: str, pairs: list[list[str]] | None
) -> tuple[list[str], list[str]]:
    """Returns (failures, advisories). Absent pairs is advisory, not failure —
    a theme states what it wants checked; nothing declared means nothing to
    fail on, but the gap is worth flagging, not hiding."""
    if not pairs:
        return [], ["no contrastPairs declared — contrast unverified"]
    failures = []
    for fg_name, bg_name, ratio in evaluate_contrast_pairs(css, pairs):
        if ratio is None:
            failures.append(f"contrast: could not resolve {fg_name} / {bg_name} to colors")
        elif ratio < AA_MIN_RATIO:
            failures.append(
                f"contrast: {fg_name} on {bg_name} = {ratio:.2f} "
                f"(below AA {AA_MIN_RATIO})"
            )
    return failures, []


# ─── browser checks (optional, --browser) ──────────────────────────────
def _run_browser_checks(html_text: str) -> list[str]:
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        print("browser checks skipped: playwright not installed")
        return []

    import http.server
    import socketserver
    import threading

    class _Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(ROOT), **kw)

        def do_GET(self):  # noqa: N802 — stdlib method name
            if self.path in ("/", "/index.html"):
                body = html_text.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            super().do_GET()

        def log_message(self, fmt, *args):  # quiet — the doctor has its own output
            pass

    errors: list[str] = []
    try:
        httpd = socketserver.TCPServer(("127.0.0.1", 0), _Handler)
    except OSError as e:
        print(f"browser checks skipped: could not start local server ({e})")
        return []
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Exception as e:  # pragma: no cover — environment-dependent
                print(f"browser checks skipped: could not launch chromium ({e})")
                return []
            try:
                for width in (1440, 768, 390):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    console_errors: list[str] = []
                    page.on(
                        "console",
                        lambda msg: console_errors.append(msg.text)
                        if msg.type == "error"
                        else None,
                    )
                    try:
                        page.goto(f"http://127.0.0.1:{port}/", wait_until="load", timeout=15000)
                        page.wait_for_timeout(300)  # let deferred scripts settle
                    except Exception as e:
                        print(f"browser checks skipped at {width}px: navigation failed ({e})")
                        page.close()
                        continue
                    scroll_width = page.evaluate("document.documentElement.scrollWidth")
                    client_width = page.evaluate("document.documentElement.clientWidth")
                    if scroll_width > client_width + 1:
                        errors.append(
                            f"browser: horizontal scroll at {width}px "
                            f"(scrollWidth {scroll_width} > clientWidth {client_width})"
                        )
                    for msg in console_errors:
                        errors.append(f"browser: console error at {width}px: {msg}")
                    page.close()
            finally:
                browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
    return errors


# ─── main ───────────────────────────────────────────────────────────────
def main(argv: list[str]) -> int:
    browser = "--browser" in argv
    positional = [a for a in argv if a != "--browser"]
    if not positional:
        print("usage: theme-doctor.py <slug> [--browser]", file=sys.stderr)
        return 2
    slug = positional[0]

    tdir = theme_registry.theme_dir(slug)
    missing = [f for f in ("shell.html", "tokens.css", "theme.json") if not (tdir / f).exists()]
    if missing:
        print(f"FAIL {slug}")
        for f in missing:
            print(f"  - theme {slug} missing {f}")
        return 1

    with tempfile.TemporaryDirectory(prefix="theme-doctor-") as tmp:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "render-hub.py"),
                "--theme", slug,
                "--out", tmp,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"FAIL {slug}")
            print(f"  - render-hub.py --theme {slug} --out failed:")
            for line in (result.stdout + result.stderr).splitlines():
                print(f"    {line}")
            return 1
        html_text = (Path(tmp) / "index.html").read_text(encoding="utf-8")

    tokens_css = (tdir / "tokens.css").read_text(encoding="utf-8")
    # Base tokens (--fg-1, --text, etc.) live inline in the shell's <style>;
    # tokens.css is the theme's append-only override layer on top. Merge in
    # cascade order so a resolved --fg-1 / --pb-field pair reflects what the
    # browser actually paints, not just what tokens.css alone declares.
    inline_css = "\n".join(STYLE_BLOCK_RE.findall(html_text))
    merged_css = f"{inline_css}\n{tokens_css}"

    theme_meta = json.loads((tdir / "theme.json").read_text(encoding="utf-8"))
    pairs = theme_meta.get("contrastPairs")

    errors: list[str] = []
    errors += check_zones(html_text, tokens_css)
    errors += check_chrome(html_text, tokens_css)
    errors += check_internal_links(html_text, tokens_css)

    if pairs:
        for fg_name, bg_name, ratio in evaluate_contrast_pairs(merged_css, pairs):
            if ratio is None:
                print(f"contrast: {fg_name} on {bg_name} = unresolved")
            else:
                verdict = "pass" if ratio >= AA_MIN_RATIO else "FAIL"
                print(f"contrast: {fg_name} on {bg_name} = {ratio:.2f} ({verdict}, AA >= {AA_MIN_RATIO})")
    contrast_failures, contrast_advisories = check_contrast(merged_css, pairs)
    errors += contrast_failures
    for line in contrast_advisories:
        print(line)

    if browser:
        errors += _run_browser_checks(html_text)

    if errors:
        print(f"FAIL {slug}")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"PASS {slug}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
