const CACHE_NAME = 'kisan-smart-v1';
const ASSETS = [
  '/dashboard',
  '/static/css/theme.css',
  '/static/css/dashboard_premium.css',
  '/static/js/api.js',
  '/static/js/dashboard_premium.js',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
  'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap'
];

// Install Event
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    })
  );
});

// Activate Event
self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
});

// Fetch Event (Offline first for assets)
self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((cachedResponse) => {
      return cachedResponse || fetch(e.request).catch(() => {
        // If offline and request is for a page, return the cached dashboard
        if (e.request.mode === 'navigate') {
          return caches.match('/dashboard');
        }
      });
    })
  );
});
