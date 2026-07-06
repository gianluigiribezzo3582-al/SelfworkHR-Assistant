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
            Domanda dell'utente: [[[ {question} ]]].
            Contesto disponibile (candidato piu' simile trovato nel database): [[[
            {context}
            ]]].
            Se la domanda e' una richiesta di trovare un candidato o un profilo professionale, usa il contesto per rispondere:
            spiega che nel file individuato c'e' il profilo piu' adatto, argomenta la scelta utilizzando il contenuto del
            testo individuato nel contesto, poi crea una sezione per i contatti del candidato indicando nome, email e
            numero di telefono, e infine indica il nome del file del cv (non nominarlo mai prima di questa sezione).
            Se invece la domanda e' un saluto, una richiesta generica o comunque non riguarda la ricerca di un candidato,
            rispondi in modo naturale e pertinente alla domanda, senza menzionare il contesto ne' alcun candidato.
        """
