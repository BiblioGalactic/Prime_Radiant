#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
WikiRAG D4
========================================
Sistema inteligente de Recuperación Aumentada por Generación

Versión: 1.0.0 (D4 Release)
Estado: Producción
Portable: ✅ Sí

Uso como módulo:
    from VERSIOND4 import WikiRAGD4
    wikirag = WikiRAGD4()
    response = wikirag.query("tu consulta")

Uso como CLI:
    python -m VERSIOND4
    python main.py
"""

__version__ = "1.0.0"
__release__ = "D4"
__author__ = "WikiRAG Team"
__license__ = "MIT"

# Importar API pública
from core import (
    CONFIG,
    get_config,
    get_portable_path,
    IntentClassifier,
    Intent,
    ActionType,
    SmartRouter,
    RouteResult,
    RAGManager,
    Orchestrator,
    ToolDecider,
    DirectOrder,
    Memory,
    SharedState,
    initialize_core,
)

# Clase de conveniencia
class WikiRAGD4:
    """Interfaz simplificada para WikiRAG D4"""

    def __init__(self, verbose: bool = False):
        """Inicializar WikiRAG D4"""
        self.verbose = verbose
        self.router = SmartRouter(verbose=verbose) if SmartRouter else None
        self.classifier = IntentClassifier() if IntentClassifier else None

    def query(self, query: str, context: str = "") -> str:
        """Procesar una consulta"""
        if not self.router:
            raise RuntimeError("Router no inicializado")
        result = self.router.route(query, context)
        return result.response

    def classify(self, query: str):
        """Clasificar una consulta"""
        if not self.classifier:
            raise RuntimeError("Classifier no inicializado")
        return self.classifier.classify(query)


__all__ = [
    # Versión
    "__version__",
    "__release__",

    # Configuración
    "CONFIG",
    "get_config",
    "get_portable_path",

    # Clasificación
    "IntentClassifier",
    "Intent",
    "ActionType",

    # Enrutamiento
    "SmartRouter",
    "RouteResult",

    # RAG
    "RAGManager",

    # Orquestación
    "Orchestrator",

    # Toma de decisiones
    "ToolDecider",
    "DirectOrder",

    # Estado
    "Memory",
    "SharedState",

    # Utilidades
    "initialize_core",

    # Clase de conveniencia
    "WikiRAGD4",
]


if __name__ == "__main__":
    print(f"🤖 WikiRAG {__release__} v{__version__}")
    print(f"Ubicación: {CONFIG.VERSIOND4_DIR if CONFIG else 'No disponible'}")
    print("\nPara usar como CLI:")
    print("  python main.py")
    print("\nPara usar como módulo:")
    print("  from VERSIOND4 import WikiRAGD4")
    print("  wikirag = WikiRAGD4()")
    print("  response = wikirag.query('tu consulta')")
