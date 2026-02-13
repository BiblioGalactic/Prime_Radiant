#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
CONFIG PORTABLE - Configuración Relativa
========================================
Sistema de IA con Agentes y RAGs
Detecta automáticamente rutas relativas al proyecto

Este config es portable: funciona copiando la carpeta a cualquier lugar.
Las rutas se calculan dinámicamente relativas al directorio de la versión.
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json

# === DETECTAR RUTA BASE AUTOMÁTICAMENTE ===
# El directorio base es donde está este archivo (core/)
_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
_VERSIOND4_DIR = os.path.dirname(_CORE_DIR)  # Subir un nivel
_WIKIRAG_BASE = os.path.dirname(_VERSIOND4_DIR)  # Subir a releases/
_WIKIRAG_BASE = os.path.dirname(_WIKIRAG_BASE)  # Subir a mnt/wikirag

# Añadir el directorio de VERSIOND4 al path de Python
if _VERSIOND4_DIR not in sys.path:
    sys.path.insert(0, _VERSIOND4_DIR)


def get_portable_path(relative_path: str) -> str:
    """
    Obtener una ruta portátil relativa a VERSIOND4.

    Ejemplos:
        get_portable_path("data/index") -> /sesiones/.../VERSIOND4/data/index
        get_portable_path("../models/mistral.gguf") -> /sesiones/.../models/mistral.gguf
    """
    path = Path(_VERSIOND4_DIR) / relative_path
    return str(path.resolve())


@dataclass
class ModelConfig:
    """Configuración de un modelo LLM"""
    path: str
    ctx_size: int = 24576
    threads: int = 4
    n_predict: int = 500
    temperature: float = 0.3
    repeat_penalty: float = 1.1


@dataclass
class RAGConfig:
    """Configuración de un RAG"""
    name: str
    index_path: str
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    top_k: int = 5
    semantic_threshold: float = 0.3
    keyword_threshold: int = 1


