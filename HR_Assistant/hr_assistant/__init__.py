import os
import chainlit as cl
from document_processor import DocumentProcessor
from database import Database
from config import Config
from utils import LLMHelper


# Process documents
documents, metadatas, ids = DocumentProcessor.process_documents()

# Initialize database and add documents
db = Database()
db.add_documents(documents, metadatas, ids)


@cl.on_chat_start
def start():
    cl.user_session.set(
        "messages",
        [
            {
                "role": "system",
                "content": """
                    Sei un assistente specializzato nel mondo HR, rispondi in modo professionale, sintetico e pragmatico.
                    Il tuo ruolo è individuare il candidato ideale rispetto alle richieste dell'utente.
                """,
            }
        ],
    )


@cl.on_message
async def handle_message(message: cl.Message):
    user_question = message.content
    results = db.query(user_question)
    distance = results["distances"][0][0]

    if distance <= Config.RELEVANCE_THRESHOLD:
        filename = results["metadatas"][0][0]["source"]
        context_lines = DocumentProcessor.read_first_lines(
            os.path.join(Config.DOCUMENTS_DIR, filename), 10
        )

        context = f"CONTESTO: ecco il paragrafo piu' significativo del profilo individuato: {results['documents'][0][0]}"

        candidate_name = await LLMHelper.get_candidate_name(context_lines)

        prompt = LLMHelper.create_prompt(context, user_question, candidate_name)
    else:
        # Nessun CV sufficientemente pertinente: rispondi senza forzare un abbinamento
        prompt = user_question

    messages = cl.user_session.get("messages", [])
    messages.append({"role": "user", "content": prompt})

    response_message = cl.Message(content="")
    await response_message.send()

    try:
        stream = LLMHelper.chat(messages)

        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                await response_message.stream_token(delta)

        messages.append({"role": "assistant", "content": response_message.content})
        await response_message.update()

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        await cl.Message(content=error_message).send()
        print(error_message)

    cl.user_session.set("messages", messages)
