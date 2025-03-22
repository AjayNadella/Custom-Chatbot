window.askChatbot = async function () {
    const userMessage = document.getElementById("user-message").value;
    const chatbotName = localStorage.getItem("selectedChatbot");
    const chatbotType = localStorage.getItem("selectedChatbotType");
    const user_id = localStorage.getItem("userID");

    if (!chatbotName || !chatbotType || !userMessage.trim()) {
        alert("Missing chatbot name, type, or message.");
        return;
    }

    
    addMessageToChat(userMessage, "user");

    
    const typingMessage = addMessageToChat("Chatbot is typing...", "bot");

    try {
        const response = await fetch("http://localhost:8000/generate-response", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${localStorage.getItem("userToken")}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: user_id,
                chatbot_name: chatbotName,
                user_question: userMessage,
                chatbot_type: chatbotType
            })
        });

        const data = await response.json();
        typingMessage.remove();  

        addMessageToChat(data.response, "bot");

    } catch (error) {
        console.error("Chatbot Error:", error);
        typingMessage.remove();
        addMessageToChat("Error retrieving chatbot response.", "bot");
    }

    document.getElementById("user-message").value = "";
};


function addMessageToChat(message, sender) {
    const chatBox = document.getElementById("chat-box");
    const messageDiv = document.createElement("div");

    messageDiv.classList.add("message");
    messageDiv.classList.add(sender === "user" ? "user-message" : "bot-message");
    messageDiv.innerText = message;

    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;  

    return messageDiv; 
}
