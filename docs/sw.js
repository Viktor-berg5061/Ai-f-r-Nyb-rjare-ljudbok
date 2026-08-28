/* Service worker — network-first PWA cache so updates always reach the device,
   while still working offline from the last-loaded copy. */
const CACHE='aibok-v3';
const CORE=['./index.html','./manifest.json','./data/index.json','./data/chapters.json'];
self.addEventListener('install',e=>{ self.skipWaiting(); e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE).catch(()=>{}))); });
self.addEventListener('activate',e=>{
  e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch',e=>{
  const url=new URL(e.request.url);
  if(url.origin!==location.origin) return;
  if(e.request.method!=='GET') return;
  // network-first, cache as offline fallback (guarantees latest content online)
  e.respondWith(
    fetch(e.request).then(res=>{
      if(res && res.ok){ const copy=res.clone(); caches.open(CACHE).then(c=>c.put(e.request,copy)); }
      return res;
    }).catch(()=>caches.match(e.request).then(c=>c||caches.match('./index.html')))
  );
});
