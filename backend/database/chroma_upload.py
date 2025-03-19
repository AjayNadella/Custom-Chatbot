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

@router.post("/upload-knowledge/{chatbot_name}")
async def upload_knowledge(
    chatbot_name: str,
    file: UploadFile = File(...),
    user: dict = Depends(verify_firebase_token)
):
    """Handles file uploads and stores knowledge in ChromaDB for a specific chatbot."""

    user_id = user["localId"]
    chatbot_folder = os.path.join(UPLOAD_DIR, user_id, chatbot_name)
    os.makedirs(chatbot_folder, exist_ok=True)

    file_path = os.path.join(chatbot_folder, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    if not file.filename.endswith(".pdf"):
        return {"error": "Unsupported file format. Only PDFs are supported."}

    text_pages = extract_text_from_pdf(file_path)
    processed_pages = [preprocess_text(page) for page in text_pages if page.strip()]

    if not processed_pages:
        print(f"No text extracted from {file.filename}. Check file format.")
        return {"error": f"No text extracted from {file.filename}. Ensure it's a valid PDF."}
    
    global knowledge_base 

    ids = [f"{user_id}_{chatbot_name}_{file.filename}_{i}" for i in range(len(processed_pages))]

    knowledge_base.add(
        documents=processed_pages,
        metadatas=[
            {"user_id": user_id, "chatbot_name": chatbot_name, "file": file.filename, "page_number": i} for i in range(len(processed_pages))
        ],
        ids=ids
    )

    stored_data = knowledge_base.query(
        query_texts=[""], 
        n_results=5,
        where={"$and": [{"user_id": user_id}, {"chatbot_name": chatbot_name}]}
    )
    print(f"Debug: Stored Data in ChromaDB for '{chatbot_name}': {stored_data}")

    return {"message": "Knowledge uploaded successfully!", "user_id": user_id, "filename": file.filename}


@router.get("/list-knowledge/{user_id}/{chatbot_name}")
async def list_uploaded_knowledge(user_id: str,chatbot_name: str, user: dict = Depends(verify_firebase_token)):
    auth_user_id = user["localId"]
    if auth_user_id != user_id: 
        raise HTTPException(status_code=403, detail="Access denied.")

    chatbot_folder = os.path.join(UPLOAD_DIR, user_id, chatbot_name)
    if not os.path.exists(chatbot_folder):
        return {"documents": []}

    files = os.listdir(chatbot_folder)
    return {"documents": [{"filename": file} for file in files]}


@router.delete("/delete-knowledge/{user_id}/{chatbot_name}/{filename}")
async def delete_knowledge(user_id: str,chatbot_name: str,filename: str, user: dict = Depends(verify_firebase_token)):
    """Deletes a document's embeddings from ChromaDB and removes the file from storage."""

    global knowledge_base  

    auth_user_id = user["localId"]  

    if auth_user_id != user_id:  
        raise HTTPException(status_code=403, detail="Access denied. You can only delete your own documents.")

    
    try:
        docs_to_delete = knowledge_base.get(where={"$and": [{"user_id": user_id}, {"chatbot_name": chatbot_name}, {"file": filename}]})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents from ChromaDB: {str(e)}")
    

    if docs_to_delete and "ids" in docs_to_delete and docs_to_delete["ids"]:
        knowledge_base.delete(ids=docs_to_delete["ids"])  
        print(f"Successfully deleted embeddings for file '{filename}'")
    else:
      print(f"No embeddings found for '{filename}'. Skipping ChromaDB deletion.")

    
    file_path = os.path.join(UPLOAD_DIR,user_id,chatbot_name, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted from Storage: {file_path}")
    else:
        print(f"File not found: {file_path}")
    
    return {"message": f"Document '{filename}' and related embeddings deleted successfully from chatbot '{chatbot_name}'."}

@router.post("/refresh-knowledge-base/{user_id}/{chatbot_name}")
async def refresh_knowledge_base(user_id: str, chatbot_name: str, user: dict = Depends(verify_firebase_token)):

    global knowledge_base  
    auth_user_id = user["localId"]

    if auth_user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied. You can only refresh your own chatbot's knowledge base.")

    try:
        knowledge_base = chroma_client.get_collection(name="chatbot_knowledge")
        print(f"Knowledge base refreshed for chatbot '{chatbot_name}'.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing knowledge base: {str(e)}")

    return {"message": f"Knowledge base refreshed for chatbot '{chatbot_name}'."}


@router.delete("/clear-knowledge-base/{user_id}/{chatbot_name}")
async def clear_knowledge_base(user_id: str, chatbot_name: str, user: dict = Depends(verify_firebase_token)):
    """Deletes all stored knowledge and uploaded files for a specific chatbot of a user."""
    
    global knowledge_base
    auth_user_id = user["localId"]
    
    if auth_user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied. You can only clear knowledge for your own chatbots.")

    
    try:
        chatbot_docs = knowledge_base.get(where={"user_id": user_id, "chatbot_name": chatbot_name})
        chatbot_doc_ids = chatbot_docs.get("ids", [])

        if chatbot_doc_ids:
            knowledge_base.delete(ids=chatbot_doc_ids)
            print(f"Deleted {len(chatbot_doc_ids)} documents from ChromaDB for chatbot '{chatbot_name}'.")
        else:
            print(f"No documents found in ChromaDB for chatbot '{chatbot_name}'.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chatbot knowledge: {str(e)}")

    
    chatbot_folder = os.path.join(UPLOAD_DIR, user_id, chatbot_name)
    if os.path.exists(chatbot_folder):
        shutil.rmtree(chatbot_folder)
        os.makedirs(chatbot_folder, exist_ok=True)
        print(f"Deleted all uploaded files for chatbot '{chatbot_name}'.")
    else:
        print(f"No uploaded files found for chatbot '{chatbot_name}'.")

    
    try:
        knowledge_base = chroma_client.get_or_create_collection(name="chatbot_knowledge")
        print(f"Knowledge base reset for chatbot '{chatbot_name}'.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting knowledge base: {str(e)}")

    return {"message": f"All knowledge and uploaded files for chatbot '{chatbot_name}' have been deleted."}