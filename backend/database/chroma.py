import chromadb

chroma_client = chromadb.PersistentClient(path="./chroma_db")

knowledge_base = chroma_client.get_or_create_collection(name="chatbot_knowledge",metadata={"hnsw:space": "cosine"}) 