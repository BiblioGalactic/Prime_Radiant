#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    MEMORY - Memoria a Largo Plazo
========================================
Sistema de IA con Agentes y RAGs

Implementa tres tipos de memoria:
1. Episódica: (query, response, rating) - conversaciones pasadas
2. Semántica: (concept, facts) - conocimiento extraído
3. Procedural: (task_type, best_plan) - planes exitosos
"""

import os
import sys
import sqlite3
import hashlib
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import threading

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Memory")

# Intentar importar sentence-transformers para embeddings
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    logger.warning("sentence-transformers no disponible, memoria sin embeddings")


class MemoryType(Enum):
    """Tipos de memoria"""
    EPISODIC = "episodic"      # Conversaciones pasadas
    SEMANTIC = "semantic"      # Conocimiento extraído
    PROCEDURAL = "procedural"  # Planes y procesos


@dataclass
class Memory:
    """Una memoria individual"""
    id: str
    memory_type: MemoryType
    content: str
    metadata: Dict[str, Any]
    timestamp: float
    access_count: int = 0
    last_accessed: float = 0.0
    success_rate: float = 1.0  # Para procedural
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.memory_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "access_count": self.access_count,
            "success_rate": self.success_rate
        }


class LongTermMemory:
    """
    Sistema de memoria a largo plazo con SQLite.

    Tipos de memoria:
    1. Episódica: (query, response, rating) - conversaciones pasadas
    2. Semántica: (concept, facts) - conocimiento extraído
    3. Procedural: (task_type, best_plan) - planes exitosos
    """

    # Schema de la base de datos
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS memories (
        id TEXT PRIMARY KEY,
        memory_type TEXT NOT NULL,
        content TEXT NOT NULL,
        metadata TEXT,
        timestamp REAL NOT NULL,
        access_count INTEGER DEFAULT 0,
        last_accessed REAL DEFAULT 0,
        success_rate REAL DEFAULT 1.0,
        embedding BLOB
    );

    CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type);
    CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp);
    CREATE INDEX IF NOT EXISTS idx_access_count ON memories(access_count);

    CREATE TABLE IF NOT EXISTS memory_relations (
        source_id TEXT,
        target_id TEXT,
        relation_type TEXT,
        strength REAL DEFAULT 1.0,
        PRIMARY KEY (source_id, target_id)
    );
    """

    # Configuración
    MAX_MEMORIES = 10000       # Máximo memorias totales
    CLEANUP_THRESHOLD = 9000   # Umbral para limpieza
    TTL_DAYS = 90             # Tiempo de vida en días

    def __init__(self, db_path: str = None):
        """
        Inicializar sistema de memoria.

        Args:
            db_path: Ruta a la base de datos SQLite
        """
        self.db_path = db_path or os.path.expanduser("~/wikirag/memory/memory.db")
        Path(os.path.dirname(self.db_path)).mkdir(parents=True, exist_ok=True)

        # Modelo de embeddings (lazy loading)
        self._embed_model = None

        # Lock para thread-safety
        self._lock = threading.Lock()

        # Inicializar DB
        self._init_db()

    def _init_db(self):
        """Inicializar base de datos"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.executescript(self.SCHEMA)
            conn.commit()
            conn.close()
        logger.info(f"[Memory] Base de datos inicializada: {self.db_path}")

    @property
    def embed_model(self):
        """Modelo de embeddings (lazy loading)"""
        if self._embed_model is None and HAS_EMBEDDINGS:
            try:
                model_path = config.SEMANTIC_MODEL
                if os.path.exists(model_path):
                    self._embed_model = SentenceTransformer(model_path)
                else:
                    self._embed_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                logger.info("[Memory] Modelo de embeddings cargado")
            except Exception as e:
                logger.warning(f"[Memory] No se pudo cargar modelo de embeddings: {e}")
        return self._embed_model

    def _generate_id(self, content: str, memory_type: MemoryType) -> str:
        """Generar ID único para memoria"""
        data = f"{memory_type.value}:{content}:{time.time()}"
        return hashlib.md5(data.encode()).hexdigest()[:16]

    def _get_embedding(self, text: str) -> Optional[bytes]:
        """Obtener embedding de texto"""
        if self.embed_model:
            try:
                emb = self.embed_model.encode(text, convert_to_numpy=True)
                return emb.tobytes()
            except:
                pass
        return None

    def remember(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Dict = None,
        success: bool = True
    ) -> str:
        """
        Almacenar una memoria.

        Args:
            content: Contenido de la memoria
            memory_type: Tipo de memoria
            metadata: Metadatos adicionales
            success: Si fue exitosa (para procedural)

        Returns:
            ID de la memoria creada
        """
        memory_id = self._generate_id(content, memory_type)
        timestamp = time.time()
        metadata = metadata or {}

        # Generar embedding
        embedding = self._get_embedding(content[:500])

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Verificar si ya existe contenido similar
            existing = self._find_duplicate(cursor, content, memory_type)
            if existing:
                # Actualizar existente
                cursor.execute("""
                    UPDATE memories
                    SET access_count = access_count + 1,
                        last_accessed = ?,
                        success_rate = (success_rate * access_count + ?) / (access_count + 1)
                    WHERE id = ?
                """, (timestamp, 1.0 if success else 0.0, existing))
                conn.commit()
                conn.close()
                logger.debug(f"[Memory] Actualizada memoria existente: {existing}")
                return existing

            # Crear nueva
            cursor.execute("""
                INSERT INTO memories (id, memory_type, content, metadata, timestamp, success_rate, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                memory_id,
                memory_type.value,
                content,
                json.dumps(metadata),
                timestamp,
                1.0 if success else 0.0,
                embedding
            ))

            conn.commit()
            conn.close()

        logger.info(f"[Memory] Nueva memoria creada: {memory_id} ({memory_type.value})")

        # Verificar límites
        self._check_limits()

        return memory_id

    def _find_duplicate(self, cursor, content: str, memory_type: MemoryType) -> Optional[str]:
        """Buscar memoria duplicada o muy similar"""
        content_hash = hashlib.md5(content.encode()).hexdigest()

        cursor.execute("""
            SELECT id, content FROM memories
            WHERE memory_type = ?
            LIMIT 100
        """, (memory_type.value,))

        for row in cursor.fetchall():
            existing_hash = hashlib.md5(row[1].encode()).hexdigest()
            if existing_hash == content_hash:
                return row[0]

        return None

    def recall(
        self,
        query: str,
        memory_type: MemoryType = None,
        k: int = 5,
        use_embeddings: bool = True
    ) -> List[Memory]:
        """
        Recuperar memorias relevantes.

        Args:
            query: Consulta de búsqueda
            memory_type: Filtrar por tipo (None = todos)
            k: Número de resultados
            use_embeddings: Usar similitud semántica

        Returns:
            Lista de memorias relevantes
        """
        memories = []

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Consulta base
            if memory_type:
                cursor.execute("""
                    SELECT id, memory_type, content, metadata, timestamp,
                           access_count, last_accessed, success_rate, embedding
                    FROM memories
                    WHERE memory_type = ?
                    ORDER BY access_count DESC, timestamp DESC
                    LIMIT ?
                """, (memory_type.value, k * 3))  # Recuperar más para filtrar
            else:
                cursor.execute("""
                    SELECT id, memory_type, content, metadata, timestamp,
                           access_count, last_accessed, success_rate, embedding
                    FROM memories
                    ORDER BY access_count DESC, timestamp DESC
                    LIMIT ?
                """, (k * 3,))

            rows = cursor.fetchall()

            for row in rows:
                memory = Memory(
                    id=row[0],
                    memory_type=MemoryType(row[1]),
                    content=row[2],
                    metadata=json.loads(row[3]) if row[3] else {},
                    timestamp=row[4],
                    access_count=row[5],
                    last_accessed=row[6],
                    success_rate=row[7]
                )
                memories.append(memory)

            conn.close()

        # Si hay embeddings, reordenar por similitud
        if use_embeddings and self.embed_model and memories:
            memories = self._rank_by_similarity(query, memories)

        # Actualizar acceso
        self._update_access([m.id for m in memories[:k]])

        return memories[:k]

    def _rank_by_similarity(self, query: str, memories: List[Memory]) -> List[Memory]:
        """Reordenar por similitud semántica"""
        try:
            query_emb = self.embed_model.encode(query, convert_to_numpy=True)

            scored = []
            for mem in memories:
                if mem.content:
                    mem_emb = self.embed_model.encode(mem.content[:500], convert_to_numpy=True)
                    sim = np.dot(query_emb, mem_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(mem_emb))
                    scored.append((mem, float(sim)))
                else:
                    scored.append((mem, 0.0))

            scored.sort(key=lambda x: x[1], reverse=True)
            return [m for m, _ in scored]
        except:
            return memories

    def _update_access(self, memory_ids: List[str]):
        """Actualizar contador de acceso"""
        if not memory_ids:
            return

        timestamp = time.time()
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for mid in memory_ids:
                cursor.execute("""
                    UPDATE memories
                    SET access_count = access_count + 1,
                        last_accessed = ?
                    WHERE id = ?
                """, (timestamp, mid))
            conn.commit()
            conn.close()

    def remember_episode(
        self,
        query: str,
        response: str,
        rating: float = 1.0,
        context: str = None
    ) -> str:
        """
        Recordar una interacción (memoria episódica).

        Args:
            query: Consulta del usuario
            response: Respuesta dada
            rating: Calificación (0-1)
            context: Contexto usado

        Returns:
            ID de la memoria
        """
        content = f"Q: {query}\nA: {response}"
        metadata = {
            "query": query,
            "response_preview": response[:200],
            "rating": rating,
            "has_context": bool(context)
        }

        return self.remember(
            content=content,
            memory_type=MemoryType.EPISODIC,
            metadata=metadata,
            success=(rating >= 0.5)
        )

    def remember_fact(
        self,
        concept: str,
        facts: List[str],
        source: str = None
    ) -> str:
        """
        Recordar conocimiento (memoria semántica).

        Args:
            concept: Concepto central
            facts: Lista de hechos sobre el concepto
            source: Fuente de la información

        Returns:
            ID de la memoria
        """
        content = f"Concepto: {concept}\nHechos:\n" + "\n".join(f"- {f}" for f in facts)
        metadata = {
            "concept": concept,
            "fact_count": len(facts),
            "source": source
        }

        return self.remember(
            content=content,
            memory_type=MemoryType.SEMANTIC,
            metadata=metadata
        )

    def remember_plan(
        self,
        task_type: str,
        plan: Dict,
        success: bool,
        execution_time: float = None
    ) -> str:
        """
        Recordar un plan ejecutado (memoria procedural).

        Args:
            task_type: Tipo de tarea
            plan: Plan ejecutado
            success: Si fue exitoso
            execution_time: Tiempo de ejecución

        Returns:
            ID de la memoria
        """
        content = f"Task: {task_type}\nPlan: {json.dumps(plan, indent=2)}"
        metadata = {
            "task_type": task_type,
            "step_count": len(plan.get("steps", [])),
            "execution_time": execution_time,
            "success": success
        }

        return self.remember(
            content=content,
            memory_type=MemoryType.PROCEDURAL,
            metadata=metadata,
            success=success
        )

    def recall_similar_episodes(self, query: str, k: int = 5) -> List[Memory]:
        """Recuperar episodios similares"""
        return self.recall(query, MemoryType.EPISODIC, k)

    def recall_facts(self, concept: str, k: int = 5) -> List[Memory]:
        """Recuperar hechos sobre un concepto"""
        return self.recall(concept, MemoryType.SEMANTIC, k)

    def recall_successful_plans(self, task_type: str, k: int = 3) -> List[Memory]:
        """Recuperar planes exitosos para un tipo de tarea"""
        memories = self.recall(task_type, MemoryType.PROCEDURAL, k * 2)
        # Filtrar por éxito
        successful = [m for m in memories if m.success_rate >= 0.7]
        return successful[:k]

    def _check_limits(self):
        """Verificar límites y limpiar si es necesario"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM memories")
            count = cursor.fetchone()[0]

            conn.close()

        if count > self.CLEANUP_THRESHOLD:
            logger.info(f"[Memory] Iniciando limpieza: {count} memorias")
            self.consolidate()

    def consolidate(self):
        """
        Proceso de consolidación: eliminar memorias antiguas/poco usadas.
        """
        cutoff_time = time.time() - (self.TTL_DAYS * 24 * 3600)

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Eliminar memorias antiguas no accedidas
            cursor.execute("""
                DELETE FROM memories
                WHERE timestamp < ?
                  AND access_count < 3
                  AND last_accessed < ?
            """, (cutoff_time, cutoff_time))

            deleted = cursor.rowcount

            # Eliminar memorias con bajo success_rate (procedural)
            cursor.execute("""
                DELETE FROM memories
                WHERE memory_type = 'procedural'
                  AND success_rate < 0.3
                  AND access_count < 5
            """)

            deleted += cursor.rowcount

            conn.commit()
            conn.close()

        logger.info(f"[Memory] Consolidación completada: {deleted} memorias eliminadas")

    def get_stats(self) -> Dict:
        """Obtener estadísticas de la memoria"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Contar por tipo
            cursor.execute("""
                SELECT memory_type, COUNT(*), AVG(success_rate), AVG(access_count)
                FROM memories
                GROUP BY memory_type
            """)

            stats = {"total": 0, "by_type": {}}
            for row in cursor.fetchall():
                stats["by_type"][row[0]] = {
                    "count": row[1],
                    "avg_success_rate": round(row[2], 3) if row[2] else 0,
                    "avg_access_count": round(row[3], 2) if row[3] else 0
                }
                stats["total"] += row[1]

            conn.close()

        return stats

    def clear(self, memory_type: MemoryType = None):
        """Limpiar memorias"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if memory_type:
                cursor.execute("DELETE FROM memories WHERE memory_type = ?", (memory_type.value,))
            else:
                cursor.execute("DELETE FROM memories")

            conn.commit()
            conn.close()

        logger.info(f"[Memory] Memoria limpiada: {memory_type.value if memory_type else 'todas'}")


# === Factory ===
_memory: Optional[LongTermMemory] = None


def get_memory() -> LongTermMemory:
    """Obtener instancia singleton de memoria"""
    global _memory
    if _memory is None:
        _memory = LongTermMemory()
    return _memory


# === CLI para pruebas ===
if __name__ == "__main__":
    print("=== Test Long Term Memory ===\n")

    memory = LongTermMemory(db_path="/tmp/test_memory.db")

    # Test episódica
    print("1. Memoria Episódica:")
    mid = memory.remember_episode(
        "¿Qué es Python?",
        "Python es un lenguaje de programación interpretado...",
        rating=0.9
    )
    print(f"   Creada: {mid}")

    # Test semántica
    print("\n2. Memoria Semántica:")
    mid = memory.remember_fact(
        "Python",
        ["Creado por Guido van Rossum", "Primera versión en 1991", "Lenguaje interpretado"]
    )
    print(f"   Creada: {mid}")

    # Test procedural
    print("\n3. Memoria Procedural:")
    mid = memory.remember_plan(
        "search_and_answer",
        {"steps": ["retrieve", "generate", "evaluate"]},
        success=True,
        execution_time=2.5
    )
    print(f"   Creada: {mid}")

    # Test recall
    print("\n4. Recall:")
    episodes = memory.recall_similar_episodes("Python programming")
    print(f"   Episodios encontrados: {len(episodes)}")

    # Stats
    print("\n5. Estadísticas:")
    stats = memory.get_stats()
    print(f"   {stats}")

    # Cleanup
    os.remove("/tmp/test_memory.db")
    print("\n✅ Test completado")
