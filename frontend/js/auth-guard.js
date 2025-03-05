document.addEventListener("DOMContentLoaded", function () {
    if (!firebase.apps.length) {
        console.error("🚨 Firebase not initialized. Ensure `firebaseConfig.js` is loaded first.");
        return;
    }

    const auth = firebase.auth();

    
    auth.onAuthStateChanged((user) => {
        if (!user) {
            window.location.href = "login.html";
        }
    });

    
    document.getElementById("logout-btn").addEventListener("click", function () {
        auth.signOut().then(() => {
            localStorage.removeItem("userToken");
            window.location.href = "login.html";
        });
    });
});
