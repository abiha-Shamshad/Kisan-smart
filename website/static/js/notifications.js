/**
 * Firebase Notifications Handler for Kisan Smart
 * 
 * Handles browser notification permissions and 
 * FCM token registration with the backend via api.js
 */

async function initNotifications() {
    // 1. Check for browser support
    if (!('serviceWorker' in navigator)) {
        console.warn('Service Worker not supported by this browser.');
        return;
    }

    try {
        // 2. Register Service Worker
        // Note: The service worker file should be in the root or accessible via static
        const registration = await navigator.serviceWorker.register('/firebase-messaging-sw.js');
        console.log('FCM Service Worker registered');

        const messaging = firebase.messaging();

        // 3. Request Notification Permission
        const permission = await Notification.requestPermission();
        
        if (permission === 'granted') {
            console.log('Notification permission granted.');
            
            // 4. Get FCM Token
            // The VAPID key provided by the user
            const vapidKey = 'BIzmskfvF37Ka58HKPqxfnwaCs0Nh4qVZCZ4tDW2oEP2FEZ6sXLiRHGEdBze6LLqhYnaeyHBHj__pCHcuwxfVAs'; 
            
            const token = await messaging.getToken({
                vapidKey: vapidKey,
                serviceWorkerRegistration: registration
            });

            if (token) {
                console.log('FCM Token generated:', token);
                await updateFcmTokenWithApi(token);
            } else {
                console.warn('No registration token available.');
            }
        } else {
            console.warn('Unable to get permission to notify.');
        }

    } catch (err) {
        console.error('Error initializing Firebase messaging:', err);
    }
}

/**
 * Sends the FCM token to the backend using the global api client
 */
async function updateFcmTokenWithApi(token) {
    if (!api.isAuthenticated()) {
        console.warn('User not authenticated, skipping FCM registration');
        return;
    }

    try {
        // Use the profile update endpoint
        await api.request('/profile/', {
            method: 'PUT',
            body: JSON.stringify({ fcm_token: token })
        });
        console.log('Successfully registered FCM token with Kisan Smart backend');
    } catch (err) {
        console.error('Failed to register FCM token:', err);
    }
}

// Auto-initialize when page loads if user is authenticated
document.addEventListener('DOMContentLoaded', () => {
    if (api.isAuthenticated()) {
        initNotifications();
    }
});
