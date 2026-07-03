"""Render the RoRoRo Ur family launch kit: transparent icons (256/512/1024),
a 5:2 family header (1500x600), and per-plugin X body cards (1200x675).
Glyphs match the approved concept board."""
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)

HEX = '<path d="M90 14 L156 50 L156 122 L90 158 L24 122 L24 50 Z" stroke="#17d4fa" stroke-width="5" stroke-linejoin="round"/>'
SWOOSH = ('<path d="M40 138 q30 16 55 4 q28 -13 48 4" stroke="#17d4fa" stroke-width="4" fill="none" stroke-linecap="round"/>'
          '<path d="M40 148 q30 -14 55 -2 q28 12 48 -4" stroke="#f22f89" stroke-width="4" fill="none" stroke-linecap="round"/>')

def grad(gid, horizontal=False):
    xy = 'x1="0" y1="0" x2="1" y2="0"' if horizontal else 'x1="0" y1="0" x2="1" y2="1"'
    return f'<linearGradient id="{gid}" {xy}><stop offset="0" stop-color="#17d4fa"/><stop offset="1" stop-color="#f22f89"/></linearGradient>'

OCR_GLYPH = (
    '<path d="M58 66 v-10 h12 M110 56 h12 v10 M122 104 v10 h-12 M70 114 h-12 v-10" stroke="#17d4fa" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>'
    '<rect x="64" y="78" width="52" height="7" rx="3.5" fill="url(#G)"/>'
    '<rect x="64" y="90" width="40" height="7" rx="3.5" fill="url(#G)"/>'
)
TASK_GLYPH = (
    '<circle cx="70" cy="86" r="13" fill="#f22f89"/>'
    '<path d="M100 74 L124 86 L100 98 Z" fill="url(#G)"/>'
    '<path d="M58 66 q32 -20 64 0" stroke="#17d4fa" stroke-width="4" fill="none" stroke-linecap="round"/>'
    '<path d="M122 66 l0 -9 M122 66 l-9 0" stroke="#17d4fa" stroke-width="4" fill="none" stroke-linecap="round"/>'
)
AFK_GLYPH = (
    '<path d="M42 80 h20 l7 -20 l11 40 l8 -27 l6 13 h42" stroke="url(#G)" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    '<rect x="52" y="102" width="76" height="30" rx="6" stroke="#17d4fa" stroke-width="4" fill="none"/>'
    '<circle cx="64" cy="112" r="2.4" fill="#17d4fa"/><circle cx="78" cy="112" r="2.4" fill="#17d4fa"/>'
    '<circle cx="92" cy="112" r="2.4" fill="#17d4fa"/><circle cx="106" cy="112" r="2.4" fill="#17d4fa"/>'
    '<circle cx="118" cy="112" r="2.4" fill="#17d4fa"/>'
    '<rect x="70" y="121" width="40" height="4.5" rx="2.25" fill="#17d4fa"/>'
)

ICONS = {"ur-ocr": (OCR_GLYPH, False), "ur-task": (TASK_GLYPH, False), "ur-afk": (AFK_GLYPH, True)}

def icon_svg(glyph, horizontal, size, gid="G"):
    g = glyph.replace("#G", "#"+gid) if gid != "G" else glyph
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 180 180" fill="none">'
            f'<defs>{grad(gid, horizontal)}</defs>{HEX}{g}{SWOOSH}</svg>')

def icon_html(glyph, horizontal, size):
    return f'<!doctype html><html><head><style>*{{margin:0;padding:0}}html,body{{background:transparent}}</style></head><body>{icon_svg(glyph, horizontal, size)}</body></html>'

FONTS = "@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=JetBrains+Mono:wght@500;600&family=Inter:wght@400;500&display=swap');"
FIELD = ("radial-gradient(80% 120% at 18% 12%, rgba(23,212,250,.16), transparent 55%),"
         "radial-gradient(80% 120% at 84% 92%, rgba(242,47,137,.16), transparent 55%),#192e44")

# ---- per-plugin body cards (no repeated "The launcher grew") ----
CARDS = {
    "ur-ocr":  ("Ur OCR",  "Eyes.",        "Watches a region of your screen and fires a keybind, or a whole Ur Task macro, the moment it matches.", OCR_GLYPH, False),
    "ur-task": ("Ur Task", "Hands.",       "Records a macro once and replays it on any alt. Window-aware, so your clicks land wherever the windows sit.", TASK_GLYPH, False),
    "ur-afk":  ("Ur AFK",  "A heartbeat.", "Keeps your idle alts alive with one keystroke, right before Roblox's timeout.", AFK_GLYPH, True),
}

