import requests

def get_walking_time_and_route(start_lat, start_lon, dest_lat, dest_lon):
    """
    呼叫 OSRM API 計算兩點之間的真實步行時間與幾何路線
    """
    coordinates = f"{start_lon},{start_lat};{dest_lon},{dest_lat}"
    url = f"http://router.project-osrm.org/route/v1/foot/{coordinates}"
    params = {
        "overview": "full",
        "geometries": "geojson"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == "Ok" and len(data["routes"]) > 0:
            route = data["routes"][0]
            distance = route["distance"] # 取得精確的物理距離 (公尺)
            
            # 【關鍵修改】放棄 OSRM 壞掉的時間，我們自己用距離來算！
            # 以每分鐘走 80 公尺來計算合理步行時間
            duration_minutes = round(distance / 80)
            
            geometry = route["geometry"] 
            
            return {
                "walking_minutes": duration_minutes,
                "geometry": geometry,
                "distance_meters": round(distance, 1) # 順便把距離四捨五入到小數點第一位，讓網頁顯示更乾淨
            }
        return None
    except Exception as e:
        print(f"[ERROR] OSRM 路線計算發生錯誤: {e}")
        return None