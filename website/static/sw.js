// Service Worker Placeholder for Kisan Smart PWA
// To be implemented with Firebase Cloud Messaging (FCM) push notification handling.
self.addEventListener('install', event => {
    console.log('Service Worker: Installed');
});

self.addEventListener('activate', event => {
    console.log('Service Worker: Activated');
});

self.addEventListener('push', event => {
    const data = event.data ? event.data.json() : {};
    const title = data.title || 'Kisan Smart Alert';
    const body = data.body || 'New agricultural update available.';
    const options = {
        body: body,
        icon: '/static/img/logo.png', // Update if logo path is different
        badge: '/static/img/badge.png',
        data: data
    };
    event.waitUntil(self.registration.showNotification(title, options));
});
