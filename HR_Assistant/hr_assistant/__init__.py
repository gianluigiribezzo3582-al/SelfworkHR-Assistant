import os
import chainlit as cl
from document_processor import DocumentProcessor
from database import Database
from config import Config
from utils import LLMHelper


db = Database()

# Sincronizza i CV in resumes/ con il database (add/update/remove basati su hash)
added, updated, removed = DocumentProcessor.process_documents(db)
print(f"Sync CV completato: {added} aggiunti, {updated} aggiornati, {removed} rimossi")


@cl.action_callback("db_stats")
async def on_db_stats(action: cl.Action):
    db_info = db.get_stats()
    response = await LLMHelper.get_db_stats(db_info)
    await cl.Message(response).send()


@cl.action_callback("db_reindex")
async def on_db_reindex(action: cl.Action):
    added, updated, removed = DocumentProcessor.process_documents(db)
    await cl.Message(
        f"DB reindicizzato con successo. Sync CV completato: {added} aggiunti, {updated} aggiornati, {removed} rimossi"
    ).send()


@cl.on_chat_start
async def start():
    actions = [
        cl.Action(
            name="db_stats",
            icon="mouse-pointer-click",
            payload={"value": "db_stats"},
            label="Statistiche Database",
        ),
        cl.Action(
            name="db_reindex",
            icon="mouse-pointer-click",
            payload={"value": "db_reindex"},
            label="Reindex Database",
        ),
    ]
    await cl.Message(content="Informazioni del sistema:", actions=actions).send()

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
    filename = results["metadatas"][0][0]["source"]
    candidate_info = DocumentProcessor.read_first_lines(
        os.path.join(Config.DOCUMENTS_DIR, filename), 10
    )

    context = f"CONTESTO: nome file {filename}, ecco il paragrafo piu' significativo: {results['documents'][0][0]}, qui trovi le informazioni del candidato: {candidate_info}"

    prompt = LLMHelper.create_prompt(context, user_question)

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
