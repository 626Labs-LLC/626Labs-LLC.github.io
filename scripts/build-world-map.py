#!/usr/bin/env python3
"""Generate data/world-robinson.json — the base geometry the Store reach map draws.

WHY THERE IS NO TILE PROVIDER HERE. A slippy map (Leaflet/MapLibre/Mapbox) needs
tiles, and tile hosts are what force an API key and stamp a watermark on the
result. This map answers "which countries, how many" — it needs geographic
CONTEXT, not zoomable imagery. So the whole thing is inline SVG projected from
public-domain geometry: no key, no watermark, no runtime request, nothing that
can expire out from under the site.

WHY ROBINSON. Web Mercator inflates high latitudes without bound and would draw
Antarctica as a continent-sized slab. Antarctica is a real data point here (one
install), so the projection has to render it at honest area. Robinson is the
standard compromise for world thematic maps.

SOURCE. Natural Earth 110m admin-0 countries, public domain (CC0). The source
GeoJSON is ~820 KB and is NOT committed: this script fetches it on demand and
commits only the derived 130 KB artifact. Re-run after a Natural Earth bump.

    python scripts/build-world-map.py            # write the artifact
    python scripts/build-world-map.py --check    # CI: fail if it would change
"""
import argparse
import json
import math
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "data" / "world-robinson.json"
CACHE = ROOT / ".cache" / "ne_110m_admin_0_countries.geojson"
SRC_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_110m_admin_0_countries.geojson"
)

# Robinson, tabulated at 5-degree steps. X = length of the parallel relative to
# the equator, Y = distance from the equator. Linear interpolation between stops
# is fine at this granularity for a thematic map.
LAT_STOPS = list(range(0, 95, 5))
RX = [1.0000, 0.9986, 0.9954, 0.9900, 0.9822, 0.9730, 0.9600, 0.9427, 0.9216,
      0.8962, 0.8679, 0.8350, 0.7986, 0.7597, 0.7186, 0.6732, 0.6213, 0.5722, 0.5322]
RY = [0.0000, 0.0620, 0.1240, 0.1860, 0.2480, 0.3100, 0.3720, 0.4340, 0.4958,
      0.5571, 0.6176, 0.6769, 0.7346, 0.7903, 0.8435, 0.8936, 0.9394, 0.9761, 1.0000]

# Natural Earth 110m omits micro-states and small territories that are still real
# Store markets. Measured against live install data, 8 of 100 countries had no
# 110m feature — only 1.1% of installs, but Hong Kong and Singapore are among
# them and those are not noise. Centre coordinates are enough to place a symbol;
# the landmass stays undrawn at this resolution, which is fine because the dot is
# the data and the map is only context.
SUPPLEMENT = {
    "HK": ("Hong Kong SAR", 114.17, 22.32), "SG": ("Singapore", 103.82, 1.35),
    "MO": ("Macao SAR", 113.55, 22.20), "MV": ("Maldives", 73.51, 4.18),
    "BH": ("Bahrain", 50.58, 26.07), "AW": ("Aruba", -69.97, 12.52),
    "AS": ("American Samoa", -170.70, -14.31),
    "IO": ("British Indian Ocean Territory", 71.88, -6.34),
    "MT": ("Malta", 14.44, 35.90), "LU": ("Luxembourg", 6.13, 49.61),
    "MU": ("Mauritius", 57.55, -20.35), "BB": ("Barbados", -59.54, 13.19),
    "LI": ("Liechtenstein", 9.55, 47.17), "AD": ("Andorra", 1.52, 42.51),
    "MC": ("Monaco", 7.42, 43.74), "SM": ("San Marino", 12.46, 43.94),
    "BM": ("Bermuda", -64.75, 32.31), "GI": ("Gibraltar", -5.35, 36.14),
    "KY": ("Cayman Islands", -81.25, 19.31), "CW": ("Curacao", -68.99, 12.17),
    "GU": ("Guam", 144.79, 13.44), "MF": ("Saint Martin", -63.08, 18.08),
    "SC": ("Seychelles", 55.49, -4.68), "TT": ("Trinidad and Tobago", -61.22, 10.69),
}

