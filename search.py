import requests  # pip install requests
import time

# ---------- 新增：依 OSM 標籤判斷類別 ----------
def get_category(tags):
    """根據 OSM 標籤回傳統一類別字串"""
    network = tags.get("network", "").lower()
    # 交流道（高架交流道節點）
    if tags.get("highway") == "motorway_junction":
        return "交流道"
    # 國道系統：高速公路/國道
    if tags.get("highway") == "motorway" or (tags.get("route") == "road" and "國道" in tags.get("network", "")):
        return "國道系統"
    # 三鐵優先
    if "高鐵" in network or tags.get("station") == "high_speed":
        return "高鐵站"
    if "捷運" in network or tags.get("station") == "subway" or tags.get("railway") == "subway":
        return "捷運站"
    if "鐵" in network or tags.get("railway") in ("station", "halt"):
        return "火車站"
    # 公車站
    if tags.get("highway") == "bus_stop" or tags.get("amenity") == "bus_station":
        return "公車站"
    # 公園
    if tags.get("leisure") == "park":
        return "公園"
    # 傳統市場
    if tags.get("amenity") == "marketplace" or tags.get("shop") == "market":
        return "傳統市場"
    # 學校
    if tags.get("amenity") == "school":
        return "學校"
    # 餐飲
    if tags.get("amenity") in ("restaurant", "cafe", "fast_food"):
        return "餐飲"
    # 超市/賣場
    if tags.get("shop") in ("supermarket", "mall", "department_store", "convenience"):
        return "超市/賣場"
    # 公共建設
    if tags.get("amenity") in ("townhall", "library", "police", "fire_station", "post_office", "courthouse"):
        return "公共建設"
    # 醫院
    if tags.get("amenity") == "hospital" or tags.get("healthcare") == "hospital":
        return "醫院"
    return "其他"


