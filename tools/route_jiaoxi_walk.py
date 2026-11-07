"""Compute the night-walk route along OSM streets and add it to streets.json as class 'walk'."""
import heapq, json, math, re, sys

OSM, STREETS, HTML = sys.argv[1], sys.argv[2], sys.argv[3]
osm = json.load(open(OSM, encoding="utf-8"))
adj, coord = {}, {}
for e in osm["elements"]:
    t = e.get("tags", {})
    if e["type"] != "way" or "geometry" not in e or "highway" not in t or t["highway"] in ("motorway", "trunk"):
        continue
    for nid, g in zip(e["nodes"], e["geometry"]):
        coord[nid] = (g["lat"], g["lon"])
    for a, b in zip(e["nodes"], e["nodes"][1:]):
        (y1, x1), (y2, x2) = coord[a], coord[b]
        d = math.hypot((y2 - y1) * 111320, (x2 - x1) * 111320 * math.cos(math.radians(y1)))
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
    return [coord[n] for n in reversed(path)], dist[t]


HOTEL = (24.8288597, 121.7672528)
stops = [HOTEL, (24.82687, 121.771924), (24.827558, 121.772066),
         (24.8281157, 121.7724378), HOTEL]
pts, total = [], 0
for a, b in zip(stops, stops[1:]):
    seg, d = leg(a, b)
    pts += seg if not pts else seg[1:]
    total += d

streets = json.load(open(STREETS, encoding="utf-8"))
streets["jxnight"] = [w for w in streets.get("jxnight", []) if w["c"] != "walk"]
streets["jxnight"].append({"c": "walk", "n": "", "p": " ".join(f"{a:.6f},{b:.6f}" for a, b in pts)})
json.dump(streets, open(STREETS, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

km = total / 1000
mins = round(total / 70 / 5) * 5  # ~70 m/min stroll, rounded to 5 min
label = f"約 {km:.1f} 公里（純走路約 {mins} 分鐘）"
html = open(HTML, encoding="utf-8").read()
html = re.sub(r"<!--WALKLEN-->|約 [\d.]+ 公里（純走路約 \d+ 分鐘）", label, html, count=1)
open(HTML, "w", encoding="utf-8", newline="\n").write(html)
print("walk", round(total), "m", label)
