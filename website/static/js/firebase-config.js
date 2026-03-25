/**
 * Firebase Configuration for Kisan Smart
 * 
 * REPLACE THESE placeholder values with your Firebase Web App configuration
 * from the Firebase Console (Project Settings > General > Your apps).
 */

const firebaseConfig = {
    apiKey: "AIzaSyB23KL_XMbPFHqYdwf0ixXAJ8orgOYKbbg",
    authDomain: "kissan-smart-48.firebaseapp.com",
    projectId: "kissan-smart-48",
    storageBucket: "kissan-smart-48.firebasestorage.app",
    messagingSenderId: "111302122582",
    appId: "1:111302122582:web:03a9015a338d96fcdceff7",
    measurementId: "G-9ECL3SG9KK"
};

// Initialize Firebase
if (typeof firebase !== 'undefined') {
    firebase.initializeApp(firebaseConfig);
    console.log("Firebase initialized for web client");
}
