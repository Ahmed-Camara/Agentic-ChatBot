from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from rag.embedding import embeddings

def ingest_rag_document(file_path):
    DB_PATH = "db/rag_db/faiss_db"
    loader = PyPDFLoader(file_path=file_path)
    docs = loader.load()
    
    splitter = RecursiveCharacterTextSplitter(separators=["\n\n","\n","."," "])
    chunks = splitter.split_documents(docs)
    
    vector_store = FAISS.from_documents(chunks,embeddings)
    vector_store.save_local(DB_PATH)
    return 