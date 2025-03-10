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
    auth_user_id = user["localId"]
    if auth_user_id != user_id: 
        raise HTTPException(status_code=403, detail="Access denied.")

    upload_folder = f"uploaded_knowledge/{user_id}"
    if not os.path.exists(upload_folder):
        return {"documents": []}

    files = os.listdir(upload_folder)
    return {"documents": [{"filename": file} for file in files]}


@router.delete("/delete-knowledge/{user_id}/{filename}")
async def delete_knowledge(user_id: str, filename: str, user: dict = Depends(verify_firebase_token)):
    """Deletes a document's embeddings from ChromaDB and removes the file from storage."""

    global knowledge_base  

    auth_user_id = user["localId"]  

    if auth_user_id != user_id:  
        raise HTTPException(status_code=403, detail="Access denied. You can only delete your own documents.")

    
    try:
        docs_to_delete = knowledge_base.get(where={
            "$and": [
                {"user_id": user_id},
                {"file": filename}
            ]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents from ChromaDB: {str(e)}")

    
    if docs_to_delete and "ids" in docs_to_delete:
        knowledge_base.delete(ids=docs_to_delete["ids"])
        print(f"Deleted {len(docs_to_delete['ids'])} embeddings from ChromaDB for {filename}")
    else:
        print(f"No embeddings found in ChromaDB for {filename}")

    
    file_path = os.path.join(UPLOAD_DIR, user_id, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted from Storage: {file_path}")
    else:
        print(f"File not found: {file_path}")

    
    try:
        knowledge_base = chroma_client.get_or_create_collection(name="chatbot_knowledge")
        print("Knowledge base refreshed after deletion.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing ChromaDB: {str(e)}")

    return {"message": "Document and related data deleted successfully"}




@router.post("/refresh-knowledge-base")
async def refresh_knowledge_base():
    """Reinitializes the ChromaDB knowledge base to reflect updates."""
    global knowledge_base

    knowledge_base = chroma_client.get_or_create_collection(name="chatbot_knowledge", metadata={"hnsw:space": "cosine"})
    
    return {"message": "Knowledge base refreshed successfully!"}


@router.delete("/clear-knowledge-base")
async def clear_knowledge_base(user: dict = Depends(verify_firebase_token)):
    """Deletes all stored knowledge and uploaded files for the logged-in user only."""
    global knowledge_base
    user_id = user["localId"]  

    
    user_docs = knowledge_base.get(where={"user_id": user_id})
    user_doc_ids = user_docs.get("ids", [])

    if user_doc_ids:
        knowledge_base.delete(ids=user_doc_ids)
        print(f"Deleted {len(user_doc_ids)} documents from ChromaDB for user {user_id}.")
    else:
        print(f"No documents found in ChromaDB for user {user_id}.")

    
    user_folder = os.path.join(UPLOAD_DIR, user_id)
    if os.path.exists(user_folder):
        shutil.rmtree(user_folder)  
        os.makedirs(user_folder, exist_ok=True)  
        print(f"Deleted all uploaded files for user {user_id}.")
    else:
        print(f"No uploaded files found for user {user_id}.")

    
    knowledge_base = chroma_client.get_or_create_collection(name="chatbot_knowledge")
    print("Knowledge base reset successfully.")

    return {"message": f"All knowledge and uploaded files for user {user_id} have been deleted."}