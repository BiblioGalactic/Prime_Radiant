#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    RAG AGENT - Agente RAG Especializado
========================================
Sistema de IA con Agentes y RAGs

Combina recuperación inteligente con generación:
- Búsqueda adaptativa
- Evaluación de calidad
- Refinamiento iterativo
- Crítica y mejora
"""

import os
import sys
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config import config
from core.rag_manager import RAGManager, RetrievalStrategy, SearchResult
from core.evaluator import ConfidenceCalculator, HeuristicEvaluator, Verdict
from core.query_refiner import QueryRefiner, get_refiner
from core.critic import ResponseCritic, CriticVerdict, get_critic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAGAgent")


class RAGPipelineStage(Enum):
    """Etapas del pipeline RAG"""
    RETRIEVE = "retrieve"
    GENERATE = "generate"
    EVALUATE = "evaluate"
    REFINE = "refine"
    CRITIC = "critic"
    FINAL = "final"


@dataclass
class RAGPipelineResult:
    """Resultado del pipeline RAG completo"""
    query: str
    final_response: str
    iterations: int
    strategy_used: str
    confidence: float
    sources: List[str]
    refinements: List[str]  # Queries refinadas usadas
    evaluation_history: List[Dict]  # Historial de evaluaciones


class RAGAgent:
    """
    Agente RAG especializado que combina:
    1. Recuperación adaptativa (broad/focused/iterative)
    2. Generación con LLM
    3. Evaluación de calidad
    4. Refinamiento de queries
    5. Crítica y mejora de respuestas
    """

    # Configuración del pipeline
    MAX_ITERATIONS = 3
    QUALITY_THRESHOLD = 0.6
    CRITIC_THRESHOLD = 0.5

    def __init__(
        self,
        rag_manager: RAGManager = None,
        use_llm: bool = True
    ):
        """
        Inicializar agente RAG.

        Args:
            rag_manager: Gestor de RAGs
            use_llm: Si usar LLM para refinamiento/crítica
        """
        self.rag_manager = rag_manager
        self.use_llm = use_llm

        # Componentes
        self._refiner = None
        self._critic = None

        # Historial de la sesión
        self.history: List[RAGPipelineResult] = []

    @property
    def refiner(self) -> QueryRefiner:
        if self._refiner is None:
            self._refiner = get_refiner(use_llm=self.use_llm)
        return self._refiner

    @property
    def critic(self) -> ResponseCritic:
        if self._critic is None:
            self._critic = get_critic(use_llm=self.use_llm)
        return self._critic

    def process(
        self,
        query: str,
        generate_fn=None,
        strategy: RetrievalStrategy = None
    ) -> RAGPipelineResult:
        """
        Procesar consulta con pipeline completo.

        Args:
            query: Consulta del usuario
            generate_fn: Función de generación (recibe query, context)
            strategy: Estrategia de recuperación (auto si None)

        Returns:
            RAGPipelineResult con respuesta y métricas
        """
        if not self.rag_manager:
            raise ValueError("RAGManager no configurado")

        logger.info(f"[RAGAgent] Procesando: {query[:50]}...")

        # Estado del pipeline
        current_query = query
        refinements = []
        evaluation_history = []
        sources = []
        best_response = ""
        best_confidence = 0.0

        # Auto-seleccionar estrategia
        if strategy is None:
            strategy = self.rag_manager.select_strategy(query)

        logger.info(f"[RAGAgent] Estrategia: {strategy.value}")

        # Loop principal
        for iteration in range(self.MAX_ITERATIONS):
            logger.info(f"[RAGAgent] Iteración {iteration + 1}/{self.MAX_ITERATIONS}")

            # 1. RETRIEVE - Obtener contexto
            context, ctx_sources, metrics = self.rag_manager.get_context_adaptive(
                current_query,
                strategy=strategy
            )
            sources.extend(ctx_sources)

            if not context:
                logger.warning("[RAGAgent] Sin contexto, intentando refinar query")
                # Refinar y reintentar
                refined = self.refiner.refine(current_query)
                if refined.refined != current_query:
                    current_query = refined.refined
                    refinements.append(current_query)
                    continue
                else:
                    break

            # 2. GENERATE - Generar respuesta
            if generate_fn:
                response = generate_fn(current_query, context)
            else:
                response = f"[Placeholder] Respuesta para: {current_query}\nContexto: {context[:200]}..."

            # 3. EVALUATE - Evaluar calidad
            eval_result = HeuristicEvaluator.evaluate_with_metrics(
                current_query, response, context
            )

            evaluation_history.append({
                "iteration": iteration + 1,
                "query": current_query,
                "verdict": eval_result.verdict.value,
                "confidence": eval_result.confidence,
                "metrics": eval_result.metrics.to_dict() if eval_result.metrics else None
            })

            # Guardar mejor respuesta
            if eval_result.confidence > best_confidence:
                best_response = response
                best_confidence = eval_result.confidence

            # 4. Verificar si calidad es suficiente
            if eval_result.verdict == Verdict.OK and eval_result.confidence >= self.QUALITY_THRESHOLD:
                logger.info(f"[RAGAgent] Calidad OK en iteración {iteration + 1}")
                break

            # 5. REFINE o CRITIC si no es suficiente
            if eval_result.needs_refinement():
                # Refinar query basándose en contexto
                refined = self.refiner.refine(
                    current_query,
                    context_docs=[context],
                    strategy="contextual"
                )
                if refined.refined != current_query:
                    current_query = refined.refined
                    refinements.append(current_query)
                    logger.info(f"[RAGAgent] Query refinada: {current_query[:50]}...")

                    # Cambiar a estrategia más focused
                    if strategy == RetrievalStrategy.BROAD:
                        strategy = RetrievalStrategy.BALANCED
                    elif strategy == RetrievalStrategy.BALANCED:
                        strategy = RetrievalStrategy.FOCUSED

            # 6. CRITIC - Intentar mejorar respuesta
            if iteration < self.MAX_ITERATIONS - 1:
                critic_feedback = self.critic.evaluate_and_improve(
                    response, current_query, [context],
                    auto_improve=True
                )

                if critic_feedback.improved_response:
                    # Evaluar respuesta mejorada
                    improved_eval = HeuristicEvaluator.evaluate_with_metrics(
                        current_query, critic_feedback.improved_response, context
                    )

                    if improved_eval.confidence > best_confidence:
                        best_response = critic_feedback.improved_response
                        best_confidence = improved_eval.confidence
                        logger.info(f"[RAGAgent] Respuesta mejorada por critic: {best_confidence:.2f}")

        # Eliminar duplicados de sources
        sources = list(dict.fromkeys(sources))

        result = RAGPipelineResult(
            query=query,
            final_response=best_response,
            iterations=iteration + 1,
            strategy_used=strategy.value,
            confidence=best_confidence,
            sources=sources,
            refinements=refinements,
            evaluation_history=evaluation_history
        )

        # Guardar en historial
        self.history.append(result)

        logger.info(f"[RAGAgent] Completado: {result.iterations} iteraciones, confianza: {result.confidence:.2f}")

        return result

    def quick_retrieve(self, query: str) -> Tuple[str, List[str]]:
        """
        Recuperación rápida sin pipeline completo.

        Args:
            query: Consulta

        Returns:
            (contexto, fuentes)
        """
        if not self.rag_manager:
            return "", []

        context, sources, _ = self.rag_manager.get_context_adaptive(query)
        return context, sources

    def iterative_rag(
        self,
        query: str,
        generate_fn=None,
        max_iterations: int = None
    ) -> RAGPipelineResult:
        """
        RAG iterativo con refinamiento automático.

        Similar a process() pero siempre usa estrategia ITERATIVE.
        """
        return self.process(
            query,
            generate_fn=generate_fn,
            strategy=RetrievalStrategy.ITERATIVE
        )

    def get_history_summary(self) -> Dict:
        """Obtener resumen del historial"""
        if not self.history:
            return {"total_queries": 0}

        avg_confidence = sum(r.confidence for r in self.history) / len(self.history)
        avg_iterations = sum(r.iterations for r in self.history) / len(self.history)

        strategies = {}
        for r in self.history:
            strategies[r.strategy_used] = strategies.get(r.strategy_used, 0) + 1

        return {
            "total_queries": len(self.history),
            "avg_confidence": round(avg_confidence, 3),
            "avg_iterations": round(avg_iterations, 2),
            "strategies_used": strategies,
            "total_refinements": sum(len(r.refinements) for r in self.history)
        }

    def clear_history(self):
        """Limpiar historial"""
        self.history = []


# === Factory ===
_rag_agent: Optional[RAGAgent] = None


def get_rag_agent(rag_manager: RAGManager = None) -> RAGAgent:
    """Obtener instancia singleton del agente RAG"""
    global _rag_agent
    if _rag_agent is None:
        _rag_agent = RAGAgent(rag_manager=rag_manager)
    elif rag_manager:
        _rag_agent.rag_manager = rag_manager
    return _rag_agent


# === CLI para pruebas ===
if __name__ == "__main__":
    print("=== Test RAG Agent ===\n")

    # Crear mock RAGManager para test
    class MockRAGManager:
        def select_strategy(self, query):
            return RetrievalStrategy.BALANCED

        def get_context_adaptive(self, query, strategy=None):
            context = f"Contexto mock para: {query[:30]}..."
            sources = ["wikipedia"]
            metrics = {"strategy": "mock"}
            return context, sources, metrics

    # Test
    agent = RAGAgent(rag_manager=MockRAGManager(), use_llm=False)

    def mock_generate(query, context):
        return f"Respuesta generada para '{query[:30]}' basada en contexto disponible."

    result = agent.process(
        "¿Qué es la inteligencia artificial?",
        generate_fn=mock_generate
    )

    print(f"📝 Query: {result.query}")
    print(f"✅ Response: {result.final_response[:100]}...")
    print(f"📊 Iterations: {result.iterations}")
    print(f"📈 Confidence: {result.confidence:.2f}")
    print(f"📚 Sources: {result.sources}")
    print(f"🔄 Refinements: {result.refinements}")
    print()
    print("📊 History Summary:")
    print(agent.get_history_summary())
