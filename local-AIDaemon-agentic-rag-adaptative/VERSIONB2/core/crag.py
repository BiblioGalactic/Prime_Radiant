#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
🔄 CRAG - Corrective RAG
========================================
Implementación de CRAG (Yan et al., 2024).

RAG que se auto-corrige:
1. Recupera documentos locales
2. Evalúa calidad de recuperación
3. Si calidad < umbral → busca en web
4. Combina fuentes y genera respuesta

Flujo:
Query → Retrieve Local → Evaluate Quality
                            ↓
              Quality >= threshold?
                  ├─ YES → Generate with local docs
                  └─ NO  → Web Search → Combine → Generate
"""

import os
import sys
import logging
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CRAG")


class RetrievalQuality(Enum):
    """Niveles de calidad de recuperación"""
    EXCELLENT = "excellent"    # >= 0.8
    GOOD = "good"              # >= 0.6
    ACCEPTABLE = "acceptable"  # >= 0.4
    POOR = "poor"              # < 0.4


class CorrectionAction(Enum):
    """Acciones de corrección"""
    NONE = "none"              # No se necesita corrección
    WEB_SEARCH = "web_search"  # Buscar en web
    REFINE_QUERY = "refine"    # Refinar query y re-buscar
    EXPAND_K = "expand_k"      # Aumentar k y re-buscar


@dataclass
class CRAGResult:
    """Resultado de CRAG con métricas de corrección"""
    response: str
    local_quality: float
    correction_action: CorrectionAction
    sources_used: List[str] = field(default_factory=list)  # "local", "web"
    documents: List[Dict] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class CorrectiveRAG:
    """
    RAG que se auto-corrige buscando fuentes adicionales
    cuando la calidad de recuperación local es baja.

    Estrategias de corrección:
    1. Web Search: Busca en internet si docs locales son pobres
    2. Query Refinement: Reformula la query y re-busca
    3. Expand K: Aumenta número de documentos recuperados

    Uso:
        crag = CorrectiveRAG(rag_manager, web_searcher=web_client)
        result = crag.retrieve_and_generate("¿Qué pasó en 2024?")
    """

    # Umbrales de calidad
    QUALITY_THRESHOLDS = {
        RetrievalQuality.EXCELLENT: 0.8,
        RetrievalQuality.GOOD: 0.6,
        RetrievalQuality.ACCEPTABLE: 0.4,
        RetrievalQuality.POOR: 0.0
    }

    def __init__(
        self,
        rag_manager: Any,
        llm_interface: Any = None,
        web_searcher: Any = None,
        quality_threshold: float = 0.5,
        max_corrections: int = 2,
        web_results_count: int = 5
    ):
        """
        Inicializar CRAG.

        Args:
            rag_manager: Gestor de RAG local
            llm_interface: Interfaz LLM para generación
            web_searcher: Cliente para búsqueda web (MCP o similar)
            quality_threshold: Umbral mínimo de calidad
            max_corrections: Máximo de intentos de corrección
            web_results_count: Número de resultados web a obtener
        """
        self.rag = rag_manager
        self.llm = llm_interface
        self.web_searcher = web_searcher
        self.quality_threshold = quality_threshold
        self.max_corrections = max_corrections
        self.web_results_count = web_results_count

        # Cache de embeddings para evaluación de calidad
        self._embedder = None

        logger.info(f"🔄 CRAG inicializado (threshold={quality_threshold})")

    @property
    def embedder(self):
        """Lazy loading del embedder para evaluación"""
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                # Usar modelo ligero para evaluación
                self._embedder = SentenceTransformer(
                    'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
                )
            except ImportError:
                logger.warning("⚠️ sentence-transformers no disponible")
        return self._embedder

    def retrieve_with_correction(
        self,
        query: str,
        k: int = 5
    ) -> Tuple[List[Dict], CorrectionAction, float]:
        """
        Recuperar documentos con corrección automática.

        Args:
            query: Consulta del usuario
            k: Número de documentos a recuperar

        Returns:
            (documentos, acción_tomada, calidad_final)
        """
        corrections_made = 0
        current_query = query
        all_docs = []
        sources_used = []

        # === PASO 1: Búsqueda local ===
        logger.info(f"🔍 Búsqueda local: {query[:50]}...")
        local_docs = self._search_local(current_query, k=k)
        sources_used.append("local")

        if local_docs:
            all_docs.extend(local_docs)

        # === PASO 2: Evaluar calidad ===
        quality_score = self._evaluate_retrieval_quality(query, local_docs)
        quality_level = self._get_quality_level(quality_score)

        logger.info(f"📊 Calidad local: {quality_score:.2f} ({quality_level.value})")

        # === PASO 3: Decidir corrección ===
        if quality_score >= self.quality_threshold:
            logger.info("✅ Calidad suficiente, no se necesita corrección")
            return all_docs[:k], CorrectionAction.NONE, quality_score

        # === PASO 4: Aplicar correcciones ===
        action_taken = CorrectionAction.NONE

        while corrections_made < self.max_corrections and quality_score < self.quality_threshold:
            corrections_made += 1

            # Decidir qué corrección aplicar
            correction = self._decide_correction(
                quality_score,
                quality_level,
                corrections_made,
                len(local_docs)
            )

            logger.info(f"🔧 Aplicando corrección {corrections_made}: {correction.value}")

            if correction == CorrectionAction.WEB_SEARCH:
                # Buscar en web
                web_docs = self._search_web(query)
                if web_docs:
                    all_docs.extend(web_docs)
                    sources_used.append("web")
                action_taken = CorrectionAction.WEB_SEARCH

            elif correction == CorrectionAction.REFINE_QUERY:
                # Refinar query
                refined_query = self._refine_query(query, local_docs)
                if refined_query != query:
                    refined_docs = self._search_local(refined_query, k=k)
                    all_docs.extend(refined_docs)
                action_taken = CorrectionAction.REFINE_QUERY

            elif correction == CorrectionAction.EXPAND_K:
                # Expandir k
                expanded_docs = self._search_local(query, k=k*2)
                # Agregar solo los nuevos
                existing_texts = {d.get('document', '')[:100] for d in all_docs}
                for doc in expanded_docs:
                    if doc.get('document', '')[:100] not in existing_texts:
                        all_docs.append(doc)
                action_taken = CorrectionAction.EXPAND_K

            # Re-evaluar calidad
            quality_score = self._evaluate_retrieval_quality(query, all_docs)
            quality_level = self._get_quality_level(quality_score)
            logger.info(f"📊 Nueva calidad: {quality_score:.2f}")

        # Eliminar duplicados y ordenar
        final_docs = self._deduplicate_and_sort(all_docs, query)

        return final_docs[:k], action_taken, quality_score

    def retrieve_and_generate(self, query: str, k: int = 5) -> CRAGResult:
        """
        Pipeline completo: recuperar con corrección + generar respuesta.

        Args:
            query: Consulta del usuario
            k: Número de documentos

        Returns:
            CRAGResult con respuesta y métricas
        """
        start_time = time.time()

        # Recuperar con corrección
        docs, action, quality = self.retrieve_with_correction(query, k)

        # Determinar fuentes usadas
        sources = []
        for doc in docs:
            source = doc.get('source', 'local')
            if source not in sources:
                sources.append(source)

        # Generar respuesta
        if self.llm:
            response = self._generate_response(query, docs)
        else:
            response = self._format_documents_as_response(docs)

        # Calcular confianza
        confidence = self._calculate_confidence(quality, action, len(docs))

        return CRAGResult(
            response=response,
            local_quality=quality,
            correction_action=action,
            sources_used=sources,
            documents=docs,
            confidence=confidence,
            metadata={
                "time_ms": (time.time() - start_time) * 1000,
                "total_docs": len(docs),
                "quality_score": quality
            }
        )

    def _search_local(self, query: str, k: int) -> List[Dict]:
        """Búsqueda en RAG local"""
        try:
            # Intentar búsqueda híbrida primero
            if hasattr(self.rag, 'search_hybrid'):
                results = self.rag.search_hybrid(query, k=k)
            else:
                results = self.rag.search(query, k=k)

            # Normalizar formato
            docs = []
            for r in results:
                if hasattr(r, 'document'):
                    docs.append({
                        'document': r.document,
                        'score': getattr(r, 'score', 0.5),
                        'metadata': getattr(r, 'metadata', {}),
                        'source': 'local'
                    })
                elif isinstance(r, dict):
                    r['source'] = 'local'
                    docs.append(r)

            return docs

        except Exception as e:
            logger.error(f"❌ Error en búsqueda local: {e}")
            return []

    def _search_web(self, query: str) -> List[Dict]:
        """Búsqueda en web usando web_searcher"""
        if not self.web_searcher:
            logger.warning("⚠️ Web searcher no configurado")
            return []

        try:
            # Intentar diferentes interfaces de web search
            if hasattr(self.web_searcher, 'call_tool'):
                # Interfaz MCP
                results = self.web_searcher.call_tool(
                    'web_search',
                    'brave_web_search',
                    {'query': query, 'count': self.web_results_count}
                )
                return self._parse_web_results(results)

            elif hasattr(self.web_searcher, 'search'):
                # Interfaz directa
                results = self.web_searcher.search(query, count=self.web_results_count)
                return self._parse_web_results(results)

            elif callable(self.web_searcher):
                # Función callback
                results = self.web_searcher(query)
                return self._parse_web_results(results)

            else:
                logger.warning("⚠️ Interfaz de web_searcher no reconocida")
                return []

        except Exception as e:
            logger.error(f"❌ Error en búsqueda web: {e}")
            return []

    def _parse_web_results(self, results: Any) -> List[Dict]:
        """Parsear resultados web a formato estándar"""
        docs = []

        if isinstance(results, dict):
            # Formato típico de API de búsqueda
            items = results.get('results', results.get('items', []))
        elif isinstance(results, list):
            items = results
        else:
            return []

        for item in items:
            if isinstance(item, dict):
                # Construir documento desde resultado web
                title = item.get('title', '')
                description = item.get('description', item.get('snippet', ''))
                url = item.get('url', item.get('link', ''))

                doc_text = f"{title}\n\n{description}"
                if url:
                    doc_text += f"\n\nFuente: {url}"

                docs.append({
                    'document': doc_text,
                    'score': 0.7,  # Score base para web
                    'source': 'web',
                    'url': url,
                    'metadata': {'title': title, 'url': url}
                })

        return docs

    def _evaluate_retrieval_quality(
        self,
        query: str,
        docs: List[Dict]
    ) -> float:
        """
        Evaluar calidad de documentos recuperados.

        Métricas:
        1. Similitud semántica promedio
        2. Cobertura de términos de la query
        3. Diversidad de documentos
        """
        if not docs:
            return 0.0

        scores = []

        # === Métrica 1: Similitud semántica ===
        if self.embedder:
            try:
                query_emb = self.embedder.encode([query])[0]

                for doc in docs[:5]:  # Solo top 5 para eficiencia
                    doc_text = doc.get('document', '')[:500]
                    doc_emb = self.embedder.encode([doc_text])[0]

                    # Cosine similarity
                    sim = np.dot(query_emb, doc_emb) / (
                        np.linalg.norm(query_emb) * np.linalg.norm(doc_emb) + 1e-8
                    )
                    scores.append(float(sim))

            except Exception as e:
                logger.warning(f"⚠️ Error calculando similitud: {e}")

        # === Métrica 2: Cobertura de términos ===
        query_terms = set(query.lower().split())
        doc_terms = set()
        for doc in docs:
            doc_terms.update(doc.get('document', '').lower().split())

        term_coverage = len(query_terms & doc_terms) / len(query_terms) if query_terms else 0
        scores.append(term_coverage)

        # === Métrica 3: Score promedio de RAG ===
        rag_scores = [doc.get('score', 0.5) for doc in docs]
        if rag_scores:
            scores.append(np.mean(rag_scores))

        # Promediar todas las métricas
        return float(np.mean(scores)) if scores else 0.0

    def _get_quality_level(self, score: float) -> RetrievalQuality:
        """Convertir score a nivel de calidad"""
        if score >= self.QUALITY_THRESHOLDS[RetrievalQuality.EXCELLENT]:
            return RetrievalQuality.EXCELLENT
        elif score >= self.QUALITY_THRESHOLDS[RetrievalQuality.GOOD]:
            return RetrievalQuality.GOOD
        elif score >= self.QUALITY_THRESHOLDS[RetrievalQuality.ACCEPTABLE]:
            return RetrievalQuality.ACCEPTABLE
        else:
            return RetrievalQuality.POOR

    def _decide_correction(
        self,
        quality: float,
        level: RetrievalQuality,
        attempt: int,
        num_docs: int
    ) -> CorrectionAction:
        """Decidir qué corrección aplicar"""

        # Primera corrección
        if attempt == 1:
            if level == RetrievalQuality.POOR:
                # Calidad muy baja → web search
                return CorrectionAction.WEB_SEARCH
            elif num_docs < 3:
                # Pocos docs → expandir k
                return CorrectionAction.EXPAND_K
            else:
                # Calidad media → refinar query
                return CorrectionAction.REFINE_QUERY

        # Segunda corrección
        elif attempt == 2:
            if self.web_searcher and level in [RetrievalQuality.POOR, RetrievalQuality.ACCEPTABLE]:
                return CorrectionAction.WEB_SEARCH
            else:
                return CorrectionAction.EXPAND_K

        return CorrectionAction.NONE

    def _refine_query(self, query: str, docs: List[Dict]) -> str:
        """Refinar query usando contexto de documentos"""
        if not self.llm:
            # Sin LLM, hacer expansión simple
            return self._simple_query_expansion(query, docs)

        try:
            # Extraer términos relevantes de docs
            doc_context = "\n".join([d.get('document', '')[:200] for d in docs[:3]])

            prompt = f"""Dada esta consulta y el contexto de documentos encontrados, genera una versión mejorada de la consulta que sea más específica y capture mejor la intención del usuario.

