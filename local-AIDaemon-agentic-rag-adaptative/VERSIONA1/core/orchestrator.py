#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    ORCHESTRATOR - Orquestador Principal
========================================
Coordina el flujo completo:
1. Recibe consulta del usuario
2. Busca contexto en RAGs
3. Encola mensaje para el daemon
4. Espera respuesta
5. Evalúa con modelo separado
6. Archiva en RAG correspondiente
7. Genera plan de agentes si es necesario
8. Ejecuta agentes y sintetiza respuesta final
"""

import os
import sys
import time
import threading
import uuid
import signal
import atexit
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path
import logging
import json

# === Setup paths para imports absolutos ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config import config, Config
from core.queue_manager import QueueManager, QueueMessage, Priority
from core.daemon_interface import DaemonInterface, DaemonCLI, DaemonResponse, ResponseVerdict
from core.rag_manager import RAGManager, RetrievalStrategy
from core.evaluator import ResponseEvaluator, HeuristicEvaluator, Verdict, EvaluationResult, create_evaluator, ConfidenceCalculator
from core.shared_state import SharedState, get_shared_state
from core.query_refiner import QueryRefiner, get_refiner
from core.critic import ResponseCritic, CriticVerdict, get_critic
from core.memory import LongTermMemory, MemoryType, get_memory
from core.prompts import PromptBuilder, PromptStyle

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger("Orchestrator")


@dataclass
class QueryResult:
    """Resultado de una consulta"""
    query: str
    response: str
    verdict: str
    confidence: float
    used_agents: bool
    total_time: float
    rag_sources: List[str] = field(default_factory=list)
    agent_results: Optional[Dict] = None
    session_id: str = ""
    iterations: int = 1            # Número de iteraciones RAG
    strategy_used: str = "direct"  # Estrategia utilizada
    refinements: List[str] = field(default_factory=list)  # Queries refinadas


class Orchestrator:
    """
    Orquestador principal del sistema de IA.

    Flujo:
    1. Usuario envía consulta
    2. Buscar contexto en RAGs (Wikipedia, éxitos, fallos, agentes)
    3. Encolar mensaje para el daemon
    4. Daemon responde
    5. EVALUADOR SEPARADO evalúa (OK/PARCIAL/FALLA)
    6. Archivar en RAG de éxitos o fallos
    7. Si es necesario, generar plan de agentes (con límite de recursión)
    8. Ejecutar agentes (usando estado compartido)
    9. Sintetizar respuesta final
    """

    def __init__(self, config_obj: Config = None):
        """
        Inicializar orquestador.

        Args:
            config_obj: Configuración personalizada (opcional)
        """
        self.config = config_obj or config

        # Componentes core
        self.queue = QueueManager()
        # Usar DaemonCLI (llamadas directas) en lugar de DaemonInterface (pipes)
        self.daemon_cli = DaemonCLI()
        self.rag_manager = RAGManager()
        self.shared_state = get_shared_state()

        # Evaluador separado (Fix crítico #2)
        self.evaluator = create_evaluator(use_llm=True)

        # Inicializar RAGs
        logger.info("Inicializando RAGs...")
        self.rag_manager.init_default_rags()

        # === NUEVOS COMPONENTES VANGUARDIA ===
        # Query Refiner
        self.query_refiner = get_refiner(use_llm=True)

        # Response Critic
        self.critic = get_critic(use_llm=True)

        # Long Term Memory
        self.memory = get_memory()

        # Componentes de agentes (lazy)
        self.planner = None
        self.executor = None
        self.react_agent = None
        self.rag_agent = None
        self._init_agent_components()

        # Estado
        self._running = False
        self._worker_thread = None

        # Configuración adaptativa
        self.adaptive_mode = True  # Habilitar modo adaptativo
        self.max_rag_iterations = 3

        logger.info("Orquestador inicializado (modo vanguardia)")

    def _init_agent_components(self):
        """Inicializar componentes de agentes de forma lazy"""
        try:
            from agents.planner import AgentPlanner
            from agents.executor import AgentExecutor

            self.planner = AgentPlanner(max_steps=self.config.MAX_PLAN_STEPS)
            self.executor = AgentExecutor(
                max_retries=self.config.MAX_RETRIES,
                step_timeout=self.config.AGENT_TIMEOUT,
                total_timeout=self.config.DAEMON_TIMEOUT * 2,
                max_recursion=self.config.MAX_RECURSION_DEPTH  # Fix crítico #3
            )
            logger.info("Componentes de agentes inicializados")
        except ImportError as e:
            logger.warning(f"No se pudieron cargar componentes de agentes: {e}")

        # Nuevos agentes vanguardia
        try:
            from agents.react_agent import ReActAgent, get_react_agent
            from agents.rag_agent import RAGAgent, get_rag_agent

            # Configurar función de búsqueda para ReAct
            def search_fn(query):
                context, _ = self.rag_manager.get_context(query, k=3)
                return context

            self.react_agent = get_react_agent(search_fn=search_fn)
            self.rag_agent = get_rag_agent(rag_manager=self.rag_manager)
            logger.info("Agentes vanguardia (ReAct, RAG) inicializados")
        except ImportError as e:
            logger.warning(f"Agentes vanguardia no disponibles: {e}")

    def process_query_adaptive(
        self,
        query: str,
        session_id: str = None,
        use_memory: bool = True
    ) -> QueryResult:
        """
        Procesar consulta con pipeline adaptativo completo.

        Flujo vanguardia:
        1. Consultar memoria por episodios similares
        2. Seleccionar estrategia de recuperación
        3. Loop RAG iterativo con refinamiento
        4. Evaluación y crítica
        5. Guardar en memoria

        Args:
            query: Consulta del usuario
            session_id: ID de sesión
            use_memory: Si usar memoria a largo plazo

        Returns:
            QueryResult con respuesta y métricas
        """
        start_time = time.time()
        session_id = session_id or str(uuid.uuid4())
        refinements = []
        iterations = 0

        logger.info(f"[Adaptive] Procesando: {query[:50]}...")

        # 1. CONSULTAR MEMORIA
        memory_context = ""
        if use_memory and self.memory:
            similar_episodes = self.memory.recall_similar_episodes(query, k=2)
            if similar_episodes:
                memory_context = "\n".join([
                    f"[Memoria]: {ep.content[:200]}..."
                    for ep in similar_episodes
                ])
                logger.info(f"[Adaptive] Encontrados {len(similar_episodes)} episodios similares en memoria")

        # 2. SELECCIONAR ESTRATEGIA
        strategy = self.rag_manager.select_strategy(query)
        logger.info(f"[Adaptive] Estrategia seleccionada: {strategy.value}")

        # 3. LOOP RAG ITERATIVO
        current_query = query
        best_response = ""
        best_confidence = 0.0
        best_verdict = Verdict.FALLA

        for iteration in range(self.max_rag_iterations):
            iterations += 1
            logger.info(f"[Adaptive] Iteración {iteration + 1}/{self.max_rag_iterations}")

            # Obtener contexto adaptativo
            context, sources, metrics = self.rag_manager.get_context_adaptive(
                current_query, strategy=strategy
            )

            # Añadir contexto de memoria
            if memory_context and iteration == 0:
                context = f"{memory_context}\n\n{context}" if context else memory_context

            if not context:
                # Refinar query y reintentar
                refined = self.query_refiner.refine(current_query)
                if refined.refined != current_query:
                    current_query = refined.refined
                    refinements.append(current_query)
                    continue
                else:
                    break

            # Construir prompt con estilo apropiado
            prompt_style = PromptBuilder.select_style(query)
            prompt = PromptBuilder.build_prompt(prompt_style, query, context)

            # Generar respuesta
            response = self.daemon_cli.query(prompt, timeout=self.config.DAEMON_TIMEOUT)
            response = self._clean_llm_output(response)

            # Evaluar
            eval_result = HeuristicEvaluator.evaluate_with_metrics(query, response, context)

            # Guardar si es mejor
            if eval_result.confidence > best_confidence:
                best_response = response
                best_confidence = eval_result.confidence
                best_verdict = eval_result.verdict

            # Verificar si calidad es suficiente
            if eval_result.verdict == Verdict.OK and eval_result.confidence >= 0.6:
                logger.info(f"[Adaptive] Calidad OK en iteración {iteration + 1}")
                break

            # Refinar query para siguiente iteración
            if eval_result.needs_refinement() and iteration < self.max_rag_iterations - 1:
                refined = self.query_refiner.refine(
                    current_query,
                    context_docs=[context],
                    strategy="contextual"
                )
                if refined.refined != current_query:
                    current_query = refined.refined
                    refinements.append(current_query)

                    # Ajustar estrategia
                    if strategy == RetrievalStrategy.BROAD:
                        strategy = RetrievalStrategy.BALANCED
                    elif strategy == RetrievalStrategy.BALANCED:
                        strategy = RetrievalStrategy.FOCUSED

        # 4. CRÍTICA Y MEJORA
        if best_confidence < 0.7 and self.critic:
            logger.info("[Adaptive] Aplicando crítico...")
            critic_feedback = self.critic.evaluate_and_improve(
                best_response, query, [context] if context else [],
                auto_improve=True
            )

            if critic_feedback.improved_response:
                improved_eval = HeuristicEvaluator.evaluate_with_metrics(
                    query, critic_feedback.improved_response, context
                )
                if improved_eval.confidence > best_confidence:
                    best_response = critic_feedback.improved_response
                    best_confidence = improved_eval.confidence
                    best_verdict = improved_eval.verdict
                    logger.info(f"[Adaptive] Respuesta mejorada: {best_confidence:.2f}")

        # 5. GUARDAR EN MEMORIA
        if use_memory and self.memory:
            self.memory.remember_episode(
                query=query,
                response=best_response,
                rating=best_confidence,
                context=context if context else None
            )
            logger.info("[Adaptive] Episodio guardado en memoria")

        total_time = time.time() - start_time

        return QueryResult(
            query=query,
            response=best_response,
            verdict=best_verdict.value,
            confidence=best_confidence,
            used_agents=False,
            total_time=total_time,
            rag_sources=sources if sources else [],
            session_id=session_id,
            iterations=iterations,
            strategy_used=strategy.value,
            refinements=refinements
        )

    def recursive_rag_loop(
        self,
        query: str,
        max_iterations: int = 3,
        quality_threshold: float = 0.6
    ) -> QueryResult:
        """
        Loop RAG recursivo con calidad mínima.

        Continúa refinando hasta alcanzar el umbral de calidad
        o agotar iteraciones.
        """
        return self.process_query_adaptive(query, use_memory=True)

    def process_query(
        self,
        query: str,
        priority: int = Priority.NORMAL,
        session_id: str = None,
        depth: int = 0  # Control de recursión
    ) -> QueryResult:
        """
        Procesar una consulta del usuario.

        Args:
            query: Consulta del usuario
            priority: Prioridad de la consulta
            session_id: ID de sesión para estado compartido
            depth: Profundidad de recursión actual

        Returns:
            QueryResult con la respuesta
        """
        # Verificar límite de recursión (Fix crítico #4)
        if depth > self.config.MAX_RECURSION_DEPTH:
            logger.warning(f"Límite de recursión alcanzado: depth={depth}")
            return QueryResult(
                query=query,
                response="Error: Límite de recursión alcanzado",
                verdict="ERROR",
                confidence=0.0,
                used_agents=False,
                total_time=0.0,
                session_id=session_id or ""
            )

        # Si modo adaptativo está habilitado y es primera llamada, usar pipeline adaptativo
        if self.adaptive_mode and depth == 0:
            return self.process_query_adaptive(query, session_id=session_id)

        start_time = time.time()
        session_id = session_id or str(uuid.uuid4())

        logger.info(f"[D{depth}] Procesando: {query[:50]}...")

        # Guardar estado de sesión
        self.shared_state.set("current_query", query, session_id, "orchestrator")
        self.shared_state.set("depth", depth, session_id, "orchestrator")

        # 1. Buscar contexto en RAGs (limitado a 3 docs, 2000 chars max)
        logger.info("Buscando contexto en RAGs...")
        context, rag_sources = self.rag_manager.get_context(
            query,
            k=3,
            max_chars=2000,
            max_per_doc=400
        )

        if context:
            logger.info(f"Contexto de: {rag_sources}")

        # 2. Encolar y enviar al daemon
        logger.info("Enviando al daemon...")
        msg = self.queue.enqueue(
            query=query,
            context=context,
            priority=priority,
            depth=depth,
            source="user" if depth == 0 else "agent"
        )

        if msg is None:
            return QueryResult(
                query=query,
                response="Error: No se pudo encolar el mensaje",
                verdict="ERROR",
                confidence=0.0,
                used_agents=False,
                total_time=time.time() - start_time,
                session_id=session_id
            )

        # Obtener respuesta usando DaemonCLI (llamada directa al modelo)
        logger.info("Ejecutando modelo LLM...")
        prompt = self._build_prompt(query, context)
        response_content = self.daemon_cli.query(
            prompt,
            max_tokens=self.config.MODEL_DAEMON.n_predict,
            timeout=self.config.DAEMON_TIMEOUT
        )

        # Limpiar respuesta de logs de Metal/GPU
        response_content = self._clean_llm_output(response_content)

        # Marcar como completado en cola
        self.queue.complete(msg.id, response_content)

        # 3. EVALUAR CON MODELO SEPARADO (Fix crítico #2)
        logger.info("Evaluando respuesta con modelo dedicado...")
        evaluation = self.evaluator.evaluate(query, response_content, context)

        verdict = evaluation.verdict.value
        confidence = evaluation.confidence

        logger.info(f"Evaluación: {verdict} (confianza: {confidence:.2f})")

        # 4. Archivar en RAG correspondiente
        self._archive_response(query, response_content, verdict, evaluation)

        # 5. Determinar si necesita agentes
        used_agents = False
        agent_results = None

        if evaluation.needs_agents() and depth < self.config.MAX_RECURSION_DEPTH:
            logger.info(f"Activando agentes (depth={depth})...")
            used_agents = True
            agent_results = self._run_agents(
                query, response_content, context,
                session_id=session_id,
                depth=depth + 1
            )

            if agent_results and agent_results.get("success"):
                # Sintetizar respuesta final
                response_content = self._synthesize_final(
                    query, response_content,
                    agent_results.get("output", "")
                )

                # Re-evaluar
                re_eval = self.evaluator.evaluate(query, response_content, context)
                verdict = re_eval.verdict.value
                confidence = re_eval.confidence

        total_time = time.time() - start_time

        # Guardar resultado en estado compartido
        self.shared_state.save_agent_result(
            session_id, "orchestrator",
            {"verdict": verdict, "response_length": len(response_content)}
        )

        result = QueryResult(
            query=query,
            response=response_content,
            verdict=verdict,
            confidence=confidence,
            used_agents=used_agents,
            total_time=total_time,
            rag_sources=rag_sources,
            agent_results=agent_results,
            session_id=session_id
        )

        logger.info(f"Consulta procesada en {total_time:.1f}s (agentes: {used_agents})")
        return result

    def _run_agents(
        self,
        query: str,
        daemon_response: str,
        context: str,
        session_id: str,
        depth: int
    ) -> Dict[str, Any]:
        """Ejecutar sistema de agentes con límite de recursión"""
        if not self.planner or not self.executor:
            return {"success": False, "error": "Sistema de agentes no disponible"}

        # Verificar límite
        if depth > self.config.MAX_RECURSION_DEPTH:
            return {"success": False, "error": "Límite de recursión alcanzado"}

        try:
            # Crear plan
            plan = self.planner.create_plan(query, daemon_response, context)

            # Pasar session_id y depth al ejecutor
            result = self.executor.execute_plan(
                plan,
                session_id=session_id,
                current_depth=depth
            )

            # Archivar plan en RAG de agentes
            self.rag_manager.add_plan(
                plan.to_dict() if hasattr(plan, 'to_dict') else {"description": str(plan)},
                [{"step": r.agent_name, "status": r.status.value}
                 for r in result.step_results] if hasattr(result, 'step_results') else []
            )

            return {
                "success": result.success,
                "output": result.final_output if hasattr(result, 'final_output') else str(result),
                "steps_completed": result.completed_steps if hasattr(result, 'completed_steps') else 0,
                "total_time": result.total_time if hasattr(result, 'total_time') else 0
            }

        except Exception as e:
            logger.error(f"Error ejecutando agentes: {e}")
            return {"success": False, "error": str(e)}

    def _build_prompt(self, query: str, context: str) -> str:
        """Construir prompt para el modelo"""
        if context:
            return f"""CONTEXTO (información relevante):
{context[:2000]}

