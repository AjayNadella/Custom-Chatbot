import os
import sys
from fastapi import FastAPI, HTTPException, Depends, Security, Form, Query,Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from database.chroma import knowledge_base, chroma_client
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
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(upload_router, prefix="/api/upload", tags=["User Knowledge Upload"])


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

@app.get("/")
async def root():
    """Root endpoint for API health check."""
    return {"message": "AI Copilot is running"}

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


class ChatbotCreateRequest(BaseModel):
    chatbot_name: str
    chatbot_type: str = "general"

@app.post("/chatbot/create")
async def create_chatbot(chatbot_name: str = Body(...), chatbot_type:str= Body(...),user: dict = Depends(verify_firebase_token)):
    """Creates a chatbot for the user."""
    user_id = user["localId"]
    chatbot_folder = f"uploaded_knowledge/{user_id}/{chatbot_name}"
    
    if os.path.exists(chatbot_folder):
        raise HTTPException(status_code=400, detail="Chatbot already exists.")
    
    os.makedirs(chatbot_folder, exist_ok=True)
    return {"message": f"Chatbot '{chatbot_name}' created successfully.", "chatbot_name": chatbot_name}

@app.get("/chatbot/list")
async def list_chatbots(user: dict = Depends(verify_firebase_token)):
    """Lists all chatbots created by a user."""
    user_id = user["localId"]
    chatbot_folder = f"uploaded_knowledge/{user_id}"
    
    if not os.path.exists(chatbot_folder):
        return {"chatbots": []}
    
    chatbots = os.listdir(chatbot_folder)
    return {"chatbots": chatbots}
import shutil

@app.delete("/chatbot/delete/{chatbot_name}")
async def delete_chatbot(chatbot_name: str, user: dict = Depends(verify_firebase_token)):
    """Deletes a chatbot and its knowledge base (even if it has no uploaded knowledge)."""

    global knowledge_base  

    user_id = user["localId"]
    chatbot_folder = f"uploaded_knowledge/{user_id}/{chatbot_name}"

    print(f"🔍 Attempting to delete chatbot: {chatbot_name} for User: {user_id}")

    
    if not os.path.exists(chatbot_folder):
        print(f"Chatbot '{chatbot_name}' folder not found. Returning 404.")
        raise HTTPException(status_code=404, detail=f"Chatbot '{chatbot_name}' not found.")

    
    try:
        docs_to_delete = knowledge_base.get(where={"$and": [{"user_id": user_id}, {"chatbot_name": chatbot_name}]})

        if docs_to_delete and "ids" in docs_to_delete and docs_to_delete["ids"]:
            print(f"Found {len(docs_to_delete['ids'])} embeddings. Deleting them...")
            knowledge_base.delete(ids=docs_to_delete["ids"])
            print(f"Deleted {len(docs_to_delete['ids'])} embeddings from ChromaDB for chatbot '{chatbot_name}'.")
        else:
            print(f"No embeddings found in ChromaDB for chatbot '{chatbot_name}'. Skipping ChromaDB deletion.")
    except Exception as e:
        print(f"Error checking/deleting chatbot from ChromaDB: {str(e)}")
        pass  

    try:
        print(f"Deleting chatbot files from: {chatbot_folder}")
        shutil.rmtree(chatbot_folder, ignore_errors=True)
        print(f"Deleted chatbot files: {chatbot_folder}")
    except Exception as e:
        print(f"Error deleting chatbot files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting chatbot files: {str(e)}")

   
    try:
        print(f"Refreshing ChromaDB knowledge base...")
        knowledge_base = chroma_client.get_or_create_collection(name="chatbot_knowledge")
        print(f"Knowledge base refreshed after deleting chatbot '{chatbot_name}'.")
    except Exception as e:
        print(f"Error refreshing ChromaDB: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error refreshing ChromaDB: {str(e)}")

    print(f"Chatbot '{chatbot_name}' deleted successfully!")
    return {"message": f"Chatbot '{chatbot_name}' and all related data have been deleted successfully."}



class ChatbotRequest(BaseModel):
    user_question: str
    chatbot_type: str = "general"
    chatbot_name:str
