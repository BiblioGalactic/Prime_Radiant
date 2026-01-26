#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    RAG MANAGER - Gestor Unificado de RAGs
========================================
Gestiona múltiples RAGs: Wikipedia, Éxitos, Fallos, Agentes.
Permite búsqueda en cascada, paralela e indexación incremental.
"""

import os
import sys
import re
import pickle
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import logging

# === Setup paths para imports absolutos ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Intentar importar dependencias
try:
    from sentence_transformers import SentenceTransformer, util
    import faiss
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    print("⚠️ Instalar: pip install sentence-transformers faiss-cpu")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAGManager")


# === SINGLETON DE EMBEDDINGS ===
class EmbeddingModelManager:
    """
    Singleton para compartir modelos de embeddings entre todos los RAGs.
    Evita cargar el mismo modelo múltiples veces.
    """
    _instance = None
    _models: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._models = {}
        return cls._instance

    def get_model(self, model_name: str, model_path: str = None) -> Any:
        """
        Obtener modelo de embeddings (cached).

        Args:
            model_name: Nombre del modelo
            model_path: Ruta local (opcional)

        Returns:
            SentenceTransformer model
        """
        if not HAS_DEPS:
            return None

        # Usar path como key si existe, sino model_name
        key = model_path if model_path and os.path.exists(model_path) else model_name

        if key not in self._models:
            logger.info(f"[EmbeddingManager] Cargando modelo: {key}")
            if model_path and os.path.exists(model_path):
                self._models[key] = SentenceTransformer(model_path)
            else:
                self._models[key] = SentenceTransformer(model_name)
            logger.info(f"[EmbeddingManager] Modelo cargado ✓")

        return self._models[key]

    def preload_default_model(self):
        """Precargar el modelo por defecto del sistema"""
        default_model = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.get_model(default_model)


# Instancia global
_embedding_manager = EmbeddingModelManager()


def get_embedding_model(model_name: str = None, model_path: str = None):
    """Helper para obtener modelo de embeddings"""
    model_name = model_name or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    return _embedding_manager.get_model(model_name, model_path)


@dataclass
class SearchResult:
    """Resultado de búsqueda"""
    document: str
    score: float
    metadata: Dict[str, Any]
    source_rag: str


class RetrievalStrategy(Enum):
    """Estrategias de recuperación adaptativa"""
    BROAD = "broad"        # k=50, threshold bajo → exploración
    FOCUSED = "focused"    # k=10, threshold alto → precisión
    BALANCED = "balanced"  # k=20, threshold medio → default
    ITERATIVE = "iterative"  # Búsqueda recursiva con refinamiento


@dataclass
class RAGStats:
    """Estadísticas de un RAG"""
    name: str
    total_documents: int
    index_size_mb: float
    last_updated: float


class BaseRAG:
    """
    Clase base para RAGs con FAISS.
    Basada en WikipediaRAG del usuario pero más genérica.
    """

    def __init__(
        self,
        name: str,
        index_path: str,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_path: str = None
    ):
        """
        Inicializar RAG.

        Args:
            name: Nombre identificador del RAG
            index_path: Ruta al directorio del índice
            model_name: Nombre del modelo de embeddings
            model_path: Ruta local al modelo (opcional)
        """
        self.name = name
        self.index_path = index_path
        self.model_name = model_name
        self.model_path = model_path

        # Datos
        self.documents: List[str] = []
        self.metadata: List[Dict] = []
        self.index: Optional[Any] = None  # FAISS index
        self.dimension: int = 0

        # Modelo de embeddings
        self._model = None
        self._ids_set: set = set()  # Para evitar duplicados

        # Crear directorio si no existe
        Path(index_path).mkdir(parents=True, exist_ok=True)

    @property
    def model(self):
        """Lazy loading del modelo (usa singleton compartido)"""
        if self._model is None and HAS_DEPS:
            # Usar singleton en lugar de cargar modelo propio
            self._model = get_embedding_model(self.model_name, self.model_path)
        return self._model

    def load_index(self) -> bool:
        """Cargar índice desde disco"""
        if not HAS_DEPS:
            logger.error("Dependencias no instaladas")
            return False

        index_file = os.path.join(self.index_path, "faiss_index.index")
        docs_file = os.path.join(self.index_path, "documents.pkl")
        meta_file = os.path.join(self.index_path, "metadata.pkl")

        if not all(os.path.exists(f) for f in [index_file, docs_file, meta_file]):
            logger.warning(f"[{self.name}] Índice no encontrado en {self.index_path}")
            return False

        try:
            self.index = faiss.read_index(index_file)
            self.dimension = self.index.d

            with open(docs_file, 'rb') as f:
                self.documents = pickle.load(f)

            with open(meta_file, 'rb') as f:
                self.metadata = pickle.load(f)

            # Reconstruir set de IDs
            self._ids_set = set()
            for doc in self.documents:
                h = hashlib.md5(doc.encode('utf-8')).hexdigest()
                self._ids_set.add(h)

            logger.info(f"[{self.name}] Índice cargado: {len(self.documents)} documentos")
            return True

        except Exception as e:
            logger.error(f"[{self.name}] Error cargando índice: {e}")
            return False

    def save_index(self):
        """Guardar índice a disco"""
        if self.index is None:
            logger.warning(f"[{self.name}] No hay índice que guardar")
            return

        try:
            index_file = os.path.join(self.index_path, "faiss_index.index")
            docs_file = os.path.join(self.index_path, "documents.pkl")
            meta_file = os.path.join(self.index_path, "metadata.pkl")

            faiss.write_index(self.index, index_file)

            with open(docs_file, 'wb') as f:
                pickle.dump(self.documents, f)

            with open(meta_file, 'wb') as f:
                pickle.dump(self.metadata, f)

            logger.info(f"[{self.name}] Índice guardado: {len(self.documents)} documentos")

        except Exception as e:
            logger.error(f"[{self.name}] Error guardando índice: {e}")

    def add_document(
        self,
        content: str,
        metadata: Dict[str, Any] = None,
        save: bool = True
    ) -> bool:
        """
        Añadir un documento al índice.

        Args:
            content: Contenido del documento
            metadata: Metadatos asociados
            save: Si guardar inmediatamente

        Returns:
            True si se añadió, False si ya existía
        """
        if not HAS_DEPS:
            return False

        # Verificar duplicado
        doc_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        if doc_hash in self._ids_set:
            logger.debug(f"[{self.name}] Documento duplicado, ignorando")
            return False

        # Generar embedding
        embedding = self.model.encode([content], convert_to_numpy=True)
        faiss.normalize_L2(embedding)

        # Inicializar índice si es necesario
        if self.index is None:
            self.dimension = embedding.shape[1]
            self.index = faiss.IndexFlatIP(self.dimension)

        # Añadir al índice
        self.index.add(embedding.astype('float32'))
        self.documents.append(content)
        self.metadata.append(metadata or {})
        self._ids_set.add(doc_hash)

        if save:
            self.save_index()

        return True

    def add_documents_batch(
        self,
        documents: List[str],
        metadatas: List[Dict] = None,
        batch_size: int = 100
    ):
        """
        Añadir múltiples documentos en lote.

        Args:
            documents: Lista de documentos
            metadatas: Lista de metadatos (opcional)
            batch_size: Tamaño de lote para embeddings
        """
        if not HAS_DEPS:
            return

        metadatas = metadatas or [{}] * len(documents)

        # Filtrar duplicados
        new_docs = []
        new_metas = []
        for doc, meta in zip(documents, metadatas):
            doc_hash = hashlib.md5(doc.encode('utf-8')).hexdigest()
            if doc_hash not in self._ids_set:
                new_docs.append(doc)
                new_metas.append(meta)
                self._ids_set.add(doc_hash)

        if not new_docs:
            logger.info(f"[{self.name}] Todos los documentos ya existían")
            return

        logger.info(f"[{self.name}] Añadiendo {len(new_docs)} documentos nuevos...")

        # Procesar en lotes
        for i in range(0, len(new_docs), batch_size):
            batch_docs = new_docs[i:i+batch_size]
            batch_metas = new_metas[i:i+batch_size]

            # Generar embeddings
            embeddings = self.model.encode(
                batch_docs,
                batch_size=32,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            faiss.normalize_L2(embeddings)

            # Inicializar índice si es necesario
            if self.index is None:
                self.dimension = embeddings.shape[1]
                self.index = faiss.IndexFlatIP(self.dimension)

            # Añadir al índice
            self.index.add(embeddings.astype('float32'))
            self.documents.extend(batch_docs)
            self.metadata.extend(batch_metas)

            logger.info(f"[{self.name}] Procesados {min(i+batch_size, len(new_docs))}/{len(new_docs)}")

        self.save_index()

    def search(
        self,
        query: str,
        k: int = 5,
        threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        Buscar documentos similares.

        Args:
            query: Consulta
            k: Número de resultados
            threshold: Umbral mínimo de similitud

        Returns:
            Lista de SearchResult
        """
        if not HAS_DEPS or self.index is None:
            return []

        # Generar embedding de la consulta
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)

        # Buscar
        scores, indices = self.index.search(query_embedding.astype('float32'), k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents) and score >= threshold:
                results.append(SearchResult(
                    document=self.documents[idx],
                    score=float(score),
                    metadata=self.metadata[idx],
                    source_rag=self.name
                ))

        return results

    def get_stats(self) -> RAGStats:
        """Obtener estadísticas del RAG"""
        index_size = 0
        if os.path.exists(os.path.join(self.index_path, "faiss_index.index")):
            index_size = os.path.getsize(os.path.join(self.index_path, "faiss_index.index"))

        return RAGStats(
            name=self.name,
            total_documents=len(self.documents),
            index_size_mb=index_size / (1024 * 1024),
            last_updated=time.time()
        )


