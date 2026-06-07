import requests
import re

def get_coordinates(address):
    url = "https://nominatim.openstreetmap.org/search"
    headers = {
        "User-Agent": "NTHU_FinalProject_LunchApp/1.0 (contact: your_email@gmail.com)",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8" 
    }
    
    clean_address = re.sub(r'^\d{3,5}\s*', '', address)
    clean_address = re.sub(r'[\u4e00-\u9fa5]{1,3}里', '', clean_address)
    clean_address = re.sub(r'\d+鄰', '', clean_address)
    clean_address = clean_address.replace('臺', '台')
    
    search_queries = [clean_address]
    if '號' in clean_address:
        fallback_address = re.sub(r'\d+之?\d*號.*', '', clean_address)
        if fallback_address != clean_address:
            search_queries.append(fallback_address)
            
    for query in search_queries:
        params = {"q": query, "format": "json", "limit": 1, "countrycodes": "tw"}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return {
                    "lat": float(data[0]["lat"]),
                    "lon": float(data[0]["lon"]),
                    "display_name": data[0]["display_name"]
                }
        except Exception as e:
            print(f"[ERROR] Nominatim Geocoding 發生錯誤: {e}")
            
    return None

def get_nearby_restaurants(lat, lon, max_time, keyword="", limit=50):
    url = "https://nominatim.openstreetmap.org/search"
    headers = {
        "User-Agent": "NTHU_FinalProject_LunchApp/1.0 (contact: your_email@gmail.com)",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8"
    }
    
    times_to_search = [5]
    if max_time > 5:
        times_to_search.append(max_time)
        
    all_candidates = {} 
    search_term = keyword if keyword else "restaurant"
    
    # 定義非商業設施的黑名單
    blocked_classes = ["office", "highway", "waterway", "boundary", "historic", "landuse"]
    # 如果使用者沒有自訂關鍵字，才額外封鎖一般 building 建築
    if not keyword:
        blocked_classes.append("building")
    
    for t in times_to_search:
        max_straight_distance = t * 80 * 0.75 
        degree_offset = max_straight_distance / 111000
        
        left = lon - degree_offset
        top = lat + degree_offset
        right = lon + degree_offset
        bottom = lat - degree_offset
        viewbox = f"{left},{top},{right},{bottom}"
        
        params = {
            "q": search_term, 
            "lat": lat,
            "lon": lon,
            "format": "json",
            "viewbox": viewbox,
            "bounded": 1,
            "limit": limit
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for item in data:
                name = item.get("display_name").split(",")[0]
                osm_class = item.get("class", "")
                
                # 如果命中黑名單類別，則跳過
                if osm_class in blocked_classes:
                    continue
                    
                if name in ["餐廳", "Restaurant"]:
                    continue
                
                if name not in all_candidates:
                    all_candidates[name] = {
                        "name": name,
                        "lat": float(item["lat"]),
                        "lon": float(item["lon"]),
                        "full_address": item.get("display_name")
                    }
        except Exception as e:
            print(f"[ERROR] Nominatim 同心圓搜尋發生錯誤: {e}")
            
    return list(all_candidates.values())