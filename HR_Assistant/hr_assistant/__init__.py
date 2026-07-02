import os
import uuid
from dotenv import load_dotenv
import chainlit as cl
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()

## FASE 1 - Lettura Files e Chunking

documents_dir = "resumes"

documents = []
metadatas = []
ids = []

for filename in os.listdir(documents_dir):
    if filename.endswith(".txt"):
        with open(os.path.join(documents_dir, filename), "r") as file:
            chunks = file.read().replace("\n", ".").split("### ")

            for chunk in chunks:
                if not chunk.isspace() and not chunk == "":
                    documents.append(chunk)
                    metadatas.append({"source": filename})
                    # Genera un nuovo GUID per ogni chunk
                    guid = str(uuid.uuid4())
                    ids.append(guid)

## Fase 2 - Embeddings e inserimento nel DB Vettoriale

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"), model_name="text-embedding-3-small"
)

chroma_client = chromadb.PersistentClient(path="data/chromadb")

# Using OpenAI embedding function instead of the default model to convert text into embeddings.
collection = chroma_client.get_or_create_collection(
    name="CVs", embedding_function=openai_ef
)

collection.add(documents=documents, metadatas=metadatas, ids=ids)

## FASE 3 - CHAT (placeholder, completata nel prossimo avanzamento)


@cl.on_message
async def handle_message(message: cl.Message):
    response = f"Ciao, mi hai scritto: {message.content}!"
    await cl.Message(response).send()
