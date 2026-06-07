import random
import concurrent.futures
from api.nominatim_api import get_nearby_restaurants
from api.osrm_api import get_walking_time_and_route
from api.weather_api import check_if_raining

def find_group_intersection_restaurant(users, max_time, keyword="", history_list=None, weather_override="auto"):
    if history_list is None:
        history_list = []
        
    if not users:
        return {"error": "房間內沒有使用者"}

    center_lat = sum(u['lat'] for u in users) / len(users)
    center_lon = sum(u['lon'] for u in users) / len(users)

    if weather_override == 'rain':
        is_raining = True
    elif weather_override == 'clear':
        is_raining = False
    else:
        is_raining = check_if_raining(center_lat, center_lon)

    if is_raining: 
        max_time = int(max_time * 0.7)
        if max_time < 1: max_time = 1

    candidates = get_nearby_restaurants(center_lat, center_lon, max_time=max_time, keyword=keyword, limit=50)

    def check_restaurant_for_all(rest):
        eta_details = {}
        for user in users:
            route = get_walking_time_and_route(user['lat'], user['lon'], rest['lat'], rest['lon'])
            if not route or route['walking_minutes'] > max_time:
                return None
            calories = round(route['distance_meters'] * 0.05)
            eta_details[user['name']] = {
                "minutes": route['walking_minutes'],
                "calories": calories
            }
        rest['eta_details'] = eta_details
        return rest

    valid_restaurants = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check_restaurant_for_all, r) for r in candidates]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                valid_restaurants.append(res)

    if not valid_restaurants:
        return {"error": "找不到所有人都能在時間內走到的交集餐廳！"}

    fresh_restaurants = [r for r in valid_restaurants if r['name'] not in history_list]
    
    # 【升級：一次抽出 3 家作為備選方案】
    if fresh_restaurants:
        chosen_list = random.sample(fresh_restaurants, min(3, len(fresh_restaurants)))
        is_fresh = True
    else:
        chosen_list = random.sample(valid_restaurants, min(3, len(valid_restaurants)))
        is_fresh = False
    
    return {
        "is_raining": is_raining,
        "chosen_restaurants": chosen_list, # 變成回傳一個陣列
        "selectedIndex": 0,                # 預設選中第一家
        "is_fresh": is_fresh,
        "error": None
    }