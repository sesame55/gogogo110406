"""Build a true-scale Taipingshan route overview SVG from cached OSM data and splice it into the page."""
import heapq, json, math, re, sys

HTML, OSM, LAKE = sys.argv[1], sys.argv[2], sys.argv[3]
osm = json.load(open(OSM, encoding="utf-8"))

# ---- road graph ----
adj, coord = {}, {}
for e in osm["elements"]:
    if e["type"] != "way" or "geometry" not in e or "highway" not in e.get("tags", {}):
        continue
    ids, geo = e["nodes"], e["geometry"]
    for nid, g in zip(ids, geo):
        coord[nid] = (g["lat"], g["lon"])
    for a, b in zip(ids, ids[1:]):
        (la1, lo1), (la2, lo2) = coord[a], coord[b]
        d = math.hypot((la2 - la1), (lo2 - lo1) * math.cos(math.radians(la1)))
        adj.setdefault(a, []).append((b, d))
        adj.setdefault(b, []).append((a, d))


def nearest(lat, lng):
    return min(adj, key=lambda n: (coord[n][0] - lat) ** 2 + ((coord[n][1] - lng) * 0.91) ** 2)


def route(*pts):
    out = []
    for (a, b) in zip(pts, pts[1:]):
        s, t = nearest(*a), nearest(*b)
        dist, prev, pq = {s: 0}, {}, [(0, s)]
        while pq:
            d, u = heapq.heappop(pq)
            if u == t:
                break
            if d > dist[u]:
                continue
            for v, w in adj[u]:
                nd = d + w
                if nd < dist.get(v, 1e9):
                    dist[v], prev[v] = nd, u
                    heapq.heappush(pq, (nd, v))
        path, u = [t], t
        while u != s:
            u = prev[u]
            path.append(u)
        seg = [coord[n] for n in reversed(path)]
        out += seg if not out else seg[1:]
    return out


TUCHANG = (24.57314, 121.49624)
RENZE = (24.55419, 121.50794)
JIUZHIZE = (24.54563, 121.50865)
BAILING = (24.52755, 121.51879)
JIANQING = (24.50559, 121.52569)
LODGE = (24.49237, 121.53652)
SUNRISE = (24.51035, 121.59416)
CUIFENG = (24.50954, 121.61091)

low_a = route(TUCHANG, RENZE, BAILING, JIANQING)
low_b = route(JIANQING, LODGE)
spur = route(RENZE, JIUZHIZE)
upper = route(LODGE, SUNRISE, CUIFENG)

lake = []
for e in json.load(open(LAKE, encoding="utf-8"))["elements"]:
    if e.get("tags", {}).get("natural") == "water" and "geometry" in e:
        lake.append([(g["lat"], g["lon"]) for g in e["geometry"]])

# ---- projection ----
allpts = low_a + low_b + spur + upper
lat0 = sum(p[0] for p in allpts) / len(allpts)
k = math.cos(math.radians(lat0))
minlat, maxlat = min(p[0] for p in allpts), max(p[0] for p in allpts)
minlng, maxlng = min(p[1] for p in allpts), max(p[1] for p in allpts)
W, PADX, PADT, PADB = 340, 30, 34, 40
s = (W - 2 * PADX) / ((maxlng - minlng) * k)
H = round((maxlat - minlat) * s + PADT + PADB)


def P(p):
    return (PADX + (p[1] - minlng) * k * s, PADT + (maxlat - p[0]) * s)


def simplify(pts, tol=0.5):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    L = math.hypot(x2 - x1, y2 - y1) or 1e-9
    best, idx = 0, 0
    for i in range(1, len(pts) - 1):
        d = abs((y2 - y1) * pts[i][0] - (x2 - x1) * pts[i][1] + x2 * y1 - y2 * x1) / L
        if d > best:
            best, idx = d, i
    if best <= tol:
        return [pts[0], pts[-1]]
    return simplify(pts[: idx + 1], tol)[:-1] + simplify(pts[idx:], tol)


