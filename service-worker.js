const CACHE = 'basair-mushaf-complete-v6-18';
const AUDIO_CACHE = 'basair-quran-audio-v1';
const CORE = ['./', './index.html', './mushaf-v2.css', './mushaf-v2.js', './question-parts/questions-part-001.js', './question-parts/questions-part-002.js', './question-parts/questions-part-003.js', './question-parts/questions-part-004.js', './question-parts/questions-part-005.js', './question-parts/questions-part-006.js', './question-parts/questions-part-007.js', './question-parts/questions-part-008.js', './question-parts/questions-part-009.js', './question-parts/questions-part-010.js', './question-parts/questions-part-011.js', './question-parts/questions-part-012.js', './question-parts/questions-part-013.js', './question-parts/questions-part-014.js', './question-parts/questions-part-015.js', './question-parts/questions-part-016.js', './question-parts/questions-part-017.js', './question-parts/questions-part-018.js', './question-parts/questions-part-019.js', './question-parts/questions-part-020.js', './question-parts/questions-part-021.js', './question-parts/questions-part-022.js', './question-parts/questions-part-023.js', './question-parts/questions-part-024.js', './question-parts/questions-part-025.js', './question-parts/questions-counts.js', './page-layout.js', './amiri-quran.ttf', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png'];
self.addEventListener('install', event => event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(CORE)).then(() => self.skipWaiting())));
self.addEventListener('activate', event => event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE && key !== AUDIO_CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim())));
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const sameOrigin = new URL(event.request.url).origin === self.location.origin;
  if (event.request.mode === 'navigate') {
    event.respondWith(fetch(event.request).then(response => {
      const copy = response.clone();
      caches.open(CACHE).then(cache => cache.put('./index.html', copy)).catch(() => {});
      return response;
    }).catch(() => caches.match('./index.html').then(cached => cached || caches.match('./'))));
    return;
  }
  event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
    if (!sameOrigin) return response;
    const copy = response.clone();
    caches.open(CACHE).then(cache => cache.put(event.request, copy)).catch(() => {});
    return response;
  }).catch(() => cached)));
});
