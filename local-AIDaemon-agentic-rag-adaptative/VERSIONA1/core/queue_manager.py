#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    QUEUE MANAGER - Cola SQLite Thread-Safe
========================================
Sistema de IA con Agentes y RAGs

Cola de mensajes con SQLite + WAL mode para operaciones atómicas.
"""

import os
import sys
import sqlite3
import time
import uuid
import json
import logging
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# === Setup paths para imports absolutos ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Priority(IntEnum):
    """Prioridades de mensajes (menor = más urgente)"""
    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    AGENT = 5  # Consultas de agentes tienen menor prioridad


class MessageStatus:
    """Estados de mensajes"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class QueueMessage:
    """Mensaje en la cola"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    context: str = ""
    priority: int = Priority.NORMAL
    status: str = MessageStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    response: str = ""
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Control de recursión
    depth: int = 0
    parent_id: Optional[str] = None
    source: str = "user"  # user, agent, system

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "query": self.query,
            "context": self.context,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "response": self.response,
            "error": self.error,
            "metadata": json.dumps(self.metadata),
            "depth": self.depth,
            "parent_id": self.parent_id,
            "source": self.source
        }

    @classmethod
    def from_row(cls, row: tuple) -> 'QueueMessage':
        """Crear mensaje desde fila SQLite"""
        return cls(
            id=row[0],
            query=row[1],
            context=row[2] or "",
            priority=row[3],
            status=row[4],
            created_at=row[5],
            started_at=row[6],
            completed_at=row[7],
            response=row[8] or "",
            error=row[9] or "",
            metadata=json.loads(row[10]) if row[10] else {},
            depth=row[11] or 0,
            parent_id=row[12],
            source=row[13] or "user"
        )


class QueueManager:
    """
    Gestor de cola de mensajes con SQLite.

    Características:
    - WAL mode para concurrencia
    - Prioridades
    - Control de recursión (depth)
    - Timeouts automáticos
    - Atómico y thread-safe
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS queue (
        id TEXT PRIMARY KEY,
        query TEXT NOT NULL,
        context TEXT,
        priority INTEGER DEFAULT 3,
        status TEXT DEFAULT 'pending',
        created_at REAL,
        started_at REAL,
        completed_at REAL,
        response TEXT,
        error TEXT,
        metadata TEXT,
        depth INTEGER DEFAULT 0,
        parent_id TEXT,
        source TEXT DEFAULT 'user'
    );

    CREATE INDEX IF NOT EXISTS idx_status_priority
        ON queue(status, priority, created_at);

    CREATE INDEX IF NOT EXISTS idx_parent
        ON queue(parent_id);
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.QUEUE_DB
        self.max_depth = config.MAX_RECURSION_DEPTH
        self.timeout = config.QUEUE_TIMEOUT
        self._init_db()

    def _init_db(self):
        """Inicializar base de datos"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with self._get_connection() as conn:
            conn.executescript(self.SCHEMA)
            # WAL mode para mejor concurrencia
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")

    @contextmanager
    def _get_connection(self):
        """Context manager para conexiones"""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            isolation_level=None  # Autocommit
        )
        try:
            yield conn
        finally:
            conn.close()

    def enqueue(
        self,
        query: str,
        context: str = "",
        priority: int = Priority.NORMAL,
        depth: int = 0,
        parent_id: Optional[str] = None,
        source: str = "user",
        metadata: Optional[Dict] = None
    ) -> Optional[QueueMessage]:
        """
        Añadir mensaje a la cola.

        Args:
            query: Consulta del usuario
            context: Contexto RAG
            priority: Prioridad (1=urgent, 5=low)
            depth: Profundidad de recursión
            parent_id: ID del mensaje padre (si es sub-consulta)
            source: Origen (user, agent, system)
            metadata: Metadatos adicionales

        Returns:
            QueueMessage si éxito, None si rechazado
        """
        # Verificar límite de recursión
        if depth > self.max_depth:
            logger.warning(f"Recursión máxima alcanzada: depth={depth}")
            return None

        msg = QueueMessage(
            query=query,
            context=context,
            priority=priority,
            depth=depth,
            parent_id=parent_id,
            source=source,
            metadata=metadata or {}
        )

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO queue
                (id, query, context, priority, status, created_at,
                 metadata, depth, parent_id, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                msg.id, msg.query, msg.context, msg.priority,
                msg.status, msg.created_at, json.dumps(msg.metadata),
                msg.depth, msg.parent_id, msg.source
            ))

        logger.info(f"📥 Encolado: {msg.id[:8]}... [P{priority}] [D{depth}]")
        return msg

    # Alias para compatibilidad
    def push(self, query: str, context: str = "", priority: int = Priority.NORMAL,
             source: str = "user") -> Optional[QueueMessage]:
        return self.enqueue(query, context, priority, source=source)

    def dequeue(self) -> Optional[QueueMessage]:
        """
        Obtener siguiente mensaje pendiente (atómico).

        Usa UPDATE ... RETURNING para operación atómica.
        Ordena por prioridad y luego por antigüedad.
        """
        with self._get_connection() as conn:
            # Primero, marcar timeouts
            self._mark_timeouts(conn)

            # Obtener y marcar como processing en una operación
            cursor = conn.execute("""
                UPDATE queue
                SET status = 'processing', started_at = ?
                WHERE id = (
                    SELECT id FROM queue
                    WHERE status = 'pending'
                    ORDER BY priority ASC, created_at ASC
                    LIMIT 1
                )
                RETURNING *
            """, (time.time(),))

            row = cursor.fetchone()
            if row:
                msg = QueueMessage.from_row(row)
                logger.info(f"📤 Dequeue: {msg.id[:8]}... '{msg.query[:30]}...'")
                return msg

            return None

    # Alias para compatibilidad
    def pop(self) -> Optional[QueueMessage]:
        return self.dequeue()

    def complete(
        self,
        message_id: str,
        response: str = "",
        success: bool = True,
        error: str = ""
    ):
        """Marcar mensaje como completado"""
        status = MessageStatus.COMPLETED if success else MessageStatus.FAILED

        with self._get_connection() as conn:
            conn.execute("""
                UPDATE queue
                SET status = ?, completed_at = ?, response = ?, error = ?
                WHERE id = ?
            """, (status, time.time(), response, error, message_id))

        logger.info(f"{'✅' if success else '❌'} Completado: {message_id[:8]}...")

    def fail(self, message_id: str, error: str = ""):
        """Marcar mensaje como fallido"""
        self.complete(message_id, response="", success=False, error=error)

    def _mark_timeouts(self, conn):
        """Marcar mensajes en timeout"""
        threshold = time.time() - self.timeout
        conn.execute("""
            UPDATE queue
            SET status = 'timeout', error = 'Timeout exceeded'
            WHERE status = 'processing' AND started_at < ?
        """, (threshold,))

    def get_pending_count(self) -> int:
        """Número de mensajes pendientes"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM queue WHERE status = 'pending'"
            )
            return cursor.fetchone()[0]

    def get_message(self, message_id: str) -> Optional[QueueMessage]:
        """Obtener mensaje por ID"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM queue WHERE id = ?", (message_id,)
            )
            row = cursor.fetchone()
            return QueueMessage.from_row(row) if row else None

    # Alias para compatibilidad
    def get(self, message_id: str) -> Optional[QueueMessage]:
        return self.get_message(message_id)

    def peek(self) -> Optional[QueueMessage]:
        """Ver siguiente mensaje sin marcarlo"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM queue
                WHERE status = 'pending'
                ORDER BY priority ASC, created_at ASC
                LIMIT 1
            """)
            row = cursor.fetchone()
            return QueueMessage.from_row(row) if row else None

    def get_children(self, parent_id: str) -> List[QueueMessage]:
        """Obtener mensajes hijos (sub-consultas)"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM queue WHERE parent_id = ? ORDER BY created_at",
                (parent_id,)
            )
            return [QueueMessage.from_row(row) for row in cursor.fetchall()]

    def size(self) -> Dict[str, int]:
        """Estadísticas de la cola"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT status, COUNT(*)
                FROM queue
                GROUP BY status
            """)
            stats = {row[0]: row[1] for row in cursor.fetchall()}

            cursor = conn.execute("SELECT COUNT(*) FROM queue")
            stats["total"] = cursor.fetchone()[0]

            cursor = conn.execute(
                "SELECT COUNT(*) FROM queue WHERE depth > 0"
            )
            stats["recursive"] = cursor.fetchone()[0]

            return stats

    def cleanup(self, days: int = 7):
        """Limpiar mensajes antiguos completados"""
        threshold = time.time() - (days * 86400)
        with self._get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM queue
                WHERE status IN ('completed', 'failed', 'timeout')
                AND completed_at < ?
            """, (threshold,))
            logger.info(f"🧹 Limpieza: {cursor.rowcount} mensajes eliminados")

    def clear_completed(self, keep_last: int = 10):
        """Limpiar mensajes completados excepto los últimos N"""
        with self._get_connection() as conn:
            conn.execute("""
                DELETE FROM queue
                WHERE status = 'completed'
                AND id NOT IN (
                    SELECT id FROM queue
                    WHERE status = 'completed'
                    ORDER BY completed_at DESC
                    LIMIT ?
                )
            """, (keep_last,))

    def clear_all(self):
        """Limpiar toda la cola"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM queue")
        logger.info("🗑️ Cola limpiada completamente")

    def reset_stuck(self):
        """Reset mensajes stuck en processing"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                UPDATE queue
                SET status = 'pending', started_at = NULL
                WHERE status = 'processing'
            """)
            if cursor.rowcount > 0:
                logger.info(f"🔄 Reset: {cursor.rowcount} mensajes stuck")

    def wait_for_result(self, message_id: str, timeout: int = None) -> Optional[str]:
        """Esperar resultado de un mensaje"""
        timeout = timeout or self.timeout
        start = time.time()

        while (time.time() - start) < timeout:
            msg = self.get_message(message_id)
            if msg:
                if msg.status == MessageStatus.COMPLETED:
                    return msg.response
                elif msg.status in (MessageStatus.FAILED, MessageStatus.TIMEOUT):
                    logger.error(f"Mensaje {message_id[:8]} falló: {msg.error}")
                    return None
            time.sleep(0.5)

        logger.error(f"Timeout esperando {message_id[:8]}")
        return None

    def close(self):
        """Cerrar conexiones y liberar recursos"""
        try:
            # Checkpoint WAL para asegurar que todo está escrito
            with self._get_connection() as conn:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            logger.info("QueueManager cerrado correctamente")
        except Exception as e:
            logger.warning(f"Error cerrando QueueManager: {e}")


