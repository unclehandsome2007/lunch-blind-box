from flask import Flask, jsonify, request, render_template, redirect, url_for
import random
import uuid
import concurrent.futures 
import os
from api.nominatim_api import get_coordinates, get_nearby_restaurants
from api.osrm_api import get_walking_time_and_route
from api.weather_api import check_if_raining
from services.map_service import generate_map
from services.room_service import find_group_intersection_restaurant 

app = Flask(__name__)
app.json.ensure_ascii = False

@app.route('/')
def demo_page():
    # 首頁現在導向你的 Proposal 展示頁面
    return render_template('demo.html')

@app.route('/app')
def index():
    # 原本的抽盲盒系統移到 /app
    return render_template('index.html')

@app.route('/draw_blind_box')
def draw_blind_box():
    address = request.args.get('address')
    max_time = int(request.args.get('max_time', 15))
    keyword = request.args.get('keyword', '').strip() 
    weather_override = request.args.get('weather_override', 'auto')
    
    history_str = request.args.get('history', '')
    history_list = [h.strip() for h in history_str.split(',') if h.strip()]
    
    if not address:
        return render_template('index.html', error="請輸入地址！")

    start_location = get_coordinates(address)
    if not start_location:
        return render_template('index.html', error="找不到該地址，請嘗試輸入知名地標。")
        
    start_lat = start_location["lat"]
    start_lon = start_location["lon"]
    
    if weather_override == 'rain':
        is_raining = True
    elif weather_override == 'clear':
        is_raining = False
    else:
        is_raining = check_if_raining(start_lat, start_lon)

    if is_raining:
        max_time = int(max_time * 0.7)
        if max_time < 1: max_time = 1
    
    candidates = get_nearby_restaurants(start_lat, start_lon, max_time=max_time, keyword=keyword, limit=50)
    if not candidates:
        return render_template('index.html', error=f"附近找不到符合「{keyword}」的餐廳。")

    valid_restaurants = []
    # 請檢查或替換 app.py 內 draw_blind_box 函式中的多執行緒收集區塊：
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_rest = {
            executor.submit(get_walking_time_and_route, start_lat, start_lon, r["lat"], r["lon"]): r 
            for r in candidates
        }
        for future in concurrent.futures.as_completed(future_to_rest):
            rest = future_to_rest[future]
            try:
                route_info = future.result()
                # 【優化：如果是手動輸入關鍵字，步行時間給予額外 2 分鐘的容錯空間，避免因為繞路圖資被一刀切】
                allowed_time = max_time + 2 if keyword else max_time
                if route_info and route_info["walking_minutes"] <= allowed_time:
                    rest["walking_minutes"] = route_info["walking_minutes"]
                    rest["distance_meters"] = route_info["distance_meters"]
                    rest["geometry"] = route_info["geometry"]
                    rest["calories"] = round(route_info["distance_meters"] * 0.05)
                    valid_restaurants.append(rest)
            except Exception as e:
                pass

    if not valid_restaurants:
        return render_template('index.html', error=f"在 {max_time} 分鐘內走不到任何符合的餐廳，請增加時間或換個起點！")

    fresh_restaurants = [r for r in valid_restaurants if r['name'] not in history_list]
    
    if fresh_restaurants:
        chosen_restaurants = random.sample(fresh_restaurants, min(3, len(fresh_restaurants)))
        is_fresh = True
    else:
        chosen_restaurants = random.sample(valid_restaurants, min(3, len(valid_restaurants)))
        is_fresh = False

    chosen_restaurant = chosen_restaurants[0]

    # app.py 裡面的對應呼叫部分
    map_html = generate_map(
        start_lat=start_lat, start_lon=start_lon, 
        dest_lat=chosen_restaurant["lat"], dest_lon=chosen_restaurant["lon"], 
        geometry_geojson=chosen_restaurant["geometry"], # 傳入經緯度矩陣
        start_name=start_location["display_name"].split(",")[0],
        dest_name=chosen_restaurant["name"]
    )

    return render_template('index.html', 
                           restaurant=chosen_restaurant, 
                           chosen_restaurants=chosen_restaurants,
                           start_lat=start_lat, start_lon=start_lon,
                           map_html=map_html, 
                           all_restaurants=valid_restaurants, is_raining=is_raining, 
                           adjusted_time=max_time, keyword=keyword, is_fresh=is_fresh)

# 【新增】供前端 JS 原地切換地圖使用的 API
@app.route('/api/generate_map', methods=['POST'])
def api_generate_map():
    data = request.json
    map_html = generate_map(
        start_lat=data['start_lat'], start_lon=data['start_lon'],
        dest_lat=data['dest_lat'], dest_lon=data['dest_lon'],
        geometry_geojson=data.get('geometry'),
        start_name="起點", dest_name=data.get('dest_name', '目的地')
    )
    return jsonify({"map_html": map_html})

@app.route('/create_room', methods=['POST'])
def create_room():
    room_id = str(uuid.uuid4())[:6].upper()
    max_time = request.form.get('max_time', 15)
    keyword = request.form.get('keyword', '').strip() 
    weather_override = request.form.get('weather_override', 'auto') 
    return redirect(url_for('room', room_id=room_id, max_time=max_time, keyword=keyword, weather_override=weather_override))

@app.route('/room/<room_id>')
def room(room_id):
    max_time = request.args.get('max_time', 15)
    keyword = request.args.get('keyword', '')
    weather_override = request.args.get('weather_override', 'auto') 
    return render_template('room.html', room_id=room_id, max_time=max_time, keyword=keyword, weather_override=weather_override)

@app.route('/api/multi_draw', methods=['POST'])
def multi_draw():
    data = request.json
    users = data.get('users', [])
    max_time = int(data.get('max_time', 15))
    keyword = data.get('keyword', '').strip() 
    history_list = data.get('history', []) 
    weather_override = data.get('weather_override', 'auto') 

    result = find_group_intersection_restaurant(users, max_time, keyword, history_list, weather_override)

    if result.get("error"):
        return jsonify({"error": result["error"]}), 404

    return jsonify({
        "is_raining": result["is_raining"], 
        "chosen_restaurants": result["chosen_restaurants"], 
        "selectedIndex": 0,           
        "is_fresh": result["is_fresh"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)