def d(pts, close=False):
    q = [P(p) for p in pts] if close else simplify([P(p) for p in pts])
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in q) + ("Z" if close else "")


road = d(low_a) + d(low_b) + d(spur) + d(upper)
# label: (point, dot class, name, time, dx, dy, anchor)
POIS = [
    (TUCHANG, "rm-dot", "土場", "售票站", 9, 4, "start"),
    ((24.54538, 121.50784), "rm-dot-ab", "鳩之澤", "14:00 會合", -10, 4, "end"),
    ((24.53091, 121.51871), "rm-dot", "白嶺巨木", "", 9, 4, "start"),
    ((24.50250, 121.52503), "rm-dot-b", "見晴步道", "B 09:00", -10, 4, "end"),
    (LODGE, "rm-dot-b", "太平山莊", "B 10:30–13:00", 0, 20, "middle"),
    (SUNRISE, "rm-dot", "觀日台", "", 0, -10, "middle"),
    ((24.51599, 121.60593), None, "翠峰湖", "", 0, -10, "middle"),
    (CUIFENG, "rm-dot-a", "翠峰山屋", "A 09:15 山毛櫸", 0, 20, "end"),
]

parts = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="太平山路線圖：依實際比例，土場往南經鳩之澤、白嶺、見晴到太平山莊，再往東到翠峰湖">']
for poly in lake:
    parts.append(f'<path class="rm-lake" d="{d(poly, True)}" />')
parts.append('<g fill="none" stroke-linecap="round" stroke-linejoin="round">')
parts.append(f'<path class="rm-road-edge" d="{road}" />')
parts.append(f'<path class="rm-road" d="{road}" />')
parts.append(f'<path class="rm-b" d="{d(low_b)}" />')
parts.append(f'<path class="rm-a" d="{d(upper)}" />')
parts.append("</g>")
for pt, cls, name, time, dx, dy, anchor in POIS:
    x, y = P(pt)
    if cls:
        r = 8 if name == "太平山莊" else 6.5 if cls != "rm-dot" else 5.5
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" class="{cls}" />')
    ny = y + dy
    parts.append(f'<text class="rm-name" x="{x + dx:.1f}" y="{ny:.1f}" text-anchor="{anchor}">{name}</text>')
    if time:
        parts.append(f'<text class="rm-time" x="{x + dx:.1f}" y="{ny + 13:.1f}" text-anchor="{anchor}">{time}</text>')
# legend (top right)
parts.append(f'<g class="rm-legend" transform="translate({W - 150} 16)">'
             '<circle cx="0" cy="0" r="5" class="rm-dot-a" /><text x="9" y="4">A 團</text>'
             '<circle cx="46" cy="0" r="5" class="rm-dot-b" /><text x="55" y="4">B 團</text>'
             '<circle cx="92" cy="0" r="5" class="rm-dot-ab" /><text x="101" y="4">會合</text></g>')
# scale bar: 2 km
px2 = 2 / 111.32 * s
parts.append(f'<g transform="translate({W - px2 - 14:.1f} {H - 14})"><path class="rm-scale" d="M0 -4V0H{px2:.1f}V-4" />'
             f'<text class="rm-time" x="{px2 / 2:.1f}" y="-7" text-anchor="middle">2 公里</text></g>')
# north arrow
parts.append(f'<g transform="translate(16 {H - 22})"><path class="rm-north" d="M0 -9 L4 3 L0 1 L-4 3Z" />'
             '<text class="rm-time" y="12" text-anchor="middle">N</text></g>')
parts.append("</svg>")
svg = "\n".join("              " + p for p in parts)

html = open(HTML, encoding="utf-8").read()
new, n = re.subn(r"(<figure class=\"route-map\">\n)(?:<!--OVERVIEW-->|\s*<svg viewBox=\"0 0 340 .*?</svg>)\n",
                 lambda m: m.group(1) + svg + "\n", html, count=1, flags=re.S)
assert n == 1, "overview slot not found"
open(HTML, "w", encoding="utf-8", newline="\n").write(new)
print("overview", W, "x", H, "road pts", len(allpts))
