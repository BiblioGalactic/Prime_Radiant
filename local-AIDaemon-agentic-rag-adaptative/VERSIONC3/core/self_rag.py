#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
🧠 SELF-RAG - RAG con Auto-Validación
========================================
Implementación de Self-RAG (Asai et al., 2023).

El modelo decide autónomamente:
1. ¿Necesito recuperar contexto? (Retrieve?)
2. ¿Los documentos son relevantes? (IsRel)
3. ¿Mi respuesta está soportada? (IsSup)
4. ¿La respuesta es útil? (IsUse)

Ventajas:
- Reduce alucinaciones
- Solo usa RAG cuando es necesario
- Auto-verifica sus respuestas
"""

import os
import sys
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SelfRAG")


class RetrievalDecision(Enum):
    """Decisiones de recuperación"""
    RETRIEVE = "retrieve"      # Necesita contexto externo
    NO_RETRIEVE = "no_retrieve"  # Puede responder directo
    UNCERTAIN = "uncertain"    # No está seguro


class RelevanceLevel(Enum):
    """Niveles de relevancia de documentos"""
    RELEVANT = "relevant"
    PARTIALLY_RELEVANT = "partially_relevant"
    NOT_RELEVANT = "not_relevant"


class SupportLevel(Enum):
    """Nivel de soporte de la respuesta"""
    FULLY_SUPPORTED = "fully_supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    NOT_SUPPORTED = "not_supported"


class UsefulnessLevel(Enum):
    """Utilidad de la respuesta"""
    USEFUL = "useful"
    PARTIALLY_USEFUL = "partially_useful"
    NOT_USEFUL = "not_useful"


@dataclass
class SelfRAGResult:
    """Resultado de Self-RAG con métricas de auto-evaluación"""
    response: str
    retrieval_decision: RetrievalDecision
    documents_used: List[Dict] = field(default_factory=list)
    relevance_scores: List[Tuple[str, RelevanceLevel]] = field(default_factory=list)
    support_level: SupportLevel = SupportLevel.NOT_SUPPORTED
    usefulness_level: UsefulnessLevel = UsefulnessLevel.NOT_USEFUL
    iterations: int = 0
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SelfRAG:
    """
    RAG que se auto-valida y decide cuándo recuperar contexto.

    Flujo:
    1. Retrieve? → Decide si necesita RAG
    2. Retrieve → Busca documentos (si decidió que sí)
    3. IsRel → Valida relevancia de cada documento
    4. Generate → Genera respuesta con docs relevantes
    5. IsSup → Verifica si respuesta está soportada
    6. IsUse → Valida utilidad de la respuesta

    Uso:
        self_rag = SelfRAG(rag_manager, llm_interface)
        result = self_rag.generate("¿Qué es Python?")
        print(result.response)
        print(f"Confianza: {result.confidence}")
    """

    # Patrones que indican necesidad de contexto externo
    RETRIEVAL_KEYWORDS = [
        "qué es", "quién es", "cuándo", "dónde", "cómo funciona",
        "explica", "define", "describe", "historia de", "origen de",
        "estadísticas", "datos sobre", "información sobre",
        "comparar", "diferencia entre", "ventajas de", "desventajas de"
    ]

    # Patrones que NO necesitan RAG
    NO_RETRIEVAL_KEYWORDS = [
        "hola", "gracias", "adiós", "ok", "de acuerdo",
        "escribe un", "genera un", "crea un", "traduce",
        "calcula", "resuelve", "convierte"
    ]

    # Frases que indican respuesta inútil
    USELESS_PHRASES = [
        "no tengo información",
        "no puedo responder",
        "no sé",
        "desconozco",
        "no tengo datos",
        "información no disponible",
        "fuera de mi conocimiento"
    ]

    def __init__(
        self,
        rag_manager: Any,
        llm_interface: Any,
        max_iterations: int = 2,
        relevance_threshold: float = 0.5,
        min_docs_required: int = 1
    ):
        """
        Inicializar Self-RAG.

        Args:
            rag_manager: Instancia de RAGManager
            llm_interface: Interfaz al LLM (daemon_interface)
            max_iterations: Máximo de intentos de regeneración
            relevance_threshold: Umbral para considerar doc relevante
            min_docs_required: Mínimo de docs relevantes necesarios
        """
        self.rag = rag_manager
        self.llm = llm_interface
        self.max_iterations = max_iterations
        self.relevance_threshold = relevance_threshold
        self.min_docs_required = min_docs_required

        logger.info("🧠 Self-RAG inicializado")

    def generate(self, query: str) -> SelfRAGResult:
        """
        Generar respuesta con auto-validación.

        Args:
            query: Consulta del usuario

        Returns:
            SelfRAGResult con respuesta y métricas
        """
        start_time = time.time()
        iterations = 0

        # === PASO 1: ¿Necesito RAG? ===
        retrieval_decision = self._should_retrieve(query)
        logger.info(f"🔍 Decisión de recuperación: {retrieval_decision.value}")

        if retrieval_decision == RetrievalDecision.NO_RETRIEVE:
            # Generar directamente sin RAG
            response = self._generate_without_context(query)
            return SelfRAGResult(
                response=response,
                retrieval_decision=retrieval_decision,
                confidence=0.7,  # Confianza moderada sin contexto
                metadata={"time_ms": (time.time() - start_time) * 1000}
            )

        # === PASO 2: Recuperar documentos ===
        all_docs = self._retrieve_documents(query, k=10)

        if not all_docs:
            logger.warning("⚠️ No se encontraron documentos")
            response = self._generate_without_context(
                query + "\n[Sin contexto disponible, responde con tu conocimiento]"
            )
            return SelfRAGResult(
                response=response,
                retrieval_decision=retrieval_decision,
                confidence=0.4,
                metadata={"time_ms": (time.time() - start_time) * 1000}
            )

        # === PASO 3: Validar relevancia de documentos ===
        relevant_docs, relevance_scores = self._filter_relevant_docs(query, all_docs)
        logger.info(f"📄 Docs relevantes: {len(relevant_docs)}/{len(all_docs)}")

        if len(relevant_docs) < self.min_docs_required:
            logger.warning("⚠️ Pocos docs relevantes, generando con contexto parcial")
            # Usar los mejores aunque no pasen el umbral
            relevant_docs = all_docs[:3]

        # === PASO 4-6: Generar y validar respuesta ===
        best_response = None
        best_support = SupportLevel.NOT_SUPPORTED
        best_usefulness = UsefulnessLevel.NOT_USEFUL

        for iteration in range(self.max_iterations):
            iterations += 1

            # === PASO 4: Generar respuesta ===
            response = self._generate_with_context(query, relevant_docs, iteration)

            # === PASO 5: Verificar soporte ===
            support_level = self._check_support(response, relevant_docs)
            logger.info(f"📊 Soporte (iter {iteration+1}): {support_level.value}")

            # === PASO 6: Verificar utilidad ===
            usefulness = self._check_usefulness(response)
            logger.info(f"📊 Utilidad (iter {iteration+1}): {usefulness.value}")

            # Guardar mejor resultado
            if self._is_better_result(support_level, usefulness, best_support, best_usefulness):
                best_response = response
                best_support = support_level
                best_usefulness = usefulness

            # Si es suficientemente bueno, terminar
            if support_level == SupportLevel.FULLY_SUPPORTED and usefulness == UsefulnessLevel.USEFUL:
                break

        # Calcular confianza final
        confidence = self._calculate_confidence(best_support, best_usefulness, len(relevant_docs))

        return SelfRAGResult(
            response=best_response or "No pude generar una respuesta satisfactoria.",
            retrieval_decision=retrieval_decision,
            documents_used=relevant_docs,
            relevance_scores=relevance_scores,
            support_level=best_support,
            usefulness_level=best_usefulness,
            iterations=iterations,
            confidence=confidence,
            metadata={
                "time_ms": (time.time() - start_time) * 1000,
                "total_docs_retrieved": len(all_docs),
                "relevant_docs_used": len(relevant_docs)
            }
        )

    def _should_retrieve(self, query: str) -> RetrievalDecision:
        """
        Decide si la query necesita recuperación de contexto.

        Usa heurísticas + LLM para decidir.
        """
        query_lower = query.lower()

        # Heurística 1: Keywords que NO necesitan RAG
        if any(kw in query_lower for kw in self.NO_RETRIEVAL_KEYWORDS):
            return RetrievalDecision.NO_RETRIEVE

        # Heurística 2: Keywords que SÍ necesitan RAG
        if any(kw in query_lower for kw in self.RETRIEVAL_KEYWORDS):
            return RetrievalDecision.RETRIEVE

        # Heurística 3: Preguntas factuales (¿?, quién, qué, cuándo, dónde)
        if "?" in query or query_lower.startswith(("quién", "qué", "cuándo", "dónde", "cómo", "por qué")):
            return RetrievalDecision.RETRIEVE

        # Si no está claro, preguntar al LLM
        try:
            decision = self._ask_llm_retrieval_decision(query)
            return decision
        except Exception as e:
            logger.warning(f"⚠️ Error en decisión LLM: {e}")
            # Por defecto, recuperar (más seguro)
            return RetrievalDecision.RETRIEVE

    def _ask_llm_retrieval_decision(self, query: str) -> RetrievalDecision:
        """Pregunta al LLM si necesita contexto externo"""
        prompt = f"""Analiza esta pregunta y decide si necesitas buscar información externa para responderla bien.