Consulta original: {query}

Contexto encontrado (parcial):
{doc_context}

Genera SOLO la consulta mejorada, sin explicación:"""

            refined = self.llm.generate_simple(prompt, max_tokens=100)
            return refined.strip() if refined else query

        except Exception as e:
            logger.warning(f"⚠️ Error refinando query: {e}")
            return query

    def _simple_query_expansion(self, query: str, docs: List[Dict]) -> str:
        """Expansión simple de query sin LLM"""
        # Extraer términos frecuentes de docs
        from collections import Counter

        all_words = []
        for doc in docs[:3]:
            words = doc.get('document', '').lower().split()
            # Filtrar palabras cortas y stopwords básicos
            words = [w for w in words if len(w) > 4]
            all_words.extend(words)

        # Obtener términos más frecuentes
        common = Counter(all_words).most_common(3)

        # Expandir query
        expansion_terms = [term for term, _ in common if term not in query.lower()]
        if expansion_terms:
            return f"{query} {' '.join(expansion_terms[:2])}"

        return query

    def _deduplicate_and_sort(
        self,
        docs: List[Dict],
        query: str
    ) -> List[Dict]:
        """Eliminar duplicados y ordenar por relevancia"""
        seen = set()
        unique_docs = []

        for doc in docs:
            doc_text = doc.get('document', '')
            # Hash simple para detectar duplicados
            doc_hash = hash(doc_text[:200])

            if doc_hash not in seen:
                seen.add(doc_hash)
                unique_docs.append(doc)

        # Ordenar por score
        unique_docs.sort(key=lambda x: x.get('score', 0), reverse=True)

        return unique_docs

    def _generate_response(self, query: str, docs: List[Dict]) -> str:
        """Generar respuesta usando LLM"""
        # Construir contexto
        context_parts = []
        for i, doc in enumerate(docs[:5], 1):
            source = doc.get('source', 'local')
            doc_text = doc.get('document', '')[:600]
            context_parts.append(f"[Fuente {i} ({source})]\n{doc_text}")

        context = "\n\n".join(context_parts)

        prompt = f"""Basándote en el siguiente contexto, responde la pregunta de forma precisa y completa.

