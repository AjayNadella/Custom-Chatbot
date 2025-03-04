import chromadb

chroma_client = chromadb.PersistentClient(path="./chroma_db")

def get_knowledge_base():
    return chroma_client.get_or_create_collection(name="chatbot_knowledge", metadata={"hnsw:space": "cosine"})

knowledge_base = get_knowledge_base()