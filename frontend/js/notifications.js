/**
 * Firebase Notifications Handler for Kisan Smart
 * 
 * This script handles browser notification permissions and 
 * FCM token registration with the backend.
 */

async function initNotifications() {
    // 1. Check for browser support
    if (!('serviceWorker' in navigator)) {
        console.warn('Service Worker not supported by this browser.');
        return;
    }

    try {
        // 2. Register Service Worker (standard Firebase requirement)
        const registration = await navigator.serviceWorker.register('/app/firebase-messaging-sw.js');
        console.log('FCM Service Worker registered');

        const messaging = firebase.messaging();

        // 3. Request Notification Permission
        const permission = await Notification.requestPermission();
        
        if (permission === 'granted') {
            console.log('Notification permission granted.');
            
            // 4. Get FCM Token
            // REPLACEME: Paste your VAPID Key from Firebase Console here
            const vapidKey = 'YOUR_VAPID_PUBLIC_KEY_HERE'; 
            
            const token = await messaging.getToken({
                vapidKey: vapidKey,
                serviceWorkerRegistration: registration
            });

            if (token) {
                console.log('FCM Token generated:', token);
                await updateFcmTokenOnBackend(token);
            } else {
                console.warn('No registration token available. Request permission to generate one.');
            }
        } else {
            console.warn('Unable to get permission to notify.');
        }

    } catch (err) {
        console.error('Error initializing Firebase messaging:', err);
    }
}

/**
 * Sends the FCM token to the backend profile update endpoint
 */
async function updateFcmTokenOnBackend(token) {
    const authToken = localStorage.getItem('auth_token');
    if (!authToken) {
        console.warn('No auth token found, skipping FCM registration');
        return;
    }

    try {
        const response = await fetch('/api/v1/profile/', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ fcm_token: token })
        });

        if (response.ok) {
            console.log('Successfully registered FCM token with Kisan Smart backend');
        } else {
            const error = await response.json();
            console.error('Failed to register FCM token:', error);
        }
    } catch (err) {
        console.error('Network error registering FCM token:', err);
    }
}

// Auto-initialize when page loads if user is authenticated
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (localStorage.getItem('auth_token')) {
            initNotifications();
        }
    });
} else {
    if (localStorage.getItem('auth_token')) {
        initNotifications();
    }
}
