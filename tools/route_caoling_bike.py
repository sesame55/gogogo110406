"""Bike route Fulong -> old Caoling tunnel -> Shicheng along OSM ways; add to streets.json as 'walk'."""
import heapq, json, math, re, sys

OSM, STREETS, HTML = sys.argv[1], sys.argv[2], sys.argv[3]
osm = json.load(open(OSM, encoding="utf-8"))
adj, coord = {}, {}
for e in osm["elements"]:
    t = e.get("tags", {})
    if e["type"] != "way" or "geometry" not in e or "highway" not in t:
        continue
    for nid, g in zip(e["nodes"], e["geometry"]):
        coord[nid] = (g["lat"], g["lon"])
    for a, b in zip(e["nodes"], e["nodes"][1:]):
        (y1, x1), (y2, x2) = coord[a], coord[b]
        d = math.hypot((y2 - y1) * 111320, (x2 - x1) * 111320 * math.cos(math.radians(y1)))
        if t["highway"] == "cycleway":
            d *= 0.5  # prefer the bike path / tunnel
        adj.setdefault(a, []).append((b, d)); adj.setdefault(b, []).append((a, d))


def nearest(p):
    return min(adj, key=lambda n: (coord[n][0] - p[0]) ** 2 + ((coord[n][1] - p[1]) * 0.91) ** 2)


def leg(a, b):
    s, t = nearest(a), nearest(b)
    dist, prev, pq = {s: 0}, {}, [(0, s)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == t:
            break
        if d > dist[u]:
            continue
        for v, w in adj[u]:
            if d + w < dist.get(v, 1e18):
                dist[v], prev[v] = d + w, u
                heapq.heappush(pq, (d + w, v))
    path = [t]
    while path[-1] != s:
        path.append(prev[path[-1]])
    return [coord[n] for n in reversed(path)]


stops = [(25.016202, 121.944785), (25.004497, 121.958090), (24.983539, 121.955212)]
pts = []
for a, b in zip(stops, stops[1:]):
    seg = leg(a, b)
    pts += seg if not pts else seg[1:]
meters = sum(math.hypot((b[0] - a[0]) * 111320, (b[1] - a[1]) * 111320 * math.cos(math.radians(a[0])))
             for a, b in zip(pts, pts[1:]))

streets = json.load(open(STREETS, encoding="utf-8"))
streets["caoling"] = [w for w in streets.get("caoling", []) if w["c"] != "walk"]
streets["caoling"].append({"c": "walk", "n": "", "p": " ".join(f"{a:.6f},{b:.6f}" for a, b in pts)})
json.dump(streets, open(STREETS, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

label = f"約 {meters / 1000:.1f} 公里"
html = open(HTML, encoding="utf-8").read()
html = re.sub(r"單程 (?:<!--BIKELEN-->|約 [\d.]+ 公里)", "單程 " + label, html, count=1)
open(HTML, "w", encoding="utf-8", newline="\n").write(html)
print("bike route", round(meters), "m")
