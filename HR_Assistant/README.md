# HR Assistant

Assistente HR basato su RAG (Retrieval-Augmented Generation): indicizza i CV presenti in `resumes/`,
recupera il candidato piu' pertinente rispetto alla richiesta dell'utente e genera una risposta
professionale tramite OpenAI Chat Completion.

Flusso: CV (`resumes/*.txt`) → chunking → embedding OpenAI → ChromaDB (persistito in `data/`) →
domanda utente → embedding → retrieval → contesto → prompt → OpenAI Chat Completion → risposta in chat.

## Installazione Poetry

- https://python-poetry.org/

## Setup

```
$ git clone <repo>
$ cd HR_Assistant

$ poetry install
$ poetry env activate
```

se c'e' un errore di versioni di librerie, fare questa modifica al file `pyproject.toml`

```
requires-python = ">=3.12,<4.0.0"
```

e poi provare a rilanciare `poetry add chromadb openai chainlit python-dotenv`

> Nota: su Windows, `chroma-hnswlib` (dipendenza di vecchie versioni di `chromadb`) non ha una wheel precompilata per Python 3.12, quindi qui si usa una versione recente di `chromadb` (>=1.5) che non dipende piu' da `chroma-hnswlib` e installa senza bisogno di un compilatore C++.

## Configurazione

Crea un file `.env` nella root del progetto con la tua chiave OpenAI:

```
OPENAI_API_KEY=sk-...
```

La chiave non va mai scritta nel codice: viene letta a runtime da `.env` tramite `python-dotenv`.

## CV indicizzati

I CV di esempio si trovano in `resumes/*.txt`. Per aggiungere nuovi candidati basta inserire un nuovo
file `.txt` in quella cartella (i paragrafi vanno separati con `### `).

## Avvio dell'applicazione

```
$ poetry run chainlit run hr_assistant/__init__.py -w
```

All'avvio i CV vengono (ri)letti, suddivisi in chunk e indicizzati in ChromaDB (`data/chromadb`,
escluso da git). Apri `http://localhost:8000` e chiedi in chat il profilo che stai cercando, ad
esempio: *"Ho bisogno di una persona esperta di marketing"*.
