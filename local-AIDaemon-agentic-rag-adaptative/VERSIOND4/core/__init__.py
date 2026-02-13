#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
CORE - Módulos Centrales de WikiRAG D4
========================================
Importa automáticamente todos los módulos disponibles.
Usa config_portable para rutas relativas.
"""

import logging
import sys
import os

# Configuración portátil
try:
    from .config_portable import get_config, get_portable_path, PortableConfig
    CONFIG = get_config()
except ImportError:
    # Fallback a config original si no está disponible
    try:
        from .config import get_config, Config
        CONFIG = get_config()
    except ImportError:
        CONFIG = None

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("wikirag.core")

# === Importaciones de Módulos Principales ===
try:
    from .intent_classifier import (
        IntentClassifier,
        Intent,
        ActionType,
        SystemCommand,
        ClassificationResult,
        get_intent_classifier
    )
    logger.debug("✅ IntentClassifier importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar IntentClassifier: {e}")
    IntentClassifier = None

try:
    from .smart_router import (
        SmartRouter,
        RouteResult,
        should_bypass_rag,
        detect_explicit_path,
        get_smart_router
    )
    logger.debug("✅ SmartRouter importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar SmartRouter: {e}")
    SmartRouter = None

try:
    from .rag_manager import RAGManager, get_rag_manager
    logger.debug("✅ RAGManager importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar RAGManager: {e}")
    RAGManager = None

try:
    from .hybrid_search import HybridSearch
    logger.debug("✅ HybridSearch importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar HybridSearch: {e}")
    HybridSearch = None

try:
    from .orchestrator import Orchestrator, get_orchestrator
    logger.debug("✅ Orchestrator importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar Orchestrator: {e}")
    Orchestrator = None

try:
    from .evaluator import Evaluator, get_evaluator
    logger.debug("✅ Evaluator importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar Evaluator: {e}")
    Evaluator = None

try:
    from .daemon_interface import DaemonInterface, get_daemon_interface
    logger.debug("✅ DaemonInterface importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar DaemonInterface: {e}")
    DaemonInterface = None

try:
    from .tool_decider import ToolDecider, DirectOrder, get_tool_decider
    logger.debug("✅ ToolDecider importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar ToolDecider: {e}")
    ToolDecider = None

try:
    from .memory import Memory, get_memory
    logger.debug("✅ Memory importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar Memory: {e}")
    Memory = None

try:
    from .shared_state import SharedState, get_shared_state
    logger.debug("✅ SharedState importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar SharedState: {e}")
    SharedState = None

try:
    from .queue_manager import QueueManager
    logger.debug("✅ QueueManager importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar QueueManager: {e}")
    QueueManager = None

try:
    from .prompts import SYSTEM_PROMPTS, get_prompt
    logger.debug("✅ Prompts importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar Prompts: {e}")
    SYSTEM_PROMPTS = {}

try:
    from .mental_theater import MentalTheater
    logger.debug("✅ MentalTheater importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar MentalTheater: {e}")
    MentalTheater = None

try:
    from .streaming import StreamingLLM
    logger.debug("✅ StreamingLLM importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar StreamingLLM: {e}")
    StreamingLLM = None

try:
    from .reranker import Reranker
    logger.debug("✅ Reranker importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar Reranker: {e}")
    Reranker = None

try:
    from .self_rag import SelfRAG
    logger.debug("✅ SelfRAG importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar SelfRAG: {e}")
    SelfRAG = None

try:
    from .crag import CRAG
    logger.debug("✅ CRAG importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar CRAG: {e}")
    CRAG = None

try:
    from .query_decomposer import QueryDecomposer
    logger.debug("✅ QueryDecomposer importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar QueryDecomposer: {e}")
    QueryDecomposer = None

try:
    from .prompt_cache import PromptCache
    logger.debug("✅ PromptCache importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar PromptCache: {e}")
    PromptCache = None

try:
    from .critic import Critic
    logger.debug("✅ Critic importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar Critic: {e}")
    Critic = None

try:
    from .query_refiner import QueryRefiner
    logger.debug("✅ QueryRefiner importado")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo importar QueryRefiner: {e}")
    QueryRefiner = None


# === Exportar API Pública ===
__all__ = [
    # Configuración
    'CONFIG',
    'get_config',
    'get_portable_path',
    'PortableConfig',

    # Clasificación y Enrutamiento
    'IntentClassifier',
    'Intent',
    'ActionType',
    'SystemCommand',
    'ClassificationResult',
    'get_intent_classifier',
    'SmartRouter',
    'RouteResult',
    'should_bypass_rag',
    'detect_explicit_path',
    'get_smart_router',

    # RAG y Búsqueda
    'RAGManager',
    'get_rag_manager',
    'HybridSearch',
    'Reranker',
    'SelfRAG',
    'CRAG',

    # Orquestación
    'Orchestrator',
    'get_orchestrator',
    'Evaluator',
    'get_evaluator',
    'DaemonInterface',
    'get_daemon_interface',

    # Toma de Decisiones
    'ToolDecider',
    'DirectOrder',
    'get_tool_decider',

    # Estado y Memoria
    'Memory',
    'get_memory',
    'SharedState',
    'get_shared_state',
    'QueueManager',
    'PromptCache',

    # Procesamiento de Queries
    'QueryDecomposer',
    'QueryRefiner',

    # LLM y Generación
    'StreamingLLM',
    'MentalTheater',
    'Critic',

    # Prompts
    'SYSTEM_PROMPTS',
    'get_prompt',
]


def initialize_core(verbose: bool = True) -> dict:
    """
    Inicializar todos los componentes del core.

    Args:
        verbose: Mostrar detalles de inicialización

    Returns:
        dict con estado de inicialización
    """
    from collections import OrderedDict

    status = OrderedDict()

    components = [
        ('Config', CONFIG is not None),
        ('IntentClassifier', IntentClassifier is not None),
        ('SmartRouter', SmartRouter is not None),
        ('RAGManager', RAGManager is not None),
        ('HybridSearch', HybridSearch is not None),
        ('Orchestrator', Orchestrator is not None),
        ('Evaluator', Evaluator is not None),
        ('DaemonInterface', DaemonInterface is not None),
        ('ToolDecider', ToolDecider is not None),
        ('Memory', Memory is not None),
        ('SharedState', SharedState is not None),
        ('QueueManager', QueueManager is not None),
        ('QueryDecomposer', QueryDecomposer is not None),
        ('QueryRefiner', QueryRefiner is not None),
        ('StreamingLLM', StreamingLLM is not None),
        ('MentalTheater', MentalTheater is not None),
        ('Reranker', Reranker is not None),
        ('SelfRAG', SelfRAG is not None),
        ('CRAG', CRAG is not None),
        ('PromptCache', PromptCache is not None),
        ('Critic', Critic is not None),
    ]

    for name, available in components:
        status[name] = '✅' if available else '⚠️'

    if verbose:
        print("\n📚 Estado de Inicialización del Core:")
        print("=" * 50)
        for name, icon in status.items():
            print(f"  {icon} {name}")
        print("=" * 50)

    return dict(status)


# Inicializar automáticamente si se ejecuta como módulo principal
if __name__ == "__main__":
    print("🚀 Inicializando WikiRAG Core D4...\n")
    initialize_core(verbose=True)
    print("\n✅ Core inicializado correctamente")
    print(f"📁 Directorio base: {CONFIG.VERSIOND4_DIR if CONFIG else 'No disponible'}")