CONSULTA: {query}

INSTRUCCIONES:
- Responde basándote en el contexto proporcionado
- Sé preciso, completo y útil
- Si no tienes suficiente información, indícalo

RESPUESTA:"""
        else:
            return f"""CONSULTA: {query}

INSTRUCCIONES:
- Responde de forma precisa, completa y útil
- Si no tienes suficiente información, indícalo

RESPUESTA:"""

    def _clean_llm_output(self, output: str) -> str:
        """Limpiar output del LLM de logs de GPU/Metal"""
        import re

        # Patrones de logs a eliminar
        patterns = [
            r'ggml_metal_\w+:.*?\n',
            r'ggml_backend_\w+:.*?\n',
            r'llama_\w+:.*?\n',
            r'llm_load_\w+:.*?\n',
            r'MTLGPUFamily\w+.*?\n',
            r'GPU \w+:.*?\n',
            r'Main GPU:.*?\n',
            r'simdgroup.*?\n',
            r'has unified memory.*?\n',
            r'recommendedMaxWorkingSetSize.*?\n',
            r'maxTransferRate.*?\n',
            r'loaded in \d+\.\d+ sec.*?\n',
            r'sampling:.*?\n',
            r'sampler chain:.*?\n',
            r'generate:.*?\n',
            r'\[end of text\]',
            r'<\|.*?\|>',
        ]

        cleaned = output
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # Limpiar líneas vacías múltiples
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

        return cleaned.strip()

    def _archive_response(
        self,
        query: str,
        response: str,
        verdict: str,
        evaluation: EvaluationResult
    ):
        """Archivar respuesta en RAG correspondiente"""
        if verdict == "OK":
            self.rag_manager.add_success(query, response)
            logger.debug("Archivado en RAG de éxitos")
        elif verdict in ["PARCIAL", "FALLA"]:
            suggestion = evaluation.reason
            if evaluation.suggestions:
                suggestion += " | " + " | ".join(evaluation.suggestions)
            self.rag_manager.add_failure(query, response, suggestion)
            logger.debug("Archivado en RAG de fallos")

    def _synthesize_final(
        self,
        query: str,
        daemon_response: str,
        agent_output: str
    ) -> str:
        """Sintetizar respuesta final combinando daemon y agentes"""
        # Limpiar inputs primero
        clean_daemon = self._clean_llm_output(daemon_response)
        clean_agent = self._clean_llm_output(agent_output)

        synthesis_prompt = f"""Sintetiza una respuesta final combinando estas fuentes:

