window.uploadKnowledge = function () {
    const fileInput = document.getElementById("knowledge-file");
    if (!fileInput.files.length) {
        alert("Please select a file to upload.");
        return;
    }

    const chatbotName = localStorage.getItem("selectedChatbot");
    if (!chatbotName) {
        alert("No chatbot selected. Please go back and select a chatbot.");
        return;
    }

    const user_id = localStorage.getItem("userID");
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    fetch(`http://localhost:8000/api/upload/upload-knowledge/${chatbotName}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${localStorage.getItem("userToken")}` },
        body: formData
    })
    .then(response => response.json())
    .then((data) => {
        console.log("Upload Successful:", data);
        alert(`Knowledge uploaded successfully to chatbot "${chatbotName}"!`);
        fetchUploadedDocuments();
    })
    .catch(error => {
        console.error("Upload Error:", error);
        alert(`Upload Error: ${error.message}`);
    });
};

window.fetchUploadedDocuments = function () {
    const chatbotName = localStorage.getItem("selectedChatbot");
    const user_id = localStorage.getItem("userID");
    const token = localStorage.getItem("userToken");

    if (!user_id || !token || !chatbotName) {
        console.error("Missing data. Ensure the user is logged in and chatbot is selected.");
        document.getElementById("uploaded-docs").innerHTML = "<p style='color:red;'>User not authenticated or chatbot not selected.</p>";
        return;
    }

    fetch(`http://localhost:8000/api/upload/list-knowledge/${user_id}/${chatbotName}`, {
        method: "GET",
        headers: { "Authorization": `Bearer ${token}` }
    })
    .then(response => response.json())
    .then(data => {
        const docList = document.getElementById("uploaded-docs");
        docList.innerHTML = "";

        if (!data.documents || data.documents.length === 0) {
            docList.innerHTML = "<p>No documents uploaded for this chatbot.</p>";
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
        console.error("Error fetching documents:", error);
        document.getElementById("uploaded-docs").innerHTML = `<p style="color:red;">${error.message}</p>`;
    });
};

window.deleteKnowledge = function (filename) {
    const chatbotName = localStorage.getItem("selectedChatbot");
    const user_id = localStorage.getItem("userID");
    const token = localStorage.getItem("userToken");

    if (!chatbotName) {
        alert("No chatbot selected. Please select a chatbot.");
        return;
    }

    fetch(`http://localhost:8000/api/upload/delete-knowledge/${user_id}/${chatbotName}/${filename}`, {
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
        console.log(" Delete Successful:", data);
        alert("Document deleted successfully!");

        fetchUploadedDocuments();

        return fetch(`http://localhost:8000/api/upload/refresh-knowledge-base/${user_id}/${chatbotName}`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` }
        });
    })
    .then(() => {
        console.log("Knowledge base refreshed.");
    })
    .catch(error => {
        console.error("Delete Error:", error);
        alert(`Error deleting document: ${error.message}`);
    });
};

window.clearAllKnowledge = function () {
    const chatbotName = localStorage.getItem("selectedChatbot");
    const user_id = localStorage.getItem("userID");
    const token = localStorage.getItem("userToken");

    fetch(`http://localhost:8000/api/upload/clear-knowledge-base/${user_id}/${chatbotName}`, {
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
        alert(`All stored knowledge for chatbot "${chatbotName}" has been deleted!`);

        document.getElementById("uploaded-docs").innerHTML = "<p>No documents uploaded for this chatbot.</p>";

        return fetch(`http://localhost:8000/api/upload/refresh-knowledge-base/${user_id}/${chatbotName}`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` }
        });
    })
    .then(() => {
        console.log("Knowledge base refreshed.");
    })
    .catch(error => {
        console.error("Clear Knowledge Error:", error);
        alert(`Error clearing knowledge: ${error.message}`);
    });
};

window.onload = function () {
    setTimeout(fetchUploadedDocuments, 500);
};