def fetch_poi(lat: float, lon: float, radius: int = 2000, max_retries: int = 3, backoff: int = 5):
    """
    向 Overpass API 查詢 POI，並在遇到 504 或網路錯誤時重試。
    radius：查詢半徑，單位公尺
    """
    query = f"""
    [out:json][timeout:60];
    (
      /* 交流道 */
      node(around:{radius},{lat},{lon})[highway=motorway_junction];
      way(around:{radius},{lat},{lon})[highway=motorway_junction];
      relation(around:{radius},{lat},{lon})[highway=motorway_junction];

      /* 國道系統 */
      way(around:{radius},{lat},{lon})[highway=motorway];
      relation(around:{radius},{lat},{lon})[route=road][network~"國道"];

      /* 三鐵與公共交通 */
      node(around:{radius},{lat},{lon})[railway=station];
      way(around:{radius},{lat},{lon})[railway=station];
      relation(around:{radius},{lat},{lon})[railway=station];
      node(around:{radius},{lat},{lon})[station=high_speed];
      way(around:{radius},{lat},{lon})[station=high_speed];
      relation(around:{radius},{lat},{lon})[station=high_speed];
      node(around:{radius},{lat},{lon})[station=subway];
      way(around:{radius},{lat},{lon})[station=subway];
      relation(around:{radius},{lat},{lon})[station=subway];
      node(around:{radius},{lat},{lon})[railway=subway];
      way(around:{radius},{lat},{lon})[railway=subway];
      relation(around:{radius},{lat},{lon})[railway=subway];
      node(around:{radius},{lat},{lon})[public_transport=station][subway=yes];
      way(around:{radius},{lat},{lon})[public_transport=station][subway=yes];
      relation(around:{radius},{lat},{lon})[public_transport=station][subway=yes];

      /* 公車站 */
      node(around:{radius},{lat},{lon})[highway=bus_stop];
      way(around:{radius},{lat},{lon})[highway=bus_stop];
      relation(around:{radius},{lat},{lon})[highway=bus_stop];
      node(around:{radius},{lat},{lon})[amenity=bus_station];
      way(around:{radius},{lat},{lon})[amenity=bus_station];
      relation(around:{radius},{lat},{lon})[amenity=bus_station];

      /* 公園 */
      node(around:{radius},{lat},{lon})[leisure=park];
      way(around:{radius},{lat},{lon})[leisure=park];
      relation(around:{radius},{lat},{lon})[leisure=park];

      /* 傳統市場 */
      node(around:{radius},{lat},{lon})[amenity=marketplace];
      way(around:{radius},{lat},{lon})[amenity=marketplace];
      relation(around:{radius},{lat},{lon})[amenity=marketplace];
      node(around:{radius},{lat},{lon})[shop=market];
      way(around:{radius},{lat},{lon})[shop=market];
      relation(around:{radius},{lat},{lon})[shop=market];

      /* 生活設施 */
      node(around:{radius},{lat},{lon})[shop=convenience];
      way(around:{radius},{lat},{lon})[shop=convenience];
      relation(around:{radius},{lat},{lon})[shop=convenience];
      node(around:{radius},{lat},{lon})[shop=supermarket];
      way(around:{radius},{lat},{lon})[shop=supermarket];
      relation(around:{radius},{lat},{lon})[shop=supermarket];
      node(around:{radius},{lat},{lon})[shop=department_store];
      way(around:{radius},{lat},{lon})[shop=department_store];
      relation(around:{radius},{lat},{lon})[shop=department_store];
      node(around:{radius},{lat},{lon})[shop=mall];
      way(around:{radius},{lat},{lon})[shop=mall];
      relation(around:{radius},{lat},{lon})[shop=mall];
      node(around:{radius},{lat},{lon})[amenity=restaurant];
      way(around:{radius},{lat},{lon})[amenity=restaurant];
      relation(around:{radius},{lat},{lon})[amenity=restaurant];
      node(around:{radius},{lat},{lon})[amenity=cafe];
      way(around:{radius},{lat},{lon})[amenity=cafe];
      relation(around:{radius},{lat},{lon})[amenity=cafe];
      node(around:{radius},{lat},{lon})[amenity=fast_food];
      way(around:{radius},{lat},{lon})[amenity=fast_food];
      relation(around:{radius},{lat},{lon})[amenity=fast_food];
      node(around:{radius},{lat},{lon})[amenity=school];
      way(around:{radius},{lat},{lon})[amenity=school];
      relation(around:{radius},{lat},{lon})[amenity=school];
      node(around:{radius},{lat},{lon})[amenity=townhall];
      way(around:{radius},{lat},{lon})[amenity=townhall];
      relation(around:{radius},{lat},{lon})[amenity=townhall];
      node(around:{radius},{lat},{lon})[amenity=library];
      way(around:{radius},{lat},{lon})[amenity=library];
      relation(around:{radius},{lat},{lon})[amenity=library];
      node(around:{radius},{lat},{lon})[amenity=police];
      way(around:{radius},{lat},{lon})[amenity=police];
      relation(around:{radius},{lat},{lon})[amenity=police];
      node(around:{radius},{lat},{lon})[amenity=fire_station];
      way(around:{radius},{lat},{lon})[amenity=fire_station];
      relation(around:{radius},{lat},{lon})[amenity=fire_station];
      node(around:{radius},{lat},{lon})[amenity=post_office];
      way(around:{radius},{lat},{lon})[amenity=post_office];
      relation(around:{radius},{lat},{lon})[amenity=post_office];
      node(around:{radius},{lat},{lon})[amenity=courthouse];
      way(around:{radius},{lat},{lon})[amenity=courthouse];
      relation(around:{radius},{lat},{lon})[amenity=courthouse];

      /* 醫院 */
      node(around:{radius},{lat},{lon})[amenity=hospital];
      way(around:{radius},{lat},{lon})[amenity=hospital];
      relation(around:{radius},{lat},{lon})[amenity=hospital];
      node(around:{radius},{lat},{lon})[healthcare=hospital];
      way(around:{radius},{lat},{lon})[healthcare=hospital];
      relation(around:{radius},{lat},{lon})[healthcare=hospital];
    );
    out center;
    """
    url = "https://overpass-api.de/api/interpreter"
    resp = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, data={"data": query}, timeout=120)
            resp.raise_for_status()
            break
        except requests.exceptions.HTTPError as e:
            if resp is not None and resp.status_code == 504 and attempt < max_retries:
                time.sleep(backoff * attempt)
                continue
            raise
        except requests.exceptions.RequestException:
            if attempt < max_retries:
                time.sleep(backoff * attempt)
                continue
            raise

    data = resp.json()
    results = []
    for e in data.get("elements", []):
        tags = e.get("tags", {})
        # 跳過路線或名稱含“線”
        if tags.get("type") == "route" or tags.get("route"):
            continue
        name = tags.get("name", "")
        # 過濾無名稱與路線
        if not name or "線" in name:
            continue
        cat = get_category(tags)
        if cat == "其他":
            continue
        results.append({
            "name": name,
            "category": cat,
            "lat": e.get("lat") or e.get("center", {}).get("lat"),
            "lon": e.get("lon") or e.get("center", {}).get("lon"),
            "osm_tags": tags,
        })
    return results


if __name__ == "__main__":
    # 範例位置：附近 POI 搜尋 (radius 預設 2000 公尺，可自行修改)
    lat, lon = 23.719069456631303, 120.43518146935267
    for p in fetch_poi(lat, lon, radius=1500):
        print(f"{p['category']}：{p['name']} ({p['lat']}, {p['lon']})")
        #print("  OSM 標籤：", p['osm_tags'])
