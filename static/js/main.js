// PWA Service Worker 註冊
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js').then(() => console.log("PWA Ready"));
}

function prepareHistory() {
    let history = JSON.parse(localStorage.getItem('lunch_history_v2') || '[]');
    const historyInput = document.getElementById('history-input');
    if (historyInput) historyInput.value = history.map(h => h.name).join(',');
}

function startGachaAnimation(event, formId) {
    event.preventDefault(); 
    prepareHistory();
    const overlay = document.getElementById('gacha-overlay');
    if (overlay) {
        overlay.classList.remove('hidden');
        overlay.classList.add('flex');
    }
    setTimeout(() => { document.getElementById(formId).submit(); }, 2500);
}

function saveToHistory(restaurantName) {
    let history = JSON.parse(localStorage.getItem('lunch_history_v2') || '[]');
    let today = new Date().toLocaleDateString();
    let existingItem = history.find(h => h.name === restaurantName);
    
    if (existingItem) {
        existingItem.visitCount = (existingItem.visitCount || 1) + 1;
        existingItem.lastDate = today;
    } else {
        history.push({ id: Date.now(), name: restaurantName, date: today, price: '', rating: '', visitCount: 1 });
    }
    if(history.length > 20) history.shift(); 
    localStorage.setItem('lunch_history_v2', JSON.stringify(history));
}

function removeHistoryByName(restaurantName) {
    let history = JSON.parse(localStorage.getItem('lunch_history_v2') || '[]');
    let existingItem = history.find(h => h.name === restaurantName);
    if (existingItem) {
        if (existingItem.visitCount > 1) existingItem.visitCount -= 1; 
        else history = history.filter(h => h.name !== restaurantName); 
        localStorage.setItem('lunch_history_v2', JSON.stringify(history));
    }
}

function deleteHistoryItem(id) {
    let history = JSON.parse(localStorage.getItem('lunch_history_v2') || '[]');
    history = history.filter(h => h.id !== id);
    localStorage.setItem('lunch_history_v2', JSON.stringify(history));
    renderHistory(); // 刪除後重新渲染畫面
}

let myChart = null; // 圖表變數

// 負責把 LocalStorage 的資料畫到畫面上
function renderHistory() {
    let history = JSON.parse(localStorage.getItem('lunch_history_v2') || '[]');
    const container = document.getElementById('history-list');
    const emptyState = document.getElementById('history-empty'); // 抓取新版 Tailwind 的空狀態 UI
    
    // 【繪製 Chart.js 圖表】
    const prices = history.map(h => parseFloat(h.price)).filter(p => !isNaN(p));
    const chartCanvas = document.getElementById('expenseChart');
    if(chartCanvas) {
        if(prices.length > 0) {
            const ctx = chartCanvas.getContext('2d');
            if(myChart) myChart.destroy();
            myChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: history.filter(h => h.price).map(h => h.lastDate || h.date).reverse(),
                    datasets: [{
                        label: '午餐花費趨勢 (元)',
                        data: prices.reverse(),
                        borderColor: '#ff6b6b', backgroundColor: 'rgba(255, 107, 107, 0.2)',
                        fill: true, tension: 0.3
                    }]
                }
            });
            chartCanvas.style.display = 'block';
        } else {
            chartCanvas.style.display = 'none'; // 沒價格時隱藏圖表
        }
    }

    // 控制空狀態顯示/隱藏
    if(history.length === 0) {
        container.innerHTML = '';
        if (emptyState) emptyState.classList.remove('hidden');
        return;
    } else {
        if (emptyState) emptyState.classList.add('hidden');
    }
    
    // 生成歷史紀錄卡片
    container.innerHTML = history.slice().reverse().map(h => `
        <div class="history-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <h3 style="margin:0; font-size:16px; color:#2c3e50; font-weight: bold;">
                    ${h.name} ${h.visitCount > 1 ? `<span style="color:#ba1a1a; font-size:13px; margin-left:5px;">(${h.visitCount}訪)</span>` : ''}
                </h3>
                <button onclick="deleteHistoryItem(${h.id})" style="width:auto; padding:4px 12px; background:transparent; color:#ba1a1a; border:1px solid #ba1a1a; border-radius:8px; font-size:12px; font-weight: bold; cursor: pointer;">刪除</button>
            </div>
            <div style="display:flex; gap:10px;">
                <div style="flex:1;"><span style="font-size:12px;color:gray; font-weight: 500;">花費</span><input type="number" placeholder="金額" value="${h.price || ''}" onchange="updateHistory(${h.id}, 'price', this.value)"></div>
                <div style="flex:1;"><span style="font-size:12px;color:gray; font-weight: 500;">評價(1-5)</span><input type="number" min="1" max="5" placeholder="分數" value="${h.rating || ''}" onchange="updateHistory(${h.id}, 'rating', this.value)"></div>
            </div>
        </div>
    `).join('');
}

function updateHistory(id, field, value) {
    let history = JSON.parse(localStorage.getItem('lunch_history_v2') || '[]');
    let item = history.find(h => h.id === id);
    if(item) { 
        item[field] = value; 
        localStorage.setItem('lunch_history_v2', JSON.stringify(history)); 
        renderHistory(); 
    }
}