#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    CONFIGURACIÓN PORTÁTIL - VERSIONA1
========================================
Configuración para versión portátil del sistema.
Editar las rutas según tu sistema.
"""

import os
from pathlib import Path

# === RUTAS BASE - EDITAR SEGÚN TU SISTEMA ===
HOME = os.path.expanduser("~")

# Ruta donde están tus modelos GGUF
MODELOS_BASE = os.path.join(HOME, "modelo/modelos_grandes")

# Ruta al ejecutable llama-cli
LLAMA_CLI = os.path.join(HOME, "modelo/llama.cpp/build/bin/llama-cli")

# Ruta base del proyecto WikiRAG
WIKIRAG_BASE = os.path.dirname(os.path.abspath(__file__))

# === CONFIGURACIÓN DE MODELOS ===
# Ajustar según los modelos que tengas disponibles

MODELOS = {
    # Modelo principal (default)
    "default": {
        "path": os.path.join(MODELOS_BASE, "M6/mistral-7b-instruct-v0.1.Q6_K.gguf"),
        "ctx_size": 4096,
        "n_predict": 1000,
        "threads": 6,
    },

    # Modelo rápido para evaluación
    "fast": {
        "path": os.path.join(MODELOS_BASE, "phi/phi-2.Q5_K_M.gguf"),
        "ctx_size": 2048,
        "n_predict": 100,
        "threads": 4,
    },

    # Modelo para código
    "code": {
        "path": os.path.join(MODELOS_BASE, "deep/deepseek-coder-6.7b-instruct.Q8_0.gguf"),
        "ctx_size": 4096,
        "n_predict": 1500,
        "threads": 6,
    },

    # Modelo grande (ÚLTIMO RECURSO)
    "giant": {
        "path": os.path.join(MODELOS_BASE, "llama31-70b/Meta-Llama-3.1-70B-Instruct-Q4_K_M.gguf"),
        "ctx_size": 4096,
        "n_predict": 500,
        "threads": 2,
        "throttle_delay": 0.1,  # 100ms entre tokens
    },
}

# === CONFIGURACIÓN DE RAGs ===
RAGS = {
    "wikipedia": {
        "enabled": True,
        "path": os.path.join(WIKIRAG_BASE, "data/wikipedia"),
        "max_docs": 1000000,
    },
    "exitos": {
        "enabled": True,
        "path": os.path.join(WIKIRAG_BASE, "data/exitos"),
    },
    "fallos": {
        "enabled": True,
        "path": os.path.join(WIKIRAG_BASE, "data/fallos"),
    },
    "agentes": {
        "enabled": True,
        "path": os.path.join(WIKIRAG_BASE, "data/agentes"),
    },
}

# === CONFIGURACIÓN DE TRIAJE ===
TRIAJE = {
    # Puntuación mínima para usar modelos LARGE
    "threshold_large": 60,

    # Puntuación mínima para usar modelos GIANT
    "threshold_giant": 95,

    # Multiplicadores
    "complexity_multiplier": 10,
    "failure_multiplier": 25,
}

# === CONFIGURACIÓN GENERAL ===
CONFIG = {
    "timeout_llm": 120,  # Segundos
    "max_recursion": 3,
    "max_rag_iterations": 3,
    "adaptive_mode": True,
    "use_memory": True,
}

# === VERIFICACIÓN ===
def verify_paths():
    """Verificar que las rutas existen"""
    issues = []

    if not os.path.exists(LLAMA_CLI):
        issues.append(f"❌ llama-cli no encontrado: {LLAMA_CLI}")

    for name, modelo in MODELOS.items():
        if not os.path.exists(modelo["path"]):
            issues.append(f"⚠️ Modelo '{name}' no encontrado: {modelo['path']}")

    if issues:
        print("=" * 50)
        print("PROBLEMAS DE CONFIGURACIÓN:")
        print("=" * 50)
        for issue in issues:
            print(issue)
        print()
        print("Edita config_portable.py para ajustar las rutas.")
        print("=" * 50)
        return False

    print("✅ Configuración verificada correctamente")
    return True


if __name__ == "__main__":
    verify_paths()
