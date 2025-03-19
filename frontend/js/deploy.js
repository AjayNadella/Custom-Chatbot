window.getChatbotEmbedCode = function () {
    const user_id = localStorage.getItem("userID");
    const token = localStorage.getItem("userToken");
    const chatbot_type = localStorage.getItem("selectedChatbotType"); 

    if (!user_id || !token || !chatbot_type) {
        alert("User not authenticated. Please log in.");
        return;
    }

    fetch(`http://localhost:8000/deploy-chatbot/${user_id}/${chatbot_type}`, {
        method: "GET",
        headers: { "Authorization": `Bearer ${token}` }  
    })
    .then(response => response.json())
    .then(data => {
        if (data.embed_code) {
            document.getElementById("embed-code-container").innerHTML = `
                <textarea id="embed-code" readonly style="width:100%; height:150px;">${data.embed_code}</textarea>
                <button onclick="copyEmbedCode()">Copy Code</button>
            `;
        } else {
            alert("Failed to generate chatbot embed code.");
        }
    })
    .catch(error => {
        console.error("Error fetching chatbot embed code:", error);
        alert("Error retrieving chatbot embed code.");
    });
};


window.copyEmbedCode = function () {
    const embedCode = document.getElementById("embed-code");
    embedCode.select();
    document.execCommand("copy");
    alert("Embed code copied to clipboard!");
};