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
file `.txt` in quella cartella.

## Chunking Semantico

Invece di dividere i CV in modo meccanico (per marcatori di paragrafo `### ` o per lunghezza fissa),
il testo viene prima diviso in frasi; ogni frase viene poi combinata con quelle immediatamente vicine
per darle contesto e se ne calcola l'embedding OpenAI. Confrontando via similarita' coseno l'embedding
di frasi consecutive si individuano i punti in cui il significato cambia in modo significativo (sopra il
95° percentile delle distanze): li' si spezza il testo in un nuovo chunk. Il risultato sono chunk che
raggruppano frasi semanticamente coerenti, invece di frammenti tagliati arbitrariamente. Vedi
`hr_assistant/semantic_chunking.py`.

## Avvio dell'applicazione

```
$ poetry run chainlit run hr_assistant/__init__.py -w
```

All'avvio i CV vengono sincronizzati con ChromaDB (`data/chromadb`, escluso da git). Apri
`http://localhost:8000` e chiedi in chat il profilo che stai cercando, ad esempio: *"Ho bisogno di
una persona esperta di marketing"*.

## Sincronizzazione dei CV

Ad ogni avvio, invece di reindicizzare tutti i CV da zero, il sistema sincronizza `resumes/` con il
database confrontando gli hash MD5 dei file:

- **file nuovi** (in `resumes/` ma non nel DB) → vengono suddivisi in chunk e indicizzati;
- **file modificati** (hash del contenuto diverso da quello tracciato) → i vecchi frammenti vengono
  rimossi e sostituiti con quelli aggiornati;
- **file rimossi** (tracciati nel DB ma non piu' presenti in `resumes/`) → i relativi frammenti
  vengono eliminati dal DB.

Questo evita duplicazioni, riduce le chiamate all'API di embedding al minimo necessario e mantiene
il database sempre coerente con lo stato reale della cartella `resumes/`.

All'avvio della chat sono disponibili due bottoni:
- **Statistiche Database**: numero di frammenti indicizzati e di CV distinti nel DB.
- **Reindex Database**: rilancia manualmente il sync sopra descritto senza riavviare l'app.
