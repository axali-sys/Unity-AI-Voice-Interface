/* AXALIAI roaming PWA shell cache. API requests are never cached. */
const CACHE_NAME = "axaliai-shell-v1";
const SHELL = ["/axaliai.html", "/manifest.webmanifest", "/axaliai-icon.svg"];
self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(SHELL)));
  self.skipWaiting();
});
self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key)))));
  self.clients.claim();
});
self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/public/") || url.pathname.startsWith("/memory") ||
      url.pathname.startsWith("/chat") || url.pathname.startsWith("/conversations") ||
      url.pathname === "/health" || url.pathname.startsWith("/_vercel/")) return;
  if (request.mode === "navigate" && url.pathname === "/axaliai.html") {
    event.respondWith(fetch(request).then(response => {
      if (response.ok) caches.open(CACHE_NAME).then(cache => cache.put("/axaliai.html", response.clone()));
      return response;
    }).catch(() => caches.match("/axaliai.html")));
    return;
  }
  if (SHELL.includes(url.pathname)) event.respondWith(caches.match(request).then(cached => cached || fetch(request)));
});