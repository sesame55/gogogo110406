"""Day 1 route: National Freeway 1 northbound -> Badu -> Prov. Hwy 62 -> Ruifang.

The departure point is deliberately left out: the map and table start at the
first service area on the freeway.

Draws a true-proportion SVG from real interchange / service-area coordinates
(OpenStreetMap), estimates pass times from freeway km markers, and writes
the figure + timetable into index.html (between the DAY1-FREEWAY markers).

Usage: python tools/day1_freeway.py index.html
"""
import math, re, sys

HTML = sys.argv[1]
DEPART = "06:20"  # shown in the table only, no place
START = 6 * 60 + 30  # 06:30 passing Rende service area

# name, lat, lng, km (freeway km marker; None = interpolate), kind, note
# kind: start / rest / pass / city / end
STOPS = [
    ("仁德服務區", 22.9060, 120.2659, 335, "start", "上國道後第一個服務區，路過"),
    ("永康（台南）", 23.0420, 120.2515, 319, "city", ""),
    ("新營服務區", 23.3397, 120.3121, None, "pass", ""),
    ("嘉義", 23.4950, 120.3918, 264, "city", ""),
    ("西螺服務區", 23.7890, 120.4783, 229, "rest", "休息約 20 分鐘"),
    ("彰化", 24.0650, 120.5230, 198, "city", ""),
    ("台中", 24.1752, 120.6304, 178, "city", ""),
    ("泰安服務區", 24.3296, 120.7139, None, "pass", ""),
    ("新竹", 24.7987, 121.0081, 95, "city", ""),
    ("湖口服務區", 24.8596, 121.0109, None, "rest", "休息約 20 分鐘"),
    ("中壢服務區", 25.0040, 121.2520, None, "pass", ""),
    ("台北（圓山）", 25.0730, 121.5330, 23, "city", ""),
    ("汐止", 25.0700, 121.6420, 11, "city", ""),
    ("八堵交流道", 25.1034, 121.7206, 2, "pass", "下國道一號，接台 62 萬瑞快速道路"),
    ("瑞芳交流道", 25.1137, 121.7937, None, "end", "下交流道到瑞芳車站約 5 分鐘"),
]
# label placement overrides where the route bunches up near Taipei: (dx, dy, anchor) or None to hide
LABEL_AT = {
    "新竹": None,
    "台北（圓山）": None,
    "汐止": None,
    "八堵交流道": (-6, -12, "end"),
    "瑞芳交流道": (8, 22, "end"),
}
REST_MIN = 20
TAI62_KM = 11  # Badu -> Ruifang interchange on Prov. Hwy 62 (approx.)


def hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


# interpolate km markers for service areas by straight-line share between known neighbours
kms = [s[3] for s in STOPS]
for i, s in enumerate(STOPS[:-1]):
    if kms[i] is None:
        j0 = max(j for j in range(i) if kms[j] is not None)
        j1 = min(j for j in range(i + 1, len(STOPS) - 1) if kms[j] is not None)
        d0 = sum(hav(STOPS[k][1:3], STOPS[k + 1][1:3]) for k in range(j0, i))
        d1 = sum(hav(STOPS[k][1:3], STOPS[k + 1][1:3]) for k in range(i, j1))
        kms[i] = round(kms[j0] - (kms[j0] - kms[j1]) * d0 / (d0 + d1))

# times: 85 km/h on the freeway, 60 km/h inside the Taipei section (km < 30), 50 km/h on Hwy 62
t, times = START, []
for i, s in enumerate(STOPS):
    if i:
        if s[4] == "end":
            t += TAI62_KM / 50 * 60
        else:
            a, b = kms[i - 1], kms[i]
            fast = max(0, a - max(b, 30))
            slow = (a - b) - fast
            t += fast / 85 * 60 + slow / 60 * 60
    times.append(t)
    if s[4] == "rest":
        t += REST_MIN


def hm(m):
    m = int(round(m / 5) * 5)
    return f"{m // 60:02d}:{m % 60:02d}"


total_km = kms[0] - kms[-2] + TAI62_KM

# ---- SVG (north up, true proportion) ----
lat0 = sum(s[1] for s in STOPS) / len(STOPS)
k = math.cos(math.radians(lat0))
minlat, maxlat = min(s[1] for s in STOPS), max(s[1] for s in STOPS)
minlng, maxlng = min(s[2] for s in STOPS), max(s[2] for s in STOPS)
W, PADT, PADB = 340, 26, 30
sc = 440 / (maxlat - minlat)
H = round((maxlat - minlat) * sc + PADT + PADB)
ox = (W - (maxlng - minlng) * k * sc) / 2


def P(lat, lng):
    return ox + (lng - minlng) * k * sc, PADT + (maxlat - lat) * sc


pts = [P(s[1], s[2]) for s in STOPS]
d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
svg = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="國道一號路線圖：北上經台南、嘉義、台中、新竹、台北到八堵，接台 62 到瑞芳">',
       '<g fill="none" stroke-linecap="round" stroke-linejoin="round">',
       f'<path class="rm-road-edge" d="{d}" />', f'<path class="rm-road" d="{d}" />',
       f'<path class="rm-a" d="{d}" />', "</g>"]