X_MAX = 0.8487 * math.pi
Y_MAX = 1.3523
WIDTH = 1000.0
HEIGHT = WIDTH * (Y_MAX / X_MAX)


def _interp(table, alat):
    if alat >= 90:
        return table[-1]
    i = int(alat // 5)
    t = (alat - LAT_STOPS[i]) / 5.0
    return table[i] + (table[i + 1] - table[i]) * t


def to_svg(lon, lat):
    alat = min(abs(lat), 90.0)
    x = 0.8487 * _interp(RX, alat) * math.radians(lon)
    y = 1.3523 * _interp(RY, alat)
    if lat < 0:
        y = -y
    return ((x / X_MAX) * (WIDTH / 2) + WIDTH / 2,
            HEIGHT / 2 - (y / Y_MAX) * (HEIGHT / 2))


def ring_to_path(ring):
    pts = [f"{round(x, 1)},{round(y, 1)}" for x, y in (to_svg(a, b) for a, b in ring)]
    return ("M" + "L".join(pts) + "Z") if pts else ""


def fetch_source():
    if CACHE.exists():
        return CACHE.read_text(encoding="utf-8")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    print(f"fetching {SRC_URL}")
    with urllib.request.urlopen(SRC_URL, timeout=120) as r:
        text = r.read().decode("utf-8")
    CACHE.write_text(text, encoding="utf-8")
    return text


def build():
    gj = json.loads(fetch_source())
    land, points = [], {}
    for ft in gj["features"]:
        p, geom = ft["properties"], ft["geometry"]
        polys = ([geom["coordinates"]] if geom["type"] == "Polygon"
                 else geom["coordinates"] if geom["type"] == "MultiPolygon" else [])
        d = "".join(ring_to_path(poly[0]) for poly in polys if poly and poly[0])
        if d:
            land.append(d)
        # ISO_A2_EH beats ISO_A2: the plain field is -99 for France, Norway, others.
        iso = (p.get("ISO_A2_EH") or p.get("ISO_A2") or "").strip().upper()
        lx, ly = p.get("LABEL_X"), p.get("LABEL_Y")
        if iso and iso not in ("-9", "-99") and lx is not None and ly is not None:
            x, y = to_svg(float(lx), float(ly))
            # LABEL_X/Y are cartographer-placed label anchors, which is exactly what
            # a symbol wants. A naive polygon centroid would drop the US dot in the
            # Pacific (Alaska + Hawaii) and France's off the coast of Africa.
            points[iso] = {"name": p.get("NAME") or iso, "x": round(x, 1), "y": round(y, 1)}
    for iso, (name, lon, lat) in SUPPLEMENT.items():
        if iso in points:
            continue  # never override real geometry
        x, y = to_svg(lon, lat)
        points[iso] = {"name": name, "x": round(x, 1), "y": round(y, 1), "pt": 1}
    return {
        "$comment": "Generated by scripts/build-world-map.py. Do not hand-edit.",
        "projection": "robinson",
        "viewBox": [0, 0, round(WIDTH, 1), round(HEIGHT, 1)],
        "source": "Natural Earth 110m admin-0 countries (public domain, CC0)",
        "land": land,
        "points": points,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit nonzero if the committed artifact is stale")
    args = ap.parse_args()
    payload = json.dumps(build(), separators=(",", ":")) + "\n"
    if args.check:
        current = DEST.read_text(encoding="utf-8") if DEST.exists() else ""
        if current != payload:
            print("world-robinson.json is STALE — re-run scripts/build-world-map.py")
            return 1
        print("world-robinson.json is up to date.")
        return 0
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(payload, encoding="utf-8")
    data = json.loads(payload)
    print(f"wrote {DEST.relative_to(ROOT)} ({len(payload)/1024:.0f} KB)")
    print(f"  land paths: {len(data['land'])}  |  ISO points: {len(data['points'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
