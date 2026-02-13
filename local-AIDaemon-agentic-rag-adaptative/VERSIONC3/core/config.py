#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    CONFIG - Configuración Centralizada
========================================
Sistema de IA con Agentes y RAGs
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json

# === Añadir paths para imports ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


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
class Config:
    """Configuración centralizada del sistema"""

    # === Rutas Base ===
    HOME: str = field(default_factory=lambda: os.path.expanduser("~"))
    BASE_DIR: str = field(default_factory=lambda: os.path.expanduser("~/wikirag"))

    # === Ejecutable LLM ===
    LLAMA_CLI: str = field(default_factory=lambda: os.path.expanduser(
        "~/modelo/llama.cpp/build/bin/llama-cli"
    ))

    # === Modelos Principales ===
    # Orquestador principal - Qwen3 multilingüe
    MODEL_DAEMON: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=os.path.expanduser(
            "~/modelo/modelos_grandes/qwen3/Qwen3-8B-Q4_K_M.gguf"
        ),
        ctx_size=8192,
        threads=6,
        n_predict=1500,
        temperature=0.7
    ))

    # Fallback si Qwen3 no está disponible
    MODEL_DAEMON_FALLBACK: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=os.path.expanduser(
            "~/modelo/modelos_grandes/mistral3/Ministral-8B-Instruct-2410-Q8_0.gguf"
        ),
        ctx_size=8192,
        threads=6,
        n_predict=1500,
        temperature=0.7
    ))

    # Agentes - Hermes especializado en multitarea
    MODEL_AGENTS: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=os.path.expanduser(
            "~/modelo/modelos_grandes/agentes/nosaltres-hermes-2-pro.Q5_K_M.gguf"
        ),
        ctx_size=4096,
        threads=6,
        n_predict=1000,
        temperature=0.5,
        repeat_penalty=1.1
    ))

    # Código - DeepSeek Coder
    MODEL_CODE: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=os.path.expanduser(
            "~/modelo/modelos_grandes/deep/deepseek-coder-6.7b-instruct.Q8_0.gguf"
        ),
        ctx_size=8192,
        threads=6,
        n_predict=2000,
        temperature=0.3
    ))

    # Evaluador rápido - Phi-2 ultra ligero
    MODEL_EVALUATOR: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=os.path.expanduser(
            "~/modelo/modelos_grandes/phi/phi-2.Q5_K_M.gguf"
        ),
        ctx_size=2048,
        threads=4,
        n_predict=100,
        temperature=0.1
    ))

    # Consultas complejas - Llama 70B (usar con cuidado, es lento)
    MODEL_COMPLEX: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=os.path.expanduser(
            "~/modelo/modelos_grandes/llama31-70b/Meta-Llama-3.1-70B-Instruct-Q4_K_M.gguf"
        ),
        ctx_size=16384,
        threads=8,
        n_predict=2000,
        temperature=0.7
    ))

    # Rápido y limpio - Mistral para planificación
    MODEL_FAST: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=os.path.expanduser(
            "~/modelo/modelos_grandes/M6/mistral-7b-instruct-v0.1.Q6_K.gguf"
        ),
        ctx_size=4096,
        threads=6,
        n_predict=1000,
        temperature=0.7
    ))

    # === Modelo Semántico ===
    SEMANTIC_MODEL: str = field(default_factory=lambda: os.path.expanduser(
        "~/modelo/modelos_grandes/semantico/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
    ))

    # === RAGs ===
    RAG_WIKIPEDIA: RAGConfig = field(default_factory=lambda: RAGConfig(
        name="wikipedia",
        index_path=os.path.expanduser("~/wikirag/index"),
        top_k=5
    ))

    RAG_EXITOS: RAGConfig = field(default_factory=lambda: RAGConfig(
        name="exitos",
        index_path=os.path.expanduser("~/wikirag/rags/exitos"),
        top_k=3
    ))

    RAG_FALLOS: RAGConfig = field(default_factory=lambda: RAGConfig(
        name="fallos",
        index_path=os.path.expanduser("~/wikirag/rags/fallos"),
        top_k=3
    ))

    RAG_AGENTES: RAGConfig = field(default_factory=lambda: RAGConfig(
        name="agentes",
        index_path=os.path.expanduser("~/wikirag/rags/agentes"),
        top_k=3
    ))

    # === Comunicación ===
    PIPE_ENTRADA: str = field(default_factory=lambda: os.path.expanduser(
        "~/wikirag/pipes/entrada.pipe"
    ))
    PIPE_SALIDA: str = field(default_factory=lambda: os.path.expanduser(
        "~/wikirag/pipes/salida.pipe"
    ))

    # === Cola de Mensajes (SQLite) ===
    QUEUE_DB: str = field(default_factory=lambda: os.path.expanduser(
        "~/wikirag/queue/queue.db"
    ))
    QUEUE_MAX_SIZE: int = 100
    QUEUE_TIMEOUT: int = 300  # 5 minutos

    # === Estado compartido entre agentes ===
    SHARED_STATE_DB: str = field(default_factory=lambda: os.path.expanduser(
        "~/wikirag/queue/shared_state.db"
    ))

    # === Logs ===
    LOG_DAEMON: str = field(default_factory=lambda: os.path.expanduser(
        "~/wikirag/logs/daemon.log"
    ))
    LOG_ORCHESTRATOR: str = field(default_factory=lambda: os.path.expanduser(
        "~/wikirag/logs/orchestrator.log"
    ))
    LOG_AGENTS: str = field(default_factory=lambda: os.path.expanduser(
        "~/wikirag/logs/agents.log"
    ))

    # === Timeouts ===
    DAEMON_TIMEOUT: int = 90   # 1.5 minutos para respuesta del daemon
    AGENT_TIMEOUT: int = 60    # 1 minuto por agente
    MCP_TIMEOUT: int = 30      # 30 segundos para herramientas MCP
    LLM_TIMEOUT: int = 60      # 1 minuto para ejecución directa de llama-cli

    # === Agentes - Límites de recursión ===
    MAX_AGENTS_PARALLEL: int = 1  # Ejecutar de uno en uno
    MAX_PLAN_STEPS: int = 5       # Máximo pasos en un plan
    MAX_RETRIES: int = 3          # Reintentos por agente
    MAX_RECURSION_DEPTH: int = 3  # Máximo llamadas daemon desde agentes
    MAX_DAEMON_CALLS_PER_AGENT: int = 2  # Máximo consultas al daemon por agente

    # === Personalidades ===
    PERSONALITIES_DIR: str = field(default_factory=lambda: os.path.expanduser(
        "~/proyecto/txtapoyo/perfilesdeia/Personalidad/"
    ))

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
        ]
        for d in dirs_to_create:
            Path(d).mkdir(parents=True, exist_ok=True)

    def validate(self) -> Dict[str, bool]:
        """Validar que todos los recursos existen"""
        checks = {
            "llama_cli": os.path.isfile(self.LLAMA_CLI) and os.access(self.LLAMA_CLI, os.X_OK),
            "model_daemon": os.path.isfile(self.MODEL_DAEMON.path),
            "model_agents": os.path.isfile(self.MODEL_AGENTS.path),
            "rag_wikipedia": os.path.isdir(self.RAG_WIKIPEDIA.index_path),
            "queue_dir": os.path.isdir(os.path.dirname(self.QUEUE_DB)),
            "logs_dir": os.path.isdir(os.path.dirname(self.LOG_DAEMON)),
        }
        return checks

    def to_dict(self) -> dict:
        """Exportar configuración como diccionario"""
        return {
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


# === Instancia global ===
config = Config()


# === Función helper para obtener config desde cualquier lugar ===
def get_config() -> Config:
    """Obtener instancia de configuración"""
    return config


if __name__ == "__main__":
    # Test de configuración
    cfg = Config()
    print("=== Configuración del Sistema ===")
    print(f"LLAMA_CLI: {cfg.LLAMA_CLI}")
    print(f"MODEL_DAEMON: {cfg.MODEL_DAEMON.path}")
    print(f"MODEL_AGENTS: {cfg.MODEL_AGENTS.path}")
    print(f"RAG_WIKIPEDIA: {cfg.RAG_WIKIPEDIA.index_path}")
    print(f"QUEUE_DB: {cfg.QUEUE_DB}")
    print(f"MAX_RECURSION: {cfg.MAX_RECURSION_DEPTH}")
    print()
    print("=== Validación ===")
    for key, valid in cfg.validate().items():
        status = "✅" if valid else "❌"
        print(f"  {status} {key}")
