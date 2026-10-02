/**
 * Kill-switch service worker.
 *
 * Una versión anterior de la app registraba un SW cache-first que dejaba
 * congelados el index.html y los bundles del dev server (loop infinito de
 * reloads con assets viejos). La registración ya no existe, pero los
 * navegadores que la ejecutaron siguen controlados por ese SW.
 *
 * El navegador siempre busca actualizaciones de sw.js directo de la red,
 * así que esta versión se instala sola en los clientes afectados y se
 * auto-destruye: borra todos los caches, se desregistra y recarga las
 * pestañas para que tomen el HTML/JS frescos.
 */
self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map((key) => caches.delete(key)));
    await self.registration.unregister();
    const clients = await self.clients.matchAll({ type: 'window' });
    clients.forEach((client) => client.navigate(client.url));
  })());
});