@dataclass
class PortableConfig:
    """
    Configuración centralizada del sistema - PORTABLE

    Rutas relativas a VERSIOND4/ se conviertes automáticamente a absolutas.
    Esto permite copiar VERSIOND4 a cualquier ubicación y funcionará.
    """

    # === Rutas Base (Automáticas) ===
    HOME: str = field(default_factory=lambda: os.path.expanduser("~"))
    VERSIOND4_DIR: str = field(default_factory=lambda: _VERSIOND4_DIR)
    BASE_DIR: str = field(default_factory=lambda: _WIKIRAG_BASE)

    # === Ejecutable LLM (Se busca en la carpeta local primero, luego en home) ===
    LLAMA_CLI: str = field(default_factory=lambda: _find_llama_cli())

    # === Modelos (Se buscan localmente primero, luego en home) ===
    # Para versión portable, buscar en ./models/ primero
    MODEL_DAEMON: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=_find_model("models/qwen3/Qwen3-8B-Q4_K_M.gguf"),
        ctx_size=8192,
        threads=6,
        n_predict=1500,
        temperature=0.7
    ))

    MODEL_DAEMON_FALLBACK: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=_find_model("models/mistral/Ministral-8B-Instruct-Q8_0.gguf"),
        ctx_size=8192,
        threads=6,
        n_predict=1500,
        temperature=0.7
    ))

    MODEL_AGENTS: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=_find_model("models/agents/hermes-2-pro.gguf"),
        ctx_size=4096,
        threads=6,
        n_predict=1000,
        temperature=0.5,
        repeat_penalty=1.1
    ))

    MODEL_CODE: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=_find_model("models/code/deepseek-coder.gguf"),
        ctx_size=8192,
        threads=6,
        n_predict=2000,
        temperature=0.3
    ))

    MODEL_EVALUATOR: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=_find_model("models/phi/phi-2.gguf"),
        ctx_size=2048,
        threads=4,
        n_predict=100,
        temperature=0.1
    ))

    MODEL_COMPLEX: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=_find_model("models/llama/llama-70b.gguf"),
        ctx_size=16384,
        threads=8,
        n_predict=2000,
        temperature=0.7
    ))

    MODEL_FAST: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=_find_model("models/mistral/mistral-7b.gguf"),
        ctx_size=4096,
        threads=6,
        n_predict=1000,
        temperature=0.7
    ))

    # === Modelo Semántico ===
    SEMANTIC_MODEL: str = field(default_factory=lambda: _find_model(
        "models/semantic/all-MiniLM-L6-v2"
    ))

    # === RAGs (relativos a data/) ===
    RAG_WIKIPEDIA: RAGConfig = field(default_factory=lambda: RAGConfig(
        name="wikipedia",
        index_path=get_portable_path("data/index/wikipedia"),
        top_k=5
    ))

    RAG_EXITOS: RAGConfig = field(default_factory=lambda: RAGConfig(
        name="exitos",
        index_path=get_portable_path("data/rags/exitos"),
        top_k=3
    ))

    RAG_FALLOS: RAGConfig = field(default_factory=lambda: RAGConfig(
        name="fallos",
        index_path=get_portable_path("data/rags/fallos"),
        top_k=3
    ))

    RAG_AGENTES: RAGConfig = field(default_factory=lambda: RAGConfig(
        name="agentes",
        index_path=get_portable_path("data/rags/agentes"),
        top_k=3
    ))

    # === Comunicación (relativos a data/) ===
    PIPE_ENTRADA: str = field(default_factory=lambda: get_portable_path("data/pipes/entrada.pipe"))
    PIPE_SALIDA: str = field(default_factory=lambda: get_portable_path("data/pipes/salida.pipe"))

    # === Cola de Mensajes (relativos a data/) ===
    QUEUE_DB: str = field(default_factory=lambda: get_portable_path("data/queue/queue.db"))
    QUEUE_MAX_SIZE: int = 100
    QUEUE_TIMEOUT: int = 300  # 5 minutos

    # === Estado compartido ===
    SHARED_STATE_DB: str = field(default_factory=lambda: get_portable_path("data/queue/shared_state.db"))

    # === Logs (relativos a data/) ===
    LOG_DAEMON: str = field(default_factory=lambda: get_portable_path("data/logs/daemon.log"))
    LOG_ORCHESTRATOR: str = field(default_factory=lambda: get_portable_path("data/logs/orchestrator.log"))
    LOG_AGENTS: str = field(default_factory=lambda: get_portable_path("data/logs/agents.log"))

    # === Timeouts ===
    DAEMON_TIMEOUT: int = 90
    AGENT_TIMEOUT: int = 60
    MCP_TIMEOUT: int = 30
    LLM_TIMEOUT: int = 60

    # === Agentes - Límites de recursión ===
    MAX_AGENTS_PARALLEL: int = 1
    MAX_PLAN_STEPS: int = 5
    MAX_RETRIES: int = 3
    MAX_RECURSION_DEPTH: int = 3
    MAX_DAEMON_CALLS_PER_AGENT: int = 2

    # === Personalidades (buscar localmente primero) ===
    PERSONALITIES_DIR: str = field(default_factory=lambda: get_portable_path("data/personalities"))

    def __post_init__(self):
        """Validar y crear directorios necesarios"""
        self._ensure_directories()

    def _ensure_directories(self):
        """Crear directorios si no existen"""
        dirs_to_create = [
            os.path.dirname(self.QUEUE_DB),
            os.path.dirname(self.LOG_DAEMON),
            os.path.dirname(self.PIPE_ENTRADA),
            self.RAG_EXITOS.index_path,
            self.RAG_FALLOS.index_path,
            self.RAG_AGENTES.index_path,
            self.PERSONALITIES_DIR,
        ]
        for d in dirs_to_create:
            Path(d).mkdir(parents=True, exist_ok=True)

    def validate(self) -> Dict[str, bool]:
        """
        Validar que todos los recursos existen.

        Nota: Modelos pueden no estar disponibles en versión portable básica.
        Muestra advertencias pero no falla.
        """
        checks = {
            "llama_cli": os.path.isfile(self.LLAMA_CLI) and os.access(self.LLAMA_CLI, os.X_OK),
            "data_dir": os.path.isdir(self.VERSIOND4_DIR),
            "queue_dir": os.path.isdir(os.path.dirname(self.QUEUE_DB)),
            "logs_dir": os.path.isdir(os.path.dirname(self.LOG_DAEMON)),
        }

        # Modelos - opcional en versión portable
        model_checks = {
            "model_daemon": os.path.isfile(self.MODEL_DAEMON.path),
            "model_agents": os.path.isfile(self.MODEL_AGENTS.path),
            "rag_wikipedia": os.path.isdir(self.RAG_WIKIPEDIA.index_path),
        }

        return {**checks, "models": all(model_checks.values())}

    def to_dict(self) -> dict:
        """Exportar configuración como diccionario"""
        return {
            "versiond4_dir": self.VERSIOND4_DIR,
            "base_dir": self.BASE_DIR,
            "llama_cli": self.LLAMA_CLI,
            "model_daemon": self.MODEL_DAEMON.path,
            "model_agents": self.MODEL_AGENTS.path,
            "rag_wikipedia": self.RAG_WIKIPEDIA.index_path,
            "queue_db": self.QUEUE_DB,
            "timeouts": {
                "daemon": self.DAEMON_TIMEOUT,
                "agent": self.AGENT_TIMEOUT,
                "mcp": self.MCP_TIMEOUT
            },
            "limits": {
                "max_recursion": self.MAX_RECURSION_DEPTH,
                "max_daemon_calls": self.MAX_DAEMON_CALLS_PER_AGENT
            }
        }


