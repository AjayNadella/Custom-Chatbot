document.addEventListener("DOMContentLoaded", function () {
    console.log("Auth.js Loaded");

    if (!firebase.apps.length) {
        console.error("Firebase not initialized. Make sure `firebaseConfig.js` loads first.");
        return;
    }

    const auth = firebase.auth();

    const signupForm = document.getElementById("signup-form");
    const loginForm = document.getElementById("login-form");

    
    if (signupForm) {
        signupForm.addEventListener("submit", function (event) {
            event.preventDefault();
            const email = document.getElementById("signup-email").value;
            const password = document.getElementById("signup-password").value;

            auth.createUserWithEmailAndPassword(email, password)
                .then((userCredential) => {
                    return userCredential.user.getIdToken()
                        .then((token) => {
                            localStorage.setItem("userToken", token);
                            console.log("User signed up:", email);

                            
                            return fetch("https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=AIzaSyDZqYgp8LnOZHj8gqi10PgbIbv-h_NQ51g", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ idToken: token })
                            });
                        });
                })
                .then(response => response.json())
                .then(data => {
                    if (data.users && data.users.length > 0) {
                        const userID = data.users[0].localId;
                        localStorage.setItem("userID", userID);  
                        console.log("User ID stored:", userID);
                    }
                    window.location.href = "index.html";
                })
                .catch((error) => {
                    console.error("Signup Error:", error.message);
                    alert(error.message);
                });
        });
    }

    
    if (loginForm) {
        loginForm.addEventListener("submit", function (event) {
            event.preventDefault();
            const email = document.getElementById("login-email").value;
            const password = document.getElementById("login-password").value;

            auth.signInWithEmailAndPassword(email, password)
                .then((userCredential) => {
                    return userCredential.user.getIdToken()
                        .then((token) => {
                            localStorage.setItem("userToken", token);
                            console.log("Logged in successfully.");

                            
                            return fetch("https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=AIzaSyDZqYgp8LnOZHj8gqi10PgbIbv-h_NQ51g", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ idToken: token })
                            });
                        });
                })
                .then(response => response.json())
                .then(data => {
                    if (data.users && data.users.length > 0) {
                        const userID = data.users[0].localId;
                        localStorage.setItem("userID", userID);  
                        console.log("User ID stored:", userID);
                    }
                    window.location.href = "index.html";
                })
                .catch((error) => {
                    console.error("Login Error:", error.message);
                    alert(error.message);
                });
        });
    }

    
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", function () {
            auth.signOut()
                .then(() => {
                    localStorage.removeItem("userToken");  
                    localStorage.removeItem("userID");  
                    console.log("User logged out.");
                    window.location.href = "login.html";  
                })
                .catch((error) => {
                    console.error("Logout Error:", error.message);
                    alert(error.message);
                });
        });
    }
});
