#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    DIAGNÓSTICO DE MEMORIA - WikiRAG
========================================
Script para identificar y reportar uso de memoria.
Ejecutar ANTES de iniciar el orchestrator para ver baseline.
"""

import os
import sys
import gc
import psutil

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


def get_memory_mb():
    """Obtener memoria usada por este proceso en MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def get_system_memory():
    """Obtener estado de memoria del sistema"""
    mem = psutil.virtual_memory()
    return {
        'total_gb': mem.total / (1024**3),
        'available_gb': mem.available / (1024**3),
        'used_gb': mem.used / (1024**3),
        'percent': mem.percent
    }


def print_header(title: str):
    print(f"\n{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}   {title}{RESET}")
    print(f"{CYAN}{'='*60}{RESET}\n")


def print_memory_status(label: str, before_mb: float = None):
    """Imprimir estado de memoria"""
    current = get_memory_mb()
    sys_mem = get_system_memory()

    if before_mb:
        delta = current - before_mb
        delta_str = f" ({'+' if delta > 0 else ''}{delta:.1f} MB)"
    else:
        delta_str = ""

    print(f"   {label}: {current:.1f} MB{delta_str}")
    print(f"   Sistema: {sys_mem['used_gb']:.1f}/{sys_mem['total_gb']:.1f} GB ({sys_mem['percent']}%)")
    return current


def test_imports():
    """Probar imports y medir memoria"""
    print_header("1. IMPORTS BÁSICOS")

    mem_start = get_memory_mb()
    print_memory_status("Inicio")

    # Core config
    print("\n   Importando core.config...")
    from core.config import config
    mem_after_config = print_memory_status("Después de config", mem_start)

    # Sentence transformers (pesado)
    print("\n   Importando sentence_transformers...")
    from sentence_transformers import SentenceTransformer
    mem_after_st = print_memory_status("Después de SentenceTransformer", mem_after_config)

    # FAISS
    print("\n   Importando faiss...")
    import faiss
    mem_after_faiss = print_memory_status("Después de FAISS", mem_after_st)

    return mem_after_faiss


def test_rag_loading():
    """Probar carga de RAGs"""
    print_header("2. CARGA DE RAGs")

    mem_start = get_memory_mb()
    print_memory_status("Antes de RAGManager")

    from core.rag_manager import RAGManager

    manager = RAGManager()
    mem_after_init = print_memory_status("Después de RAGManager()", mem_start)

    # Inicializar RAGs
    print("\n   Inicializando RAGs por defecto...")
    manager.init_default_rags()
    mem_after_rags = print_memory_status("Después de init_default_rags()", mem_after_init)

    # Stats
    print("\n   📊 Estadísticas de RAGs:")
    for name, stats in manager.get_all_stats().items():
        print(f"      - {name}: {stats.total_documents} docs, {stats.index_size_mb:.1f} MB")

    return manager, mem_after_rags


def test_vanguard_features(manager):
    """Probar features de vanguardia"""
    print_header("3. VANGUARD FEATURES (LAZY)")

    mem_start = get_memory_mb()
    print_memory_status("Antes de vanguard features")

    # Inicializar con lazy_bm25=True (default)
    print("\n   Inicializando vanguard features (lazy_bm25=True)...")
    manager.init_vanguard_features("wikipedia", lazy_bm25=True)
    mem_after_vanguard = print_memory_status("Después de init_vanguard_features()", mem_start)

    # Verificar que BM25 NO se cargó
    if hasattr(manager, '_hybrid_engine') and manager._hybrid_engine:
        bm25_loaded = manager._hybrid_engine._bm25_loaded
        print(f"\n   BM25 cargado: {RED if bm25_loaded else GREEN}{'Sí' if bm25_loaded else 'No (lazy)'}{RESET}")
    else:
        print(f"\n   {YELLOW}Hybrid engine no disponible{RESET}")

    return mem_after_vanguard


