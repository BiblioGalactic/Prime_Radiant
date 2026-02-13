#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
🔥 HYBRID SEARCH - Dense + Sparse (BM25)
========================================
Combina búsqueda semántica (FAISS) con búsqueda léxica (BM25).
Técnica de vanguardia 2024-2025 para mejorar recall y precisión.

Ventajas:
- FAISS: Captura similitud semántica ("rey" ≈ "monarca")
- BM25: Captura keywords exactos ("Python 3.12" = "Python 3.12")
- Combinación: Lo mejor de ambos mundos
"""

import os
import sys
import logging
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Intentar importar dependencias
try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False
    print("⚠️ Instalar BM25: pip install rank-bm25 --break-system-packages")

try:
    import faiss
    from sentence_transformers import SentenceTransformer
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HybridSearch")


@dataclass
class HybridResult:
    """Resultado de búsqueda híbrida"""
    document: str
    score: float
    dense_score: float  # Score de FAISS
    sparse_score: float  # Score de BM25
    rank: int
    metadata: Dict[str, Any] = None
    source: str = "hybrid"


class HybridSearchEngine:
    """
    Motor de búsqueda híbrida que combina Dense (FAISS) + Sparse (BM25).

    Algoritmo:
    1. Búsqueda densa con FAISS (embeddings semánticos)
    2. Búsqueda sparse con BM25 (keywords exactos)
    3. Fusión con Reciprocal Rank Fusion (RRF) o weighted sum

    Uso:
        engine = HybridSearchEngine(faiss_index, documents, embedder)
        results = engine.search("¿Qué es Python?", k=10, alpha=0.6)

    OPTIMIZACIÓN DE MEMORIA:
    - BM25 se carga LAZY (solo cuando se necesita)
    - Si existe cache en disco, se usa sin recomputar
    - Límite de documentos para evitar OOM
    """

    # Límite de documentos para BM25 (evitar OOM con datasets grandes)
    MAX_BM25_DOCS = 500000  # 500K docs máximo

    def __init__(
        self,
        faiss_index: Any,
        documents: List[str],
        embedder: Any,
        metadata: List[Dict] = None,
        bm25_index_path: str = None,
        lazy_bm25: bool = True  # NUEVO: cargar BM25 bajo demanda
    ):
        """
        Inicializar motor híbrido.

        Args:
            faiss_index: Índice FAISS existente
            documents: Lista de documentos
            embedder: Modelo SentenceTransformer
            metadata: Metadatos de documentos (opcional)
            bm25_index_path: Ruta para persistir BM25 (opcional)
            lazy_bm25: Si cargar BM25 bajo demanda (default True)
        """
        if not HAS_BM25:
            raise ImportError("rank-bm25 no instalado. pip install rank-bm25")

        self.faiss_index = faiss_index
        self.documents = documents
        self.embedder = embedder
        self.metadata = metadata or [{}] * len(documents)
        self.bm25_index_path = bm25_index_path
        self._lazy_bm25 = lazy_bm25

        # BM25 - LAZY LOADING
        self._bm25 = None
        self._bm25_loaded = False

        # Solo cargar inmediatamente si no es lazy Y hay pocos docs
        if not lazy_bm25 and len(documents) <= self.MAX_BM25_DOCS:
            self._load_or_create_bm25()

        logger.info(f"🔥 HybridSearch inicializado: {len(documents)} docs (BM25: {'lazy' if lazy_bm25 else 'loaded'})")

    @property
    def bm25(self):
        """Acceso lazy a BM25"""
        if not self._bm25_loaded:
            self._load_or_create_bm25()
        return self._bm25

    def _load_or_create_bm25(self):
        """Cargar o crear índice BM25 (con límite de memoria)"""
        if self._bm25_loaded:
            return

        # Intentar cargar desde disco PRIMERO
        if self.bm25_index_path and os.path.exists(self.bm25_index_path):
            try:
                with open(self.bm25_index_path, 'rb') as f:
                    data = pickle.load(f)
                    self._bm25 = data['bm25']
                    self._bm25_loaded = True
                    logger.info(f"📂 BM25 cargado desde cache: {self.bm25_index_path}")
                    return
            except Exception as e:
                logger.warning(f"⚠️ Error cargando BM25 desde cache: {e}")

        # Verificar límite de documentos
        num_docs = len(self.documents)
        if num_docs > self.MAX_BM25_DOCS:
            logger.warning(f"⚠️ BM25: {num_docs} docs > límite {self.MAX_BM25_DOCS}, usando subset")
            # Usar solo los primeros N documentos para BM25
            docs_to_index = self.documents[:self.MAX_BM25_DOCS]
        else:
            docs_to_index = self.documents

        # Crear nuevo índice
        logger.info(f"🔨 Creando índice BM25 para {len(docs_to_index)} documentos...")

        # Tokenizar documentos en batches para mostrar progreso
        tokenized_docs = []
        batch_size = 10000
        for i in range(0, len(docs_to_index), batch_size):
            batch = docs_to_index[i:i+batch_size]
            tokenized_docs.extend([self._tokenize(doc) for doc in batch])
            if i > 0 and i % 50000 == 0:
                logger.info(f"   BM25: tokenizados {i}/{len(docs_to_index)} docs...")

        self._bm25 = BM25Okapi(tokenized_docs)
        self._bm25_loaded = True

        # Guardar si hay path
        if self.bm25_index_path:
            self._save_bm25(self._bm25)

        logger.info(f"✅ BM25 creado: {len(tokenized_docs)} documentos indexados")

    def _save_bm25(self, bm25: BM25Okapi):
        """Persistir índice BM25"""
        try:
            Path(self.bm25_index_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.bm25_index_path, 'wb') as f:
                pickle.dump({'bm25': bm25}, f)
            logger.info(f"💾 BM25 guardado en {self.bm25_index_path}")
        except Exception as e:
            logger.error(f"❌ Error guardando BM25: {e}")

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenizar texto para BM25.
        Simple split + lowercase. Mejorable con stemming/lemmatization.
        """
        # Limpiar y normalizar
        text = text.lower()

        # Remover caracteres especiales (mantener letras, números, espacios)
        import re
        text = re.sub(r'[^\w\s]', ' ', text)

        # Split y filtrar tokens vacíos
        tokens = [t.strip() for t in text.split() if len(t.strip()) > 1]

        return tokens

    def search(
        self,
        query: str,
        k: int = 10,
        alpha: float = 0.5,
        fusion_method: str = "weighted"
    ) -> List[HybridResult]:
        """
        Búsqueda híbrida Dense + Sparse.

        Args:
            query: Consulta del usuario
            k: Número de resultados a devolver
            alpha: Peso de FAISS (dense). BM25 = (1-alpha)
                   - alpha=1.0: Solo FAISS
                   - alpha=0.0: Solo BM25
                   - alpha=0.5: Balanceado (default)
                   - alpha=0.6: Favorece semántica
            fusion_method: "weighted" o "rrf" (Reciprocal Rank Fusion)

        Returns:
            Lista de HybridResult ordenados por score combinado
        """
        if not self.documents:
            return []

        # 1. Búsqueda densa con FAISS
        dense_results = self._search_dense(query, k=k*2)

        # 2. Búsqueda sparse con BM25
        sparse_results = self._search_sparse(query, k=k*2)

        # 3. Fusionar resultados
        if fusion_method == "rrf":
            combined = self._fuse_rrf(dense_results, sparse_results, k)
        else:
            combined = self._fuse_weighted(dense_results, sparse_results, k, alpha)

        return combined

    def _search_dense(self, query: str, k: int) -> Dict[int, float]:
        """Búsqueda densa con FAISS"""
        results = {}

        try:
            # Generar embedding de query
            query_embedding = self.embedder.encode([query], convert_to_numpy=True)

            # Normalizar si el índice usa IP (Inner Product)
            if hasattr(self.faiss_index, 'metric_type'):
                faiss.normalize_L2(query_embedding)

            # Buscar
            distances, indices = self.faiss_index.search(
                query_embedding.astype('float32'), k
            )

            # Convertir distancias a scores (0-1)
            for dist, idx in zip(distances[0], indices[0]):
                if idx >= 0 and idx < len(self.documents):
                    # Para IndexFlatIP, dist ya es similarity
                    # Para IndexFlatL2, convertir a similarity
                    score = float(dist) if dist <= 1.0 else 1.0 / (1.0 + dist)
                    results[idx] = score

            # Normalizar scores
            if results:
                max_score = max(results.values())
                if max_score > 0:
                    results = {k: v/max_score for k, v in results.items()}

        except Exception as e:
            logger.error(f"❌ Error en búsqueda densa: {e}")

        return results

    def _search_sparse(self, query: str, k: int) -> Dict[int, float]:
        """Búsqueda sparse con BM25"""
        results = {}

        try:
            # Tokenizar query
            tokenized_query = self._tokenize(query)

            if not tokenized_query:
                return results

            # Obtener scores BM25 para todos los documentos
            scores = self.bm25.get_scores(tokenized_query)

            # Obtener top-k índices
            top_indices = np.argsort(scores)[::-1][:k]

            # Normalizar scores
            max_score = scores.max() if scores.max() > 0 else 1.0

            for idx in top_indices:
                if scores[idx] > 0:
                    results[int(idx)] = float(scores[idx] / max_score)

        except Exception as e:
            logger.error(f"❌ Error en búsqueda sparse: {e}")

        return results

    def _fuse_weighted(
        self,
        dense: Dict[int, float],
        sparse: Dict[int, float],
        k: int,
        alpha: float
    ) -> List[HybridResult]:
        """
        Fusión por suma ponderada.

        Score final = alpha * dense_score + (1-alpha) * sparse_score
        """
        combined_scores = {}

        # Combinar scores
        all_indices = set(dense.keys()) | set(sparse.keys())

        for idx in all_indices:
            dense_score = dense.get(idx, 0.0)
            sparse_score = sparse.get(idx, 0.0)

            combined_scores[idx] = {
                'combined': alpha * dense_score + (1 - alpha) * sparse_score,
                'dense': dense_score,
                'sparse': sparse_score
            }

        # Ordenar por score combinado
        sorted_indices = sorted(
            combined_scores.items(),
            key=lambda x: x[1]['combined'],
            reverse=True
        )[:k]

        # Crear resultados
        results = []
        for rank, (idx, scores) in enumerate(sorted_indices, 1):
            results.append(HybridResult(
                document=self.documents[idx],
                score=scores['combined'],
                dense_score=scores['dense'],
                sparse_score=scores['sparse'],
                rank=rank,
                metadata=self.metadata[idx] if idx < len(self.metadata) else {},
                source="hybrid_weighted"
            ))

        return results

    def _fuse_rrf(
        self,
        dense: Dict[int, float],
        sparse: Dict[int, float],
        k: int,
        rrf_k: int = 60
    ) -> List[HybridResult]:
        """
        Reciprocal Rank Fusion (RRF).

        Score_RRF = Σ 1/(k + rank)

        Más robusto que weighted sum cuando los scores
        tienen diferentes distribuciones.
        """
        rrf_scores = {}

        # Ordenar resultados densos por score
        dense_ranked = sorted(dense.items(), key=lambda x: x[1], reverse=True)
        sparse_ranked = sorted(sparse.items(), key=lambda x: x[1], reverse=True)

        # Calcular RRF scores
        for rank, (idx, score) in enumerate(dense_ranked, 1):
            rrf_scores[idx] = rrf_scores.get(idx, {'rrf': 0, 'dense': 0, 'sparse': 0})
            rrf_scores[idx]['rrf'] += 1.0 / (rrf_k + rank)
            rrf_scores[idx]['dense'] = score

        for rank, (idx, score) in enumerate(sparse_ranked, 1):
            rrf_scores[idx] = rrf_scores.get(idx, {'rrf': 0, 'dense': 0, 'sparse': 0})
            rrf_scores[idx]['rrf'] += 1.0 / (rrf_k + rank)
            rrf_scores[idx]['sparse'] = score

        # Ordenar por RRF score
        sorted_indices = sorted(
            rrf_scores.items(),
            key=lambda x: x[1]['rrf'],
            reverse=True
        )[:k]

        # Crear resultados
        results = []
        for rank, (idx, scores) in enumerate(sorted_indices, 1):
            results.append(HybridResult(
                document=self.documents[idx],
                score=scores['rrf'],
                dense_score=scores['dense'],
                sparse_score=scores['sparse'],
                rank=rank,
                metadata=self.metadata[idx] if idx < len(self.metadata) else {},
                source="hybrid_rrf"
            ))

        return results

    def explain_search(self, query: str, k: int = 5) -> Dict[str, Any]:
        """
        Búsqueda con explicación detallada (para debug/análisis).
        """
        dense_results = self._search_dense(query, k=k*2)
        sparse_results = self._search_sparse(query, k=k*2)

        # Analizar overlap
        dense_set = set(list(dense_results.keys())[:k])
        sparse_set = set(list(sparse_results.keys())[:k])
        overlap = dense_set & sparse_set

        return {
            "query": query,
            "query_tokens": self._tokenize(query),
            "dense_top_k": list(dense_results.keys())[:k],
            "sparse_top_k": list(sparse_results.keys())[:k],
            "overlap": list(overlap),
            "overlap_ratio": len(overlap) / k if k > 0 else 0,
            "analysis": {
                "dense_only": list(dense_set - sparse_set),
                "sparse_only": list(sparse_set - dense_set),
                "both": list(overlap)
            }
        }


