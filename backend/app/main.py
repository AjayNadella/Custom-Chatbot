import os
import sys
from fastapi import FastAPI, HTTPException, Depends, Security, Form, Query,Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from database.chroma import knowledge_base
from dotenv import load_dotenv
from database.chroma_upload import router as upload_router
from app.authe import router as auth_router
import requests
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

print("Starting FastAPI...")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print("Importing dependencies...")

load_dotenv()

print("Initializing FastAPI app...")

app = FastAPI(title="AI Copilot", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500"],  # ✅ Allow requests from frontend
    allow_credentials=True,
    allow_methods=["*"],  # ✅ Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # ✅ Allow all headers
)
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(upload_router, prefix="/api/upload", tags=["User Knowledge Upload"])

# Security scheme for Firebase authentication
security = HTTPBearer()

# Firebase API URL for token verification
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

    return data["users"][0]  # Returns authenticated user info

@app.get("/")
async def root():
    """Root endpoint for API health check."""
    return {"message": "AI Copilot is running 🚀"}

@app.get("/chatbot-types", dependencies=[Depends(verify_firebase_token)])
async def get_chatbot_types():
    """Returns available chatbot types (Protected: Requires login)."""
    return {
        "available_chatbot_types": {
            "general": "A general-purpose chatbot for answering any type of question.",
            "healthcare": "A medical chatbot for health-related topics.",
            "finance": "A financial chatbot for banking and investment queries.",
            "legal": "A legal assistant providing general legal definitions and case law insights.",
            "education": "An AI tutor assisting with learning and study materials.",
            "ecommerce": "A shopping assistant helping users find and compare products."
        }
    }
class ChatbotRequest(BaseModel):
    user_id: str
    user_question: str
    chatbot_type: str = "general"
@app.post("/generate-response", dependencies=[Depends(verify_firebase_token)])
async def generate_response(request: ChatbotRequest):
    """Handles chatbot queries (Protected: Requires login)."""
    chatbot_type = request.chatbot_type
    user_question = request.user_question
    user_id = request.user_id

    chatbot_types_response = await get_chatbot_types()
    chatbot_types = chatbot_types_response["available_chatbot_types"]
    chatbot_description = chatbot_types.get(chatbot_type, "A general-purpose chatbot.")
    
    retrieved_docs = knowledge_base.query(
        query_texts=[user_question],
        n_results=3,
        where={"user_id": user_id}
    )
    documents = retrieved_docs["documents"]

    retrieved_docs_text = "\n".join(
            doc if isinstance(doc, str) else " ".join(doc) for doc in documents
    )

    prompt_qa = PromptTemplate.from_template("""
    You are an AI assistant specialized in **{chatbot_type}**.
    Your role: {chatbot_description}

    ### KNOWLEDGE BASE:
    The following information has been retrieved from the medical knowledge base:
    {document_context}

    ### USER QUESTION:
    {user_question}

    ### INSTRUCTIONS:
    - Use the information in the knowledge base to craft your response.
    - If the knowledge base does not contain sufficient information to fully answer the question, supplement your response with your own medical expertise.
    - Provide your answer in a clear and concise format, suitable for a layperson.

    ### RESPONSE:
    """)

    chain = prompt_qa | ChatGroq(
        temperature=0.5,
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama3-70b-8192"
    )

    response = chain.invoke({
        "user_question": user_question,
        "chatbot_type": chatbot_type.capitalize(),
        "chatbot_description": chatbot_description,
        "document_context": retrieved_docs_text
    })

    return {"chatbot_type": chatbot_type, "response": response.content.strip()}

if __name__ == "__main__":
    print("Running Uvicorn...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
