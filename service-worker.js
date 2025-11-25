console.log("[SW] loaded (no offline caching).");

// evento de instalação (install):
self.addEventListener('install', (event) => {
    console.log("[SW] installed");
    self.skipWaiting();
});

// evento de ativação (activate):
self.addEventListener('activate', (event) => {
    console.log("[SW] activated");
});

// evento de fetch (buscas de recurso)
self.addEventListener('fetch', (event) => {
    event.respondWith(fetch(event.request));
});
