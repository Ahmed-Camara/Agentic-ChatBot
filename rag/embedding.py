import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()
API_KEY = os.getenv("API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL")

embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL,base_url=EMBEDDING_BASE_URL,api_key=API_KEY)