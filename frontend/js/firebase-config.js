/**
 * Firebase Configuration for Kisan Smart
 * 
 * Replace the values below with your specific Firebase Web App configuration.
 * You can find this in the Firebase Console:
 * Project Settings > General > Your apps > Firebase SDK snippet > Config
 */

const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT_ID.appspot.com",
  messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
  appId: "YOUR_APP_ID"
};

// Initialize Firebase (will be called in main.js)
if (typeof firebase !== 'undefined') {
    firebase.initializeApp(firebaseConfig);
}
