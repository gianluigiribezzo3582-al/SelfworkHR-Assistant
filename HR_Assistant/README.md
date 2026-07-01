## Installazione Poetry

- https://python-poetry.org/

## Nuovo progetto Poetry

```
$ poetry new HR_Assistant

$ cd HR_Assistant

$ poetry env activate

$ poetry add chromadb openai chainlit python-dotenv
```

se c'e' un errore di versioni di librerie, fare questa modifica al file pyproject.toml

```
requires-python = ">=3.12,<4.0.0"
```

e poi provare a rilanciare `poetry add chromadb openai chainlit python-dotenv`

> Nota: su Windows, `chroma-hnswlib` (dipendenza di vecchie versioni di `chromadb`) non ha una wheel precompilata per Python 3.12, quindi qui si usa una versione recente di `chromadb` (>=1.5) che non dipende piu' da `chroma-hnswlib` e installa senza bisogno di un compilatore C++.

## per eseguire l'applicazione

```
$ poetry install
$ eval $(poetry env activate)

$ chainlit run hr_assistant/__init__.py -w
```
