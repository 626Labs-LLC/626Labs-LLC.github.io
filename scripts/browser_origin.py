"""Third-party isolation for every headless-Chromium run in this repo.

Two callers, one rule, and the reason it is shared rather than copied:

- scripts/theme-doctor.py's `--browser` gate, which is what stands between a
  queued theme and an unattended promotion to live on the 1st.
- scripts/freeze-theme.py's `capture_theme_screenshot`, which runs EARLIER in
  that same rotation (twice: once for the outgoing theme's archive thumbnail,
  once for the incoming theme's gallery card).

The gate was isolated first and the capture was not, which left the worse of
the two exposures open: a slow or unreachable gc.zgo.at hangs the capture's
`wait_until="load"` until its 15s timeout, the step fails, and the rotation
never reaches the gate that is now immune. Worse, theme thumbnails are
capture-once — `freeze()` refuses to overwrite an existing archive month — so
a flake there is permanent rather than retried.

Every page either tool opens is served from a local ephemeral port and its
own assets are root-relative, so "off-origin" is exactly "not ours": the
analytics beacon (`//gc.zgo.at/count.js`, on 9 of the 10 documents the gate
opens), and on index.html the Bacon Trail widget's TMDB calls and its
fonts.googleapis.com @import.

What this does NOT cover, written down rather than assumed away: `page.route`
does not see WebSocket handshakes, Service Worker requests, or requests made
by popup pages. No page in this repo opens any of the three today.
"""
from __future__ import annotations

import urllib.parse


def page_origin(url: str) -> str:
    """`scheme://host:port` of `url` — what "the page's own origin" means to
    the two filters below."""
    parts = urllib.parse.urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def is_off_origin(url: str, origin: str) -> bool:
    """True when `url` leaves the page's own origin.

    `data:` / `blob:` / `about:` are the page's own content under another
    scheme and are never off-origin. An EMPTY url is treated as the page's
    own — a console error the browser could not attribute is reported, never
    filtered away, because the failure mode these gates exist to prevent is
    silently covering less than they claim.
    """
    if not url:
        return False
    if url.startswith(("data:", "blob:", "about:")):
        return False
    # Compared as (scheme, netloc), never as a string prefix. The prefix form
    # calls `http://127.0.0.1:8000?q=1` off-origin — a query string with no
    # path — and aborts a request the page's own server was about to answer.
    return urllib.parse.urlsplit(url)[:2] != urllib.parse.urlsplit(origin)[:2]


def block_off_origin(page, url: str, fulfill: dict[str, tuple[str, str]] | None = None) -> None:
    """Install the abort route on a playwright Page for the origin `url`
    belongs to. Call BEFORE `page.goto`.

    `fulfill` maps a URL SUBSTRING to `(content_type, body)`. An off-origin
    request whose URL contains that substring is answered from the body
    instead of being aborted — the escape hatch for a page whose CONTENT
    arrives off-origin, so the gate can check its populated layout rather
    than its fetch-failed fallback. It is a substitution, not an exemption:
    nothing leaves the machine either way, so the determinism the abort buys
    is preserved.
    """
    origin = page_origin(url)
    fulfill = fulfill or {}

    def _handle(route):
        req_url = route.request.url
        if not is_off_origin(req_url, origin):
            route.continue_()
            return
        for needle, (content_type, body) in fulfill.items():
            if needle in req_url:
                route.fulfill(status=200, content_type=content_type, body=body)
                return
        route.abort()

    page.route("**/*", _handle)


def console_message_url(msg) -> str:
    """The URL a console message is attributed to, or "" when the browser
    attributed it to nothing."""
    loc = getattr(msg, "location", None) or {}
    try:
        return loc.get("url", "") or ""
    except AttributeError:  # a location object rather than a dict
        return getattr(loc, "url", "") or ""
