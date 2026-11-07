"""Fetch OSM streets for each mini map's visible area, simplify, write streets.json."""
import json, math, re, sys, urllib.request, urllib.parse

HTML = sys.argv[1]
OUT = sys.argv[2]
html = open(HTML, encoding="utf-8").read()

LM = {
    "ruifang": [(25.1087356, 121.8059692)],
    "jiaoxi": [(24.827034, 121.775353), (24.8288597, 121.7672528)],
    "taiping": [],
    "fulong": [(25.0159203, 121.9446682)],
    "tpslodge": [(24.49237, 121.53652)],
    "tpscuifeng": [(24.50966, 121.61058)],
    "jiuzhize": [],
    "jxnight": [(24.8288597, 121.7672528)],
    "yinyang": [],
    "caoling": [(25.0159203, 121.9446682)],
}
WALK = {"tpslodge", "tpscuifeng", "jiuzhize", "jxnight", "yinyang", "caoling"}  # walking-area maps: trails + water too
PATHS = {"footway", "steps", "path", "pedestrian", "track"}
W, H, PAD = 360, 270, 44


def blocks():
    for m in re.finditer(r'data-map="(\w+)"(.*?)</details>', html, re.S):
        pts = [(float(a), float(b)) for a, b in re.findall(
            r'data-lat="([\d.]+)"\s+data-lng="([\d.]+)"', m.group(2))]
        yield m.group(1), pts


def projection(pts):
    """Mirror of the page's JS projection."""
    la = [p[0] for p in pts]; ln = [p[1] for p in pts]
    minLat, maxLat, minLng, maxLng = min(la), max(la), min(ln), max(ln)
    lat0 = (minLat + maxLat) / 2
    k = math.cos(lat0 * math.pi / 180)
    sx = (maxLng - minLng) * k; sy = maxLat - minLat; mn = 0.0026
    if sx < mn:
        c = (minLng + maxLng) / 2; minLng = c - mn / k / 2; maxLng = c + mn / k / 2; sx = mn
    if sy < mn * 0.75:
        c = (minLat + maxLat) / 2; minLat = c - mn * 0.375; maxLat = c + mn * 0.375; sy = mn * 0.75
    s = min((W - 2 * PAD) / sx, (H - 2 * PAD) / sy)
    ox = (W - sx * s) / 2; oy = (H - sy * s) / 2 + 6
    P = lambda lat, lng: (ox + (lng - minLng) * k * s, oy + (maxLat - lat) * s)
    # visible extent
    south = maxLat - (H - oy) / s; north = maxLat + oy / s
    west = minLng - ox / (k * s); east = minLng + (W - ox) / (k * s)
    return P, (south, west, north, east), s


def simplify(pts, tol):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy) or 1e-9
    best, idx = 0, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / L
        if d > best:
            best, idx = d, i
    if best <= tol:
        return [pts[0], pts[-1]]
    return simplify(pts[: idx + 1], tol)[:-1] + simplify(pts[idx:], tol)


def overpass(q):
    import time
    data = urllib.parse.urlencode({"data": q}).encode()
    hosts = ["https://overpass-api.de/api/interpreter",
             "https://overpass.kumi.systems/api/interpreter",
             "https://overpass.private.coffee/api/interpreter",
             "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]
    err = None
    for attempt in range(16):
        url = hosts[attempt % len(hosts)]
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "trip-guide-minimap/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:
            err = e
            print("retry", url, e, file=sys.stderr)
            time.sleep(5)
    raise err


MAJOR = {"motorway", "trunk", "primary", "secondary", "tertiary",
         "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link"}
MINOR = {"residential", "unclassified", "living_street", "pedestrian", "road"}

out = {}
for key, shops in blocks():
    P, (S, Wst, N, E), scale = projection(shops + LM[key])
    big = scale < 3000  # wide area (Taipingshan): major roads only
    hw = "motorway|trunk|primary|secondary|tertiary|unclassified" + ("" if big else "|residential|living_street|pedestrian|road|.*_link")
    bbox = f"{S:.5f},{Wst:.5f},{N:.5f},{E:.5f}"
    q = f'[out:json][timeout:90];(way["highway"~"^({hw})$"]({bbox});way["railway"="rail"]({bbox}););out geom;'
    if key in WALK:
        q = (f'[out:json][timeout:90];(way["highway"]({bbox});way["railway"~"^(rail|narrow_gauge)$"]({bbox});'
             f'way["natural"="water"]({bbox}););out geom;')
    import os
    cache = os.path.join(os.path.dirname(OUT), f"osm_{key}.json")
    if os.path.exists(cache):
        res = json.load(open(cache, encoding="utf-8"))
    elif os.environ.get("OFFLINE"):
        continue
    else:
        res = overpass(q)
        json.dump(res, open(cache, "w", encoding="utf-8"))
    ways = []
    for el in res["elements"]:
        tags = el.get("tags", {})
        if tags.get("natural") == "water":
            cls = "water"
        elif "railway" in tags:
            cls = "rail"
        elif tags.get("highway") in PATHS:
            cls = "path"
        else:
            h = tags.get("highway", "")
            cls = "major" if h in MAJOR else "minor"
            if big and h == "unclassified":
                cls = "minor"
        if key in ("yinyang", "caoling") and (cls == "path" or tags.get("highway") == "service"):
            continue  # wide area: roads only, keeps the data small
        geom = [(g["lat"], g["lon"]) for g in el["geometry"]]
        px = [P(a, b) for a, b in geom]
        keep = simplify(px, 1.2 if big or key in ("yinyang", "caoling") else 0.6)
        # map simplified pixel points back to lat/lng by index lookup
        idxs = [px.index(p) for p in keep]
        coords = [geom[i] for i in idxs]
        if len(coords) < 2:
            continue
        ways.append({"c": cls, "n": tags.get("name", ""),
                     "p": " ".join(f"{a:.5f},{b:.5f}" for a, b in coords)})
    out[key] = ways
    print(key, "scale", round(scale), "ways", len(ways),
          "chars", sum(len(w["p"]) for w in ways), file=sys.stderr)

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
