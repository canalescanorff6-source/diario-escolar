const CACHE='diario-ia-shell-v34';
const ASSETS=['/static/css/premium_base_final.css','/static/css/desktop_pwa_mobile.css'];
self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(ASSETS)).catch(()=>null).then(()=>self.skipWaiting()));
});
self.addEventListener('activate',event=>{
  event.waitUntil(self.clients.claim());
});
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET') return;
  event.respondWith(fetch(event.request).catch(()=>caches.match(event.request)));
});
