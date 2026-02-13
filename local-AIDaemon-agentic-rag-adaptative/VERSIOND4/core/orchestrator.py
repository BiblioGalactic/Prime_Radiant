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

# === SISTEMA DE AUTO-APRENDIZAJE ===
try:
    from core.self_learning import (
        SessionLogger, SelfReflection, LearningOrchestrator,
        get_learning_orchestrator, EventType
    )
    HAS_SELF_LEARNING = True
except ImportError:
    HAS_SELF_LEARNING = False
    SessionLogger = None

# === TEATRO MENTAL (Deliberación multi-perspectiva) ===
try:
    from core.mental_theater import (
        MentalTheater, get_theater, should_use_theater, create_theater
    )
    HAS_MENTAL_THEATER = True
except ImportError:
    HAS_MENTAL_THEATER = False
    MentalTheater = None

from core.prompts import PromptBuilder, PromptStyle

# === CLASIFICADOR DE INTENCIONES Y SMART ROUTER ===
try:
    from core.intent_classifier import IntentClassifier, Intent, ActionType, get_intent_classifier
    from core.smart_router import SmartRouter, RouteResult
    HAS_INTENT_CLASSIFIER = True
except ImportError:
    HAS_INTENT_CLASSIFIER = False
    logger.warning("⚠️ Clasificador de intenciones no disponible")

# Daemon Persistente (opcional)
try:
    from core.daemon_persistent import PersistentDaemon, get_persistent_daemon, DaemonStatus
    HAS_PERSISTENT_DAEMON = True
except ImportError:
    HAS_PERSISTENT_DAEMON = False
    PersistentDaemon = None

# Prompt Cache (opcional)
try:
    from core.prompt_cache import HybridPromptCache, get_prompt_cache
    HAS_PROMPT_CACHE = True
except ImportError:
    HAS_PROMPT_CACHE = False
    get_prompt_cache = None

# === SISTEMA AGENTICO ===
try:
    from core.agentic import (
        AgentRuntime, AgentResult, AgentState,
        ToolRegistry, get_tool_registry,
        get_agent_prompts
    )
    HAS_AGENTIC = True
