import os
import fitz  
from fastapi import APIRouter, UploadFile, File, Form,HTTPException,Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database.chroma import knowledge_base
import requests
from fastapi import APIRouter
from database.chroma import chroma_client

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
    """Extracts text from a PDF file."""
    doc = fitz.open(pdf_path)
    return "\n".join([page.get_text("text") for page in doc])

@router.post("/upload-knowledge", dependencies=[Depends(verify_firebase_token)])
async def upload_knowledge(file: UploadFile = File(...), user: dict = Depends(verify_firebase_token)):
    """Handles file uploads and stores knowledge in ChromaDB for a specific user."""
    user_id = user["localId"] 
    upload_folder = f"uploaded_knowledge/{user_id}"
    os.makedirs(upload_folder, exist_ok=True)
    
    file_path = os.path.join(upload_folder, file.filename)
    
    
    with open(file_path, "wb") as f:
        f.write(await file.read())

    
    if file.filename.endswith(".pdf"):
        text_content = extract_text_from_pdf(file_path)
    else:
        return {"error": "Unsupported file format. Only PDFs are supported."}
    
    doc_id = f"{user_id}_{file.filename}"
    
    knowledge_base.add(
        documents=[text_content],
        metadatas=[{"user_id": user_id, "filename": file.filename}],
        ids=[f"{user_id}_{file.filename}"]
    )

    return {"message": "Knowledge uploaded successfully!", "user_id": user_id, "filename": file.filename}

@router.get("/list-knowledge/{user_id}")
async def list_uploaded_knowledge(user_id: str, user: dict = Depends(verify_firebase_token)):
    """Lists all uploaded documents for a user."""
    
    upload_folder = f"uploaded_knowledge/{user_id}"
    if not os.path.exists(upload_folder):
        return {"documents": []}

    files = os.listdir(upload_folder)
    documents = [{"filename": file} for file in files]

    return {"documents": documents}

# ✅ Delete Uploaded Document
@router.delete("/delete-knowledge/{user_id}/{filename}")
async def delete_knowledge(user_id: str, filename: str, user: dict = Depends(verify_firebase_token)):
    """Deletes a document from ChromaDB and the file system."""
    
    doc_id = f"{user_id}_{filename}"
    existing_docs = knowledge_base.get(ids=[doc_id])
    if existing_docs['documents']:  
        knowledge_base.delete(ids=[doc_id])
        print(f"✅ Deleted from ChromaDB: {doc_id}")

    # ✅ Delete from file system
    file_path = f"uploaded_knowledge/{user_id}/{filename}"
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"✅ Deleted from Storage: {file_path}")
        return {"message": "Document deleted successfully"}
    else:
        return {"error": "File not found"}
    
@router.post("/refresh-knowledge-base")
async def refresh_knowledge_base():
    """Reinitializes the ChromaDB knowledge base to reflect updates."""
    global knowledge_base

    
    knowledge_base = chroma_client.get_or_create_collection(name="chatbot_knowledge", metadata={"hnsw:space": "cosine"})
    
    return {"message": "Knowledge base refreshed successfully!"}