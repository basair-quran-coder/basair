const SHELL_CACHE = 'basair-shell-v6-48-29';
const MUSHAF_CACHE = 'basair-mushaf-pages-v6-48-1';
const CORE = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/apple-touch-icon.png',
  './data/page-lines.js',
  './data/quran-search-part-01.js',
  './data/quran-search-part-02.js',
  './data/quran-search-part-03.js',
  './data/quran-search-part-04.js',
  ...Array.from({ length: 25 }, (_, index) =>
    `./data/questions-part-${String(index + 1).padStart(2, '0')}.js`
  )
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then(cache => cache.addAll(CORE))
      .then(() => self.skipWaiting())
  );
});

async function migrateMushafCaches() {
  const keys = await caches.keys();
  const oldKeys = keys.filter(key => key.startsWith('basair-mushaf-pages-') && key !== MUSHAF_CACHE);
  const target = await caches.open(MUSHAF_CACHE);
  for (const key of oldKeys) {
    const source = await caches.open(key);
    let migrated = true;
    for (const request of await source.keys()) {
      try {
        if (!(await target.match(request))) {
          const response = await source.match(request);
          if (response) await target.put(request, response);
        }
      } catch {
        migrated = false;
        break;
      }
    }
    if (migrated) await caches.delete(key);
  }
}

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys
      .filter(key => key.startsWith('basair-shell-') && key !== SHELL_CACHE)
      .map(key => caches.delete(key)));
    await migrateMushafCaches();
    await self.clients.claim();
  })());
});

async function cacheMushafPage(request) {
  const cache = await caches.open(MUSHAF_CACHE);
  const cached = await cache.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response.ok) await cache.put(request, response.clone());
  return response;
}

async function fetchNavigation(request) {
  const cache = await caches.open(SHELL_CACHE);
  try {
    const response = await fetch(request);
    if (response.ok) await cache.put('./index.html', response.clone());
    return response;
  } catch {
    return (await cache.match('./index.html')) || (await cache.match('./'));
  }
}

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);

  if (url.origin === self.location.origin && /\/mushaf-pages\/pages-\d{2,3}\.js$/.test(url.pathname)) {
    event.respondWith(cacheMushafPage(event.request));
    return;
  }

  if (event.request.mode === 'navigate') {
    event.respondWith(fetchNavigation(event.request));
    return;
  }

  if (url.origin === self.location.origin) {
    event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request)));
  }
});
