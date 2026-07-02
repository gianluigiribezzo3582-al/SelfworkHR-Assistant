# utils.py
from config import Config
from openai import OpenAI

client = OpenAI(api_key=Config.OPENAI_API_KEY)


class LLMHelper:

    @staticmethod
    def chat(messages):
        return client.chat.completions.create(
            model=Config.CHAT_MODEL, messages=messages, stream=True
        )

    @staticmethod
    async def get_db_stats(context):
        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"""
                      Il tuo compito e' quello di descrivere in modo testuale, ma sintetico, le statistiche legate al database dei frammenti indicizzati da questo sistema. Ecco le informazioni necessarie per le statistiche da fornire: {context}
                      """,
                }
            ],
        )
        return response.choices[0].message.content

    @staticmethod
    def create_prompt(context, question):
        return f"""
            Dato il seguente contesto:
            [[[
            {context}
            ]]].
            Rispondi alla domanda dell'utente: [[[ {question}]]].
            Spiega che nel file individuato c'e' il profilo piu' adatto.
            Argomenta la scelta utilizzando il contenuto del testo individuato nel contesto.
            Alla fine crea una sezione per i contatti del candidato indicando il nome, la sua email e il numero di telefono.
            Dopo la sezione dei contatti indica il nome del file del cv, non lo nominare mai prima di questa sezione.
        """
