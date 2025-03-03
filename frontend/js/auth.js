document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ Auth.js Loaded");

    if (!firebase.apps.length) {
        console.error("🚨 Firebase not initialized. Make sure `firebaseConfig.js` loads first.");
        return;
    }

    const auth = firebase.auth();

    const signupForm = document.getElementById("signup-form");
    const loginForm = document.getElementById("login-form");

    // ✅ Signup Function
    if (signupForm) {
        signupForm.addEventListener("submit", function (event) {
            event.preventDefault();
            const email = document.getElementById("signup-email").value;
            const password = document.getElementById("signup-password").value;

            auth.createUserWithEmailAndPassword(email, password)
                .then((userCredential) => userCredential.user.getIdToken())
                .then((token) => {
                    localStorage.setItem("userToken", token);
                    window.location.href = "dashboard.html";
                })
                .catch((error) => {
                    console.error("❌ Signup Error:", error.message);
                    alert(error.message);
                });
        });
    }

    // ✅ Login Function
    if (loginForm) {
        loginForm.addEventListener("submit", function (event) {
            event.preventDefault();
            const email = document.getElementById("login-email").value;
            const password = document.getElementById("login-password").value;

            auth.signInWithEmailAndPassword(email, password)
                .then((userCredential) => userCredential.user.getIdToken())
                .then((token) => {
                    localStorage.setItem("userToken", token);
                    console.log("✅ Logged in successfully.");
                    window.location.href = "dashboard.html";
                })
                .catch((error) => {
                    console.error("❌ Login Error:", error.message);
                    alert(error.message);
                });
        });
    }

    // ✅ Logout Function
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", function () {
            auth.signOut()
                .then(() => {
                    localStorage.removeItem("userToken");
                    console.log("✅ User logged out.");
                    window.location.href = "login.html";
                })
                .catch((error) => {
                    console.error("❌ Logout Error:", error.message);
                    alert(error.message);
                });
        });
    }
});
