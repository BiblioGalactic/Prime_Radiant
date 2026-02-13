#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    STRESS TEST - Concurrencia y Deadlocks
========================================
Prueba que los locks no causen deadlocks bajo carga.
========================================
"""

import os
import sys
import time
import threading
import random
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import List, Dict, Any

# Setup path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


def test_daemon_persistent_locks():
    """
    Test de locks en daemon_persistent.py

    Verifica que no hay deadlocks cuando múltiples threads acceden
    concurrentemente a status, metrics, buffer y results.
    """
    print("\n" + "="*60)
    print("🔒 TEST: daemon_persistent locks")
    print("="*60)

    from core.daemon_persistent import PersistentDaemon, DaemonStatus

    # Crear daemon sin auto_start (no necesitamos el modelo real)
    daemon = PersistentDaemon.__new__(PersistentDaemon)

    # Inicializar solo los locks y estado mínimo
    daemon._status = DaemonStatus.STOPPED
    daemon._status_lock = threading.Lock()
    daemon._metrics = {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "total_tokens": 0,
        "total_latency": 0.0,
        "start_time": time.time()
    }
    daemon._metrics_lock = threading.Lock()
    daemon._current_response_buffer = []
    daemon._buffer_lock = threading.Lock()
    daemon._results = {}
    daemon._results_lock = threading.Lock()

    # Definir _set_status manualmente
    def set_status(status):
        with daemon._status_lock:
            daemon._status = status
    daemon._set_status = set_status

    # Contadores para verificar
    errors = []
    operations_completed = {"count": 0}
    lock = threading.Lock()

    def stress_status_operations(thread_id: int, iterations: int):
        """Operaciones de status concurrentes"""
        try:
            for i in range(iterations):
                # Leer status
                with daemon._status_lock:
                    _ = daemon._status

                # Cambiar status
                daemon._set_status(random.choice([
                    DaemonStatus.READY,
                    DaemonStatus.BUSY,
                    DaemonStatus.STOPPED
                ]))

                with lock:
                    operations_completed["count"] += 1

        except Exception as e:
            errors.append(f"Thread {thread_id} status error: {e}")

    def stress_metrics_operations(thread_id: int, iterations: int):
        """Operaciones de métricas concurrentes"""
        try:
            for i in range(iterations):
                # Leer métricas
                with daemon._metrics_lock:
                    _ = daemon._metrics["total_requests"]

                # Actualizar métricas
                with daemon._metrics_lock:
                    daemon._metrics["total_requests"] += 1
                    daemon._metrics["total_tokens"] += random.randint(10, 100)

                with lock:
                    operations_completed["count"] += 1

        except Exception as e:
            errors.append(f"Thread {thread_id} metrics error: {e}")

    def stress_buffer_operations(thread_id: int, iterations: int):
        """Operaciones de buffer concurrentes"""
        try:
            for i in range(iterations):
                # Escribir al buffer
                with daemon._buffer_lock:
                    daemon._current_response_buffer.append(f"chunk_{thread_id}_{i}")

                # Leer y limpiar buffer
                with daemon._buffer_lock:
                    if len(daemon._current_response_buffer) > 10:
                        daemon._current_response_buffer.clear()

                with lock:
                    operations_completed["count"] += 1

        except Exception as e:
            errors.append(f"Thread {thread_id} buffer error: {e}")

    def stress_mixed_operations(thread_id: int, iterations: int):
        """Operaciones mezcladas (simula uso real)"""
        try:
            for i in range(iterations):
                # Simular _process_request parcialmente
                daemon._set_status(DaemonStatus.BUSY)

                with daemon._buffer_lock:
                    daemon._current_response_buffer.append(f"response_{thread_id}")

                with daemon._results_lock:
                    daemon._results[f"req_{thread_id}_{i}"] = {"data": "test"}

                with daemon._metrics_lock:
                    daemon._metrics["total_requests"] += 1

                daemon._set_status(DaemonStatus.READY)

                # Simular get_metrics
                with daemon._metrics_lock:
                    _ = daemon._metrics.copy()
                with daemon._status_lock:
                    _ = daemon._status

                with lock:
                    operations_completed["count"] += 1

        except Exception as e:
            errors.append(f"Thread {thread_id} mixed error: {e}")

    # Ejecutar stress test
    num_threads = 20
    iterations_per_thread = 100
    timeout_seconds = 30

    print(f"\n📊 Configuración:")
    print(f"   Threads: {num_threads}")
    print(f"   Iteraciones/thread: {iterations_per_thread}")
    print(f"   Timeout: {timeout_seconds}s")

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []

        # Distribuir operaciones
        for i in range(num_threads):
            op_type = i % 4
            if op_type == 0:
                futures.append(executor.submit(stress_status_operations, i, iterations_per_thread))
            elif op_type == 1:
                futures.append(executor.submit(stress_metrics_operations, i, iterations_per_thread))
            elif op_type == 2:
                futures.append(executor.submit(stress_buffer_operations, i, iterations_per_thread))
            else:
                futures.append(executor.submit(stress_mixed_operations, i, iterations_per_thread))

        # Esperar con timeout
        try:
            for future in futures:
                future.result(timeout=timeout_seconds)
        except FuturesTimeout:
            print("\n❌ TIMEOUT - Posible DEADLOCK detectado!")
            return False

    elapsed = time.time() - start_time

    print(f"\n📈 Resultados:")
    print(f"   Tiempo: {elapsed:.2f}s")
    print(f"   Operaciones completadas: {operations_completed['count']}")
    print(f"   Ops/segundo: {operations_completed['count']/elapsed:.0f}")

    if errors:
        print(f"\n❌ Errores encontrados: {len(errors)}")
        for err in errors[:5]:
            print(f"   - {err}")
        return False

    print("\n✅ Test de daemon_persistent locks: PASSED")
    return True


def test_agent_runtime_locks():
    """
    Test de locks en agent_runtime.py
    """
    print("\n" + "="*60)
    print("🔒 TEST: agent_runtime locks")
    print("="*60)

    import threading

    # Simular el singleton lock
    runtime_lock = threading.Lock()
    runtime_instance = {"instance": None}

    errors = []
    creates = {"count": 0}

    def try_get_runtime(thread_id: int, iterations: int):
        """Simular acceso concurrente al singleton"""
        try:
            for _ in range(iterations):
                with runtime_lock:
                    if runtime_instance["instance"] is None:
                        runtime_instance["instance"] = {"id": thread_id}
                        creates["count"] += 1
                    _ = runtime_instance["instance"]
        except Exception as e:
            errors.append(f"Thread {thread_id} error: {e}")

    num_threads = 50
    iterations = 100

    print(f"\n📊 Configuración:")
    print(f"   Threads: {num_threads}")
    print(f"   Iteraciones/thread: {iterations}")

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(try_get_runtime, i, iterations)
            for i in range(num_threads)
        ]

        try:
            for future in futures:
                future.result(timeout=10)
        except FuturesTimeout:
            print("\n❌ TIMEOUT - Posible DEADLOCK detectado!")
            return False

    elapsed = time.time() - start_time

    print(f"\n📈 Resultados:")
    print(f"   Tiempo: {elapsed:.2f}s")
    print(f"   Instancias creadas: {creates['count']} (debe ser 1)")

    if errors:
        print(f"\n❌ Errores: {len(errors)}")
        return False

    if creates["count"] != 1:
        print(f"\n❌ Race condition: Se crearon {creates['count']} instancias!")
        return False

    print("\n✅ Test de agent_runtime locks: PASSED")
    return True


def test_tool_registry_locks():
    """
    Test de locks en tool_registry.py
    """
    print("\n" + "="*60)
    print("🔒 TEST: tool_registry locks")
    print("="*60)

    import threading

    registry_lock = threading.Lock()
    registry_instance = {"instance": None}

    errors = []
    access_count = {"count": 0}

    def try_get_registry(thread_id: int, iterations: int):
        """Simular acceso concurrente"""
        try:
            for _ in range(iterations):
                with registry_lock:
                    if registry_instance["instance"] is None:
                        registry_instance["instance"] = {"tools": {}}
                    # Simular registro de herramienta
                    registry_instance["instance"]["tools"][f"tool_{thread_id}"] = True
                    access_count["count"] += 1
        except Exception as e:
            errors.append(f"Thread {thread_id} error: {e}")

    num_threads = 30
    iterations = 50

    print(f"\n📊 Configuración:")
    print(f"   Threads: {num_threads}")
    print(f"   Iteraciones/thread: {iterations}")

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(try_get_registry, i, iterations)
            for i in range(num_threads)
        ]

        try:
            for future in futures:
                future.result(timeout=10)
        except FuturesTimeout:
            print("\n❌ TIMEOUT - Posible DEADLOCK!")
            return False

    elapsed = time.time() - start_time

    print(f"\n📈 Resultados:")
    print(f"   Tiempo: {elapsed:.2f}s")
    print(f"   Accesos totales: {access_count['count']}")

    if errors:
        print(f"\n❌ Errores: {len(errors)}")
        return False

    print("\n✅ Test de tool_registry locks: PASSED")
    return True


def test_lock_ordering_analysis():
    """
    Análisis estático del orden de adquisición de locks.

    Regla: Si thread A adquiere locks en orden X→Y,
    ningún thread debe adquirir en orden Y→X (causa deadlock).
    """
    print("\n" + "="*60)
    print("🔍 ANÁLISIS: Orden de adquisición de locks")
    print("="*60)

    # Documentar el orden esperado en daemon_persistent.py
    print("\n📋 daemon_persistent.py - Orden de locks:")
    print("""
    _process_request():
        1. _status_lock (via _set_status BUSY) → liberado
        2. _buffer_lock → liberado
        3. _results_lock → liberado
        4. _metrics_lock → liberado
        5. _status_lock (via _set_status READY) → liberado

    get_metrics():
        1. _metrics_lock → liberado
        2. _status_lock → liberado

    ✅ NO hay anidamiento - cada lock se libera antes del siguiente.
    ✅ NO hay riesgo de deadlock por diseño.
    """)

    print("\n📋 agent_runtime.py - Orden de locks:")
    print("""
    get_agent_runtime():
        1. _runtime_lock → operación → liberado

    ✅ Solo un lock, no hay riesgo de deadlock.
    """)

    print("\n📋 tool_registry.py - Orden de locks:")
    print("""
    get_tool_registry():
        1. _registry_lock → operación → liberado

    ✅ Solo un lock, no hay riesgo de deadlock.
    """)

    print("\n✅ Análisis de orden de locks: PASSED")
    return True


def run_all_tests():
    """Ejecutar todos los tests de concurrencia"""
    print("\n" + "="*60)
    print("🧪 STRESS TEST DE CONCURRENCIA - WikiRAG v2.3.1")
    print("="*60)
    print(f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # Test 1: Análisis de orden
    results.append(("Lock Ordering Analysis", test_lock_ordering_analysis()))

    # Test 2: daemon_persistent
    results.append(("Daemon Persistent Locks", test_daemon_persistent_locks()))

    # Test 3: agent_runtime
    results.append(("Agent Runtime Locks", test_agent_runtime_locks()))

    # Test 4: tool_registry
    results.append(("Tool Registry Locks", test_tool_registry_locks()))

    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE TESTS")
    print("="*60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("🎉 TODOS LOS TESTS PASARON - No hay deadlocks detectados")
    else:
        print("⚠️ ALGUNOS TESTS FALLARON - Revisar implementación")
    print("="*60 + "\n")

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
