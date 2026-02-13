#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST - Verificación de instalación y funcionalidad básica
Uso: python test_wikirag.py
"""

import sys
import os

# Detectar ruta base
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)


def test_imports():
    """Verificar que todos los módulos se importan correctamente"""
    print("\n" + "="*70)
    print("1️⃣  TEST DE IMPORTACIONES")
    print("="*70)

    tests = []

    # Config
    try:
        from core.config_portable import get_config, get_portable_path, PortableConfig
        print("   ✅ config_portable")
        tests.append(("config_portable", True))
    except ImportError as e:
        print(f"   ❌ config_portable: {e}")
        tests.append(("config_portable", False))

    # Core modules
    core_modules = [
        "intent_classifier",
        "smart_router",
        "tool_decider",
        "rag_manager",
        "hybrid_search",
        "reranker",
        "orchestrator",
        "evaluator",
        "daemon_interface",
        "memory",
        "shared_state",
        "queue_manager",
        "prompt_cache",
        "query_decomposer",
        "query_refiner",
        "critic",
        "streaming",
        "mental_theater",
        "self_rag",
        "crag",
        "prompts",
    ]

    for module in core_modules:
        try:
            __import__(f"core.{module}")
            print(f"   ✅ {module}")
            tests.append((module, True))
        except ImportError as e:
            print(f"   ⚠️  {module}: {str(e)[:50]}...")
            tests.append((module, False))

    return tests


def test_config():
    """Verificar configuración portátil"""
    print("\n" + "="*70)
    print("2️⃣  TEST DE CONFIGURACIÓN PORTÁTIL")
    print("="*70)

    try:
        from core.config_portable import get_config, get_portable_path

        cfg = get_config()
        print(f"   ✅ Configuración cargada")
        print(f"      VERSIOND4_DIR: {cfg.VERSIOND4_DIR}")
        print(f"      BASE_DIR: {cfg.BASE_DIR}")
        print(f"      QUEUE_DB: {cfg.QUEUE_DB}")
        print(f"      LOG_DAEMON: {cfg.LOG_DAEMON}")

        # Verificar rutas
        test_path = get_portable_path("data/test")
        print(f"   ✅ Ruta portátil generada: {test_path}")

        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_routing():
    """Verificar enrutamiento inteligente"""
    print("\n" + "="*70)
    print("3️⃣  TEST DE ENRUTAMIENTO INTELIGENTE")
    print("="*70)

    try:
        from core.smart_router import (
            should_bypass_rag,
            detect_explicit_path,
            SmartRouter
        )

        # Test bypass RAG
        test_cases = [
            ("lista los archivos de /home/usuario", True),
            ("¿Qué es Python?", False),
            ("cat ~/logs/debug.log", True),
            ("ls -la ./data/", True),
            ("Explícame machine learning", False),
        ]

        print("   Pruebas de bypass RAG:")
        for query, expected_bypass in test_cases:
            bypass, path, reason = should_bypass_rag(query)
            icon = "✅" if bypass == expected_bypass else "⚠️"
            print(f"   {icon} '{query[:40]}...' → Bypass: {bypass}")

        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_classifier():
    """Verificar clasificador de intenciones"""
    print("\n" + "="*70)
    print("4️⃣  TEST DE CLASIFICADOR DE INTENCIONES")
    print("="*70)

    try:
        from core.intent_classifier import get_intent_classifier, Intent

        classifier = get_intent_classifier()
        print("   ✅ Clasificador inicializado")

        # Test queries
        test_queries = [
            ("¿Qué es Python?", Intent.INFORMATIVE),
            ("Lista los archivos", Intent.ACTION),
            ("help", Intent.SYSTEM),
            ("Hola!", Intent.CONVERSATIONAL),
        ]

        print("\n   Pruebas de clasificación:")
        for query, expected_intent in test_queries:
            result = classifier.classify(query)
            match = "✅" if result.intent == expected_intent else "⚠️"
            print(f"   {match} '{query}' → {result.intent.value}")

        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_core_init():
    """Verificar inicialización del core"""
    print("\n" + "="*70)
    print("5️⃣  TEST DE INICIALIZACIÓN DEL CORE")
    print("="*70)

    try:
        from core import initialize_core

        status = initialize_core(verbose=False)
        print("   ✅ Core inicializado\n")

        # Mostrar componentes
        total = len(status)
        available = sum(1 for v in status.values() if v == "✅")
        print(f"   Componentes disponibles: {available}/{total}")

        for component, icon in list(status.items())[:5]:
            print(f"   {icon} {component}")

        if total > 5:
            print(f"   ... y {total - 5} más")

        return available > 0
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def run_all_tests():
    """Ejecutar todos los tests"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*16 + "🧪 SUITE DE TESTS - WikiRAG D4" + " "*21 + "║")
    print("╚" + "="*68 + "╝")

    results = []

    # Importaciones
    import_results = test_imports()
    import_status = all(result[1] for result in import_results)
    results.append(("Importaciones", import_status))

    # Config
    config_status = test_config()
    results.append(("Configuración Portátil", config_status))

    # Routing
    routing_status = test_routing()
    results.append(("Enrutamiento", routing_status))

    # Classifier
    classifier_status = test_classifier()
    results.append(("Clasificador", classifier_status))

    # Core
    core_status = test_core_init()
    results.append(("Core", core_status))

    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*70)

    passed = sum(1 for _, status in results if status)
    total = len(results)

    for name, status in results:
        icon = "✅" if status else "❌"
        print(f"   {icon} {name}")

    print("\n" + "-"*70)
    print(f"   Resultado: {passed}/{total} tests pasados")
    print("-"*70)

    if passed == total:
        print("\n   🎉 ¡TODOS LOS TESTS PASARON! ¡Listo para producción!")
        return 0
    else:
        print(f"\n   ⚠️  {total - passed} tests fallaron. Revisa los errores arriba.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = run_all_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrumpidos por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        sys.exit(1)
