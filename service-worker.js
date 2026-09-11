const CACHE = 'basair-mushaf-complete-v6-15';
const AUDIO_CACHE = 'basair-quran-audio-v1';
const CORE = ['./', './index.html', './mushaf-v2.css', './mushaf-v2.js', './questions.js', './page-layout.js', './amiri-quran.ttf', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png'];
self.addEventListener('install', event => event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(CORE)).then(() => self.skipWaiting())));
self.addEventListener('activate', event => event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE && key !== AUDIO_CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim())));
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const sameOrigin = new URL(event.request.url).origin === self.location.origin;
  event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
    if (!sameOrigin) return response;
    const copy = response.clone();
    caches.open(CACHE).then(cache => cache.put(event.request, copy)).catch(() => {});
    return response;
  }).catch(() => cached)));
});
