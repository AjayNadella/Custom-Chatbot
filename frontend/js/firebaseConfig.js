console.log("Firebase Config Loaded");


document.addEventListener("DOMContentLoaded", function () {
    if (typeof firebase === "undefined") {
        console.error("Firebase SDK not loaded. Check script order in HTML.");
        return;
    }

    const firebaseConfig = {
        apiKey: "AIzaSyDZqYgp8LnOZHj8gqi10PgbIbv-h_NQ51g",
        authDomain: "custom-chatbot-auth.firebaseapp.com",
        projectId: "custom-chatbot-auth",
        storageBucket: "custom-chatbot-auth.appspot.com",
        messagingSenderId: "637418113554",
        appId: "1:637418113554:web:839161edd155bd2d57a6cb",
        measurementId: "G-ETZZ0MKFF9"
    };

    
    if (!firebase.apps.length) {
        firebase.initializeApp(firebaseConfig);
        console.log("Firebase Initialized Successfully");
    } else {
        console.log("Firebase already initialized. Using existing instance.");
    }

    window.auth = firebase.auth(); 
});
