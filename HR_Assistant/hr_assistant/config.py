# config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DOCUMENTS_DIR = "resumes"
    COLLECTION_NAME = "CVs"
    PERSISTENT_DIR = "data/chromadb"
    # Embedding
    EMBEDDING_MODEL = "text-embedding-3-small"
    # Completamento
    CHAT_MODEL = "gpt-4o-mini"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
