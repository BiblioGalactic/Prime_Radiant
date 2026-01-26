#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    SHARED STATE - Estado Compartido
========================================
Sistema de IA con Agentes y RAGs

Estado compartido entre agentes usando SQLite.
Permite pasar datos entre agentes de forma persistente.
"""

import os
import sys
import sqlite3
import time
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class StateEntry:
    """Entrada de estado compartido"""
    key: str
    value: Any
    session_id: str
    agent_id: str
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "metadata": self.metadata
        }


class SharedState:
    """
    Estado compartido entre agentes.

    Características:
    - Persistente en SQLite
    - Aislado por sesión
    - TTL automático
    - Tipos de datos: str, int, float, dict, list
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS state (
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        value_type TEXT NOT NULL,
        session_id TEXT NOT NULL,
        agent_id TEXT,
        created_at REAL,
        expires_at REAL,
        metadata TEXT,
        PRIMARY KEY (session_id, key)
    );

    CREATE INDEX IF NOT EXISTS idx_session
        ON state(session_id);

    CREATE INDEX IF NOT EXISTS idx_expires
        ON state(expires_at);
    """

    def __init__(self, db_path: Optional[str] = None, default_ttl: int = 3600):
        self.db_path = db_path or config.SHARED_STATE_DB
        self.default_ttl = default_ttl
        self._init_db()

    def _init_db(self):
        """Inicializar base de datos"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with self._get_connection() as conn:
            conn.executescript(self.SCHEMA)
            conn.execute("PRAGMA journal_mode=WAL")

    @contextmanager
    def _get_connection(self):
        """Context manager para conexiones"""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            isolation_level=None
        )
        try:
            yield conn
        finally:
            conn.close()

    def _serialize(self, value: Any) -> tuple:
        """Serializar valor y tipo"""
        if isinstance(value, str):
            return value, "str"
        elif isinstance(value, bool):
            return str(value), "bool"
        elif isinstance(value, int):
            return str(value), "int"
        elif isinstance(value, float):
            return str(value), "float"
        elif isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False), "json"
        else:
            return str(value), "str"

    def _deserialize(self, value: str, value_type: str) -> Any:
        """Deserializar valor"""
        if value_type == "str":
            return value
        elif value_type == "bool":
            return value.lower() == "true"
        elif value_type == "int":
            return int(value)
        elif value_type == "float":
            return float(value)
        elif value_type == "json":
            return json.loads(value)
        return value

    def set(
        self,
        key: str,
        value: Any,
        session_id: str,
        agent_id: str = "system",
        ttl: Optional[int] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Guardar valor en estado compartido.

        Args:
            key: Clave
            value: Valor (str, int, float, dict, list)
            session_id: ID de sesión
            agent_id: ID del agente que guarda
            ttl: Tiempo de vida en segundos
            metadata: Metadatos adicionales
        """
        serialized, value_type = self._serialize(value)
        expires_at = time.time() + (ttl or self.default_ttl) if ttl != -1 else None

        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO state
                (key, value, value_type, session_id, agent_id,
                 created_at, expires_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                key, serialized, value_type, session_id, agent_id,
                time.time(), expires_at, json.dumps(metadata or {})
            ))

        logger.debug(f"State set: {session_id}/{key} = {value_type}")

    def get(
        self,
        key: str,
        session_id: str,
        default: Any = None
    ) -> Any:
        """
        Obtener valor del estado compartido.

        Args:
            key: Clave
            session_id: ID de sesión
            default: Valor por defecto

        Returns:
            Valor o default
        """
        self._cleanup_expired()

        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT value, value_type FROM state
                WHERE session_id = ? AND key = ?
                AND (expires_at IS NULL OR expires_at > ?)
            """, (session_id, key, time.time()))

            row = cursor.fetchone()
            if row:
                return self._deserialize(row[0], row[1])

        return default

    def get_all(self, session_id: str) -> Dict[str, Any]:
        """Obtener todo el estado de una sesión"""
        self._cleanup_expired()

        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT key, value, value_type FROM state
                WHERE session_id = ?
                AND (expires_at IS NULL OR expires_at > ?)
            """, (session_id, time.time()))

            return {
                row[0]: self._deserialize(row[1], row[2])
                for row in cursor.fetchall()
            }

    def delete(self, key: str, session_id: str):
        """Eliminar una clave"""
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM state WHERE session_id = ? AND key = ?",
                (session_id, key)
            )

    def clear_session(self, session_id: str):
        """Limpiar todo el estado de una sesión"""
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM state WHERE session_id = ?",
                (session_id,)
            )
        logger.info(f"Session cleared: {session_id}")

    def _cleanup_expired(self):
        """Limpiar entradas expiradas"""
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM state WHERE expires_at IS NOT NULL AND expires_at < ?",
                (time.time(),)
            )

    # === Métodos de conveniencia para agentes ===

    def append_to_list(
        self,
        key: str,
        value: Any,
        session_id: str,
        agent_id: str = "system"
    ):
        """Añadir elemento a una lista"""
        current = self.get(key, session_id, default=[])
        if not isinstance(current, list):
            current = [current]
        current.append(value)
        self.set(key, current, session_id, agent_id, ttl=-1)

    def update_dict(
        self,
        key: str,
        updates: Dict,
        session_id: str,
        agent_id: str = "system"
    ):
        """Actualizar un diccionario"""
        current = self.get(key, session_id, default={})
        if not isinstance(current, dict):
            current = {}
        current.update(updates)
        self.set(key, current, session_id, agent_id, ttl=-1)

    def get_agent_results(self, session_id: str) -> List[Dict]:
        """Obtener resultados de todos los agentes"""
        return self.get(f"_agent_results", session_id, default=[])

    def save_agent_result(
        self,
        session_id: str,
        agent_id: str,
        result: Any,
        metadata: Optional[Dict] = None
    ):
        """Guardar resultado de un agente"""
        entry = {
            "agent_id": agent_id,
            "result": result,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        self.append_to_list("_agent_results", entry, session_id, agent_id)

    def close(self):
        """Cerrar conexiones y liberar recursos"""
        try:
            with self._get_connection() as conn:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            logger.info("SharedState cerrado correctamente")
        except Exception as e:
            logger.warning(f"Error cerrando SharedState: {e}")


# === Singleton ===
_shared_state: Optional[SharedState] = None


def get_shared_state() -> SharedState:
    """Obtener instancia singleton"""
    global _shared_state
    if _shared_state is None:
        _shared_state = SharedState()
    return _shared_state


if __name__ == "__main__":
    print("=== Test SharedState ===\n")

    state = SharedState()
    session = "test-session-123"

    # Limpiar
    state.clear_session(session)

    # Test tipos
    print("1. Test tipos de datos:")
    state.set("string_key", "Hello World", session, "agent1")
    state.set("int_key", 42, session, "agent1")
    state.set("float_key", 3.14, session, "agent1")
    state.set("dict_key", {"name": "test", "value": 123}, session, "agent2")
    state.set("list_key", [1, 2, 3], session, "agent2")

    print(f"   string: {state.get('string_key', session)}")
    print(f"   int: {state.get('int_key', session)}")
    print(f"   float: {state.get('float_key', session)}")
    print(f"   dict: {state.get('dict_key', session)}")
    print(f"   list: {state.get('list_key', session)}")

    # Test append
    print("\n2. Test append_to_list:")
    state.append_to_list("urls", "http://example.com/1", session, "search_agent")
    state.append_to_list("urls", "http://example.com/2", session, "search_agent")
    print(f"   urls: {state.get('urls', session)}")

    # Test resultados agentes
    print("\n3. Test resultados de agentes:")
    state.save_agent_result(session, "agent1", {"data": "result1"})
    state.save_agent_result(session, "agent2", {"data": "result2"})
    results = state.get_agent_results(session)
    print(f"   Resultados: {len(results)} agentes")

    # Test get_all
    print("\n4. Estado completo:")
    all_state = state.get_all(session)
    for k, v in all_state.items():
        print(f"   {k}: {type(v).__name__}")

    print("\n✅ Test completado")