CONSULTA: {query}

RESPUESTA INICIAL:
{clean_daemon[:500]}

INFORMACIÓN ADICIONAL:
{clean_agent[:800]}

Crea una respuesta coherente, completa y útil.

RESPUESTA FINAL:"""

        try:
            result = self.daemon_cli.query(synthesis_prompt, timeout=60)
            result = self._clean_llm_output(result)
            if result and not result.startswith("Error"):
                return result
        except Exception as e:
            logger.error(f"Error en síntesis: {e}")

        # Fallback: combinar directamente
        return f"{daemon_response}\n\n[Información adicional]: {agent_output}"

    def enqueue_query(
        self,
        query: str,
        priority: int = Priority.NORMAL
    ) -> Optional[str]:
        """Encolar consulta para procesamiento asíncrono"""
        message = self.queue.enqueue(query, priority=priority)
        return message.id if message else None

    def start_worker(self):
        """Iniciar worker de procesamiento de cola"""
        if self._running:
            return

        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        logger.info("Worker de cola iniciado")

    def stop_worker(self):
        """Detener worker"""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        logger.info("Worker detenido")

    def cleanup(self):
        """Limpiar recursos al salir"""
        logger.info("Limpiando recursos...")
        self._running = False

        # Detener worker si está corriendo
        if hasattr(self, '_worker_thread') and self._worker_thread:
            self._worker_thread.join(timeout=2)

        # Cerrar conexiones de queue manager
        if hasattr(self, 'queue') and self.queue:
            try:
                self.queue.close()
            except:
                pass

        # Cerrar shared state
        if hasattr(self, 'shared_state') and self.shared_state:
            try:
                self.shared_state.close()
            except:
                pass

        logger.info("Recursos liberados")

    def _worker_loop(self):
        """Loop del worker que procesa la cola"""
        while self._running:
            try:
                message = self.queue.dequeue()
                if message:
                    logger.info(f"Procesando mensaje {message.id[:8]} de la cola")
                    result = self.process_query(
                        message.query,
                        depth=message.depth
                    )

                    if result.verdict == "OK":
                        self.queue.complete(message.id, result.response)
                    else:
                        self.queue.fail(message.id, f"Veredicto: {result.verdict}")
                else:
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error en worker: {e}")
                time.sleep(1)

    def get_queue_status(self) -> Dict[str, int]:
        """Obtener estado de la cola"""
        return self.queue.size()

    def interactive_mode(self):
        """Modo interactivo para pruebas"""
        print("=" * 60)
        print("   🤖 SISTEMA DE IA CON AGENTES Y RAGS v2.0")
        print("   == Arquitectura de Vanguardia ==")
        print("-" * 60)
        print("   Comandos:")
        print("   'salir'        - Terminar")
        print("   'status'       - Ver estado del sistema")
        print("   'adaptive on'  - Activar modo adaptativo")
        print("   'adaptive off' - Desactivar modo adaptativo")
        print("=" * 60)
        print()

        session_id = str(uuid.uuid4())

        while True:
            try:
                query = input("❓ Tu consulta: ").strip()

                if query.lower() in ['salir', 'exit', 'quit']:
                    print("👋 ¡Hasta luego!")
                    break

                if query.lower() == 'status':
                    stats = self.get_queue_status()
                    print(f"📊 Cola: {stats}")
                    rag_stats = self.rag_manager.get_all_stats()
                    print(f"📚 RAGs:")
                    for name, s in rag_stats.items():
                        print(f"   - {name}: {s.total_documents} docs")

                    # Mostrar estadísticas de memoria
                    if self.memory:
                        mem_stats = self.memory.get_stats()
                        print(f"🧠 Memoria: {mem_stats.get('total', 0)} memorias")
                        for mtype, info in mem_stats.get('by_type', {}).items():
                            print(f"   - {mtype}: {info.get('count', 0)} (success: {info.get('avg_success_rate', 0):.2f})")

                    print(f"⚙️ Modo adaptativo: {'ON' if self.adaptive_mode else 'OFF'}")
                    continue

                if query.lower() == 'adaptive on':
                    self.adaptive_mode = True
                    print("✅ Modo adaptativo activado")
                    continue

                if query.lower() == 'adaptive off':
                    self.adaptive_mode = False
                    print("❌ Modo adaptativo desactivado")
                    continue

                if not query:
                    continue

                print("🔄 Procesando...")
                result = self.process_query(query, session_id=session_id)

                print(f"\n💬 Respuesta ({result.verdict}, confianza: {result.confidence:.0%}):")
                print(result.response)
                print()

                # Métricas detalladas
                if result.iterations > 1:
                    print(f"🔄 Iteraciones: {result.iterations}")
                if result.strategy_used != "direct":
                    print(f"📊 Estrategia: {result.strategy_used}")
                if result.refinements:
                    print(f"🔧 Refinamientos: {len(result.refinements)}")
                if result.used_agents:
                    print(f"🤖 Agentes utilizados")
                if result.rag_sources:
                    print(f"📚 Fuentes: {', '.join(result.rag_sources)}")
                print(f"⏱️ Tiempo: {result.total_time:.1f}s\n")

            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                logger.exception("Error en modo interactivo")
                print(f"❌ Error: {e}\n")


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description="Orquestador de IA con Agentes y RAGs")
    parser.add_argument("query", nargs="*", help="Consulta a procesar")
    parser.add_argument("--interactive", "-i", action="store_true", help="Modo interactivo")
    parser.add_argument("--worker", "-w", action="store_true", help="Iniciar worker de cola")
    args = parser.parse_args()

    orchestrator = Orchestrator()

    # Registrar cleanup al salir
    atexit.register(orchestrator.cleanup)

    # Manejar señales para salida limpia
    def signal_handler(signum, frame):
        print("\n👋 Recibida señal de salida...")
        orchestrator.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        if args.interactive:
            orchestrator.interactive_mode()
        elif args.worker:
            print("🚀 Iniciando worker de cola...")
            orchestrator.start_worker()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        elif args.query:
            query = " ".join(args.query)
            result = orchestrator.process_query(query)

            print(f"📤 Respuesta ({result.verdict}):")
            print(result.response)

            if result.used_agents:
                print(f"\n🤖 Agentes utilizados: Sí")
            print(f"⏱️ Tiempo: {result.total_time:.1f}s")
        else:
            parser.print_help()
    finally:
        orchestrator.cleanup()


if __name__ == "__main__":
    main()
