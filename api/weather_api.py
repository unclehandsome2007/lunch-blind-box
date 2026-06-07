import requests

def check_if_raining(lat, lon):
    """
    使用免費開源的 Open-Meteo API 取得當地即時天氣。
    回傳 True (下雨) 或 False (沒下雨)
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "timezone": "Asia/Taipei"
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        weather_code = data.get("current_weather", {}).get("weathercode", 0)
        
        # 根據 WMO 天氣代碼，50 以上通常代表有降水 (毛毛雨、陣雨、雪、雷雨等)
        if weather_code >= 50:
            return True
        return False
    except Exception as e:
        print(f"[ERROR] 獲取天氣資料失敗: {e}")
        return False # 若抓不到天氣，預設沒下雨