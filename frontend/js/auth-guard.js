document.addEventListener("DOMContentLoaded", function () {
    if (!firebase.apps.length) {
        console.error("🚨 Firebase not initialized. Ensure `firebaseConfig.js` is loaded first.");
        return;
    }

    const auth = firebase.auth();

    // ✅ Ensure user is logged in, otherwise redirect to login
    auth.onAuthStateChanged((user) => {
        if (!user) {
            window.location.href = "login.html";
        }
    });

    // ✅ Logout functionality
    document.getElementById("logout-btn").addEventListener("click", function () {
        auth.signOut().then(() => {
            localStorage.removeItem("userToken");
            window.location.href = "login.html";
        });
    });
});
