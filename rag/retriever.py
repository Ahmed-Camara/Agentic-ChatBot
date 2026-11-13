from rag.embedding import embeddings
from langchain_community.vectorstores import FAISS

def get_retriever():
    DB_PATH = "db/rag_db/faiss_db"
    vector_store = FAISS.load_local(
        folder_path=DB_PATH,
        embeddings=embeddings,
        allow_dangerous_deserialization=True
    )
    
    
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k":4}
    )
    
    return retriever