for (x, y), s, tm in zip(pts, STOPS, times):
    name, kind = s[0], s[4]
    cls = {"start": "rm-dot-ab", "end": "rm-dot-ab", "rest": "rm-dot-b", "pass": "rm-dot", "city": None}[kind]
    if cls:
        r = 7 if kind in ("start", "end", "rest") else 4.5
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" class="{cls}" />')
    if name in LABEL_AT and LABEL_AT[name] is None:
        continue
    if name in LABEL_AT:
        dx, dy, anchor = LABEL_AT[name]
        tx, ty = x + dx, y + dy
    else:
        right = x < W * 0.55
        (tx, anchor), ty = ((x + 11, "start") if right else (x - 11, "end")), y + 4
    label_cls = "rm-name" if kind != "city" else "rm-time"
    svg.append(f'<text class="{label_cls}" x="{tx:.1f}" y="{ty:.1f}" text-anchor="{anchor}">{name}</text>')
    if kind in ("start", "end", "rest"):
        svg.append(f'<text class="rm-time" x="{tx:.1f}" y="{ty + 13:.1f}" text-anchor="{anchor}">{hm(tm)}'
                   + (f"–{hm(tm + REST_MIN)}" if kind == "rest" else "") + "</text>")
svg.append(f'<g class="rm-legend" transform="translate({W - 128} {H - 40})">'
           '<circle cx="0" cy="0" r="5" class="rm-dot-b" /><text x="9" y="4">休息站</text>'
           '<circle cx="62" cy="0" r="4" class="rm-dot" /><text x="70" y="4">路過</text></g>')
px100 = 100 / 111.32 * sc
svg.append(f'<g transform="translate({W - px100 - 14:.1f} {H - 12})"><path class="rm-scale" d="M0 -4V0H{px100:.1f}V-4" />'
           f'<text class="rm-time" x="{px100 / 2:.1f}" y="-7" text-anchor="middle">100 公里</text></g>')
svg.append(f'<g transform="translate(18 {H - 20})"><path class="rm-north" d="M0 -9 L4 3 L0 1 L-4 3Z" />'
           '<text class="rm-time" y="12" text-anchor="middle">N</text></g>')
svg.append("</svg>")

rows = [f'                      <tr><td class="n">{DEPART}</td><td class="n"><b>出發</b></td><td class="n">—</td><td>上國道一號北上</td></tr>']
for s, km, tm in zip(STOPS, kms, times):
    if s[4] == "city":
        continue
    when = hm(tm) + (f"–{hm(tm + REST_MIN)}" if s[4] == "rest" else "")
    kmtxt = f"{km}K" if s[4] != "end" else "台62"
    note = s[5] or ("路過" if s[4] == "pass" else "")
    strong = s[4] in ("start", "rest", "end")
    nm = f"<b>{s[0]}</b>" if strong else s[0]
    rows.append(f'                      <tr><td class="n">{when}</td><td class="n">{nm}</td><td class="n">{kmtxt}</td><td>{note}</td></tr>')

block = f"""<!--DAY1-FREEWAY-->
                <figure class="route-map">
{chr(10).join('                  ' + x for x in svg)}
                  <figcaption class="sm muted">依交流道、服務區實際位置繪製，從國道上第一個服務區開始。預估 {hm(times[-1])} 到瑞芳。</figcaption>
                </figure>
                <div class="table-wrap">
                  <table>
                    <thead>
                      <tr><th>預估時間</th><th>地點</th><th>里程</th><th>說明</th></tr>
                    </thead>
                    <tbody>
{chr(10).join(rows)}
                    </tbody>
                  </table>
                </div>
                <p class="sm muted" style="margin: 6px 0 0">
                  時間以國道里程、時速約 85 公里（台北路段約 60 公里）估算；休息站和停留時間依司機安排，塞車會延後。
                </p>
                <!--/DAY1-FREEWAY-->"""

html = open(HTML, encoding="utf-8").read()
if "<!--DAY1-FREEWAY-->" in html:
    html = re.sub(r"<!--DAY1-FREEWAY-->.*?<!--/DAY1-FREEWAY-->", lambda m: block, html, flags=re.S)
else:
    anchor = "                <h4>出發</h4>\n                <p>車程很長，帶頸枕、暈車藥和小點心。</p>\n"
    assert html.count(anchor) == 1, "day 1 anchor not found"
    html = html.replace(anchor, "                <h4>出發・國道一號北上</h4>\n"
                        "                <p>車程很長，帶頸枕、暈車藥和小點心。中途在服務區休息兩次。</p>\n"
                        "                " + block + "\n", 1)
open(HTML, "w", encoding="utf-8", newline="\n").write(html)
print("total km", round(total_km), "arrive", hm(times[-1]))
for s, km, tm in zip(STOPS, kms, times):
    print(f"  {hm(tm)}  {km}  {s[0]}")
