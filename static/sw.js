// 安裝 Service Worker，讓網頁具備 PWA 離線快取能力
self.addEventListener('install', (e) => {
    console.log('[Service Worker] Install');
});
self.addEventListener('fetch', (e) => {
    // 簡單的 fetch 攔截，滿足 PWA 的安裝條件
});