# === CLI para pruebas ===
if __name__ == "__main__":
    print("=== Test QueueManager SQLite ===\n")

    qm = QueueManager()
    qm.clear_all()

    # Test enqueue
    print("1. Enqueue mensajes:")
    msg1 = qm.enqueue("¿Qué es Python?", priority=Priority.NORMAL)
    msg2 = qm.enqueue("¿Urgente?", priority=Priority.URGENT)
    msg3 = qm.enqueue("Consulta de agente", priority=Priority.AGENT,
                      depth=1, parent_id=msg1.id, source="agent")

    print(f"   Pendientes: {qm.get_pending_count()}")

    # Test dequeue (debería salir URGENT primero)
    print("\n2. Dequeue (orden por prioridad):")
    m = qm.dequeue()
    if m:
        print(f"   Primero: '{m.query}' (P{m.priority})")
        qm.complete(m.id, "Respuesta urgente")

    m = qm.dequeue()
    if m:
        print(f"   Segundo: '{m.query}' (P{m.priority})")
        qm.complete(m.id, "Respuesta normal")

    # Test recursión
    print("\n3. Test límite recursión:")
    deep_msg = qm.enqueue("Deep query", depth=10)  # Debería fallar
    print(f"   depth=10: {'Rechazado ✅' if deep_msg is None else 'Aceptado ❌'}")

    # Stats
    print("\n4. Estadísticas:")
    stats = qm.size()
    for k, v in stats.items():
        print(f"   {k}: {v}")

    print("\n✅ Test completado")
