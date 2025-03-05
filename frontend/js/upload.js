window.uploadKnowledge = function () {
    const fileInput = document.getElementById("knowledge-file");
    if (!fileInput.files.length) {
        alert("❌ Please select a file to upload.");
        return;
    }
    const chatbotType = localStorage.getItem("selectedChatbotType");  // ✅ Retrieve chatbot type
    if (!chatbotType) {
        alert("❌ No chatbot type selected. Please go back and select a chatbot type.");
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
        console.log("✅ Upload Successful:", data);
        alert("Knowledge uploaded successfully!");
        localStorage.setItem("userID", data.user_id)
        fetchUploadedDocuments();
    })
    .catch(error => console.error("🚨 Upload Error:", error));
};

window.fetchUploadedDocuments = function () {
    const user_id = localStorage.getItem("userID");
    fetch(`http://localhost:8000/api/upload/list-knowledge/${user_id}`, {
        method: "GET",
        headers: { "Authorization": `Bearer ${localStorage.getItem("userToken")}` }
    })
    .then(response => response.json())
    .then(data => {
        const docList = document.getElementById("uploaded-docs");
        docList.innerHTML = "";  // ✅ Clear list before updating

        if (data.documents.length === 0) {
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
    .catch(error => console.error("🚨 Error fetching documents:", error));
};

// ✅ Delete Uploaded Document
window.deleteKnowledge = function (filename) {
    const user_id = localStorage.getItem("userID");

    fetch(`http://localhost:8000/api/upload/delete-knowledge/${user_id}/${filename}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${localStorage.getItem("userToken")}` }
    })
    .then(response => response.json())
    .then(data => {
        console.log("✅ Delete Successful:", data);
        alert("Document deleted successfully!");
        fetchUploadedDocuments(); // ✅ Refresh document list
        fetch("http://localhost:8000/api/upload/refresh-knowledge-base", {
            method: "POST",
            headers: { "Authorization": `Bearer ${localStorage.getItem("userToken")}` }
        }).then(() => {
            console.log("✅ Knowledge base refreshed.");
        });
    })
    .catch(error => console.error("🚨 Delete Error:", error));
};

window.clearAllKnowledge = function () {
    fetch("http://localhost:8000/api/upload/clear-knowledge-base", {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${localStorage.getItem("userToken")}` }
    })
    .then(response => response.json())
    .then(data => {
        console.log("✅ All knowledge cleared:", data);
        alert("All stored knowledge has been deleted from ChromaDB!");

        // ✅ Force clear uploaded documents from UI immediately
        const docList = document.getElementById("uploaded-docs");
        docList.innerHTML = "<p>No documents uploaded yet.</p>";

        // ✅ Ensure knowledge base is refreshed after deletion
        return fetch("http://localhost:8000/api/upload/refresh-knowledge-base", {
            method: "POST",
            headers: { "Authorization": `Bearer ${localStorage.getItem("userToken")}` }
        });
    })
    .then(() => {
        console.log("✅ Knowledge base refreshed.");
        fetchUploadedDocuments(); // ✅ Fetch updated document list
    })
    .catch(error => console.error("🚨 Clear Knowledge Error:", error));
};

