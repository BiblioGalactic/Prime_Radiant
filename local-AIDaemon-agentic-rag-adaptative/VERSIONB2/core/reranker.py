#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
🎯 RERANKER - Cross-Encoder Re-ranking
========================================
Re-rankea documentos usando un modelo Cross-Encoder.
Técnica de vanguardia para mejorar precisión del RAG.

Diferencia Bi-Encoder vs Cross-Encoder:
- Bi-Encoder (FAISS): Rápido, pero menos preciso
  query → embedding₁
  doc → embedding₂
  score = cosine(embedding₁, embedding₂)

- Cross-Encoder: Lento, pero MUY preciso
  (query, doc) → modelo → score directo
  Considera interacción completa query-documento

Uso típico:
1. FAISS devuelve top-50 candidatos (rápido)
2. Cross-Encoder re-rankea → top-5 finales (preciso)
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Intentar importar dependencias
try:
    from sentence_transformers import CrossEncoder
    HAS_CROSS_ENCODER = True
except ImportError:
    HAS_CROSS_ENCODER = False
    print("⚠️ Instalar: pip install sentence-transformers --break-system-packages")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Reranker")


@dataclass
class RerankedResult:
    """Resultado re-rankeado"""
    document: str
    original_score: float
    rerank_score: float
    original_rank: int
    new_rank: int
    metadata: Dict[str, Any] = None
    boost: float = 0.0  # Cuánto subió/bajó