def _find_llama_cli() -> str:
    """Buscar llama-cli en ubicaciones comunes"""
    candidates = [
        get_portable_path("../../../bin/llama-cli"),  # Relativo a VERSIOND4
        get_portable_path("../../../modelo/llama.cpp/build/bin/llama-cli"),
        os.path.expanduser("~/modelo/llama.cpp/build/bin/llama-cli"),
        "/usr/local/bin/llama-cli",
        "/usr/bin/llama-cli",
    ]

    for path in candidates:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    # Fallback: retornar el primero aunque no exista
    return candidates[0]


def _find_model(relative_name: str) -> str:
    """
    Buscar un modelo en ubicaciones comunes.

    Args:
        relative_name: "models/qwen3/Qwen3-8B.gguf"

    Returns:
        Ruta absoluta al modelo (aunque no exista)
    """
    # Buscar en VERSIOND4/models/ primero
    local_path = get_portable_path(relative_name)
    if os.path.isfile(local_path):
        return local_path

    # Buscar en home
    home_path = os.path.expanduser(f"~/modelo/modelos_grandes/{relative_name.split('/')[-1]}")
    if os.path.isfile(home_path):
        return home_path

    # Retornar path local como default (aunque no exista)
    return local_path


# === Instancia global ===
config = PortableConfig()


# === Función helper para obtener config desde cualquier lugar ===
def get_config() -> PortableConfig:
    """Obtener instancia de configuración portátil"""
    return config


if __name__ == "__main__":
    # Test de configuración
    cfg = PortableConfig()
    print("=== Configuración Portable del Sistema ===")
    print(f"VERSIOND4_DIR: {cfg.VERSIOND4_DIR}")
    print(f"BASE_DIR: {cfg.BASE_DIR}")
    print(f"LLAMA_CLI: {cfg.LLAMA_CLI}")
    print(f"MODEL_DAEMON: {cfg.MODEL_DAEMON.path}")
    print(f"QUEUE_DB: {cfg.QUEUE_DB}")
    print(f"LOG_DAEMON: {cfg.LOG_DAEMON}")
    print()
    print("=== Validación ===")
    for key, valid in cfg.validate().items():
        status = "✅" if valid else "⚠️"
        print(f"  {status} {key}")
    print()
    print("=== Rutas Relativas ===")
    print(f"  DATA: {get_portable_path('data')}")
    print(f"  LOGS: {get_portable_path('data/logs')}")
    print(f"  MODELS: {get_portable_path('models')}")