@app.post("/generate-response", dependencies=[Depends(verify_firebase_token)])
async def generate_response(request: ChatbotRequest, user: dict = Depends(verify_firebase_token)):
    """Handles chatbot queries (Protected: Requires login)."""
    
    user_id = user["localId"]
    chatbot_type = request.chatbot_type
    chatbot_name = request.chatbot_name  
    user_question = request.user_question

    global knowledge_base
    chatbot_types_response = await get_chatbot_types()
    chatbot_types = chatbot_types_response["available_chatbot_types"]
    chatbot_description = chatbot_types.get(chatbot_type, "A general-purpose chatbot.")

    print(f"Querying knowledge base for chatbot '{chatbot_name}' - User ID: {user_id}")

    stored_data = knowledge_base.query(
        query_texts=[""], 
        n_results=5,
        where={"$and": [{"user_id": user_id}, {"chatbot_name": chatbot_name}]}
    )
    print(f"Debug: Stored Data in ChromaDB for '{chatbot_name}': {stored_data}")

    
    retrieved_docs = knowledge_base.query(
        query_texts=[user_question],
        n_results=3,
        where={"$and": [{"user_id": user_id}, {"chatbot_name": chatbot_name}]} 
    )

    documents = retrieved_docs.get("documents", [])
    print(f"Debug: Retrieved Documents for Chatbot '{chatbot_name}': {documents}")


    retrieved_docs_text = "No relevant knowledge found." if not documents else "\n".join(
        doc if isinstance(doc, str) else " ".join(doc) for doc in documents
    )

    prompt_qa = PromptTemplate.from_template("""
    You are an AI assistant specialized in **{chatbot_type}**.
    Your role: {chatbot_description}

    ### Instructions:
    - If the user's question is general (like "hello", "how are you?", "who are you?"), respond naturally as a chatbot while briefly mentioning that you use knowledge from uploaded documents.
    - If the question relates to the uploaded knowledge, retrieve the most relevant information and provide a well-structured answer.
    - If the knowledge base does not contain relevant information, generate a response using general AI knowledge.
    - Keep responses concise and user-friendly.

    ### Retrieved Knowledge:
    {document_context}

    ### User's Question:
    {user_question}

    ### Response:
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

    return {
        "chatbot_name": chatbot_name,
        "chatbot_type": chatbot_type,
        "response": response.content.strip(),
    }

@app.post("/user-chatbot/{user_id}/{chatbot_name}")
async def user_chatbot(
    user_id: str, 
    chatbot_name: str,
    user_question: str = Body(..., embed=True),
    chatbot_type: str = Body(..., embed=True)
):
    chatbot_types_response = await get_chatbot_types()
    chatbot_types = chatbot_types_response["available_chatbot_types"]
    chatbot_description = chatbot_types.get(chatbot_type, "A general-purpose chatbot.")

    global knowledge_base
    
    retrieved_docs = knowledge_base.query(
        query_texts=[user_question],
        n_results=3,
        where={"$and": [{"user_id": user_id}, {"chatbot_name": chatbot_name}]} 
    )

    documents = retrieved_docs["documents"]
    retrieved_docs_text = "\n".join(doc if isinstance(doc, str) else " ".join(doc) for doc in documents)

    prompt_qa = PromptTemplate.from_template("""
   You are an AI assistant specialized in **{chatbot_type}**.
   Your role: {chatbot_description}
    
    ### Instructions:
    - If the user's question is general (like "hello", "how are you?", "who are you?"), respond naturally as a chatbot while briefly mentioning that you use knowledge from uploaded documents.
    - If the question relates to the uploaded knowledge, retrieve the most relevant information and provide a well-structured answer.
    - If the knowledge base does not contain relevant information, generate a response using general AI knowledge.
    - Keep responses concise and user-friendly.

    ### Retrieved Knowledge:
    {document_context}

    ### User's Question:
    {user_question}

    ### Response:
    """)

    chain = prompt_qa | ChatGroq(
        temperature=0.5,
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama3-70b-8192"
    )

    response = chain.invoke({
        "user_question": user_question,
        "document_context": retrieved_docs_text,
        "chatbot_type": chatbot_type.capitalize(),
        "chatbot_description": chatbot_description
    })

    return {"chatbot_name": chatbot_name,"chatbot_type": chatbot_type, "response": response.content.strip()}

@app.get("/deploy-chatbot/{user_id}/{chatbot_name}/{chatbot_type}")
async def deploy_chatbot(user_id: str,chatbot_name: str,chatbot_type: str, user: dict = Depends(verify_firebase_token)):
    """Generates a JavaScript chatbot embed code for external websites."""
    
    auth_user_id = user["localId"]
    if auth_user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied. You can only deploy your own chatbot.")

    
    embed_code = f"""
    <script>
        const chatbotName = "{chatbot_name}";
        const chatbotType = "{chatbot_type}";

        async function askChatbot(question) {{
            const response = await fetch("http://localhost:8000/user-chatbot/{user_id}/{chatbot_name}", {{
                method: "POST",
                headers: {{
                    "Content-Type": "application/json"
                }},
                body: JSON.stringify({{ 
                    "user_question": question,
                    "chatbot_type": chatbotType,
                     }})
            }});

            if (!response.ok) {{
                alert("API Error: " + response.status + " " + response.statusText);
                return;
            }}

            const data = await response.json();
            document.getElementById("chatbot-response").innerText = data.response;
        }}
    </script>

    <h3>Chatbot: {chatbot_name}</h3>
    <input type="text" id="chatbot-input" placeholder="Ask me anything..." />
    <button onclick="askChatbot(document.getElementById('chatbot-input').value)">Ask</button>
    <p id="chatbot-response"></p>
    """

    return {"embed_code": embed_code}



if __name__ == "__main__":
    print("Running Uvicorn...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)