class FeedbackRAG(BaseRAG):
    """
    RAG especializado para éxitos/fallos con estructura específica.
    Almacena pares (consulta, respuesta, veredicto).
    """

    def add_feedback(
        self,
        query: str,
        response: str,
        verdict: str,
        suggestion: str = None
    ):
        """
        Añadir feedback al RAG.

        Args:
            query: Consulta original
            response: Respuesta generada
            verdict: OK, PARCIAL, FALLA
            suggestion: Sugerencia de mejora (para fallos)
        """
        # Contenido combinado para búsqueda
        content = f"CONSULTA: {query}\n\nRESPUESTA: {response}"
        if suggestion:
            content += f"\n\nSUGERENCIA: {suggestion}"

        metadata = {
            "query": query,
            "response": response[:500],  # Truncar para metadata
            "verdict": verdict,
            "suggestion": suggestion,
            "timestamp": time.time()
        }

        self.add_document(content, metadata)


class AgentRAG(BaseRAG):
    """
    RAG especializado para planes y procesos de agentes.
    """

    def add_plan(
        self,
        plan: Dict[str, Any],
        results: List[Dict] = None
    ):
        """
        Añadir plan ejecutado al RAG.

        Args:
            plan: Plan con pasos
            results: Resultados de ejecución
        """
        # Serializar plan
        content = f"PLAN: {plan.get('description', 'Sin descripción')}\n\n"
        for i, step in enumerate(plan.get('steps', []), 1):
            content += f"PASO {i}: {step}\n"

        if results:
            content += "\n\nRESULTADOS:\n"
            for r in results:
                content += f"- {r.get('step', '?')}: {r.get('status', '?')}\n"

        metadata = {
            "plan": plan,
            "results": results,
            "timestamp": time.time()
        }

        self.add_document(content, metadata)


