"""
VERSIONE5: RAG básico con FAISS
Cargar índice y recuperar contexto
"""

import pickle
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer

from config import INDEX_PATH, EMBEDDINGS_MODEL, CONTEXT_WINDOW


class SimpleRAG:
    """Recuperación RAG mínima con FAISS"""

    def __init__(self):
        self.index_path = Path(INDEX_PATH)
        self.embeddings_model = SentenceTransformer(EMBEDDINGS_MODEL)

        # Cargar índice FAISS
        self.index = self._load_index()

        # Cargar metadatos (textos originales)
        self.chunks = self._load_chunks()

    def _load_index(self) -> faiss.IndexFlatL2:
        """Carga el índice FAISS"""
        index_file = str(self.index_path)

        if not self.index_path.exists():
            raise FileNotFoundError(f"Índice FAISS no encontrado en {index_file}")

        try:
            index = faiss.read_index(index_file)
            print(f"✓ Índice FAISS cargado ({index.ntotal} vectores)")
            return index
        except Exception as e:
            raise RuntimeError(f"Error al cargar índice FAISS: {e}")

    def _load_chunks(self) -> list:
        """Carga los fragmentos de texto asociados al índice"""
        chunks_file = self.index_path.parent / "chunks.pkl"

        if not chunks_file.exists():
            raise FileNotFoundError(f"Metadatos no encontrados en {chunks_file}")

        try:
            with open(chunks_file, "rb") as f:
                chunks = pickle.load(f)
            print(f"✓ {len(chunks)} fragmentos cargados")
            return chunks
        except Exception as e:
            raise RuntimeError(f"Error al cargar chunks: {e}")

    def search(self, query: str, k: int = None) -> str:
        """
        Busca fragmentos relevantes y retorna el contexto.

        Args:
            query: Pregunta del usuario
            k: Número de fragmentos (por defecto CONTEXT_WINDOW)

        Returns:
            Contexto concatenado de los fragmentos más relevantes
        """
        if k is None:
            k = min(CONTEXT_WINDOW, len(self.chunks))

        try:
            # Embed la query
            query_vector = self.embeddings_model.encode([query], convert_to_numpy=True)

            # Buscar en FAISS
            distances, indices = self.index.search(query_vector, k)

            # Recuperar chunks
            context_chunks = []
            for idx in indices[0]:
                if 0 <= idx < len(self.chunks):
                    context_chunks.append(self.chunks[idx])

            context = "\n\n".join(context_chunks)
            return context

        except Exception as e:
            raise RuntimeError(f"Error en búsqueda RAG: {e}")

    def search_with_scores(self, query: str, k: int = None) -> list:
        """
        Retorna fragmentos con scores de relevancia.

        Returns:
            Lista de tuplas (fragment, score)
        """
        if k is None:
            k = min(CONTEXT_WINDOW, len(self.chunks))

        query_vector = self.embeddings_model.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_vector, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if 0 <= idx < len(self.chunks):
                results.append((self.chunks[idx], float(dist)))

        return results
