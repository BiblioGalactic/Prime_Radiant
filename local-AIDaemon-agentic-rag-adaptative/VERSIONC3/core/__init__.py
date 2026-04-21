#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core - Núcleo del Sistema de IA con Agentes y RAGs
"""

import os
import sys

# Setup paths
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config import Config, config
from core.queue_manager import QueueManager, QueueMessage, Priority
from core.daemon_interface import DaemonInterface, DaemonCLI
from core.evaluator import ResponseEvaluator, HeuristicEvaluator, Verdict, create_evaluator
from core.shared_state import SharedState, get_shared_state

RAGManager = None
try:
    from core.rag_manager import RAGManager
except (ImportError, NameError, Exception):
    pass

# === Vanguardia 2024-2025 ===
# Imports opcionales - no fallan si dependencias no están instaladas
HAS_HYBRID = False
HAS_RERANKER = False
HAS_SELF_RAG = False
HAS_CRAG = False

HybridSearchEngine = None
HybridResult = None
Reranker = None
CachedReranker = None
RerankedResult = None
SelfRAG = None
SelfRAGResult = None
CorrectiveRAG = None
CRAGResult = None

try:
    from core.hybrid_search import HybridSearchEngine, HybridResult
    HAS_HYBRID = True
except (ImportError, NameError, Exception):
    pass

try:
    from core.reranker import Reranker, CachedReranker, RerankedResult
    HAS_RERANKER = True
except (ImportError, NameError, Exception):
    pass

try:
    from core.self_rag import SelfRAG, SelfRAGResult
    HAS_SELF_RAG = True
except (ImportError, NameError, Exception):
    pass

try:
    from core.crag import CorrectiveRAG, CRAGResult
    HAS_CRAG = True
except (ImportError, NameError, Exception):
    pass

# Daemon Persistente
HAS_PERSISTENT_DAEMON = False
PersistentDaemon = None
get_persistent_daemon = None

try:
    from core.daemon_persistent import PersistentDaemon, get_persistent_daemon, DaemonStatus
    HAS_PERSISTENT_DAEMON = True
except (ImportError, NameError, Exception):
    pass

# Streaming
HAS_STREAMING = False
StreamingHandler = None

try:
    from core.streaming import StreamingHandler, StreamMode, StreamResult
    HAS_STREAMING = True
except (ImportError, NameError, Exception):
    pass

# Prompt Cache
HAS_PROMPT_CACHE = False
HybridPromptCache = None
get_prompt_cache = None

try:
    from core.prompt_cache import HybridPromptCache, get_prompt_cache
    HAS_PROMPT_CACHE = True
except (ImportError, NameError, Exception):
    pass

# Query Decomposer
HAS_QUERY_DECOMPOSER = False
QueryDecomposer = None
get_decomposer = None

try:
    from core.query_decomposer import QueryDecomposer, get_decomposer, DecomposedQuery
    HAS_QUERY_DECOMPOSER = True
except (ImportError, NameError, Exception):
    pass

# Metadata Filter
HAS_METADATA_FILTER = False
MetadataFilter = None
get_metadata_filter = None

try:
    from core.metadata_filter import MetadataFilter, get_metadata_filter, FilterCondition
    HAS_METADATA_FILTER = True
except (ImportError, NameError, Exception):
    pass

# Graph RAG
HAS_GRAPH_RAG = False
GraphRAG = None
KnowledgeGraph = None
get_graph_rag = None

try:
    from core.graph_rag import GraphRAG, KnowledgeGraph, get_graph_rag, Entity, Relation
    HAS_GRAPH_RAG = True
except (ImportError, NameError, Exception):
    pass

__all__ = [
    'Config', 'config',
    'QueueManager', 'QueueMessage', 'Priority',
    'DaemonInterface', 'DaemonCLI',
    'RAGManager',
    'ResponseEvaluator', 'HeuristicEvaluator', 'Verdict', 'create_evaluator',
    'SharedState', 'get_shared_state',
    # Vanguardia
    'HybridSearchEngine', 'HybridResult',
    'Reranker', 'CachedReranker', 'RerankedResult',
    'SelfRAG', 'SelfRAGResult',
    'CorrectiveRAG', 'CRAGResult',
    # Daemon Persistente
    'PersistentDaemon', 'get_persistent_daemon',
    # Streaming
    'StreamingHandler',
    # Prompt Cache
    'HybridPromptCache', 'get_prompt_cache',
    # Query Decomposer
    'QueryDecomposer', 'get_decomposer',
    # Metadata Filter
    'MetadataFilter', 'get_metadata_filter',
    # Graph RAG
    'GraphRAG', 'KnowledgeGraph', 'get_graph_rag',
    # Flags
    'HAS_HYBRID', 'HAS_RERANKER', 'HAS_SELF_RAG', 'HAS_CRAG',
    'HAS_PERSISTENT_DAEMON', 'HAS_STREAMING',
    'HAS_PROMPT_CACHE', 'HAS_QUERY_DECOMPOSER', 'HAS_METADATA_FILTER', 'HAS_GRAPH_RAG'
]
__version__ = '2.3.0'  # Técnicas de vanguardia completas
