import os
import fitz  
from fastapi import APIRouter, UploadFile, File, Form,HTTPException,Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database.chroma import knowledge_base
import requests
from fastapi import APIRouter
from database.chroma import chroma_client
import pdfplumber
import uuid
import shutil

router = APIRouter()

security = HTTPBearer()
FIREBASE_VERIFY_URL = "https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=AIzaSyDZqYgp8LnOZHj8gqi10PgbIbv-h_NQ51g"

def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Verifies Firebase ID token from frontend requests.
    """
    token = credentials.credentials
    headers = {"Content-Type": "application/json"}
    payload = {"idToken": token}

    response = requests.post(FIREBASE_VERIFY_URL, json=payload, headers=headers)
    data = response.json()

    if "users" not in data:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")

    return data["users"][0] 

UPLOAD_DIR = "uploaded_knowledge"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text.append(text)
    return all_text

def preprocess_text(text):
    cleaned_text = text.replace("\n", " ").strip()
    return cleaned_text

@router.post("/upload-knowledge", dependencies=[Depends(verify_firebase_token)])
async def upload_knowledge(file: UploadFile = File(...), user: dict = Depends(verify_firebase_token)):
    """Handles file uploads and stores knowledge in ChromaDB for a specific user."""
    user_id = user["localId"] 
    upload_folder = f"{UPLOAD_DIR}/{user_id}"
    os.makedirs(upload_folder, exist_ok=True)
    
    file_path = os.path.join(upload_folder, file.filename)
    
    
    with open(file_path, "wb") as f:
        f.write(await file.read())

    
    if not file.filename.endswith(".pdf"):
        return {"error": "Unsupported file format. Only PDFs are supported."}

    text_pages = extract_text_from_pdf(file_path)
    processed_pages = [preprocess_text(page) for page in text_pages]
    
    ids = [f"{user_id}_{file.filename}_{uuid.uuid4()}" for _ in range(len(processed_pages))]
    
    knowledge_base.add(
        documents=processed_pages,
        metadatas=[{"user_id": user_id, "file": file.filename, "page_number": i} for i in range(len(processed_pages))],
        ids=ids
    )

    return {"message": "Knowledge uploaded successfully!", "user_id": user_id, "filename": file.filename}

@router.get("/list-knowledge/{user_id}")
async def list_uploaded_knowledge(user_id: str, user: dict = Depends(verify_firebase_token)):
    """Lists all uploaded documents for a user."""
    
    upload_folder = f"uploaded_knowledge/{user_id}"
    if not os.path.exists(upload_folder):
        return {"documents": []}

    files = os.listdir(upload_folder)
    return {"documents": [{"filename": file} for file in files]}

# ✅ Delete Uploaded Document
@router.delete("/delete-knowledge/{user_id}/{filename}")
async def delete_knowledge(user_id: str, filename: str, user: dict = Depends(verify_firebase_token)):
    """Deletes all embeddings related to a document from ChromaDB and removes the file from storage."""
    global knowledge_base

    # ✅ Use `$and` operator to filter documents by both `user_id` and `file`
    docs_to_delete = knowledge_base.get(where={
        "$and": [
            {"user_id": user_id},
            {"file": filename}
        ]
    })

    # ✅ Extract IDs and delete them
    if docs_to_delete and "ids" in docs_to_delete:
        knowledge_base.delete(ids=docs_to_delete["ids"])
        print(f"✅ Deleted {len(docs_to_delete['ids'])} embeddings from ChromaDB for {filename}")
    else:
        print(f"⚠️ No embeddings found in ChromaDB for {filename}")

    # ✅ Delete from file system
    file_path = f"uploaded_knowledge/{user_id}/{filename}"
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"✅ Deleted from Storage: {file_path}")

    # ✅ Refresh knowledge base after deletion to reflect changes
    knowledge_base = chroma_client.get_or_create_collection(name="chatbot_knowledge")
    print("✅ Knowledge base refreshed after deletion.")

    return {"message": "Document and related data deleted successfully"}

    
@router.post("/refresh-knowledge-base")
async def refresh_knowledge_base():
    """Reinitializes the ChromaDB knowledge base to reflect updates."""
    global knowledge_base

    
    knowledge_base = chroma_client.get_or_create_collection(name="chatbot_knowledge", metadata={"hnsw:space": "cosine"})
    
    return {"message": "Knowledge base refreshed successfully!"}

import shutil  # Import shutil to delete folders

@router.delete("/clear-knowledge-base")
async def clear_knowledge_base():
    """Completely deletes all stored knowledge from ChromaDB and removes all uploaded files."""
    
    global knowledge_base  # Ensure we are modifying the global instance

    # ✅ Step 1: Retrieve all document IDs before deleting
    all_docs = knowledge_base.get()  # Retrieves all stored documents
    doc_ids = all_docs.get("ids", [])  # Extracts IDs
    
    if doc_ids:
        # ✅ Step 2: Delete all documents using their IDs
        knowledge_base.delete(ids=doc_ids)
        print(f"🚀 Deleted {len(doc_ids)} documents from ChromaDB.")
    else:
        print("⚠️ No documents found in ChromaDB.")

    # ✅ Step 3: Delete all uploaded files from `uploaded_knowledge/`
    upload_folder = "uploaded_knowledge"
    if os.path.exists(upload_folder):
        shutil.rmtree(upload_folder)  # 🔥 Deletes all user-uploaded files and folders
        os.makedirs(upload_folder, exist_ok=True)  # Recreate the folder to avoid errors
        print("✅ All uploaded knowledge files deleted.")

    # ✅ Step 4: Reinitialize the knowledge base to prevent stale queries
    knowledge_base = chroma_client.get_or_create_collection(name="chatbot_knowledge")
    print("✅ Knowledge base reset successfully.")

    return {"message": "All stored knowledge and uploaded files have been deleted from ChromaDB and storage."}


