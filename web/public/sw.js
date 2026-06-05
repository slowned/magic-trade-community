/**
 * Service Worker — MTG Trade Community PWA
 * Cache-first para assets estáticos, network-first para API calls.
 */
const CACHE_NAME = 'mtg-trade-v1';

const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  // No skipWaiting — evita forzar reloads al activar el SW
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  // No clients.claim() — evita que el SW tome control y recargue la página
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Siempre ir a la red para llamadas al backend
  if (url.port === '8000' || url.pathname.startsWith('/api/')) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request).then((response) => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        return response;
      });
    })
  );
});
