window.loadChatbotTypes = function () {
    fetch("http://localhost:8000/chatbot-types", {
        method: "GET",
        headers: {
            "Authorization": `Bearer ${localStorage.getItem("userToken")}`
        }
    })
    .then(response => response.json())
    .then(data => {
        const chatbotDropdown = document.getElementById("chatbot-type");
        chatbotDropdown.innerHTML = ""; 

        if (data.available_chatbot_types) {
            Object.keys(data.available_chatbot_types).forEach(type => {
                const option = document.createElement("option");
                option.value = type;
                option.textContent = `${type.charAt(0).toUpperCase() + type.slice(1)} - ${data.available_chatbot_types[type]}`;
                chatbotDropdown.appendChild(option);
            });
        } else {
            console.error("Error: No chatbot types found");
        }
    })
    .catch(error => console.error("Error fetching chatbot types:", error));
};
document.addEventListener("DOMContentLoaded", function () {
    loadChatbotTypes();
});