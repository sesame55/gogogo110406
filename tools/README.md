# 地圖資料工具

網頁的小地圖（街道、步道、湖泊、步行／騎車路線）和太平山路線總覽圖，都是用這裡的腳本從 OpenStreetMap 資料產生的。
從專案根目錄執行，需要 Python 3。

## 檔案

| 檔案 | 用途 |
|---|---|
| `streets.py` | 依 `index.html` 裡每個 `data-map` 區塊的店家座標，算出地圖範圍、抓道路並簡化，輸出 `data/streets.json` |
| `route_jiaoxi_walk.py` | 沿街道算第 2 天晚上礁溪散步路線，寫進 `streets.json`，並更新頁面上的公里數 |
| `route_caoling_bike.py` | 算第 3 天福隆→舊草嶺隧道→石城的騎車路線，寫進 `streets.json`，並更新單程公里數 |
| `build_streets_js.py` | 把 `data/streets.json` 轉成網頁載入的 `streets.js` |
| `fetch_tps_osm.py` | 抓太平山一帶道路與景點，存成 `data/tps_osm.json` |
| `tps_overview.py` | 依實際道路與比例畫太平山路線總覽圖，寫進 `index.html` |
| `day1_freeway.py` | 第 1 天國道一號北上→瑞芳路線圖與時間表（交流道、服務區實際座標），改出發時間或休息站就改檔案開頭的設定再執行 |
| `list_pois.py` | 列出某個地點周邊的店家、景點，依距離排序（找新店家時用） |
| `data/osm_*.json` | 各地圖抓下來的 OpenStreetMap 原始資料（快取） |

## 重新產生地圖資料

```sh
# OFFLINE=1：只用 data/ 裡的快取，不連網（Overpass 伺服器常忙線）
OFFLINE=1 python tools/streets.py index.html tools/data/streets.json
python tools/route_jiaoxi_walk.py tools/data/osm_jxnight.json tools/data/streets.json index.html
python tools/route_caoling_bike.py tools/data/osm_caoling.json tools/data/streets.json index.html
python tools/build_streets_js.py tools/data/streets.json streets.js
```

`streets.py` 會整份重建 `streets.json`，所以之後一定要再跑兩支路線腳本，不然散步和騎車路線會消失。

太平山總覽圖：

```sh
python tools/tps_overview.py index.html tools/data/tps_osm.json tools/data/osm_tpscuifeng.json
```

## 新增一張地圖

1. 在 `index.html` 加一個 `<details class="card food" data-map="新代號">` 區塊，店家用 `<li class="shop" data-lat data-lng data-short>`。
2. 在 `app.js` 的 `LM` 加上同名設定（車站、飯店地標、是否畫步行圈）。
3. 在 `streets.py` 的 `LM` 加同名項目；要畫步道、湖泊就把代號加進 `WALK`。
4. 刪掉 `OFFLINE=1` 跑一次 `streets.py` 抓新資料，再照上面的步驟產生 `streets.js`。

找周邊店家可以先用：

```sh
python tools/list_pois.py tools/data/poi_cache.json pois.txt 25.0159 121.9447 "24.98,121.93,25.05,122.01"
```

地圖資料 © OpenStreetMap 貢獻者，以 ODbL 授權；網頁上已標註出處。