def test_hybrid_search(manager):
    """Probar búsqueda híbrida (esto cargará BM25)"""
    print_header("4. BÚSQUEDA HÍBRIDA (carga BM25)")

    mem_start = get_memory_mb()
    print_memory_status("Antes de búsqueda híbrida")

    # Esta búsqueda cargará BM25 si es lazy
    print("\n   Ejecutando búsqueda híbrida...")
    results = manager.search_hybrid("Python programación lenguaje", k=3)
    mem_after_search = print_memory_status("Después de search_hybrid()", mem_start)

    print(f"\n   Resultados: {len(results)}")

    # Verificar que BM25 ahora está cargado
    if hasattr(manager, '_hybrid_engine') and manager._hybrid_engine:
        bm25_loaded = manager._hybrid_engine._bm25_loaded
        print(f"   BM25 cargado: {GREEN if bm25_loaded else RED}{'Sí' if bm25_loaded else 'No'}{RESET}")

    return mem_after_search


def test_daemon_persistent():
    """Probar daemon persistente (SIN iniciar)"""
    print_header("5. DAEMON PERSISTENTE (solo config)")

    mem_start = get_memory_mb()
    print_memory_status("Antes de daemon")

    try:
        from core.daemon_persistent import PersistentDaemon, DaemonStatus

        # Solo instanciar, NO iniciar
        daemon = PersistentDaemon(auto_start=False)
        mem_after_daemon = print_memory_status("Después de PersistentDaemon(auto_start=False)", mem_start)

        print(f"\n   Status: {daemon.status.value}")
        print(f"   Modelo: {os.path.basename(daemon.model_path)}")
        print(f"\n   {GREEN}✓ Daemon NO cargó modelo (auto_start=False){RESET}")

        return mem_after_daemon

    except Exception as e:
        print(f"   {RED}Error: {e}{RESET}")
        return mem_start


def run_full_diagnostic():
    """Ejecutar diagnóstico completo"""
    print(f"\n{BOLD}{CYAN}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     DIAGNÓSTICO DE MEMORIA - WikiRAG v2.3               ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{RESET}")

    # Estado inicial del sistema
    sys_mem = get_system_memory()
    print(f"   Sistema: {sys_mem['total_gb']:.1f} GB total, {sys_mem['available_gb']:.1f} GB disponible")
    print(f"   Uso actual: {sys_mem['percent']}%")

    # Ejecutar tests
    mem_after_imports = test_imports()

    gc.collect()

    manager, mem_after_rags = test_rag_loading()

    gc.collect()

    mem_after_vanguard = test_vanguard_features(manager)

    gc.collect()

    # Opcional: cargar BM25
    print(f"\n{YELLOW}   ⚠️ La siguiente prueba cargará BM25 en memoria{RESET}")
    user_input = input("   ¿Continuar con búsqueda híbrida? (s/n): ").strip().lower()

    if user_input == 's':
        mem_after_search = test_hybrid_search(manager)
        gc.collect()
    else:
        mem_after_search = mem_after_vanguard

    mem_after_daemon = test_daemon_persistent()

    # Resumen
    print_header("RESUMEN")

    total_used = get_memory_mb()
    sys_mem = get_system_memory()

    print(f"   📊 Memoria del proceso: {total_used:.1f} MB")
    print(f"   📊 Memoria del sistema: {sys_mem['used_gb']:.1f}/{sys_mem['total_gb']:.1f} GB")
    print()
    print(f"   Desglose:")
    print(f"      - Imports: {mem_after_imports:.1f} MB")
    print(f"      - RAGs: +{mem_after_rags - mem_after_imports:.1f} MB")
    print(f"      - Vanguard (lazy): +{mem_after_vanguard - mem_after_rags:.1f} MB")
    if mem_after_search > mem_after_vanguard:
        print(f"      - BM25 cargado: +{mem_after_search - mem_after_vanguard:.1f} MB")
    print(f"      - Daemon config: +{mem_after_daemon - mem_after_search:.1f} MB")

    # Recomendaciones
    print()
    if total_used > 10000:  # > 10GB
        print(f"   {RED}⚠️ Uso de memoria alto (>10GB){RESET}")
        print(f"   Recomendaciones:")
        print(f"      1. Verificar que BM25 use lazy loading")
        print(f"      2. No iniciar daemon persistente automáticamente")
        print(f"      3. Considerar reducir documentos de Wikipedia")
    elif total_used > 5000:  # > 5GB
        print(f"   {YELLOW}⚠️ Uso de memoria moderado (5-10GB){RESET}")
    else:
        print(f"   {GREEN}✅ Uso de memoria normal (<5GB){RESET}")


if __name__ == "__main__":
    run_full_diagnostic()
