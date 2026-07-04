# semantic_chunking.py
import re
import numpy as np
from langchain_openai import OpenAIEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
from config import Config


class SemanticChunking:
    """Divide un testo in chunk semantici: le frasi restano insieme finche' la
    distanza coseno tra frasi consecutive (con contesto) non supera una soglia
    espressa come percentile delle distanze osservate nel documento."""

    def __init__(self, breakpoint_percentile=50, buffer_size=1):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=Config.OPENAI_API_KEY, model=Config.EMBEDDING_MODEL
        )
        self.breakpoint_percentile = breakpoint_percentile
        self.buffer_size = buffer_size

    def _split_into_sentences(self, text):
        """Divide il testo in frasi, con fallback progressivi per evitare che un
        intero file (es. senza punteggiatura standard) diventi un'unica frase."""
        sentences = re.split(r"(?<=[.?!])\s+", text.strip())

        if len(sentences) == 1 and len(text) > 100:
            delimiters = r"([.!?\n;:])"
            parts = re.split(delimiters, text.strip())

            sentences = []
            for i in range(0, len(parts) - 1, 2):
                if parts[i].strip():
                    sentences.append(parts[i].strip() + parts[i + 1])

            if len(sentences) == 1:
                sentences = [s.strip() + "," for s in text.split(",") if s.strip()]
                if sentences:
                    sentences[-1] = sentences[-1][:-1] + "."

        sentences = [s for s in sentences if s.strip()]
        return sentences if sentences else [text + "."]

    def _process_sentences(self, text):
        """Divide il testo in frasi e arricchisce ognuna col contesto delle vicine."""
        sentences = [
            {"sentence": s, "index": i}
            for i, s in enumerate(self._split_into_sentences(text))
        ]

        for i, current in enumerate(sentences):
            context_range = range(
                max(0, i - self.buffer_size),
                min(len(sentences), i + self.buffer_size + 1),
            )
            current["combined_sentence"] = " ".join(
                sentences[j]["sentence"] for j in context_range
            )

        return sentences

    def _calculate_distances(self, sentences):
        """Calcola la distanza coseno tra ogni frase (con contesto) e la successiva."""
        embeddings = self.embeddings.embed_documents(
            [s["combined_sentence"] for s in sentences]
        )

        distances = []
        for i in range(len(sentences) - 1):
            distance = 1 - cosine_similarity([embeddings[i]], [embeddings[i + 1]])[0][0]
            distances.append(distance)

        return distances

    def chunk_text(self, text):
        sentences = self._process_sentences(text)
        distances = self._calculate_distances(sentences)

        threshold = np.percentile(distances, self.breakpoint_percentile)
        split_points = [i for i, d in enumerate(distances) if d > threshold]

        chunks = []
        start = 0
        for point in split_points + [len(sentences) - 1]:
            chunk = " ".join(s["sentence"] for s in sentences[start : point + 1])
            chunks.append(chunk)
            start = point + 1

        return chunks
