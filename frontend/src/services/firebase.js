// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics, isSupported } from "firebase/analytics";
import { getAuth } from "firebase/auth";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyBLfJFcvZlkFIjAkNK2w4X6izP_oifNpfk",
  authDomain: "sentinel-ai-79bad.firebaseapp.com",
  projectId: "sentinel-ai-79bad",
  storageBucket: "sentinel-ai-79bad.firebasestorage.app",
  messagingSenderId: "858832669325",
  appId: "1:858832669325:web:5a02eef1ffce657fedf0c4",
  measurementId: "G-RPHSY8FXJ1"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Analytics dynamically if supported in the browser context
let analytics = null;
isSupported().then((supported) => {
  if (supported) {
    analytics = getAnalytics(app);
  }
}).catch((err) => console.log("Analytics not supported or blocked: ", err));

const auth = getAuth(app);

export { app, analytics, auth };