Pregunta: {query}

Responde SOLO una palabra:
- "SI" si necesitas buscar información (datos, hechos, definiciones)
- "NO" si puedes responder sin buscar (tareas creativas, saludos, cálculos)

Tu decisión:"""

        response = self.llm.generate_simple(prompt, max_tokens=10)
        response_clean = response.strip().upper()

        if "SI" in response_clean:
            return RetrievalDecision.RETRIEVE
        elif "NO" in response_clean:
            return RetrievalDecision.NO_RETRIEVE
        else:
            return RetrievalDecision.UNCERTAIN

    def _retrieve_documents(self, query: str, k: int = 10) -> List[Dict]:
        """Recuperar documentos del RAG"""
        try:
            # Intentar búsqueda híbrida si está disponible
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
                        'metadata': getattr(r, 'metadata', {})
                    })
                elif isinstance(r, dict):
                    docs.append(r)

            return docs

        except Exception as e:
            logger.error(f"❌ Error en recuperación: {e}")
            return []

    def _filter_relevant_docs(
        self,
        query: str,
        docs: List[Dict]
    ) -> Tuple[List[Dict], List[Tuple[str, RelevanceLevel]]]:
        """
        Filtrar documentos por relevancia.

        Usa el score del RAG + validación semántica.
        """
        relevant = []
        scores = []

        for doc in docs:
            doc_text = doc.get('document', '')[:500]
            rag_score = doc.get('score', 0.5)

            # Determinar nivel de relevancia
            if rag_score >= 0.7:
                level = RelevanceLevel.RELEVANT
            elif rag_score >= self.relevance_threshold:
                level = RelevanceLevel.PARTIALLY_RELEVANT
            else:
                # Validación adicional con heurísticas
                level = self._quick_relevance_check(query, doc_text)

            scores.append((doc_text[:100], level))

            if level in [RelevanceLevel.RELEVANT, RelevanceLevel.PARTIALLY_RELEVANT]:
                relevant.append(doc)

        return relevant, scores

    def _quick_relevance_check(self, query: str, doc: str) -> RelevanceLevel:
        """Verificación rápida de relevancia sin LLM"""
        query_words = set(query.lower().split())
        doc_words = set(doc.lower().split())

        # Overlap de palabras
        common = query_words & doc_words
        overlap_ratio = len(common) / len(query_words) if query_words else 0

        if overlap_ratio >= 0.3:
            return RelevanceLevel.PARTIALLY_RELEVANT
        else:
            return RelevanceLevel.NOT_RELEVANT

    def _generate_without_context(self, query: str) -> str:
        """Generar respuesta sin contexto RAG"""
        prompt = f"""Responde esta pregunta de forma directa y concisa:

