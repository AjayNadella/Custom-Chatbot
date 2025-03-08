window.uploadKnowledge = function () {
    const fileInput = document.getElementById("knowledge-file");
    if (!fileInput.files.length) {
        alert("Please select a file to upload.");
        return;
    }
    const chatbotType = localStorage.getItem("selectedChatbotType");  
    if (!chatbotType) {
        alert("No chatbot type selected. Please go back and select a chatbot type.");
        return;
    }

    const user_id = localStorage.getItem("userID");
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("chatbot_type", chatbotType);

    fetch("http://localhost:8000/api/upload/upload-knowledge", {
        method: "POST",
        headers: { "Authorization": `Bearer ${localStorage.getItem("userToken")}` },
        body: formData
    })
    .then(response => response.json())
    .then((data) => {
        console.log("Upload Successful:", data);
        alert("Knowledge uploaded successfully!");
        localStorage.setItem("userID", data.user_id)
        fetchUploadedDocuments();
    })
    .catch(error => console.error("Upload Error:", error));
};

window.fetchUploadedDocuments = function () {
    const user_id = localStorage.getItem("userID");
    const token = localStorage.getItem("userToken");

    if (!user_id || !token) {
        console.error("No user ID or token found. Ensure the user is logged in.");
        document.getElementById("uploaded-docs").innerHTML = "<p style='color:red;'>User not authenticated. Please log in.</p>";
        return;
    }

    fetch(`http://localhost:8000/api/upload/list-knowledge/${user_id}`, {
        method: "GET",
        headers: { "Authorization": `Bearer ${token}` }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 403) {
                throw new Error("Access denied: You can only view your own documents.");
            } else if (response.status === 401) {
                throw new Error("Unauthorized: Please log in again.");
            } else {
                throw new Error(`Server error: ${response.status}`);
            }
        }
        return response.json();
    })
    .then(data => {
        const docList = document.getElementById("uploaded-docs");
        docList.innerHTML = "";  

        if (!data.documents || data.documents.length === 0) {
            docList.innerHTML = "<p>No documents uploaded yet.</p>";
        } else {
            data.documents.forEach(doc => {
                const listItem = document.createElement("li");
                listItem.innerHTML = `
                    ${doc.filename} 
                    <button onclick="deleteKnowledge('${doc.filename}')">Delete</button>
                `;
                docList.appendChild(listItem);
            });
        }
    })
    .catch(error => {
        console.error("Error fetching documents:", error.message);
        document.getElementById("uploaded-docs").innerHTML = `<p style="color:red;">${error.message}</p>`;
    });
};


window.onload = function () {
    setTimeout(fetchUploadedDocuments, 500);  
};


window.deleteKnowledge = function (filename) {
    const user_id = localStorage.getItem("userID");
    const token = localStorage.getItem("userToken");

    fetch(`http://localhost:8000/api/upload/delete-knowledge/${user_id}/${filename}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Delete failed: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log("Delete Successful:", data);
        alert("Document deleted successfully!");

        
        fetchUploadedDocuments();

        
        return fetch("http://localhost:8000/api/upload/refresh-knowledge-base", {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` }
        });
    })
    .then(() => {
        console.log("Knowledge base refreshed.");
    })
    .catch(error => {
        console.error("Delete Error:", error.message);
        alert("Error deleting document. Please try again.");
    });
};


window.clearAllKnowledge = function () {
    const token = localStorage.getItem("userToken");

    fetch("http://localhost:8000/api/upload/clear-knowledge-base", {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Clear Knowledge failed: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log("All knowledge cleared:", data);
        alert("All stored knowledge has been deleted from ChromaDB!");

        
        document.getElementById("uploaded-docs").innerHTML = "<p>No documents uploaded yet.</p>";

        
        return fetch("http://localhost:8000/api/upload/refresh-knowledge-base", {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` }
        });
    })
    .then(() => {
        console.log("Knowledge base refreshed.");
    })
    .catch(error => {
        console.error("Clear Knowledge Error:", error.message);
        alert("Error clearing knowledge. Please try again.");
    });
};


