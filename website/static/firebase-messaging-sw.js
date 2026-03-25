// [firebase-messaging-sw.js] SERVICE WORKER FOR BACKGROUND NOTIFICATIONS

importScripts('https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/8.10.1/firebase-messaging.js');

// Initialize Firebase in the service worker
// REPLACE THESE with your Web App configuration
firebase.initializeApp({
  apiKey: "AIzaSyB23KL_XMbPFHqYdwf0ixXAJ8orgOYKbbg",
  authDomain: "kissan-smart-48.firebaseapp.com",
  projectId: "kissan-smart-48",
  storageBucket: "kissan-smart-48.firebasestorage.app",
  messagingSenderId: "111302122582",
  appId: "1:111302122582:web:03a9015a338d96fcdceff7"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  console.log('[firebase-messaging-sw.js] Background message: ', payload);
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/static/img/favicon.png', 
    data: payload.data
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});