Contexto:
{context}

Pregunta: {query}

Instrucciones:
- Usa información del contexto proporcionado
- Si hay información de múltiples fuentes, sintetízala
- Si la información es insuficiente, indícalo

Respuesta:"""

        return self.llm.generate_simple(prompt, max_tokens=800)

    def _format_documents_as_response(self, docs: List[Dict]) -> str:
        """Formatear documentos como respuesta (sin LLM)"""
        if not docs:
            return "No se encontraron documentos relevantes."

        response_parts = ["Documentos encontrados:\n"]

        for i, doc in enumerate(docs[:5], 1):
            source = doc.get('source', 'local')
            doc_text = doc.get('document', '')[:300]
            response_parts.append(f"\n[{i}] ({source}): {doc_text}...")

        return "\n".join(response_parts)

    def _calculate_confidence(
        self,
        quality: float,
        action: CorrectionAction,
        num_docs: int
    ) -> float:
        """Calcular confianza del resultado"""
        base = quality

        # Ajustar por acción de corrección
        if action == CorrectionAction.NONE:
            base += 0.1  # No necesitó corrección
        elif action == CorrectionAction.WEB_SEARCH:
            base += 0.05  # Web puede ser menos confiable
        elif action == CorrectionAction.EXPAND_K:
            base += 0.05

        # Ajustar por número de docs
        if num_docs >= 3:
            base += 0.05
        elif num_docs == 0:
            base -= 0.2

        return min(0.95, max(0.1, base))


# === TEST ===
if __name__ == "__main__":
    print("🔄 Test de CRAG")
    print("=" * 50)

    # Mock RAG
    class MockRAG:
        def search(self, query, k=5):
            # Simular búsqueda con calidad variable
            if "python" in query.lower():
                return [
                    {"document": "Python es un lenguaje de programación.", "score": 0.85},
                    {"document": "Python fue creado por Guido van Rossum.", "score": 0.75}
                ]
            else:
                return [
                    {"document": "Documento genérico sin mucha relevancia.", "score": 0.3}
                ]

    # Mock Web Searcher
    class MockWebSearcher:
        def search(self, query, count=5):
            return [
                {"title": "Python Wikipedia", "description": "Info de web sobre Python", "url": "http://example.com"}
            ]

    # Mock LLM
    class MockLLM:
        def generate_simple(self, prompt, max_tokens=500):
            return "Respuesta generada basada en el contexto proporcionado."

    # Crear CRAG
    crag = CorrectiveRAG(
        rag_manager=MockRAG(),
        llm_interface=MockLLM(),
        web_searcher=MockWebSearcher(),
        quality_threshold=0.5
    )

    # Test 1: Query con buena calidad local
    print("\n📋 Test 1: Query con buena calidad local")
    result1 = crag.retrieve_and_generate("¿Qué es Python?")
    print(f"   Calidad: {result1.local_quality:.2f}")
    print(f"   Acción: {result1.correction_action.value}")
    print(f"   Fuentes: {result1.sources_used}")
    print(f"   Confianza: {result1.confidence:.2f}")

    # Test 2: Query con mala calidad local
    print("\n📋 Test 2: Query con mala calidad local")
    result2 = crag.retrieve_and_generate("¿Qué pasó en las elecciones?")
    print(f"   Calidad: {result2.local_quality:.2f}")
    print(f"   Acción: {result2.correction_action.value}")
    print(f"   Fuentes: {result2.sources_used}")
    print(f"   Confianza: {result2.confidence:.2f}")