class Reranker:
    """
    Re-rankea documentos con modelo Cross-Encoder.

    Modelos recomendados (de más rápido a más preciso):
    - cross-encoder/ms-marco-MiniLM-L-6-v2  (rápido, bueno)
    - cross-encoder/ms-marco-MiniLM-L-12-v2 (balanceado)
    - cross-encoder/ms-marco-TinyBERT-L-2-v2 (muy rápido, menos preciso)

    Para español:
    - cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 (multilingüe)
    """

    # Modelos disponibles con sus características
    AVAILABLE_MODELS = {
        "fast": {
            "name": "cross-encoder/ms-marco-TinyBERT-L-2-v2",
            "description": "Muy rápido, precisión básica",
            "latency_ms": 5
        },
        "balanced": {
            "name": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "description": "Buen balance velocidad/precisión",
            "latency_ms": 15
        },
        "accurate": {
            "name": "cross-encoder/ms-marco-MiniLM-L-12-v2",
            "description": "Alta precisión, más lento",
            "latency_ms": 30
        },
        "multilingual": {
            "name": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
            "description": "Multilingüe (español incluido)",
            "latency_ms": 25
        }
    }

    def __init__(
        self,
        model_name: str = None,
        preset: str = "balanced",
        max_length: int = 512,
        batch_size: int = 32
    ):
        """
        Inicializar Reranker.

        Args:
            model_name: Nombre del modelo (override preset)
            preset: "fast", "balanced", "accurate", "multilingual"
            max_length: Longitud máxima de texto
            batch_size: Tamaño de batch para inferencia
        """
        if not HAS_CROSS_ENCODER:
            raise ImportError("sentence-transformers no instalado")

        # Seleccionar modelo
        if model_name:
            self.model_name = model_name
        elif preset in self.AVAILABLE_MODELS:
            self.model_name = self.AVAILABLE_MODELS[preset]["name"]
        else:
            self.model_name = self.AVAILABLE_MODELS["balanced"]["name"]

        self.max_length = max_length
        self.batch_size = batch_size

        # Cargar modelo (lazy loading)
        self._model = None

        logger.info(f"🎯 Reranker configurado: {self.model_name}")

    @property
    def model(self) -> CrossEncoder:
        """Lazy loading del modelo"""
        if self._model is None:
            logger.info(f"📥 Cargando Cross-Encoder: {self.model_name}")
            self._model = CrossEncoder(
                self.model_name,
                max_length=self.max_length
            )
            logger.info("✅ Cross-Encoder cargado")
        return self._model

    def rerank(
        self,
        query: str,
        documents: List[Union[str, Dict]],
        top_k: int = 5,
        return_scores: bool = True
    ) -> List[RerankedResult]:
        """
        Re-rankear documentos por relevancia a la query.

        Args:
            query: Consulta del usuario
            documents: Lista de strings o dicts con 'document'
            top_k: Número de resultados a devolver
            return_scores: Si incluir scores en resultados

        Returns:
            Lista de RerankedResult ordenados por relevancia
        """
        if not documents:
            return []

        # Normalizar documentos a lista de strings
        doc_texts = []
        doc_metadata = []
        original_scores = []

        for i, doc in enumerate(documents):
            if isinstance(doc, str):
                doc_texts.append(doc)
                doc_metadata.append({})
                original_scores.append(0.0)
            elif isinstance(doc, dict):
                doc_texts.append(doc.get('document', str(doc)))
                doc_metadata.append(doc.get('metadata', {}))
                original_scores.append(doc.get('score', 0.0))
            else:
                doc_texts.append(str(doc))
                doc_metadata.append({})
                original_scores.append(0.0)

        # Crear pares (query, document)
        pairs = [(query, doc) for doc in doc_texts]

        # Calcular scores con Cross-Encoder
        logger.debug(f"🔄 Re-rankeando {len(pairs)} documentos...")
        scores = self.model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False
        )

        # Crear resultados con scores
        results = []
        for i, (doc_text, score, orig_score, meta) in enumerate(
            zip(doc_texts, scores, original_scores, doc_metadata)
        ):
            results.append({
                'document': doc_text,
                'rerank_score': float(score),
                'original_score': orig_score,
                'original_rank': i + 1,
                'metadata': meta
            })

        # Ordenar por score de reranking
        results.sort(key=lambda x: x['rerank_score'], reverse=True)

        # Crear RerankedResult con nueva posición
        final_results = []
        for new_rank, r in enumerate(results[:top_k], 1):
            boost = r['original_rank'] - new_rank  # Positivo = subió
            final_results.append(RerankedResult(
                document=r['document'],
                original_score=r['original_score'],
                rerank_score=r['rerank_score'],
                original_rank=r['original_rank'],
                new_rank=new_rank,
                metadata=r['metadata'],
                boost=boost
            ))

        return final_results

    def rerank_with_threshold(
        self,
        query: str,
        documents: List[Union[str, Dict]],
        threshold: float = 0.0,
        top_k: int = 10
    ) -> List[RerankedResult]:
        """
        Re-rankear con umbral mínimo de relevancia.

        Args:
            query: Consulta
            documents: Documentos a re-rankear
            threshold: Score mínimo para incluir (0-1 normalizado)
            top_k: Máximo de resultados

        Returns:
            Solo documentos con score >= threshold
        """
        results = self.rerank(query, documents, top_k=len(documents))

        # Normalizar scores a 0-1
        if results:
            max_score = max(r.rerank_score for r in results)
            min_score = min(r.rerank_score for r in results)
            score_range = max_score - min_score if max_score != min_score else 1.0

            filtered = []
            for r in results:
                normalized_score = (r.rerank_score - min_score) / score_range
                if normalized_score >= threshold:
                    filtered.append(r)

            return filtered[:top_k]

        return []

    def explain_reranking(
        self,
        query: str,
        documents: List[Union[str, Dict]]
    ) -> Dict[str, Any]:
        """
        Análisis detallado del reranking (para debug).

        Returns:
            Dict con estadísticas y cambios de posición
        """
        results = self.rerank(query, documents, top_k=len(documents))

        # Calcular estadísticas
        boosts = [r.boost for r in results]
        scores = [r.rerank_score for r in results]

        # Documentos que más subieron/bajaron
        sorted_by_boost = sorted(results, key=lambda x: x.boost, reverse=True)

        return {
            "query": query,
            "total_docs": len(documents),
            "stats": {
                "avg_boost": sum(boosts) / len(boosts) if boosts else 0,
                "max_boost": max(boosts) if boosts else 0,
                "min_boost": min(boosts) if boosts else 0,
                "avg_score": sum(scores) / len(scores) if scores else 0,
            },
            "biggest_movers": {
                "up": [
                    {"doc": r.document[:100], "boost": r.boost}
                    for r in sorted_by_boost[:3] if r.boost > 0
                ],
                "down": [
                    {"doc": r.document[:100], "boost": r.boost}
                    for r in sorted_by_boost[-3:] if r.boost < 0
                ]
            },
            "top_5": [
                {
                    "rank": r.new_rank,
                    "was": r.original_rank,
                    "score": round(r.rerank_score, 4),
                    "doc": r.document[:80]
                }
                for r in results[:5]
            ]
        }


