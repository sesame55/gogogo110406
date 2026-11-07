"""List named places (food, sights, temples, parks…) around a point, nearest first.

Usage: python tools/list_pois.py CACHE.json OUT.txt LAT LNG "S,W,N,E"
The Overpass response is cached in CACHE.json; delete it to refetch.
"""
import json, math, os, sys, time, urllib.parse, urllib.request

CACHE, OUT, LAT, LNG, BBOX = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
Q = f"""[out:json][timeout:120];
(nwr["amenity"~"^(restaurant|cafe|fast_food|ice_cream|food_court|marketplace|place_of_worship|public_bath)$"]["name"]({BBOX});
 nwr["shop"~"^(bakery|confectionery|pastry|deli|tea|beverages)$"]["name"]({BBOX});
 nwr["tourism"]["name"]({BBOX});
 nwr["leisure"~"^(park|garden)$"]["name"]({BBOX});
 nwr["historic"]["name"]({BBOX}););
out center tags;"""
HOSTS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
         "https://overpass.private.coffee/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]

if not os.path.exists(CACHE):
    data = urllib.parse.urlencode({"data": Q}).encode()
    for i in range(20):
        try:
            req = urllib.request.Request(HOSTS[i % len(HOSTS)], data=data, headers={"User-Agent": "trip-guide-minimap/1.0"})
            with urllib.request.urlopen(req, timeout=150) as r:
                json.dump(json.load(r), open(CACHE, "w", encoding="utf-8"))
            break
        except Exception as e:
            print("retry", e, file=sys.stderr)
            time.sleep(6)
    else:
        sys.exit("all retries failed")

rows = []
for e in json.load(open(CACHE, encoding="utf-8"))["elements"]:
    t = e.get("tags", {})
    lat = e.get("lat") or e["center"]["lat"]
    lon = e.get("lon") or e["center"]["lon"]
    dist = math.hypot((lat - LAT) * 111320, (lon - LNG) * 111320 * math.cos(math.radians(lat)))
    kind = next((f"{k}={t[k]}" for k in ("amenity", "shop", "tourism", "leisure", "historic") if k in t), "")
    extra = " ".join(f"{k}={t[k]}" for k in ("opening_hours", "cuisine", "addr:street", "addr:housenumber") if k in t)
    rows.append((dist, f"{dist:5.0f}m {lat:.6f},{lon:.6f} {t.get('name', '(無名)')} [{kind}] {extra}"))
with open(OUT, "w", encoding="utf-8") as f:
    for _, r in sorted(rows):
        f.write(r + "\n")
print(len(rows), "places ->", OUT)
