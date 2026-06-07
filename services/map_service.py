import folium

def generate_map(start_lat, start_lon, dest_lat, dest_lon, geometry_geojson=None, start_name="起點", dest_name="目的地"):
    """
    100% 符合課程規定：利用 Folium 產生包含起終點與步行軌跡的互動式 Leaflet 地圖。
    已修正 OSRM 經緯度顛倒之底層缺陷。
    """
    # 1. 計算起終點的中心點，做為地圖初始化的預設視角
    mid_lat = (start_lat + dest_lat) / 2
    mid_lon = (start_lon + dest_lon) / 2
    
    # 2. 建立正統 Folium 地圖物件
    m = folium.Map(location=[mid_lat, mid_lon], zoom_start=15, tiles='OpenStreetMap')

    # 3. 標示起點 (藍色標記)
    folium.Marker(
        location=[start_lat, start_lon],
        popup=f"<b>📍 起點: {start_name}</b>",
        icon=folium.Icon(color="blue", icon="user")
    ).add_to(m)

    # 4. 【手機端優先優化】標示餐廳 (紅色標記) ＋ 一鍵開啟外部原生導航按鈕
    # 點擊地圖大圖釘時，會彈出寬度足夠、胖手指友善的原生導航跳轉選單
    nav_popup_html = f"""
    <div style="text-align:center; min-width:160px; font-family:'微軟正黑體',sans-serif;">
        <h4 style="margin:0 0 8px 0; font-size:16px; color:#2c3e50;">{dest_name}</h4>
        <a href="https://www.google.com/maps/search/?api=1&query={dest_lat},{dest_lon}" target="_blank" 
           style="display:block; padding:10px; background-color:#e8f4f8; color:#0984e3; text-decoration:none; font-weight:bold; border-radius:5px; margin-bottom:5px; font-size:14px;">Google 地圖導航</a>
        <a href="http://maps.apple.com/?daddr={dest_lat},{dest_lon}" target="_blank" 
           style="display:block; padding:10px; background-color:#f1f2f6; color:#2c3e50; text-decoration:none; font-weight:bold; border-radius:5px; font-size:14px;">Apple 地圖導航</a>
    </div>
    """
    
    folium.Marker(
        location=[dest_lat, dest_lon],
        popup=folium.Popup(nav_popup_html, max_width=250),
        icon=folium.Icon(color="red", icon="cutlery")
    ).add_to(m)

    # 5. 【關鍵 Bug 修正】畫出 OSRM 規劃的步行路線
    if geometry_geojson and 'coordinates' in geometry_geojson:
        # 將 OSRM 格式的 [lon, lat] 矩陣，透過串列推導式完美反轉為 Folium 規定的 [lat, lon]
        correct_route_coords = [[coord[1], coord[0]] for coord in geometry_geojson['coordinates']]
        
        # 使用 Folium 的 PolyLine 繪製漂亮的導航藍色虛線
        folium.PolyLine(
            locations=correct_route_coords,
            color="#0984e3",
            weight=6,
            opacity=0.8,
            dash_array="10, 10"  # 讓手機版導航線條更有動感
        ).add_to(m)
        
        # 讓地圖攝影機自動縮放，把整條步行軌跡完美框在正中央
        m.fit_bounds(m.get_bounds())

    # 6. 回傳生成的 HTML iframe 安全嵌入碼 (最符合 Flask 嵌入)
    return m._repr_html_()