except ImportError:
    HAS_AGENTIC = False
    AgentRuntime = None

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

        # === DAEMON PERSISTENTE (ACTIVAR AUTOMÁTICAMENTE) ===
        self.persistent_daemon = None
        self.use_persistent_daemon = False
        self._init_persistent_daemon(auto_start=True)  # ACTIVAR AL INICIO

        # DaemonCLI como fallback o principal
        self.daemon_cli = DaemonCLI()
        self.rag_manager = RAGManager()
        self.shared_state = get_shared_state()

        # === PROMPT CACHE ===
        self.prompt_cache = None
        self.use_cache = True  # Habilitar por defecto
        self._init_prompt_cache()

        # Evaluador separado (Fix crítico #2)
        self.evaluator = create_evaluator(use_llm=True)

        # Inicializar RAGs
        logger.info("Inicializando RAGs...")
        self.rag_manager.init_default_rags()

        # === ACTIVAR FEATURES DE VANGUARDIA ===
        self._init_vanguard_features()

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
        self._cleaned_up = False  # Flag para evitar múltiples cleanups

        # Configuración adaptativa
        self.adaptive_mode = True  # Habilitar modo adaptativo
        self.max_rag_iterations = 1  # UNA sola iteración - respuesta directa

        # Flag para autogestión
        self.self_management_enabled = True

        # === SISTEMA AGENTICO ===
        self.agent_runtime = None
        self.agentic_mode = False  # Usar modo agentico para acciones
        self._init_agentic_system()

        logger.info("Orquestador inicializado (modo vanguardia)")

    def _init_prompt_cache(self):
        """Inicializar caché de prompts"""
        if not HAS_PROMPT_CACHE:
            logger.info("⚠️ Prompt Cache no disponible")
            return

        try:
            self.prompt_cache = get_prompt_cache()
            logger.info("💾 Prompt Cache inicializado")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo inicializar Prompt Cache: {e}")

    def _init_agentic_system(self):
        """Inicializar sistema agentico con loop Think→Act→Observe"""
        if not HAS_AGENTIC:
            logger.info("⚠️ Sistema agentic no disponible")
            return

        try:
            from core.agentic import AgentRuntime, get_tool_registry

            # Registrar herramientas
            self.tool_registry = get_tool_registry(auto_register=True)

            # Crear runtime con el daemon como LLM
            def llm_wrapper(prompt: str) -> str:
                return self._query_llm(prompt, timeout=90)

            self.agent_runtime = AgentRuntime(
                llm_interface=llm_wrapper,
                tool_registry=self.tool_registry,
                max_iterations=10,
                verbose=True
            )

            self.agentic_mode = True
            logger.info("🤖 Sistema agentic inicializado (Think→Act→Observe)")

        except Exception as e:
            logger.warning(f"⚠️ No se pudo inicializar sistema agentic: {e}")

    def process_with_agent(self, query: str) -> QueryResult:
        """
        Procesar consulta usando el sistema agentico completo.

        Usa el loop Think→Act→Observe→Repeat para tareas complejas.

        Args:
            query: Consulta del usuario

        Returns:
            QueryResult con la respuesta
        """
        if not self.agent_runtime:
            logger.warning("Sistema agentic no disponible, usando proceso normal")
            return self.process_query(query)

        start_time = time.time()

        try:
            logger.info(f"🤖 [Agentic] Procesando: {query[:50]}...")

            result = self.agent_runtime.execute(query)

            # Convertir AgentResult a QueryResult
            verdict = "OK" if result.success else "PARCIAL"
            confidence = 0.9 if result.success else 0.5

            return QueryResult(
                query=query,
                response=result.response,
                verdict=verdict,
                confidence=confidence,
                used_agents=True,
                total_time=time.time() - start_time,
                rag_sources=["agentic"],
                agent_results={
                    "steps": len(result.steps),
                    "tools_used": result.tools_used,
                    "iterations": result.metadata.get("iterations", 0)
                },
                strategy_used="agentic_loop"
            )

        except Exception as e:
            logger.error(f"Error en sistema agentic: {e}")
            return self.process_query(query)

    def enable_agentic_mode(self, enabled: bool = True):
        """Habilitar/deshabilitar modo agentic para acciones"""
        if not HAS_AGENTIC:
            logger.warning("Sistema agentic no disponible")
            return

        self.agentic_mode = enabled
        logger.info(f"🤖 Modo agentic: {'ON' if enabled else 'OFF'}")

    def _init_persistent_daemon(self, auto_start: bool = False):
        """
        Inicializar daemon persistente si está disponible.

        Con auto_start=True, el daemon se inicia inmediatamente y ESPERA
        hasta que esté listo o timeout.
        """
        if not HAS_PERSISTENT_DAEMON:
            logger.info("⚠️ Daemon persistente no disponible, usando DaemonCLI")
            return

        try:
            import time

            # Crear instancia del daemon
            self.persistent_daemon = get_persistent_daemon(auto_start=False)

            if auto_start:
                logger.info("🚀 Iniciando daemon persistente...")
                logger.info("   ⏳ Cargando modelo (esto puede tardar 30-60 segundos)...")

                # Iniciar el daemon
                started = self.persistent_daemon.start()

                if started:
                    # Esperar hasta que esté REALMENTE listo
                    max_wait = 90  # 90 segundos máximo
                    start_time = time.time()

                    while (time.time() - start_time) < max_wait:
                        if self.persistent_daemon.is_ready:
                            self.use_persistent_daemon = True
                            elapsed = time.time() - start_time
                            logger.info(f"🧠 Daemon persistente ACTIVO (cargado en {elapsed:.1f}s)")
                            return
                        time.sleep(0.5)

                    # Timeout pero puede estar funcionando
                    if self.persistent_daemon.status.value != 'stopped':
                        self.use_persistent_daemon = True
                        logger.info("🧠 Daemon persistente iniciado (verificar estado)")
                    else:
                        logger.warning("⚠️ Timeout iniciando daemon, usando DaemonCLI como fallback")
                else:
                    logger.warning("⚠️ No se pudo iniciar daemon, usando DaemonCLI como fallback")
            else:
                logger.info("🧠 Daemon persistente disponible (usa 'daemon start' para activar)")

        except Exception as e:
            logger.warning(f"⚠️ No se pudo configurar daemon persistente: {e}")

    def start_persistent_daemon(self) -> bool:
        """
        Iniciar daemon persistente para mantener modelo cargado.

        Returns:
            True si inició correctamente
        """
        if not self.persistent_daemon:
            logger.error("Daemon persistente no disponible")
            return False

        if self.persistent_daemon.is_ready:
            logger.info("Daemon persistente ya está corriendo")
            return True

        if self.persistent_daemon.start():
            self.use_persistent_daemon = True
            logger.info("🧠 Daemon persistente iniciado - modelo cargado en memoria")
            return True
        else:
            logger.error("❌ Error iniciando daemon persistente")
            return False

    def stop_persistent_daemon(self):
        """Detener daemon persistente"""
        if self.persistent_daemon:
            self.persistent_daemon.stop()
            self.use_persistent_daemon = False
            logger.info("🛑 Daemon persistente detenido")

    def get_daemon_status(self) -> Dict[str, Any]:
        """Obtener estado del daemon"""
        if self.persistent_daemon:
            return self.persistent_daemon.get_metrics()
        return {"status": "not_available", "using_cli": True}

    def _init_vanguard_features(self):
        """Inicializar features de vanguardia automáticamente"""
        try:
            # Activar Hybrid Search + Re-ranking para Wikipedia
            self.rag_manager.init_vanguard_features("wikipedia")
            logger.info("🔥 Features de vanguardia activadas (Hybrid Search + Re-ranking)")
        except Exception as e:
            logger.warning(f"⚠️ No se pudieron activar features de vanguardia: {e}")

        # Intentar inicializar MCP (SIEMPRE intentar)
        logger.info("🔌 Intentando inicializar MCP...")
        try:
            if self._try_init_mcp():
                logger.info("🔌 MCP inicializado correctamente")
            else:
                logger.info("⚠️ MCP no disponible (npx no encontrado o sin servidores)")
        except Exception as e:
            logger.warning(f"⚠️ Error inicializando MCP: {e}")

    def _try_init_mcp(self) -> bool:
        """Intentar inicializar MCP si está disponible"""
        try:
            import subprocess
            import os
            from pathlib import Path

            # Verificar si npx está disponible
            result = subprocess.run(['which', 'npx'], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                logger.debug("npx no encontrado")
                return False

            # Verificar si tenemos el módulo MCP
            try:
                from core.mcp_client import MCPClient
                from agents.mcp_agent import MCPAgent
            except ImportError as e:
                logger.debug(f"Módulos MCP no disponibles: {e}")
                return False

            # Config mínima - solo filesystem
            configs = {
                'filesystem': {
                    'command': 'npx',
                    'args': [
                        '-y',
                        '@modelcontextprotocol/server-filesystem',
                        str(Path.home())
                    ],
                    'env': {}
                }
            }

            # Agregar web search si hay API key
            brave_key = os.getenv('BRAVE_API_KEY')
            if brave_key:
                configs['brave_search'] = {
                    'command': 'npx',
                    'args': ['-y', '@modelcontextprotocol/server-brave-search'],
                    'env': {'BRAVE_API_KEY': brave_key}
                }

            logger.info(f"   Configurando MCP con {len(configs)} servidores...")
            self.mcp_client = MCPClient(configs, auto_start=True)

            # Esperar un poco y verificar que al menos un servidor esté listo
            import time
            for _ in range(3):  # Esperar hasta 3 segundos
                status = self.mcp_client.get_server_status()
                ready = any(s.get('is_ready', False) for s in status.values())
                if ready:
                    break
                time.sleep(1)

            status = self.mcp_client.get_server_status()
            ready_servers = [n for n, s in status.items() if s.get('is_ready', False)]

            if ready_servers:
                logger.info(f"   Servidores MCP listos: {ready_servers}")
                self.mcp_agent = MCPAgent(
                    mcp_client=self.mcp_client,
                    llm_interface=self.daemon_cli,
                    max_iterations=5,
                    verbose=False
                )
                self._mcp_initialized = True
                return True
            else:
                logger.debug("Ningún servidor MCP se inició correctamente")
                return False

        except Exception as e:
            logger.debug(f"Error inicializando MCP: {e}")
            return False

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

        # === MCP INTEGRATION ===
        # NOTA: No sobrescribir si ya está inicializado por _try_init_mcp()
        if not hasattr(self, 'mcp_client') or self.mcp_client is None:
            self.mcp_client = None
        if not hasattr(self, 'mcp_agent') or self.mcp_agent is None:
            self.mcp_agent = None
        if not hasattr(self, '_mcp_initialized'):
            self._mcp_initialized = False

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

        # 1. CONSULTAR MEMORIA (solo si es MUY similar, threshold alto)
        memory_context = ""
        # DESACTIVADO temporalmente - contamina respuestas con queries no relacionadas
        # if use_memory and self.memory:
        #     similar_episodes = self.memory.recall_similar_episodes(query, k=1, threshold=0.85)
        #     if similar_episodes:
        #         memory_context = f"[Memoria]: {similar_episodes[0].content[:150]}..."
        #         logger.info(f"[Adaptive] Encontrado episodio similar en memoria")

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

            # Generar respuesta (usa daemon persistente si disponible)
            response = self._query_llm(prompt, timeout=self.config.DAEMON_TIMEOUT)

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

        # 4. TEATRO MENTAL (si la respuesta es PARCIAL/FALLA)
        theater_used = False
        if HAS_MENTAL_THEATER and should_use_theater(best_verdict.value, best_confidence):
            try:
                logger.info("🎭 Activando Teatro Mental para mejorar respuesta...")
                theater = get_theater(self.daemon_cli)
                result = theater.deliberate(
                    query=query,
                    initial_response=best_response,
                    context=context if context else "",
                    use_simple=True  # Modo rápido
                )
                if result.improved_response and result.improved_response != best_response:
                    best_response = result.improved_response
                    best_confidence = min(1.0, best_confidence + result.confidence_boost)
                    theater_used = True
                    logger.info(f"🎭 Respuesta mejorada (boost: +{result.confidence_boost:.0%})")
            except Exception as e:
                logger.warning(f"⚠️ Teatro Mental falló: {e}")

        # 5. ARCHIVAR EN RAG DE ÉXITOS/FALLOS
        try:
            from core.evaluator import EvaluationResult
            eval_for_archive = EvaluationResult(
                verdict=best_verdict,
                confidence=best_confidence,
                reason=f"Estrategia: {strategy.value}, Iteraciones: {iterations}",
                suggestions=[]
            )
            self._archive_response(query, best_response, best_verdict.value, eval_for_archive)
        except Exception as e:
            logger.error(f"❌ Error archivando en RAG: {e}")

        # 6. GUARDAR EN MEMORIA
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

        # Obtener respuesta (usa daemon persistente si disponible)
        logger.info("Ejecutando modelo LLM...")
        prompt = self._build_prompt(query, context)
        response_content = self._query_llm(prompt, timeout=self.config.DAEMON_TIMEOUT)

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

    def _query_llm(self, prompt: str, timeout: int = None, use_cache: bool = None) -> str:
        """
        Ejecutar consulta LLM usando daemon persistente o CLI.

        COMPORTAMIENTO AUTOMÁTICO:
        - Primero intenta cache
        - Si daemon está listo, lo usa
        - Si no, usa DaemonCLI (carga modelo bajo demanda)
        - Todo transparente, sin intervención del usuario

        Args:
            prompt: Prompt a enviar
            timeout: Timeout en segundos
            use_cache: Forzar uso/no uso de caché

        Returns:
            Respuesta del modelo
        """
        timeout = timeout or self.config.DAEMON_TIMEOUT
        should_cache = use_cache if use_cache is not None else self.use_cache

        # === CHECK CACHE ===
        if should_cache and self.prompt_cache:
            cached_response = self.prompt_cache.get(prompt, model="daemon")
            if cached_response:
                logger.info("💾 Cache HIT - usando respuesta cacheada")
                return cached_response

        # === AUTO-ACTIVAR DAEMON SI NO ESTÁ LISTO ===
        # El daemon se activa automáticamente cuando se necesita
        if self.persistent_daemon and not self.persistent_daemon.is_ready:
            if not self.use_persistent_daemon:
                # Primera vez: intentar activar daemon automáticamente
                logger.info("🚀 Auto-activando daemon persistente...")
                if self.persistent_daemon.start():
                    self.use_persistent_daemon = True
                    logger.info("🧠 Daemon ACTIVO automáticamente")

        # Usar daemon persistente si está disponible y activo
        if self.use_persistent_daemon and self.persistent_daemon and self.persistent_daemon.is_ready:
            logger.debug("Usando daemon persistente")
            response = self.persistent_daemon.query(prompt, timeout=timeout)
        else:
            # Fallback a DaemonCLI (también carga modelo automáticamente)
            logger.debug("Usando DaemonCLI")
            response = self.daemon_cli.query(prompt, timeout=timeout)

        cleaned = self._clean_llm_output(response)

        # === SAVE TO CACHE ===
        if should_cache and self.prompt_cache and cleaned and not cleaned.startswith("Error"):
            self.prompt_cache.put(
                prompt, cleaned,
                model="daemon",
                persist=True,
                metadata={"timeout": timeout}
            )
            logger.debug("💾 Respuesta guardada en caché")

        return cleaned

    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del caché"""
        if self.prompt_cache:
            return self.prompt_cache.get_stats()
        return {"enabled": False}

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
        """Limpiar output del LLM de logs de GPU/Metal y tags especiales"""
        import re

        # === PRIMERO: Eliminar bloques <think>...</think> (Qwen3 thinking) ===
        # Esto debe hacerse antes de otros patrones para capturar bloques multilinea
        cleaned = re.sub(r'<think>.*?</think>', '', output, flags=re.DOTALL | re.IGNORECASE)

        # También eliminar tags de pensamiento incompletos
        cleaned = re.sub(r'<think>.*$', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'^.*?</think>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)

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
        try:
            if verdict == "OK":
                self.rag_manager.add_success(query, response)
                logger.info("📗 Archivado en RAG de ÉXITOS")
            elif verdict in ["PARCIAL", "FALLA"]:
                suggestion = evaluation.reason
                if evaluation.suggestions:
                    suggestion += " | " + " | ".join(evaluation.suggestions)
                self.rag_manager.add_failure(query, response, suggestion)
                logger.info("📕 Archivado en RAG de FALLOS")
            else:
                logger.warning(f"⚠️ Verdict desconocido: {verdict}, no se archiva")
        except Exception as e:
            logger.error(f"❌ Error archivando respuesta: {e}")

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
            result = self._query_llm(synthesis_prompt, timeout=60)
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
        """Limpiar recursos al salir (solo una vez)"""
        # Evitar múltiples cleanups
        if hasattr(self, '_cleaned_up') and self._cleaned_up:
            return
        self._cleaned_up = True

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

        # Limpiar MCP
        self.cleanup_mcp()

        # Detener daemon persistente (usa singleton, solo para una vez)
        if hasattr(self, 'persistent_daemon') and self.persistent_daemon:
            try:
                self.persistent_daemon.stop()
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

    def _show_startup_status(self):
        """Mostrar estado del sistema al iniciar"""
        print("-" * 60)
        print("   📊 ESTADO DEL SISTEMA")
        print("-" * 60)

        # RAGs
        rag_stats = self.rag_manager.get_all_stats()
        print("   📚 RAGs:")
        for name, s in rag_stats.items():
            print(f"      - {name}: {s.total_documents} docs")

        # Memoria
        if self.memory:
            mem_stats = self.memory.get_stats()
            total_mem = mem_stats.get('total', 0)
            print(f"   🧠 Memoria: {total_mem} memorias")

        # Daemon persistente - Verificación REAL
        if self.persistent_daemon:
            if self.persistent_daemon.is_ready:
                metrics = self.persistent_daemon.get_metrics()
                reqs = metrics.get('total_requests', 0)
                print(f"   🟢 Daemon: ACTIVO (modelo cargado, {reqs} requests)")
            elif self.use_persistent_daemon:
                print(f"   🟡 Daemon: INICIANDO...")
            else:
                print(f"   🔴 Daemon: DETENIDO (usa 'daemon start' o espera auto-activación)")
        else:
            print(f"   ⚪ Daemon: No disponible (usando DaemonCLI)")

        # MCP - Verificación REAL
        if self._mcp_initialized and self.mcp_client:
            try:
                status = self.mcp_client.get_server_status()
                ready_servers = [n for n, s in status.items() if s.get('is_ready', False)]
                tools = self.mcp_client.list_tools() if hasattr(self.mcp_client, 'list_tools') else []
                print(f"   🔌 MCP: {len(ready_servers)} servidores, {len(tools)} tools")
            except:
                print(f"   🔌 MCP: Inicializado (error obteniendo estado)")
        else:
            print(f"   ⚪ MCP: No inicializado")

        # Cache
        cache_stats = self.get_cache_stats()
        if cache_stats.get('enabled') is not False:
            hit_rate = cache_stats.get('hit_rate', 0)
            print(f"   💾 Cache: {hit_rate:.0%} hit rate")

        # Sistema Agentic
        if hasattr(self, 'agent_runtime') and self.agent_runtime:
            tools_count = len(self.tool_registry.list_tools()) if hasattr(self, 'tool_registry') else 0
            print(f"   🤖 Agentic: {'ON' if self.agentic_mode else 'OFF'} ({tools_count} herramientas)")
        else:
            print(f"   ⚪ Agentic: No disponible")

        # Modo
        print(f"   ⚙️  Modo adaptativo: {'ON' if self.adaptive_mode else 'OFF'}")

        print("-" * 60)
        print()

    def interactive_mode(self):
        """Modo interactivo con CLASIFICACIÓN DE INTENCIONES y AUTO-APRENDIZAJE"""
        print("=" * 60)
        print("   🤖 WIKIRAG v2.5 - Sistema de IA Autónomo")
        print("   🧠 Modo Agentic: Think→Act→Observe→Repeat")
        print("   📚 Auto-Aprendizaje: Análisis al salir con 'exit'")
        print("=" * 60)
        print()

        # === MOSTRAR STATUS AUTOMÁTICO AL INICIO ===
        self._show_startup_status()

        session_id = str(uuid.uuid4())

        # === INICIALIZAR SISTEMA DE AUTO-APRENDIZAJE ===
        session_logger = None
        learning_orchestrator = None
        if HAS_SELF_LEARNING:
            learning_orchestrator = get_learning_orchestrator(self.daemon_cli)
            session_logger = learning_orchestrator.start_session(session_id)
            logger.info("📚 Sistema de auto-aprendizaje activo")

        # === INICIALIZAR CLASIFICADOR DE INTENCIONES ===
        intent_classifier = None
        if HAS_INTENT_CLASSIFIER:
            intent_classifier = get_intent_classifier()
            logger.info("🎯 Clasificador de intenciones activo")

        while True:
            try:
                query = input("❓ Tu consulta: ").strip()

                if not query:
                    continue

                # === CLASIFICAR INTENCIÓN PRIMERO ===
                if intent_classifier:
                    classification = intent_classifier.classify(query)
                    logger.info(f"🎯 Intent: {classification.intent.value} ({classification.confidence:.0%})")

                    # SISTEMA: help, exit, status
                    if classification.intent == Intent.SYSTEM:
                        response = self._handle_system_command(classification)
                        if response == "__EXIT__":
                            # === AUTO-APRENDIZAJE AL SALIR ===
                            if learning_orchestrator:
                                print("\n🧠 Analizando sesión para aprender de los errores...")
                                learning_orchestrator.end_session(show_analysis=True)
                            print("\n👋 ¡Hasta luego!")
                            break
                        print(f"\n{response}\n")
                        continue

                    # ACCIÓN: filesystem, claudia, git, etc.
                    if classification.intent == Intent.ACTION:
                        print(f"🔄 Ejecutando acción: {classification.action_type.value}...")
                        if session_logger:
                            session_logger.log_query(query)
                        result = self._handle_action_intent(classification, session_id)
                        # Detectar si se usó fallback (indica que el agente falló)
                        if "📁" in result or "Contenido de" in result:
                            if session_logger:
                                session_logger.log_fallback_used(query, "filesystem_handler", result[:200])
                        print(f"\n💬 Resultado:")
                        print(result)
                        continue

                    # CONVERSACIONAL: saludos, etc.
                    if classification.intent == Intent.CONVERSATIONAL:
                        response = self._handle_conversational(classification)
                        print(f"\n{response}\n")
                        continue

                    # INFORMATIVO o HÍBRIDO: usar RAG
                    # (cae al flujo normal)

                # === FLUJO NORMAL: RAG ===
                print("🔄 Procesando...")
                if session_logger:
                    session_logger.log_query(query)

                result = self.process_query(query, session_id=session_id)

                # Capturar resultado para aprendizaje
                if session_logger:
                    session_logger.log_response(query, result.response, result.verdict, result.confidence)

                print(f"\n💬 Respuesta ({result.verdict}, {result.confidence:.0%}):")
                print(result.response)
                print(f"⏱️ {result.total_time:.1f}s\n")

            except KeyboardInterrupt:
                # === AUTO-APRENDIZAJE AL SALIR CON CTRL+C ===
                if learning_orchestrator:
                    print("\n\n🧠 Analizando sesión para aprender de los errores...")
                    learning_orchestrator.end_session(show_analysis=True)
                print("\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                logger.exception("Error en modo interactivo")
                print(f"❌ Error: {e}\n")

    def _handle_system_command(self, classification) -> str:
        """Manejar comandos del sistema"""
        from core.intent_classifier import SystemCommand

        cmd = classification.system_command

        if cmd == SystemCommand.HELP:
            return self._generate_help_text()
        elif cmd == SystemCommand.EXIT:
            return "__EXIT__"
        elif cmd == SystemCommand.STATUS:
            self._show_full_status()
            return ""
        elif cmd == SystemCommand.HISTORY:
            return self._get_history_text()
        elif cmd == SystemCommand.CONFIG:
            return self._get_config_text()
        elif cmd == SystemCommand.CLEAR:
            import os
            os.system('clear' if os.name == 'posix' else 'cls')
            return ""
        else:
            return "Comando no reconocido. Escribe 'help' para ver opciones."

    def _handle_action_intent(self, classification, session_id: str) -> str:
        """Manejar intenciones de acción (filesystem, claudia, git, etc.)"""
        from core.intent_classifier import ActionType

        action_type = classification.action_type
        query = classification.query
        entities = classification.entities

        # === MODO AGENTIC: Usar loop Think→Act→Observe ===
        if self.agentic_mode and self.agent_runtime:
            try:
                logger.info("🤖 Usando modo agentic...")
                result = self.agent_runtime.execute(query)
                if result.success:
                    return f"✅ [Agentic]\n{result.response}"
                else:
                    # Fallback a handlers específicos
                    logger.info("Agentic falló, usando handler específico")
            except Exception as e:
                logger.warning(f"Error en modo agentic: {e}")

        # === CLAUDIA ===
        if action_type == ActionType.CLAUDIA:
            return self._execute_claudia_action(query, entities)

        # === FILESYSTEM ===
        if action_type == ActionType.FILESYSTEM:
            return self._execute_filesystem_action(query, entities)

        # === GIT ===
        if action_type == ActionType.GIT:
            return self._execute_git_action(query, entities)

        # === CODE ===
        if action_type == ActionType.CODE:
            return self._execute_code_action(query, entities)

        # === MCP GENÉRICO ===
        if hasattr(self, 'mcp_agent') and self.mcp_agent:
            try:
                result = self.mcp_agent.execute(query)
                return result.response if hasattr(result, 'response') else str(result)
            except Exception as e:
                return f"❌ Error MCP: {str(e)}"

        return "⚠️ No hay handler disponible para esta acción."

    def _execute_claudia_action(self, query: str, entities: dict) -> str:
        """Ejecutar acción con Claudia - ANÁLISIS de código, no ejecución"""
        try:
            from agents.claudia_agent import get_claudia_agent

            claudia = get_claudia_agent()
            if not claudia.is_available:
                return "⚠️ Claudia no está disponible. Instala asistente-ia en ~/proyecto/asistente-ia"

            query_lower = query.lower()
            paths = entities.get("paths", [])

            # Detectar qué tipo de análisis hacer
            if "proyecto" in query_lower or "project" in query_lower:
                # Análisis de proyecto completo
                project_path = paths[0] if paths else None
                if project_path and project_path.startswith("~"):
                    project_path = os.path.expanduser(project_path)
                result = claudia.analyze_project(project_path)

            elif paths:
                # Análisis de archivo específico
                file_path = paths[0]
                if file_path.startswith("~"):
                    file_path = os.path.expanduser(file_path)

                # Extraer pregunta específica si hay
                question = None
                if "qué hace" in query_lower or "que hace" in query_lower:
                    question = "¿Qué hace este código?"
                elif "explica" in query_lower:
                    question = "Explica este código"
                elif "bug" in query_lower or "error" in query_lower:
                    question = "¿Hay errores o bugs en este código?"

                result = claudia.analyze_file(file_path, question)

            else:
                # Análisis general - usar modo normal pero SIN ejecutar
                # Reformular para que sea análisis, no ejecución
                analysis_query = f"Analiza y explica: {query}"
                result = claudia.execute(analysis_query, agentic=False)

            if result.success:
                return f"✅ [Claudia:{result.mode}]\n{result.response}"
            else:
                return f"❌ Error Claudia: {result.error}"

        except ImportError:
            return "⚠️ Módulo Claudia no disponible"
        except Exception as e:
            return f"❌ Error ejecutando Claudia: {str(e)}"

    def _execute_filesystem_action(self, query: str, entities: dict) -> str:
        """Ejecutar acción de filesystem"""
        import subprocess
        import re

        query_lower = query.lower()
        paths = entities.get("paths", [])

        # === EXTRAER PATH DE LA CONSULTA ===
        extracted_path = None
        path_patterns = [
            r'carpeta\s+([a-zA-Z0-9_\-~/\.]+)',
            r'directorio\s+([a-zA-Z0-9_\-~/\.]+)',
            r'folder\s+([a-zA-Z0-9_\-~/\.]+)',
            r'en\s+([~/][a-zA-Z0-9_\-/\.]+)',
            r'de\s+([~/][a-zA-Z0-9_\-/\.]+)',
        ]
        for pattern in path_patterns:
            match = re.search(pattern, query_lower)
            if match:
                extracted_path = match.group(1)
                break

        # === MAPA DE PATHS COMUNES ===
        path_map = {
            "proyectos": "~/proyecto",
            "proyecto": "~/proyecto",
            "completo": "~/proyecto",
            "home": "~",
            "documentos": "~/Documents",
            "documents": "~/Documents",
            "desktop": "~/Desktop",
            "escritorio": "~/Desktop",
            "descargas": "~/Downloads",
            "downloads": "~/Downloads",
            "wikirag": "~/wikirag",
            "asistente": "~/proyecto/asistente-ia",
            "asistente-ia": "~/proyecto/asistente-ia",
            "core": "~/wikirag/core",
            "agents": "~/wikirag/agents",
        }

        def resolve_path(p):
            """Resolver un path a ruta absoluta"""
            if not p or p == ".":
                return os.getcwd()
            p_lower = p.lower().strip()
            # Buscar en mapa
            if p_lower in path_map:
                return os.path.expanduser(path_map[p_lower])
            # Expandir ~
            if p.startswith("~"):
                return os.path.expanduser(p)
            # Buscar en home
            home_path = os.path.expanduser(f"~/{p}")
            if os.path.exists(home_path):
                return home_path
            # Buscar en proyecto
            proj_path = os.path.expanduser(f"~/proyecto/{p}")
            if os.path.exists(proj_path):
                return proj_path
            # Devolver como está
            return p

        # Detectar tipo de operación
        if any(kw in query_lower for kw in ["lista", "listar", "ls", "muestra", "contenido de", "archivos"]):
            # LISTAR DIRECTORIO
            path = extracted_path or (paths[0] if paths else ".")
            path = resolve_path(path)

            try:
                result = subprocess.run(
                    ["ls", "-la", path],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    return f"📁 **Contenido de `{path}`:**\n```\n{result.stdout[:3000]}\n```"
                else:
                    return f"❌ Error: {result.stderr}"
            except subprocess.TimeoutExpired:
                return "❌ Timeout ejecutando comando"
            except Exception as e:
                return f"❌ Error: {str(e)}"

        elif any(kw in query_lower for kw in ["lee", "leer", "abre", "cat", "mostrar"]):
            # LEER ARCHIVO
            if not paths:
                return "⚠️ No especificaste qué archivo leer."

            path = paths[0]
            if path.startswith("~"):
                path = os.path.expanduser(path)

            try:
                with open(path, 'r') as f:
                    content = f.read()[:5000]
                return f"📄 **Contenido de `{path}`:**\n```\n{content}\n```"
            except FileNotFoundError:
                return f"❌ Archivo no encontrado: {path}"
            except Exception as e:
                return f"❌ Error leyendo archivo: {str(e)}"

        elif any(kw in query_lower for kw in ["busca", "encuentra", "localiza", "find"]):
            # BUSCAR ARCHIVOS
            pattern = entities.get("quoted", ["*"])[0] if entities.get("quoted") else "*"
            path = paths[0] if paths else "."

            if path.startswith("~"):
                path = os.path.expanduser(path)

            try:
                result = subprocess.run(
                    ["find", path, "-name", pattern, "-maxdepth", "3"],
                    capture_output=True, text=True, timeout=15
                )
                if result.stdout:
                    return f"🔍 **Archivos encontrados:**\n```\n{result.stdout[:2000]}\n```"
                else:
                    return f"No se encontraron archivos con el patrón '{pattern}'"
            except Exception as e:
                return f"❌ Error buscando: {str(e)}"

        # Fallback: intentar ejecutar con MCP si está disponible
        if hasattr(self, 'mcp_agent') and self.mcp_agent:
            try:
                result = self.mcp_agent.execute(query)
                return result.response if hasattr(result, 'response') else str(result)
            except:
                pass

        return "⚠️ No pude determinar qué acción de filesystem ejecutar."

    def _execute_git_action(self, query: str, entities: dict) -> str:
        """Ejecutar acción de git"""
        import subprocess

        query_lower = query.lower()

        # Detectar comando git
        if "status" in query_lower:
            cmd = ["git", "status"]
        elif "log" in query_lower or "commits" in query_lower:
            cmd = ["git", "log", "--oneline", "-10"]
        elif "diff" in query_lower:
            cmd = ["git", "diff", "--stat"]
        elif "branch" in query_lower:
            cmd = ["git", "branch", "-a"]
        else:
            cmd = ["git", "status"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return f"📦 **{' '.join(cmd)}:**\n```\n{result.stdout[:2000]}\n```"
            else:
                return f"❌ {result.stderr}"
        except Exception as e:
            return f"❌ Error git: {str(e)}"

    def _execute_code_action(self, query: str, entities: dict) -> str:
        """Ejecutar acción de código"""
        # Delegar a Claudia si está disponible
        return self._execute_claudia_action(query, entities)

    def _handle_conversational(self, classification) -> str:
        """Manejar mensajes conversacionales"""
        query_lower = classification.query.lower()

        if any(g in query_lower for g in ['hola', 'hello', 'hi', 'hey']):
            return "¡Hola! 👋 ¿En qué puedo ayudarte?\n\n**Puedo:**\n• Responder preguntas (usa RAG)\n• Listar archivos: `lista los archivos de ~/proyecto`\n• Analizar código: `usa claudia para analizar main.py`\n• Comandos git: `git status`\n\nEscribe `help` para más opciones."

        elif any(g in query_lower for g in ['gracias', 'thanks']):
            return "¡De nada! 😊 ¿Algo más en lo que pueda ayudarte?"

        elif any(g in query_lower for g in ['cómo estás', 'como estas']):
            return "¡Estoy bien, gracias! 🤖 Listo para ayudarte."

        return "¿En qué puedo ayudarte? Escribe `help` para ver opciones."

    def _generate_help_text(self) -> str:
        """Generar texto de ayuda"""
        return """
╔══════════════════════════════════════════════════════════════╗
║                    📚 AYUDA - WikiRAG v2.3                   ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  🔍 CONSULTAS INFORMATIVAS (RAG)                            ║
║    • "¿Qué es Python?"                                      ║
║    • "Explícame machine learning"                           ║
║    • "Historia de la inteligencia artificial"               ║
║                                                              ║
║  ⚡ ACCIONES (ejecuta comandos)                              ║
║    • "Lista los archivos de ~/proyecto"                     ║
║    • "Lee el archivo config.json"                           ║
║    • "Busca archivos .py"                                   ║
║    • "git status"                                           ║
║    • "usa claudia para analizar el proyecto"                ║
║                                                              ║
║  🛠️ COMANDOS DEL SISTEMA                                    ║
║    • help     - Esta ayuda                                  ║
║    • status   - Estado del sistema                          ║
║    • salir    - Salir                                       ║
║                                                              ║
║  💡 EJEMPLOS:                                                ║
║    • "lista archivos de la carpeta proyectos"               ║
║    • "que claudia analice el código de main.py"             ║
║    • "qué es la fotosíntesis?"                              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

    def _get_history_text(self) -> str:
        """Obtener historial de memoria"""
        try:
            recent = self.memory.search("", limit=10)
            if not recent:
                return "📜 Historial vacío"

            lines = ["📜 **Últimas consultas:**"]
            for i, m in enumerate(recent, 1):
                lines.append(f"  {i}. {m.content[:50]}...")
            return "\n".join(lines)
        except:
            return "📜 Historial no disponible"

    def _get_config_text(self) -> str:
        """Obtener configuración actual"""
        config_info = f"""
⚙️ **CONFIGURACIÓN ACTUAL**

**Daemon:**
  • Persistente: {'✅ Activo' if self.use_persistent_daemon else '❌ Inactivo'}
  • CLI disponible: ✅

**RAGs:**
  • Wikipedia: {self.rag_manager.rag_stores.get('wikipedia', {}).doc_count if hasattr(self.rag_manager, 'rag_stores') else '?'} docs
  • Modo adaptativo: {'✅' if self.adaptive_mode else '❌'}

**Cache:**
  • Activo: {'✅' if self.prompt_cache else '❌'}

**MCP:**
  • Inicializado: {'✅' if getattr(self, '_mcp_initialized', False) else '❌'}
"""
        return config_info

    def _show_full_status(self):
        """Mostrar estado completo del sistema"""
        print("-" * 50)
        # Cola
        stats = self.get_queue_status()
        print(f"📊 Cola: {stats}")

        # RAGs
        rag_stats = self.rag_manager.get_all_stats()
        print(f"📚 RAGs:")
        for name, s in rag_stats.items():
            print(f"   - {name}: {s.total_documents} docs")

        # Memoria
        if self.memory:
            mem_stats = self.memory.get_stats()
            print(f"🧠 Memoria: {mem_stats.get('total', 0)} memorias")

        # Daemon
        daemon_status = self.get_daemon_status()
        status_str = daemon_status.get('status', 'N/A')
        if status_str == 'ready':
            print(f"🟢 Daemon: ACTIVO ({daemon_status.get('total_requests', 0)} requests)")
        else:
            print(f"⚪ Daemon: {status_str} (se activa automáticamente)")

        # MCP
        mcp_status = self.get_mcp_status()
        if mcp_status.get('initialized'):
            print(f"🔌 MCP: {mcp_status.get('total_tools', 0)} tools")

        # Cache
        cache_stats = self.get_cache_stats()
        if cache_stats.get('enabled') is not False:
            print(f"💾 Cache: {cache_stats.get('hit_rate', 0):.0%} hit rate")

        print("-" * 50)


    # =========================================================================
    # 🔌 MCP INTEGRATION - Model Context Protocol
    # =========================================================================

    def init_mcp(self, server_configs: Dict[str, Dict] = None, use_defaults: bool = True):
        """
        Inicializar cliente y agente MCP.

        Args:
            server_configs: Configuración personalizada de servidores MCP
            use_defaults: Si usar configuraciones predefinidas

        Ejemplo de server_configs:
            {
                'brave_search': {
                    'command': 'npx',
                    'args': ['-y', '@modelcontextprotocol/server-brave-search'],
                    'env': {'BRAVE_API_KEY': 'tu_api_key'}
                }
            }
        """
        try:
            from core.mcp_client import MCPClient, get_default_configs
            from agents.mcp_agent import MCPAgent

            # Preparar configuraciones
            configs = {}

            if use_defaults:
                default_configs = get_default_configs()
                # Solo usar los que tienen API keys configuradas
                for name, cfg in default_configs.items():
                    env = cfg.get('env', {})
                    # Verificar si tiene API key o no la necesita
                    has_required_keys = all(v for v in env.values() if v)
                    if has_required_keys or not env:
                        configs[name] = cfg

            if server_configs:
                configs.update(server_configs)

            if not configs:
                logger.warning("⚠️ No hay servidores MCP configurados")
                return False

            # Inicializar cliente
            self.mcp_client = MCPClient(configs, auto_start=True)

            # Verificar que al menos un servidor esté listo
            status = self.mcp_client.get_server_status()
            ready_servers = [n for n, s in status.items() if s['is_ready']]

            if not ready_servers:
                logger.error("❌ Ningún servidor MCP se inició correctamente")
                return False

            logger.info(f"✅ Servidores MCP listos: {ready_servers}")

            # Inicializar agente MCP
            self.mcp_agent = MCPAgent(
                mcp_client=self.mcp_client,
                llm_interface=self.daemon_cli,
                max_iterations=5,
                verbose=False
            )

            self._mcp_initialized = True
            logger.info("🔌 MCP Integration inicializada")
            return True

        except ImportError as e:
            logger.error(f"❌ Error importando MCP: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inicializando MCP: {e}")
            return False

    def process_with_mcp(self, query: str) -> QueryResult:
        """
        Procesar query usando agente MCP con herramientas externas.

        El agente puede usar herramientas como:
        - brave_web_search: Búsqueda en la web
        - read_file/write_file: Acceso a archivos
        - github_*: Operaciones de GitHub

        Args:
            query: Consulta del usuario

        Returns:
            QueryResult con respuesta del agente MCP
        """
        start_time = time.time()

        if not self._mcp_initialized or not self.mcp_agent:
            logger.warning("⚠️ MCP no inicializado, usando proceso normal")
            return self.process_query(query)

        try:
            logger.info(f"🔌 [MCP] Procesando: {query[:50]}...")

            result = self.mcp_agent.execute(query)

            # Convertir a QueryResult
            verdict = "OK" if result.success else "PARCIAL"
            confidence = 0.85 if result.success else 0.5

            return QueryResult(
                query=query,
                response=result.response,
                verdict=verdict,
                confidence=confidence,
                used_agents=True,
                total_time=time.time() - start_time,
                rag_sources=["mcp"] + result.tools_used,
                agent_results={
                    "steps": len(result.steps),
                    "tools_used": result.tools_used,
                    "iterations": result.total_iterations,
                    "mcp_metadata": result.metadata
                },
                strategy_used="mcp_agent"
            )

        except Exception as e:
            logger.error(f"❌ Error en MCP: {e}")
            # Fallback a proceso normal
            return self.process_query(query)

    def needs_web_search(self, query: str) -> bool:
        """
        Detectar si la query requiere búsqueda web.

        Indicadores de necesidad de web:
        - Eventos recientes/actuales
        - Preguntas sobre "hoy", "ayer", "esta semana"
        - Temas de actualidad
        - Preguntas sobre precios/clima/noticias
        """
        web_keywords = [
            "hoy", "ayer", "esta semana", "este mes", "2024", "2025",
            "actual", "reciente", "últimas noticias", "precio actual",
            "clima en", "weather", "news", "noticias sobre",
            "quién ganó", "resultado de", "cotización", "tendencia"
        ]

        query_lower = query.lower()
        return any(kw in query_lower for kw in web_keywords)

    def process_query_smart(
        self,
        query: str,
        session_id: str = None,
        force_mcp: bool = False
    ) -> QueryResult:
        """
        Procesar query decidiendo automáticamente si usar MCP o RAG local.

        Flujo:
        1. Detectar si necesita búsqueda web
        2. Si sí y MCP disponible → usar MCP
        3. Si no → usar RAG local

        Args:
            query: Consulta del usuario
            session_id: ID de sesión
            force_mcp: Forzar uso de MCP

        Returns:
            QueryResult
        """
        # Decidir si usar MCP
        use_mcp = force_mcp or (
            self._mcp_initialized and
            self.mcp_agent and
            self.needs_web_search(query)
        )

        if use_mcp:
            logger.info("🔌 Usando MCP para búsqueda web")
            return self.process_with_mcp(query)
        else:
            logger.info("📚 Usando RAG local")
            return self.process_query(query, session_id=session_id)

    def get_mcp_status(self) -> Dict[str, Any]:
        """Obtener estado de MCP"""
        if not self._mcp_initialized or not self.mcp_client:
            return {"initialized": False, "servers": {}}

        status = self.mcp_client.get_server_status()
        tools = self.mcp_client.list_tools()

        return {
            "initialized": True,
            "servers": status,
            "total_tools": len(tools),
            "tools": [{"name": t.name, "server": t.server} for t in tools]
        }

    def cleanup_mcp(self):
        """Limpiar recursos MCP"""
        if self.mcp_client:
            try:
                self.mcp_client.stop_all()
                logger.info("🔌 Servidores MCP detenidos")
            except Exception as e:
                logger.warning(f"⚠️ Error deteniendo MCP: {e}")


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