def card_html(name, role, body, glyph, horizontal):
    big = icon_svg(glyph, horizontal, 300, gid="GC")
    return f'''<!doctype html><html><head><style>{FONTS}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1200px;height:675px;overflow:hidden;font-family:'Inter',sans-serif;background:{FIELD};display:flex;align-items:center;gap:56px;padding:0 84px}}
.copy{{flex:1}}
.kicker{{font-family:'JetBrains Mono',monospace;font-size:18px;letter-spacing:.14em;color:#17d4fa;text-transform:uppercase;font-weight:600}}
h3{{font-family:'Space Grotesk',sans-serif;font-weight:700;letter-spacing:-.02em;margin:14px 0 22px;line-height:1.0}}
.name{{font-size:52px;color:#fff;display:block}}
.role{{font-size:60px;background:linear-gradient(135deg,#17d4fa,#f22f89);-webkit-background-clip:text;background-clip:text;color:transparent;display:block}}
p{{color:#c4cdda;font-size:25px;line-height:1.45;max-width:560px}}
.foot{{margin-top:32px;font-family:'JetBrains Mono',monospace;font-size:16px;letter-spacing:.12em;color:#8e9bad;text-transform:uppercase}}
.art{{width:340px;display:flex;align-items:center;justify-content:center}}
</style></head><body>
  <div class="copy">
    <div class="kicker">RoRoRo · plugin</div>
    <h3><span class="name">{name}</span><span class="role">{role}</span></h3>
    <p>{body}</p>
    <div class="foot">Free · Windows · consent-gated</div>
  </div>
  <div class="art">{big}</div>
</body></html>'''

# ---- 5:2 family header (1500x600) ----
def header_html():
    def g(glyph, horiz, gid):
        return icon_svg(glyph, horiz, 150, gid=gid)
    ocr = g(OCR_GLYPH, False, "GH1"); task = g(TASK_GLYPH, False, "GH2"); afk = g(AFK_GLYPH, True, "GH3")
    return f'''<!doctype html><html><head><style>{FONTS}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1500px;height:600px;overflow:hidden;font-family:'Inter',sans-serif;background:{FIELD};display:flex;align-items:center;padding:0 80px;gap:40px}}
.copy{{flex:1}}
.kicker{{font-family:'JetBrains Mono',monospace;font-size:20px;letter-spacing:.16em;color:#17d4fa;text-transform:uppercase;font-weight:600}}
h1{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:82px;letter-spacing:-.02em;line-height:1.0;color:#fff;margin:18px 0 20px}}
h1 .g{{background:linear-gradient(135deg,#17d4fa,#f22f89);-webkit-background-clip:text;background-clip:text;color:transparent}}
.sub{{color:#c4cdda;font-size:27px;line-height:1.4;max-width:660px}}
.tag{{margin-top:30px;font-family:'JetBrains Mono',monospace;font-size:16px;letter-spacing:.14em;color:#8e9bad;text-transform:uppercase}}
.icons{{display:flex;flex-direction:column;gap:18px}}
.icons .row{{display:flex;align-items:center;gap:18px}}
.icons .lbl{{font-family:'JetBrains Mono',monospace;font-size:15px;letter-spacing:.12em;color:#8e9bad;text-transform:uppercase;width:110px}}
</style></head><body>
  <div class="copy">
    <div class="kicker">RoRoRo · Microsoft Store</div>
    <h1>RoRoRo <span class="g">Ur Plugins</span></h1>
    <div class="sub">Eyes, hands, and a heartbeat for your alts. Three plugins, one consent-gated family.</div>
    <div class="tag">Imagine Something Else.</div>
  </div>
  <div class="icons">
    <div class="row">{ocr}<span class="lbl">OCR · eyes</span></div>
    <div class="row">{task}<span class="lbl">Task · hands</span></div>
    <div class="row">{afk}<span class="lbl">AFK · heartbeat</span></div>
  </div>
</body></html>'''

with sync_playwright() as p:
    b = p.chromium.launch()
    for name, (glyph, horiz) in ICONS.items():
        for size in (256, 512, 1024):
            pg = b.new_page(viewport={"width": size, "height": size})
            pg.set_content(icon_html(glyph, horiz, size)); pg.wait_for_timeout(150)
            pg.screenshot(path=str(OUT / f"{name}-{size}.png"), omit_background=True); pg.close()
    for name, (nm, role, body, glyph, horiz) in CARDS.items():
        pg = b.new_page(viewport={"width": 1200, "height": 675}, device_scale_factor=2)
        pg.set_content(card_html(nm, role, body, glyph, horiz)); pg.wait_for_timeout(1200)
        pg.screenshot(path=str(OUT / f"card-{name}.png")); pg.close()
    pg = b.new_page(viewport={"width": 1500, "height": 600}, device_scale_factor=2)
    pg.set_content(header_html()); pg.wait_for_timeout(1200)
    pg.screenshot(path=str(OUT / "header-ur-plugins-1500x600.png")); pg.close()
    b.close()

for f in sorted(OUT.iterdir()):
    print(f.name, f.stat().st_size)
