"""Fetch Taipingshan roads + named POIs from Overpass, cache to tps_osm.json, list POIs."""
import json, os, sys, time, urllib.parse, urllib.request

OUT = sys.argv[1]
BBOX = "24.45,121.45,24.66,121.68"
Q = f"""[out:json][timeout:150];
(way["highway"~"^(trunk|primary|secondary|tertiary|unclassified|residential|service|track)$"]({BBOX});)->.r;
.r out geom;
(nwr["name"~"鳩之澤|仁澤|土場|見晴|太平山|翠峰|山毛櫸|觀日|白嶺|遊客中心|望洋|檜木|鐵杉|蹦蹦|茂興|三疊|雲海|中央階梯|俱樂部|販賣|咖啡|餐廳"]({BBOX});)->.p;
.p out center tags;"""

HOSTS = ["https://overpass-api.de/api/interpreter",
         "https://overpass.kumi.systems/api/interpreter",
         "https://overpass.private.coffee/api/interpreter",
         "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]

if not os.path.exists(OUT):
    data = urllib.parse.urlencode({"data": Q}).encode()
    for attempt in range(20):
        url = HOSTS[attempt % len(HOSTS)]
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "trip-guide-minimap/1.0"})
            with urllib.request.urlopen(req, timeout=180) as r:
                res = json.load(r)
            json.dump(res, open(OUT, "w", encoding="utf-8"))
            break
        except Exception as e:
            print("retry", url, e, file=sys.stderr)
            time.sleep(6)
    else:
        sys.exit("all retries failed")

if len(sys.argv) > 2:
    sys.stdout = open(sys.argv[2], "w", encoding="utf-8")
res = json.load(open(OUT, encoding="utf-8"))
roads = [e for e in res["elements"] if e["type"] == "way" and "geometry" in e and "highway" in e.get("tags", {})]
print("roads:", len(roads))
for e in res["elements"]:
    t = e.get("tags", {})
    if "name" not in t or ("highway" in t and "geometry" in e):
        continue
    lat = e.get("lat") or e.get("center", {}).get("lat")
    lon = e.get("lon") or e.get("center", {}).get("lon")
    kind = next((f"{k}={t[k]}" for k in ("tourism", "amenity", "natural", "leisure", "highway", "railway", "historic", "shop", "building") if k in t), "")
    print(f'{e["type"][0]} {lat:.5f},{lon:.5f}  {t["name"]}  [{kind}]')
