document.addEventListener("DOMContentLoaded", function () {
    if (!firebase.apps.length) {
        console.error("🚨 Firebase not initialized. Ensure `firebaseConfig.js` is loaded first.");
        return;
    }

    const auth = firebase.auth();
    const userEmailElement = document.getElementById("user-email");
    const chatbotSection = document.getElementById("chatbot-section");

    auth.onAuthStateChanged((user) => {
        if (user) {
            userEmailElement.innerText = user.email || "No email found";
            chatbotSection.style.display = "block";
        } else {
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

// ✅ Define `uploadKnowledge` globally so it can be accessed from `dashboard.html`
window.uploadKnowledge = function () {
    const fileInput = document.getElementById("knowledge-file");
    if (!fileInput.files.length) {
        alert("❌ Please select a file to upload.");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    fetch("http://localhost:8000/api/upload/upload-knowledge", {
        method: "POST",
        headers: { "Authorization": `Bearer ${localStorage.getItem("userToken")}` },
        body: formData
    })
    .then(response => response.json())
    .then((data) => {
        console.log("✅ Upload Successful:", data);
        alert("Knowledge uploaded successfully!");
        localStorage.setItem("userID", data.user_id)
    })
    .catch(error => console.error("🚨 Upload Error:", error));
};

// ✅ Define `askChatbot` globally so it can be accessed from `dashboard.html`
window.askChatbot = function () {
    const question = document.getElementById("user-question").value;
    const chatbotType = document.getElementById("chatbot-type").value;
    const user_id = localStorage.getItem("userID");

    if (!question.trim()) {
        alert("❌ Please enter a question.");
        return;
    }

    fetch("http://localhost:8000/generate-response", {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${localStorage.getItem("userToken")}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ user_id: user_id,user_question: question, chatbot_type: chatbotType })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("response").innerText = data.response;
        console.log("🤖 Chatbot Response:", data);
    })
    .catch(error => console.error("🚨 Chatbot Error:", error));
};
