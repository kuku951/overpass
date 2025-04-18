import requests  # pip install requests
import time

# ---------- 新增：依 OSM 標籤判斷類別 ----------
def get_category(tags):
    """根據 OSM 標籤回傳統一類別字串"""
    network = tags.get("network", "").lower()
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
    # 學校
    if tags.get("amenity") == "school":
        return "學校"
    # 便利商店
    if tags.get("shop") == "convenience":
        return "便利商店"
    # 醫院
    if tags.get("amenity") == "hospital" or tags.get("healthcare") == "hospital":
        return "醫院"
    return "其他"


def fetch_poi(lat: float, lon: float, radius: int = 2000, max_retries: int = 3, backoff: int = 5):
    """
    向 Overpass API 查詢 POI，並在遇到 504 或網路錯誤時重試。
    radius：查詢半徑，單位公尺
    同時回傳原始 OSM 標籤以供檢視。
    """
    query = f"""
    [out:json][timeout:60];
    (
      /* 便利商店 */
      node(around:{radius},{lat},{lon})[shop=convenience];
      way(around:{radius},{lat},{lon})[shop=convenience];
      relation(around:{radius},{lat},{lon})[shop=convenience];

      /* 醫院 */
      node(around:{radius},{lat},{lon})[amenity=hospital];
      way(around:{radius},{lat},{lon})[amenity=hospital];
      relation(around:{radius},{lat},{lon})[amenity=hospital];
      node(around:{radius},{lat},{lon})[healthcare=hospital];
      way(around:{radius},{lat},{lon})[healthcare=hospital];
      relation(around:{radius},{lat},{lon})[healthcare=hospital];

      /* 學校 */
      node(around:{radius},{lat},{lon})[amenity=school];
      way(around:{radius},{lat},{lon})[amenity=school];
      relation(around:{radius},{lat},{lon})[amenity=school];

      /* 公車站 */
      node(around:{radius},{lat},{lon})[highway=bus_stop];
      way(around:{radius},{lat},{lon})[highway=bus_stop];
      relation(around:{radius},{lat},{lon})[highway=bus_stop];
      node(around:{radius},{lat},{lon})[amenity=bus_station];
      way(around:{radius},{lat},{lon})[amenity=bus_station];
      relation(around:{radius},{lat},{lon})[amenity=bus_station];

      /* 台鐵站 */
      node(around:{radius},{lat},{lon})[railway=station];
      way(around:{radius},{lat},{lon})[railway=station];
      relation(around:{radius},{lat},{lon})[railway=station];

      /* 高鐵站 */
      node(around:{radius},{lat},{lon})[station=high_speed];
      way(around:{radius},{lat},{lon})[station=high_speed];
      relation(around:{radius},{lat},{lon})[station=high_speed];

      /* 捷運／地鐵站 */
      node(around:{radius},{lat},{lon})[station=subway];
      way(around:{radius},{lat},{lon})[station=subway];
      relation(around:{radius},{lat},{lon})[station=subway];
      node(around:{radius},{lat},{lon})[railway=subway];
      way(around:{radius},{lat},{lon})[railway=subway];
      relation(around:{radius},{lat},{lon})[railway=subway];
      node(around:{radius},{lat},{lon})[public_transport=station][subway=yes];
      way(around:{radius},{lat},{lon})[public_transport=station][subway=yes];
      relation(around:{radius},{lat},{lon})[public_transport=station][subway=yes];
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
            "osm_tags": tags,  # 保留原始 OSM 標籤
        })
    return results


if __name__ == "__main__":
    # 範例位置：附近 POI 搜尋 (radius 預設 2000 公尺，可自行修改)
    lat, lon = 23.711098885837878, 120.5445971129043
    for p in fetch_poi(lat, lon, radius=1000):  # 例如查 1.5 公里範圍
        print(f"{p['category']}：{p['name']} ({p['lat']}, {p['lon']})")
        #print("  OSM 標籤：", p['osm_tags'])