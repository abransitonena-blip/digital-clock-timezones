// Funciona sin internet: guarda el sitio la primera vez y después responde desde la caché,
// actualizándola en segundo plano. Los PDF y ZIP grandes se guardan solo cuando se abren.
const CACHE = 'ap-v2'
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(['./', './index.html', './manifest.webmanifest', './icono-192.png'])).then(() => self.skipWaiting()))
})
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()))
})
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url)
  if (e.request.method !== 'GET' || u.origin !== location.origin) return
  e.respondWith(caches.open(CACHE).then(async c => {
    const guardada = await c.match(e.request, { ignoreSearch: true })
    const red = fetch(e.request).then(r => { if (r.ok) c.put(e.request, r.clone()); return r }).catch(() => guardada)
    return guardada || red
  }))
})