class RAGManager:
    """
    Gestor unificado de múltiples RAGs.
    Permite búsqueda en cascada o paralela.
    Soporta recuperación adaptativa con múltiples estrategias.
    """

    # === CONFIGURACIÓN DE ESTRATEGIAS ===
    STRATEGY_CONFIGS = {
        RetrievalStrategy.BROAD: {
            "k": 50,
            "threshold": 0.2,
            "description": "Exploración amplia, máxima cobertura"
        },
        RetrievalStrategy.FOCUSED: {
            "k": 10,
            "threshold": 0.5,
            "description": "Precisión alta, resultados muy relevantes"
        },
        RetrievalStrategy.BALANCED: {
            "k": 20,
            "threshold": 0.3,
            "description": "Balance entre cobertura y precisión"
        },
        RetrievalStrategy.ITERATIVE: {
            "k": 15,
            "threshold": 0.35,
            "max_iterations": 3,
            "description": "Búsqueda iterativa con refinamiento"
        }
    }

    def __init__(self):
        """Inicializar gestor de RAGs"""
        from core.config import config

        self.rags: Dict[str, BaseRAG] = {}
        self.config = config

        # Modelo semántico compartido para filtros
        self._semantic_model = None

        # Cache de queries para evitar búsquedas repetidas
        self._query_cache: Dict[str, List[SearchResult]] = {}
        self._cache_max_size = 100

    @property
    def semantic_model(self):
        """Modelo semántico para filtros post-búsqueda (usa singleton)"""
        if self._semantic_model is None and HAS_DEPS:
            model_path = self.config.SEMANTIC_MODEL
            self._semantic_model = get_embedding_model(
                "sentence-transformers/all-MiniLM-L6-v2",
                model_path if os.path.exists(model_path) else None
            )
        return self._semantic_model

    def register_rag(self, rag: BaseRAG, load: bool = True):
        """
        Registrar un RAG en el gestor.

        Args:
            rag: Instancia de BaseRAG
            load: Si cargar el índice inmediatamente
        """
        self.rags[rag.name] = rag
        if load:
            rag.load_index()
        logger.info(f"RAG registrado: {rag.name}")

    def init_default_rags(self):
        """Inicializar RAGs por defecto del sistema"""
        # Wikipedia (solo lectura)
        wiki_rag = BaseRAG(
            name="wikipedia",
            index_path=self.config.RAG_WIKIPEDIA.index_path
        )
        self.register_rag(wiki_rag)

        # Éxitos
        exitos_rag = FeedbackRAG(
            name="exitos",
            index_path=self.config.RAG_EXITOS.index_path
        )
        self.register_rag(exitos_rag)

        # Fallos
        fallos_rag = FeedbackRAG(
            name="fallos",
            index_path=self.config.RAG_FALLOS.index_path
        )
        self.register_rag(fallos_rag)

        # Agentes
        agentes_rag = AgentRAG(
            name="agentes",
            index_path=self.config.RAG_AGENTES.index_path
        )
        self.register_rag(agentes_rag)

    def search(
        self,
        query: str,
        rag_names: List[str] = None,
        k: int = 5,
        mode: str = "cascade"
    ) -> List[SearchResult]:
        """
        Buscar en uno o más RAGs.

        Args:
            query: Consulta
            rag_names: Lista de RAGs a buscar (None = todos)
            k: Resultados por RAG
            mode: "cascade" (secuencial) o "parallel" (todos a la vez)

        Returns:
            Lista combinada de SearchResult
        """
        if rag_names is None:
            rag_names = list(self.rags.keys())

        all_results = []

        if mode == "cascade":
            # Buscar secuencialmente, parar si hay buenos resultados
            for name in rag_names:
                if name in self.rags:
                    results = self.rags[name].search(query, k=k)
                    all_results.extend(results)

                    # Si hay resultados de alta calidad, parar
                    if any(r.score > 0.8 for r in results):
                        break
        else:
            # Buscar en todos los RAGs
            for name in rag_names:
                if name in self.rags:
                    results = self.rags[name].search(query, k=k)
                    all_results.extend(results)

        # Ordenar por score
        all_results.sort(key=lambda r: r.score, reverse=True)

        return all_results[:k * 2]  # Retornar el doble de k

    def adaptive_search(
        self,
        query: str,
        strategy: RetrievalStrategy = RetrievalStrategy.BALANCED,
        rag_names: List[str] = None,
        context_hint: str = None
    ) -> Tuple[List[SearchResult], Dict[str, Any]]:
        """
        Búsqueda adaptativa con estrategia configurable.

        Args:
            query: Consulta
            strategy: Estrategia de recuperación (BROAD, FOCUSED, BALANCED, ITERATIVE)
            rag_names: RAGs a buscar (None = todos)
            context_hint: Pista de contexto para ajustar búsqueda

        Returns:
            Tupla (resultados, métricas)
        """
        config = self.STRATEGY_CONFIGS[strategy]
        k = config["k"]
        threshold = config["threshold"]

        metrics = {
            "strategy": strategy.value,
            "initial_k": k,
            "threshold": threshold,
            "iterations": 1,
            "total_candidates": 0,
            "final_results": 0
        }

        # Cache check
        cache_key = f"{query}:{strategy.value}"
        if cache_key in self._query_cache:
            logger.debug(f"[AdaptiveSearch] Cache hit para: {query[:30]}...")
            cached = self._query_cache[cache_key]
            metrics["cached"] = True
            return cached, metrics

        if strategy == RetrievalStrategy.ITERATIVE:
            # Búsqueda iterativa con refinamiento
            results, metrics = self._iterative_search(query, rag_names, config)
        else:
            # Búsqueda estándar con parámetros de estrategia
            results = self.search(query, rag_names, k=k, mode="parallel")
            metrics["total_candidates"] = len(results)

            # Filtrar por threshold
            results = [r for r in results if r.score >= threshold]
            metrics["final_results"] = len(results)

        # Actualizar cache
        self._update_cache(cache_key, results)

        logger.info(f"[AdaptiveSearch] {strategy.value}: {metrics['total_candidates']} candidatos → {metrics['final_results']} resultados")
        return results, metrics

    def _iterative_search(
        self,
        query: str,
        rag_names: List[str],
        config: Dict
    ) -> Tuple[List[SearchResult], Dict]:
        """Búsqueda iterativa con refinamiento progresivo"""
        max_iter = config.get("max_iterations", 3)
        k = config["k"]
        threshold = config["threshold"]

        all_results = []
        seen_docs = set()
        metrics = {
            "strategy": "iterative",
            "initial_k": k,
            "threshold": threshold,
            "iterations": 0,
            "total_candidates": 0,
            "final_results": 0,
            "quality_scores": []
        }

        current_query = query

        for iteration in range(max_iter):
            metrics["iterations"] += 1

            # Buscar con query actual
            results = self.search(current_query, rag_names, k=k, mode="parallel")
            metrics["total_candidates"] += len(results)

            # Filtrar duplicados y umbral
            new_results = []
            for r in results:
                doc_hash = hashlib.md5(r.document.encode()).hexdigest()
                if doc_hash not in seen_docs and r.score >= threshold:
                    seen_docs.add(doc_hash)
                    new_results.append(r)
                    all_results.append(r)

            if not new_results:
                logger.debug(f"[IterativeSearch] Iter {iteration+1}: sin nuevos resultados, terminando")
                break

            # Calcular calidad promedio
            avg_score = sum(r.score for r in new_results) / len(new_results)
            metrics["quality_scores"].append(avg_score)

            # Si calidad es alta, terminar
            if avg_score > 0.7:
                logger.debug(f"[IterativeSearch] Iter {iteration+1}: calidad alta ({avg_score:.2f}), terminando")
                break

            # Refinar query para siguiente iteración
            # Usar términos de los mejores documentos
            if new_results:
                top_docs = " ".join([r.document[:200] for r in new_results[:3]])
                # Extraer términos frecuentes (simple)
                words = re.findall(r'\b\w{4,}\b', top_docs.lower())
                word_freq = {}
                for w in words:
                    word_freq[w] = word_freq.get(w, 0) + 1
                top_words = sorted(word_freq.items(), key=lambda x: -x[1])[:5]
                expansion_terms = " ".join([w[0] for w in top_words if w[0] not in query.lower()])
                if expansion_terms:
                    current_query = f"{query} {expansion_terms}"
                    logger.debug(f"[IterativeSearch] Query expandida: {current_query[:50]}...")

        # Ordenar todos los resultados por score
        all_results.sort(key=lambda r: r.score, reverse=True)
        metrics["final_results"] = len(all_results)

        return all_results[:k*2], metrics

    def _update_cache(self, key: str, results: List[SearchResult]):
        """Actualizar cache con límite de tamaño"""
        if len(self._query_cache) >= self._cache_max_size:
            # Eliminar entrada más antigua (FIFO simple)
            oldest_key = next(iter(self._query_cache))
            del self._query_cache[oldest_key]
        self._query_cache[key] = results

    def clear_cache(self):
        """Limpiar cache de queries"""
        self._query_cache.clear()
        logger.info("[RAGManager] Cache limpiado")

    def select_strategy(self, query: str, complexity: int = None) -> RetrievalStrategy:
        """
        Seleccionar estrategia óptima según la query.

        Args:
            query: Consulta
            complexity: Complejidad estimada (1-5), auto-calcula si None

        Returns:
            Estrategia recomendada
        """
        if complexity is None:
            # Estimar complejidad
            complexity = 2
            if len(query) > 100:
                complexity += 1
            if len(query) > 200:
                complexity += 1
            if any(w in query.lower() for w in ['detallado', 'explica', 'analiza', 'compara', 'detail', 'explain']):
                complexity += 1

        # Selección basada en complejidad
        if complexity <= 2:
            return RetrievalStrategy.FOCUSED
        elif complexity <= 3:
            return RetrievalStrategy.BALANCED
        elif complexity <= 4:
            return RetrievalStrategy.BROAD
        else:
            return RetrievalStrategy.ITERATIVE

    def search_with_filters(
        self,
        query: str,
        rag_names: List[str] = None,
        k: int = 5,
        keyword_threshold: int = 1,
        semantic_threshold: float = 0.3
    ) -> List[SearchResult]:
        """
        Buscar con filtros de palabras clave y semántico.

        Args:
            query: Consulta
            rag_names: RAGs a buscar
            k: Resultados
            keyword_threshold: Mínimo palabras coincidentes
            semantic_threshold: Umbral de similitud semántica

        Returns:
            Resultados filtrados
        """
        # Búsqueda inicial
        results = self.search(query, rag_names, k=k*2)

        if not results:
            return []

        # Filtro de palabras clave
        query_words = set(query.lower().split())
        filtered = []
        for r in results:
            doc_words = r.document.lower()
            matches = sum(1 for w in query_words if w in doc_words)
            if matches >= keyword_threshold:
                filtered.append(r)

        if not filtered:
            filtered = results[:k]  # Fallback

        # Filtro semántico
        if HAS_DEPS and self.semantic_model:
            q_emb = self.semantic_model.encode(query, convert_to_tensor=True)
            final_results = []
            for r in filtered:
                doc_emb = self.semantic_model.encode(r.document[:500], convert_to_tensor=True)
                sim = util.pytorch_cos_sim(q_emb, doc_emb).item()
                if sim >= semantic_threshold:
                    r.score = sim  # Actualizar score con similitud semántica
                    final_results.append(r)

            final_results.sort(key=lambda r: r.score, reverse=True)
            return final_results[:k]

        return filtered[:k]

    def get_context(
        self,
        query: str,
        k: int = 3,
        max_chars: int = 2000,
        max_per_doc: int = 400
    ) -> Tuple[str, List[str]]:
        """
        Obtener contexto formateado para el daemon.

        Args:
            query: Consulta
            k: Número máximo de resultados (default 3)
            max_chars: Máximo caracteres totales del contexto
            max_per_doc: Máximo caracteres por documento

        Returns:
            Tupla (contexto_string, lista_de_fuentes)
        """
        results = self.search_with_filters(query, k=k)

        if not results:
            return "", []

        context_parts = []
        sources = []
        total_chars = 0

        for r in results:
            # Limitar caracteres por documento
            doc_text = r.document[:max_per_doc]
            if len(r.document) > max_per_doc:
                doc_text += "..."

            title = r.metadata.get('title', r.source_rag)
            part = f"[{title}] (score: {r.score:.2f}):\n{doc_text}"

            # Verificar límite total
            if total_chars + len(part) > max_chars:
                logger.info(f"Contexto truncado: {total_chars}/{max_chars} chars, {len(context_parts)} docs")
                break

            context_parts.append(part)
            sources.append(r.source_rag)
            total_chars += len(part)

        logger.info(f"Contexto: {len(context_parts)} docs, {total_chars} chars")
        return "\n\n".join(context_parts), list(set(sources))

    def get_context_adaptive(
        self,
        query: str,
        strategy: RetrievalStrategy = None,
        max_chars: int = 3000,
        max_per_doc: int = 500
    ) -> Tuple[str, List[str], Dict[str, Any]]:
        """
        Obtener contexto con estrategia adaptativa.

        Args:
            query: Consulta
            strategy: Estrategia (auto-selecciona si None)
            max_chars: Máximo caracteres totales
            max_per_doc: Máximo caracteres por documento

        Returns:
            Tupla (contexto, fuentes, métricas)
        """
        # Auto-seleccionar estrategia si no se especifica
        if strategy is None:
            strategy = self.select_strategy(query)

        # Búsqueda adaptativa
        results, metrics = self.adaptive_search(query, strategy=strategy)

        if not results:
            return "", [], metrics

        # Construir contexto
        context_parts = []
        sources = []
        total_chars = 0

        for r in results:
            doc_text = r.document[:max_per_doc]
            if len(r.document) > max_per_doc:
                doc_text += "..."

            title = r.metadata.get('title', r.source_rag)
            part = f"[{title}] (score: {r.score:.2f}):\n{doc_text}"

            if total_chars + len(part) > max_chars:
                break

            context_parts.append(part)
            sources.append(r.source_rag)
            total_chars += len(part)

        metrics["context_docs"] = len(context_parts)
        metrics["context_chars"] = total_chars

        logger.info(f"[ContextAdaptive] {strategy.value}: {len(context_parts)} docs, {total_chars} chars")
        return "\n\n".join(context_parts), list(set(sources)), metrics

    def add_success(self, query: str, response: str):
        """Registrar respuesta exitosa"""
        if "exitos" in self.rags:
            self.rags["exitos"].add_feedback(query, response, "OK")

    def add_failure(self, query: str, response: str, suggestion: str = None):
        """Registrar respuesta fallida"""
        if "fallos" in self.rags:
            self.rags["fallos"].add_feedback(
                query, response, "FALLA", suggestion
            )

    def add_plan(self, plan: Dict, results: List[Dict] = None):
        """Registrar plan de agentes"""
        if "agentes" in self.rags:
            self.rags["agentes"].add_plan(plan, results)

    def get_all_stats(self) -> Dict[str, RAGStats]:
        """Obtener estadísticas de todos los RAGs"""
        return {name: rag.get_stats() for name, rag in self.rags.items()}


# === CLI para pruebas ===
if __name__ == "__main__":
    import sys

    if not HAS_DEPS:
        print("❌ Instalar dependencias: pip install sentence-transformers faiss-cpu")
        sys.exit(1)

    manager = RAGManager()
    manager.init_default_rags()

    if len(sys.argv) < 2:
        print("Uso: rag_manager.py [search|stats|add] [args]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "search":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Python programming"
        print(f"🔍 Buscando: {query}")
        results = manager.search_with_filters(query, k=3)
        for i, r in enumerate(results, 1):
            print(f"\n{i}. [{r.source_rag}] Score: {r.score:.3f}")
            print(f"   {r.document[:200]}...")

    elif cmd == "stats":
        print("📊 Estadísticas de RAGs:")
        for name, stats in manager.get_all_stats().items():
            print(f"  {name}: {stats.total_documents} docs, {stats.index_size_mb:.1f} MB")

    elif cmd == "add":
        # Test: añadir documento
        manager.add_success(
            "¿Qué es Python?",
            "Python es un lenguaje de programación interpretado..."
        )
        print("✅ Feedback añadido")

    else:
        print(f"Comando desconocido: {cmd}")