{query}

Respuesta:"""

        return self.llm.generate_simple(prompt, max_tokens=500)

    def _generate_with_context(
        self,
        query: str,
        docs: List[Dict],
        iteration: int = 0
    ) -> str:
        """Generar respuesta usando contexto de documentos"""

        # Construir contexto
        context_parts = []
        for i, doc in enumerate(docs[:5], 1):  # Máximo 5 docs
            doc_text = doc.get('document', '')[:800]
            context_parts.append(f"[Documento {i}]\n{doc_text}")

        context = "\n\n".join(context_parts)

        # Prompt varía según iteración
        if iteration == 0:
            strictness = "Basa tu respuesta en la información del contexto."
        else:
            strictness = """IMPORTANTE:
- Responde SOLO con información que esté explícitamente en el contexto
- Si algo no está en el contexto, NO lo incluyas
- Si no hay suficiente información, di "No tengo suficiente información para responder completamente"
"""

        prompt = f"""Contexto:
{context}

Pregunta: {query}

{strictness}

Respuesta:"""

        return self.llm.generate_simple(prompt, max_tokens=800)

    def _check_support(self, response: str, docs: List[Dict]) -> SupportLevel:
        """
        Verificar si la respuesta está soportada por los documentos.

        Usa heurísticas para evitar llamada extra al LLM.
        """
        if not response or len(response) < 20:
            return SupportLevel.NOT_SUPPORTED

        response_lower = response.lower()

        # Heurística: buscar frases del contexto en la respuesta
        context_phrases = []
        for doc in docs[:3]:
            doc_text = doc.get('document', '').lower()
            # Extraer frases de 3-5 palabras
            words = doc_text.split()
            for i in range(len(words) - 3):
                phrase = ' '.join(words[i:i+4])
                context_phrases.append(phrase)

        # Contar matches
        matches = sum(1 for phrase in context_phrases if phrase in response_lower)
        match_ratio = matches / len(context_phrases) if context_phrases else 0

        if match_ratio >= 0.1:
            return SupportLevel.FULLY_SUPPORTED
        elif match_ratio >= 0.03:
            return SupportLevel.PARTIALLY_SUPPORTED
        else:
            return SupportLevel.NOT_SUPPORTED

    def _check_usefulness(self, response: str) -> UsefulnessLevel:
        """Verificar si la respuesta es útil"""
        if not response:
            return UsefulnessLevel.NOT_USEFUL

        # Verificar longitud mínima
        if len(response) < 30:
            return UsefulnessLevel.NOT_USEFUL

        response_lower = response.lower()

        # Verificar frases que indican respuesta inútil
        if any(phrase in response_lower for phrase in self.USELESS_PHRASES):
            return UsefulnessLevel.NOT_USEFUL

        # Verificar respuesta genérica
        generic_phrases = [
            "depende de", "hay muchas formas", "es complejo",
            "no es posible generalizar"
        ]
        if any(phrase in response_lower for phrase in generic_phrases):
            return UsefulnessLevel.PARTIALLY_USEFUL

        # Si tiene contenido sustancial
        if len(response) >= 100:
            return UsefulnessLevel.USEFUL
        else:
            return UsefulnessLevel.PARTIALLY_USEFUL

    def _is_better_result(
        self,
        new_support: SupportLevel,
        new_useful: UsefulnessLevel,
        old_support: SupportLevel,
        old_useful: UsefulnessLevel
    ) -> bool:
        """Comparar si el nuevo resultado es mejor que el anterior"""
        support_order = {
            SupportLevel.FULLY_SUPPORTED: 3,
            SupportLevel.PARTIALLY_SUPPORTED: 2,
            SupportLevel.NOT_SUPPORTED: 1
        }
        useful_order = {
            UsefulnessLevel.USEFUL: 3,
            UsefulnessLevel.PARTIALLY_USEFUL: 2,
            UsefulnessLevel.NOT_USEFUL: 1
        }

        new_score = support_order[new_support] + useful_order[new_useful]
        old_score = support_order[old_support] + useful_order[old_useful]

        return new_score > old_score

    def _calculate_confidence(
        self,
        support: SupportLevel,
        usefulness: UsefulnessLevel,
        num_docs: int
    ) -> float:
        """Calcular confianza final de la respuesta"""
        base_confidence = 0.5

        # Ajustar por soporte
        if support == SupportLevel.FULLY_SUPPORTED:
            base_confidence += 0.25
        elif support == SupportLevel.PARTIALLY_SUPPORTED:
            base_confidence += 0.10

        # Ajustar por utilidad
        if usefulness == UsefulnessLevel.USEFUL:
            base_confidence += 0.15
        elif usefulness == UsefulnessLevel.PARTIALLY_USEFUL:
            base_confidence += 0.05

        # Ajustar por cantidad de documentos
        if num_docs >= 3:
            base_confidence += 0.10
        elif num_docs >= 1:
            base_confidence += 0.05

        return min(0.95, base_confidence)


# === TEST ===
if __name__ == "__main__":
    print("🧠 Test de Self-RAG")
    print("=" * 50)

    # Mock LLM interface
    class MockLLM:
        def generate_simple(self, prompt, max_tokens=500):
            if "SI o NO" in prompt or "SI" in prompt and "NO" in prompt:
                return "SI"
            return "Esta es una respuesta de prueba basada en el contexto proporcionado."

    # Mock RAG manager
    class MockRAG:
        def search(self, query, k=10):
            return [
                {"document": "Python es un lenguaje de programación interpretado de alto nivel.", "score": 0.85},
                {"document": "Python fue creado por Guido van Rossum en 1991.", "score": 0.75},
                {"document": "Python es popular en ciencia de datos y machine learning.", "score": 0.70}
            ]

    # Crear Self-RAG
    self_rag = SelfRAG(
        rag_manager=MockRAG(),
        llm_interface=MockLLM()
    )

    # Test
    query = "¿Qué es Python y para qué se usa?"
    print(f"\n🔍 Query: {query}")

    result = self_rag.generate(query)

    print(f"\n📝 Respuesta: {result.response[:200]}...")
    print(f"\n📊 Métricas:")
    print(f"   - Decisión recuperación: {result.retrieval_decision.value}")
    print(f"   - Documentos usados: {len(result.documents_used)}")
    print(f"   - Nivel de soporte: {result.support_level.value}")
    print(f"   - Utilidad: {result.usefulness_level.value}")
    print(f"   - Iteraciones: {result.iterations}")
    print(f"   - Confianza: {result.confidence:.2f}")
    print(f"   - Tiempo: {result.metadata.get('time_ms', 0):.0f}ms")
