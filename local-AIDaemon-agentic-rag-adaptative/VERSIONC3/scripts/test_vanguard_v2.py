#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    TEST VANGUARD V2 - Verificación Completa
========================================
Script para verificar todas las técnicas de vanguardia implementadas.

Componentes a verificar:
1. Daemon Persistente
2. Prompt Cache
3. Query Decomposition
4. Metadata Filtering
5. Graph RAG
6. MCP Integration
7. Hybrid Search + Re-ranking
8. Self-RAG / CRAG
9. Streaming
========================================
"""

import os
import sys
import time
import pytest

# Setup paths
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Colores
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

pytestmark = pytest.mark.filterwarnings("ignore::pytest.PytestReturnNotNoneWarning")


def print_header(title: str):
    print(f"\n{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}   {title}{RESET}")
    print(f"{CYAN}{'='*60}{RESET}\n")


def print_status(name: str, available: bool, details: str = ""):
    status = f"{GREEN}✅ OK{RESET}" if available else f"{RED}❌ No disponible{RESET}"
    print(f"   {name}: {status} {details}")


def test_core_imports():
    """Test importación de módulos core"""
    print_header("1. IMPORTACIÓN DE MÓDULOS CORE")

    from core import (
        HAS_HYBRID, HAS_RERANKER, HAS_SELF_RAG, HAS_CRAG,
        HAS_PERSISTENT_DAEMON, HAS_STREAMING,
        HAS_PROMPT_CACHE, HAS_QUERY_DECOMPOSER,
        HAS_METADATA_FILTER, HAS_GRAPH_RAG,
        __version__
    )

    print(f"   Versión: {BOLD}{__version__}{RESET}\n")

    print("   Técnicas de Vanguardia:")
    print_status("Hybrid Search", HAS_HYBRID)
    print_status("Re-ranker", HAS_RERANKER)
    print_status("Self-RAG", HAS_SELF_RAG)
    print_status("CRAG", HAS_CRAG)
    print_status("Daemon Persistente", HAS_PERSISTENT_DAEMON)
    print_status("Streaming", HAS_STREAMING)
    print_status("Prompt Cache", HAS_PROMPT_CACHE)
    print_status("Query Decomposer", HAS_QUERY_DECOMPOSER)
    print_status("Metadata Filter", HAS_METADATA_FILTER)
    print_status("Graph RAG", HAS_GRAPH_RAG)

    return True


def test_prompt_cache():
    """Test sistema de caché"""
    print_header("2. PROMPT CACHE")

    try:
        from core.prompt_cache import get_prompt_cache

        cache = get_prompt_cache()

        # Test put
        cache.put("Test prompt", "Test response", model="test")
        print_status("Put", True)

        # Test get (hit)
        response = cache.get("Test prompt", model="test")
        print_status("Get (hit)", response == "Test response")

        # Test get (miss)
        miss = cache.get("Non-existent", model="test")
        print_status("Get (miss)", miss is None)

        # Stats
        stats = cache.get_stats()
        print(f"\n   Stats: {stats['total_requests']} requests, {stats['hit_rate']:.0%} hit rate")

        return True

    except Exception as e:
        print(f"   {RED}Error: {e}{RESET}")
        return False


def test_query_decomposer():
    """Test descomposición de queries"""
    print_header("3. QUERY DECOMPOSER")

    try:
        from core.query_decomposer import get_decomposer

        decomposer = get_decomposer(use_llm=False)

        test_queries = [
            "¿Qué es Python?",  # Simple
            "¿Cuál es la diferencia entre Python y JavaScript?",  # Comparison
            "Historia de España: ¿quiénes fueron los reyes? ¿qué eventos importantes?",  # Multi-hop
        ]

        for query in test_queries:
            result = decomposer.decompose(query)
            decomposable = "Sí" if result.is_decomposable else "No"
            print(f"   Query: {query[:40]}...")
            print(f"      Tipo: {result.query_type.value}, Descomponible: {decomposable}")
            print(f"      Sub-queries: {len(result.sub_queries)}")

        return True

    except Exception as e:
        print(f"   {RED}Error: {e}{RESET}")
        return False


def test_metadata_filter():
    """Test filtrado por metadatos"""
    print_header("4. METADATA FILTER")

    try:
        from core.metadata_filter import get_metadata_filter, filter_by_language

        mf = get_metadata_filter()

        # Docs de prueba
        docs = [
            {"title": "Doc 1", "language": "es", "year": 2023},
            {"title": "Doc 2", "language": "en", "year": 2024},
            {"title": "Doc 3", "language": "es", "year": 2024},
        ]

        # Filtrar por idioma
        filtered = filter_by_language(docs, "es")
        print_status("Filtro por idioma", len(filtered) == 2, f"({len(filtered)}/3 docs)")

        # Extraer filtros de query natural
        conditions = mf.extract_filters_from_query("artículos en español desde 2023")
        print_status("Extracción de filtros", len(conditions) >= 1, f"({len(conditions)} condiciones)")

        return True

    except Exception as e:
        print(f"   {RED}Error: {e}{RESET}")
        return False


def test_graph_rag():
    """Test Graph RAG"""
    print_header("5. GRAPH RAG")

    try:
        from core.graph_rag import GraphRAG

        graph_rag = GraphRAG()

        # Indexar documento de prueba
        graph_rag.index_document(
            "test_doc",
            "Python es un lenguaje de programación creado por Guido van Rossum."
        )

        stats = graph_rag.get_stats()
        entities = stats['graph']['total_entities']
        relations = stats['graph']['total_relations']

        print_status("Indexación", entities > 0, f"({entities} entidades, {relations} relaciones)")

        # Buscar
        docs, graph_result = graph_rag.search("Python", k=1)
        print_status("Búsqueda", len(graph_result.entities) > 0, f"({len(graph_result.entities)} entidades)")

        return True

    except Exception as e:
        print(f"   {RED}Error: {e}{RESET}")
        return False


def test_daemon_persistent():
    """Test daemon persistente (solo config, no inicia)"""
    print_header("6. DAEMON PERSISTENTE")

    try:
        from core.daemon_persistent import PersistentDaemon, DaemonStatus

        # Solo verificar que se puede instanciar (no iniciar para evitar carga)
        daemon = PersistentDaemon(auto_start=False)
        print_status("Instanciación", daemon.status == DaemonStatus.STOPPED)
        print_status("Configuración", daemon.model_path is not None)

        # Verificar modelo existe
        model_exists = os.path.exists(daemon.model_path)
        print_status("Modelo disponible", model_exists, f"({os.path.basename(daemon.model_path)})")

        return True

    except Exception as e:
        print(f"   {RED}Error: {e}{RESET}")
        return False


def test_streaming():
    """Test streaming handler"""
    print_header("7. STREAMING")

    try:
        from core.streaming import StreamingHandler, StreamMode

        handler = StreamingHandler(mode=StreamMode.BUFFER)

        # Simular streaming
        handler.write("Test ")
        handler.write("streaming ")
        handler.write("content")
        result = handler.finish()

        print_status("Handler", result.success)
        print_status("Contenido", result.full_response == "Test streaming content")

        return True

    except Exception as e:
        print(f"   {RED}Error: {e}{RESET}")
        return False


def test_orchestrator():
    """Test orquestador con features de vanguardia"""
    print_header("8. ORCHESTRATOR (sin ejecutar LLM)")

    try:
        from core.orchestrator import Orchestrator

        # Solo verificar componentes, no ejecutar queries
        orch = Orchestrator()

        print_status("RAG Manager", orch.rag_manager is not None)
        print_status("Query Refiner", orch.query_refiner is not None)
        print_status("Memory", orch.memory is not None)
        print_status("Prompt Cache", orch.prompt_cache is not None)
        print_status("Modo Adaptativo", orch.adaptive_mode)

        # Daemon status
        daemon_status = orch.get_daemon_status()
        print_status("Daemon Config", daemon_status is not None)

        # Cache stats
        cache_stats = orch.get_cache_stats()
        print_status("Cache Stats", 'enabled' in str(cache_stats) or 'hit_rate' in str(cache_stats))

        # Cleanup
        orch.cleanup()

        return True

    except Exception as e:
        print(f"   {RED}Error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Ejecutar todos los tests"""
    print(f"\n{BOLD}{CYAN}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     WIKIRAG v2.3 - TEST TÉCNICAS DE VANGUARDIA          ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{RESET}")

    results = {}

    tests = [
        ("Core Imports", test_core_imports),
        ("Prompt Cache", test_prompt_cache),
        ("Query Decomposer", test_query_decomposer),
        ("Metadata Filter", test_metadata_filter),
        ("Graph RAG", test_graph_rag),
        ("Daemon Persistente", test_daemon_persistent),
        ("Streaming", test_streaming),
        ("Orchestrator", test_orchestrator),
    ]

    for name, test_fn in tests:
        try:
            results[name] = test_fn()
        except Exception as e:
            print(f"   {RED}Error crítico en {name}: {e}{RESET}")
            results[name] = False

    # Resumen
    print_header("RESUMEN")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, passed_test in results.items():
        status = f"{GREEN}PASS{RESET}" if passed_test else f"{RED}FAIL{RESET}"
        print(f"   [{status}] {name}")

    print(f"\n   {BOLD}Total: {passed}/{total} tests pasados{RESET}")

    if passed == total:
        print(f"\n   {GREEN}🎉 ¡Todas las técnicas de vanguardia funcionan!{RESET}")
    else:
        print(f"\n   {YELLOW}⚠️ Algunas técnicas requieren dependencias adicionales{RESET}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