# === FUNCIÓN HELPER PARA INTEGRAR CON RAGManager ===
def create_hybrid_engine_from_rag(rag: Any, bm25_cache_path: str = None) -> HybridSearchEngine:
    """
    Crear HybridSearchEngine desde un BaseRAG existente.

    Args:
        rag: Instancia de BaseRAG con índice FAISS cargado
        bm25_cache_path: Ruta para cachear índice BM25

    Returns:
        HybridSearchEngine configurado
    """
    if not HAS_BM25 or not HAS_FAISS:
        raise ImportError("Dependencias faltantes: rank-bm25, faiss-cpu")

    if rag.index is None:
        raise ValueError(f"RAG '{rag.name}' no tiene índice cargado")

    # Path por defecto para BM25 cache
    if bm25_cache_path is None:
        bm25_cache_path = os.path.join(rag.index_path, "bm25_index.pkl")

    return HybridSearchEngine(
        faiss_index=rag.index,
        documents=rag.documents,
        embedder=rag.model,
        metadata=rag.metadata,
        bm25_index_path=bm25_cache_path
    )


# === TEST ===
if __name__ == "__main__":
    print("🔥 Test de HybridSearch")
    print("=" * 50)

    if not HAS_BM25:
        print("❌ rank-bm25 no instalado")
        print("   pip install rank-bm25 --break-system-packages")
        sys.exit(1)

    # Crear datos de prueba
    test_docs = [
        "Python es un lenguaje de programación interpretado",
        "JavaScript se usa principalmente en navegadores web",
        "El aprendizaje automático usa Python frecuentemente",
        "Machine learning es una rama de la inteligencia artificial",
        "Los modelos de lenguaje grandes como GPT usan transformers",
        "FAISS es una librería de Facebook para búsqueda de vectores",
        "BM25 es un algoritmo clásico de recuperación de información",
    ]

    # Crear embedder simple
    try:
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

        # Crear índice FAISS
        import faiss
        embeddings = embedder.encode(test_docs, convert_to_numpy=True)
        faiss.normalize_L2(embeddings)

        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings.astype('float32'))

        # Crear motor híbrido
        engine = HybridSearchEngine(index, test_docs, embedder)

        # Probar búsqueda
        query = "lenguaje de programación para machine learning"
        print(f"\n🔍 Query: {query}\n")

        results = engine.search(query, k=5, alpha=0.6)

        for r in results:
            print(f"  [{r.rank}] Score: {r.score:.3f} (D:{r.dense_score:.3f} S:{r.sparse_score:.3f})")
            print(f"      {r.document[:60]}...")
            print()

        # Explicación
        print("\n📊 Análisis de búsqueda:")
        explanation = engine.explain_search(query, k=3)
        print(f"   Overlap ratio: {explanation['overlap_ratio']:.1%}")
        print(f"   Dense-only: {len(explanation['analysis']['dense_only'])}")
        print(f"   Sparse-only: {len(explanation['analysis']['sparse_only'])}")

    except ImportError as e:
        print(f"❌ Error: {e}")
