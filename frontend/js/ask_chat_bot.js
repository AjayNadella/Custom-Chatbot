window.askChatbot = function () {
    const question = document.getElementById("user-question").value;
    const chatbotType = localStorage.getItem("selectedChatbotType");  // ✅ Retrieve stored chatbot type
    const user_id = localStorage.getItem("userID");

    if (!chatbotType) {
        alert("❌ No chatbot type selected. Please go back and select a chatbot type.");
        return;
    }

    if (!question.trim()) {
        alert("❌ Please enter a question.");
        return;
    }

    // ✅ Step 1: Refresh knowledge base before asking chatbot
    fetch("http://localhost:8000/api/upload/refresh-knowledge-base", {
        method: "POST",
        headers: { "Authorization": `Bearer ${localStorage.getItem("userToken")}` }
    })
    .then(() => {
        console.log("✅ Knowledge base refreshed.");
        
        // ✅ Step 2: Ask chatbot after refreshing knowledge
        return fetch("http://localhost:8000/generate-response", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${localStorage.getItem("userToken")}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: user_id,
                user_question: question,
                chatbot_type: chatbotType  // ✅ Automatically use stored chatbot type
            })
        });
    })
    .then(response => response.json())
    .then(data => {        
        document.getElementById("response").innerText = data.response;
        console.log("🤖 Chatbot Response:", data);
    })
    .catch(error => console.error("🚨 Chatbot Error:", error));
};
