(function () {
    const userId = document.currentScript.getAttribute("data-user-id");
    const chatbotName = document.currentScript.getAttribute("data-chatbot-name");
    const chatbotType = document.currentScript.getAttribute("data-chatbot-type");

    
    const style = document.createElement("link");
    style.rel = "stylesheet";
    style.href = "http://localhost:8000/static/chatbot-widget.css";  
    document.head.appendChild(style);

    
    const container = document.getElementById("chatbot-bubble-container");

    const widgetHTML = `
        <div id="chatbot-widget">
            <button id="chatbot-button">💬 Chat with us</button>
            <div id="chatbox" style="display:none;">
                <h3>Chatbot: ${chatbotName}</h3>
                <div id="chat-box"></div>
                <div id="chat-input">
                    <input type="text" id="chatbot-input" placeholder="Ask me anything..." />
                    <button onclick="askChatbot(document.getElementById('chatbot-input').value)">Send</button>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = widgetHTML;

    
    document.getElementById("chatbot-button").onclick = function () {
        const chatbox = document.getElementById("chatbox");
        chatbox.style.display = chatbox.style.display === "none" ? "block" : "none";
    };

    
    window.askChatbot = async function (question) {
        
        addMessageToChat(question, "user");
        document.getElementById("chatbot-input").value = "";
        const typingMessage = addMessageToChat("Chatbot is typing...", "bot");

        
        const response = await fetch(`http://localhost:8000/user-chatbot/${userId}/${chatbotName}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                "user_question": question,
                "chatbot_type": chatbotType
            })
        });

        
        if (!response.ok) {
            alert("API Error: " + response.status + " " + response.statusText);
            return;
        }

        const data = await response.json();
        typingMessage.remove();
        addMessageToChat(data.response, "bot");
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
})();