class CachedReranker(Reranker):
    """
    Reranker con caché LRU para evitar re-computar pares query-doc.
    Útil cuando las mismas queries se repiten.
    """

    def __init__(self, cache_size: int = 1000, **kwargs):
        super().__init__(**kwargs)
        self._cache: Dict[str, float] = {}
        self._cache_size = cache_size
        self._cache_hits = 0
        self._cache_misses = 0

    def _cache_key(self, query: str, doc: str) -> str:
        """Generar key única para par query-doc"""
        import hashlib
        combined = f"{query}|||{doc}"
        return hashlib.md5(combined.encode()).hexdigest()

    def rerank(
        self,
        query: str,
        documents: List[Union[str, Dict]],
        top_k: int = 5,
        return_scores: bool = True
    ) -> List[RerankedResult]:
        """Rerank con caché"""

        # Normalizar documentos
        doc_texts = []
        for doc in documents:
            if isinstance(doc, str):
                doc_texts.append(doc)
            elif isinstance(doc, dict):
                doc_texts.append(doc.get('document', str(doc)))
            else:
                doc_texts.append(str(doc))

        # Separar cached vs nuevos
        cached_scores = {}
        pairs_to_compute = []
        indices_to_compute = []

        for i, doc in enumerate(doc_texts):
            key = self._cache_key(query, doc)
            if key in self._cache:
                cached_scores[i] = self._cache[key]
                self._cache_hits += 1
            else:
                pairs_to_compute.append((query, doc))
                indices_to_compute.append(i)
                self._cache_misses += 1

        # Computar nuevos scores
        if pairs_to_compute:
            new_scores = self.model.predict(
                pairs_to_compute,
                batch_size=self.batch_size,
                show_progress_bar=False
            )

            # Guardar en caché
            for idx, score in zip(indices_to_compute, new_scores):
                key = self._cache_key(query, doc_texts[idx])
                self._cache[key] = float(score)
                cached_scores[idx] = float(score)

                # Limpiar caché si excede tamaño
                if len(self._cache) > self._cache_size:
                    # Eliminar entrada más antigua (simple FIFO)
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]

        # Construir resultados usando parent class logic
        results = []
        for i, doc in enumerate(documents):
            if isinstance(doc, dict):
                results.append({
                    'document': doc.get('document', str(doc)),
                    'rerank_score': cached_scores[i],
                    'original_score': doc.get('score', 0.0),
                    'original_rank': i + 1,
                    'metadata': doc.get('metadata', {})
                })
            else:
                results.append({
                    'document': str(doc),
                    'rerank_score': cached_scores[i],
                    'original_score': 0.0,
                    'original_rank': i + 1,
                    'metadata': {}
                })

        # Ordenar y devolver
        results.sort(key=lambda x: x['rerank_score'], reverse=True)

        final_results = []
        for new_rank, r in enumerate(results[:top_k], 1):
            boost = r['original_rank'] - new_rank
            final_results.append(RerankedResult(
                document=r['document'],
                original_score=r['original_score'],
                rerank_score=r['rerank_score'],
                original_rank=r['original_rank'],
                new_rank=new_rank,
                metadata=r['metadata'],
                boost=boost
            ))

        return final_results

    def get_cache_stats(self) -> Dict[str, Any]:
        """Estadísticas de caché"""
        total = self._cache_hits + self._cache_misses
        return {
            "size": len(self._cache),
            "max_size": self._cache_size,
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "hit_rate": self._cache_hits / total if total > 0 else 0
        }


# === TEST ===
if __name__ == "__main__":
    print("🎯 Test de Reranker")
    print("=" * 50)

    if not HAS_CROSS_ENCODER:
        print("❌ sentence-transformers no instalado")
        sys.exit(1)

    # Documentos de prueba
    test_docs = [
        "Python es un lenguaje de programación interpretado",
        "JavaScript se ejecuta en navegadores web",
        "El aprendizaje automático usa Python frecuentemente",
        "Machine learning es parte de la inteligencia artificial",
        "Los gatos son mascotas populares",
        "FAISS es una librería de Facebook para vectores",
        "Python tiene librerías como NumPy y Pandas",
    ]

    query = "¿Qué lenguaje se usa para machine learning?"

    print(f"\n🔍 Query: {query}\n")
    print("📄 Documentos originales (orden arbitrario):")
    for i, doc in enumerate(test_docs, 1):
        print(f"   {i}. {doc[:50]}...")

    # Crear reranker
    reranker = Reranker(preset="balanced")

    # Re-rankear
    print("\n🔄 Re-rankeando con Cross-Encoder...")
    results = reranker.rerank(query, test_docs, top_k=5)

    print("\n✅ Resultados re-rankeados:")
    for r in results:
        boost_str = f"+{r.boost}" if r.boost > 0 else str(r.boost)
        print(f"   [{r.new_rank}] (era #{r.original_rank}, {boost_str}) Score: {r.rerank_score:.4f}")
        print(f"       {r.document[:60]}...")
        print()

    # Explicación
    print("\n📊 Análisis de reranking:")
    analysis = reranker.explain_reranking(query, test_docs)
    print(f"   Boost promedio: {analysis['stats']['avg_boost']:.2f}")
    print(f"   Mayor subida: {analysis['stats']['max_boost']}")
    print(f"   Mayor bajada: {analysis['stats']['min_boost']}")
