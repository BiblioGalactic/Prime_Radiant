#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    CONFIG - Configuración PORTABLE
========================================
WikiRAG v2.3.1 - Versión Pública Portable

Esta configuración detecta automáticamente rutas basándose
en la ubicación del proyecto. El usuario debe configurar
las rutas de llama-cli y modelos mediante:
1. Variables de entorno
2. Archivo settings.json
3. Editar DEFAULT_* en este archivo
========================================
"""

import os
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Optional

# === DETECTAR BASE_DIR AUTOMÁTICAMENTE ===
# El proyecto está en el directorio padre de 'core/'
_THIS_DIR = Path(__file__).parent.absolute()
BASE_DIR = str(_THIS_DIR.parent)

# Añadir al path
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# === DEFAULTS - EDITA ESTAS RUTAS PARA TU SISTEMA ===
DEFAULT_LLAMA_CLI = os.path.expanduser("~/modelo/llama.cpp/build/bin/llama-cli")
DEFAULT_MODEL_PATH = os.path.expanduser("~/modelo/modelos_grandes/M6/mistral-7b-instruct-v0.1.Q6_K.gguf")


def _load_settings() -> dict:
    """Cargar settings.json si existe"""
    settings_path = Path(BASE_DIR) / "settings.json"
    if settings_path.exists():
        try:
            with open(settings_path, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def _get_setting(key: str, default: str) -> str:
    """Obtener setting de ENV > settings.json > default"""
    # 1. Variable de entorno
    env_value = os.getenv(f"WIKIRAG_{key.upper()}")
    if env_value:
        return env_value

    # 2. settings.json
    settings = _load_settings()
    if key in settings:
        return settings[key]

    # 3. Default
    return default


@dataclass
class ModelConfig:
    """Configuración de un modelo LLM"""
    path: str
    ctx_size: int = 8192
    threads: int = 4
    n_predict: int = 500
    temperature: float = 0.7
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
    """
    Configuración PORTABLE del sistema WikiRAG.

    Rutas detectadas automáticamente:
    - BASE_DIR: Directorio raíz del proyecto
    - Subdirectorios: rags/, memory/, cache/, logs/, queue/

    Rutas configurables (via ENV o settings.json):
    - WIKIRAG_LLAMA_CLI: Ruta a llama-cli
    - WIKIRAG_MODEL_PATH: Ruta al modelo GGUF principal
    """

    # === Rutas Base (AUTOMÁTICAS) ===
    HOME: str = field(default_factory=lambda: os.path.expanduser("~"))
    BASE_DIR: str = field(default_factory=lambda: BASE_DIR)

    # === Ejecutable LLM (CONFIGURABLE) ===
    LLAMA_CLI: str = field(default_factory=lambda: _get_setting(
        "llama_cli", DEFAULT_LLAMA_CLI
    ))

    # === Modelo Principal (CONFIGURABLE) ===
    MODEL_DAEMON: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=_get_setting("model_path", DEFAULT_MODEL_PATH),
        ctx_size=8192,
        threads=6,
        n_predict=1500,
        temperature=0.7
    ))

    # Modelo Alternativo
    MODEL_DAEMON_FALLBACK: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=_get_setting("model_fallback", DEFAULT_MODEL_PATH),
        ctx_size=8192,
        threads=6,
        n_predict=1500,
        temperature=0.7
    ))

    # Agentes
    MODEL_AGENTS: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=_get_setting("model_agents", DEFAULT_MODEL_PATH),
        ctx_size=4096,
        threads=6,
        n_predict=1000,
        temperature=0.5
    ))

    # Código
    MODEL_CODE: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=_get_setting("model_code", DEFAULT_MODEL_PATH),
        ctx_size=8192,
        threads=6,
        n_predict=2000,
        temperature=0.3
    ))

    # Evaluador rápido
    MODEL_EVALUATOR: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=_get_setting("model_evaluator", DEFAULT_MODEL_PATH),
        ctx_size=2048,
        threads=4,
        n_predict=100,
        temperature=0.1
    ))

    # Consultas complejas
    MODEL_COMPLEX: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=_get_setting("model_complex", DEFAULT_MODEL_PATH),
        ctx_size=16384,
        threads=8,
        n_predict=2000,
        temperature=0.7
    ))

    # Rápido
    MODEL_FAST: ModelConfig = field(default_factory=lambda: ModelConfig(
        path=_get_setting("model_fast", DEFAULT_MODEL_PATH),
        ctx_size=4096,
        threads=6,
        n_predict=1000,
        temperature=0.7
    ))

    # === Modelo Semántico (OPCIONAL) ===
    SEMANTIC_MODEL: str = field(default_factory=lambda: _get_setting(
        "semantic_model",
        "sentence-transformers/all-MiniLM-L6-v2"
    ))

    # === RAGs (RUTAS RELATIVAS AL PROYECTO) ===
    RAG_WIKIPEDIA: RAGConfig = field(default_factory=lambda: RAGConfig(
        name="wikipedia",
        index_path=os.path.join(BASE_DIR, "rags", "wikipedia"),
        top_k=5
    ))

    RAG_EXITOS: RAGConfig = field(default_factory=lambda: RAGConfig(
        name="exitos",
        index_path=os.path.join(BASE_DIR, "rags", "exitos"),
        top_k=3
    ))

    RAG_FALLOS: RAGConfig = field(default_factory=lambda: RAGConfig(
        name="fallos",
        index_path=os.path.join(BASE_DIR, "rags", "fallos"),
        top_k=3
    ))

    RAG_AGENTES: RAGConfig = field(default_factory=lambda: RAGConfig(
        name="agentes",
        index_path=os.path.join(BASE_DIR, "rags", "agentes"),
        top_k=3
    ))

    # === Comunicación (RUTAS RELATIVAS) ===
    PIPE_ENTRADA: str = field(default_factory=lambda: os.path.join(
        BASE_DIR, "pipes", "entrada.pipe"
    ))
    PIPE_SALIDA: str = field(default_factory=lambda: os.path.join(
        BASE_DIR, "pipes", "salida.pipe"
    ))

    # === Cola de Mensajes (RUTAS RELATIVAS) ===
    QUEUE_DB: str = field(default_factory=lambda: os.path.join(
        BASE_DIR, "queue", "queue.db"
    ))
    QUEUE_MAX_SIZE: int = 100
    QUEUE_TIMEOUT: int = 300

    # === Estado compartido ===
    SHARED_STATE_DB: str = field(default_factory=lambda: os.path.join(
        BASE_DIR, "queue", "shared_state.db"
    ))

    # === Logs (RUTAS RELATIVAS) ===
    LOG_DAEMON: str = field(default_factory=lambda: os.path.join(
        BASE_DIR, "logs", "daemon.log"
    ))
    LOG_ORCHESTRATOR: str = field(default_factory=lambda: os.path.join(
        BASE_DIR, "logs", "orchestrator.log"
    ))
    LOG_AGENTS: str = field(default_factory=lambda: os.path.join(
        BASE_DIR, "logs", "agents.log"
    ))

    # === Timeouts ===
    DAEMON_TIMEOUT: int = 90
    AGENT_TIMEOUT: int = 60
    MCP_TIMEOUT: int = 30
    LLM_TIMEOUT: int = 60

    # === Agentes ===
    MAX_AGENTS_PARALLEL: int = 1
    MAX_PLAN_STEPS: int = 5
    MAX_RETRIES: int = 3
    MAX_RECURSION_DEPTH: int = 3
    MAX_DAEMON_CALLS_PER_AGENT: int = 2

    # === Personalidades (OPCIONAL) ===
    PERSONALITIES_DIR: str = field(default_factory=lambda: _get_setting(
        "personalities_dir",
        os.path.join(BASE_DIR, "personalities")
    ))

    def __post_init__(self):
        """Crear directorios necesarios"""
        self._ensure_directories()

    def _ensure_directories(self):
        """Crear directorios si no existen"""
        dirs_to_create = [
            os.path.join(BASE_DIR, "queue"),
            os.path.join(BASE_DIR, "logs"),
            os.path.join(BASE_DIR, "pipes"),
            os.path.join(BASE_DIR, "rags", "exitos"),
            os.path.join(BASE_DIR, "rags", "fallos"),
            os.path.join(BASE_DIR, "rags", "agentes"),
            os.path.join(BASE_DIR, "rags", "wikipedia"),
            os.path.join(BASE_DIR, "memory"),
            os.path.join(BASE_DIR, "cache"),
        ]
        for d in dirs_to_create:
            Path(d).mkdir(parents=True, exist_ok=True)

    def validate(self) -> Dict[str, bool]:
        """Validar que recursos existen"""
        checks = {
            "llama_cli": os.path.isfile(self.LLAMA_CLI) and os.access(self.LLAMA_CLI, os.X_OK),
            "model_daemon": os.path.isfile(self.MODEL_DAEMON.path),
            "base_dir": os.path.isdir(self.BASE_DIR),
            "queue_dir": os.path.isdir(os.path.dirname(self.QUEUE_DB)),
            "logs_dir": os.path.isdir(os.path.dirname(self.LOG_DAEMON)),
        }
        return checks

    def to_dict(self) -> dict:
        """Exportar configuración como diccionario"""
        return {
            "base_dir": self.BASE_DIR,
            "llama_cli": self.LLAMA_CLI,
            "model_daemon": self.MODEL_DAEMON.path,
            "model_agents": self.MODEL_AGENTS.path,
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

    def save_settings(self, path: str = None):
        """Guardar configuración actual a settings.json"""
        path = path or os.path.join(BASE_DIR, "settings.json")
        settings = {
            "llama_cli": self.LLAMA_CLI,
            "model_path": self.MODEL_DAEMON.path,
            "model_agents": self.MODEL_AGENTS.path,
            "model_code": self.MODEL_CODE.path,
            "semantic_model": self.SEMANTIC_MODEL,
        }
        with open(path, 'w') as f:
            json.dump(settings, f, indent=2)
        print(f"✅ Settings guardados en {path}")


# === Instancia global ===
config = Config()


def get_config() -> Config:
    """Obtener instancia de configuración"""
    return config


if __name__ == "__main__":
    # Test de configuración
    cfg = Config()
    print("=" * 50)
    print("  WikiRAG v2.3.1 - Configuración PORTABLE")
    print("=" * 50)
    print()
    print(f"📁 BASE_DIR: {cfg.BASE_DIR}")
    print(f"🔧 LLAMA_CLI: {cfg.LLAMA_CLI}")
    print(f"🧠 MODEL_DAEMON: {cfg.MODEL_DAEMON.path}")
    print(f"💾 QUEUE_DB: {cfg.QUEUE_DB}")
    print()
    print("=== Validación ===")
    for key, valid in cfg.validate().items():
        status = "✅" if valid else "❌"
        print(f"  {status} {key}")
    print()
    print("💡 Para configurar rutas, crea settings.json o usa variables de entorno:")
    print("   WIKIRAG_LLAMA_CLI=/path/to/llama-cli")
    print("   WIKIRAG_MODEL_PATH=/path/to/model.gguf")
