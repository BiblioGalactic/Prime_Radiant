#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    PLAN CACHE - Cache de Planes Exitosos
========================================
Sistema de IA con Agentes y RAGs

Cache inteligente para planes de agentes:
- Almacena planes exitosos
- Recupera planes similares para nuevas tareas
- Aprende de éxitos y fallos
"""

import os
import sys
import sqlite3
import hashlib
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import threading

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PlanCache")

# Intentar importar para similitud
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False


@dataclass
class CachedPlan:
    """Un plan cacheado"""
    id: str
    task_description: str
    task_type: str
    plan: Dict
    success_rate: float
    execution_count: int
    avg_execution_time: float
    last_used: float
    created: float

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "task_description": self.task_description,
            "task_type": self.task_type,
            "plan": self.plan,
            "success_rate": self.success_rate,
            "execution_count": self.execution_count,
            "avg_execution_time": self.avg_execution_time
        }


class PlanCache:
    """
    Cache inteligente de planes de agentes.

    Funcionalidades:
    1. Almacenar planes ejecutados con métricas
    2. Recuperar planes similares por tarea
    3. Actualizar estadísticas de éxito/fallo
    4. Sugerir planes basados en historial
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS plans (
        id TEXT PRIMARY KEY,
        task_description TEXT NOT NULL,
        task_type TEXT,
        plan TEXT NOT NULL,
        success_count INTEGER DEFAULT 0,
        failure_count INTEGER DEFAULT 0,
        total_execution_time REAL DEFAULT 0,
        execution_count INTEGER DEFAULT 0,
        last_used REAL,
        created REAL,
        embedding BLOB
    );

    CREATE INDEX IF NOT EXISTS idx_task_type ON plans(task_type);
    CREATE INDEX IF NOT EXISTS idx_success_rate ON plans(success_count, failure_count);
    """

    # Configuración
    MAX_PLANS = 500
    MIN_SUCCESS_RATE = 0.3  # Mínimo para recomendar

    def __init__(self, db_path: str = None):
        """
        Inicializar cache de planes.

        Args:
            db_path: Ruta a la base de datos
        """
        self.db_path = db_path or os.path.expanduser("~/wikirag/cache/plans.db")
        Path(os.path.dirname(self.db_path)).mkdir(parents=True, exist_ok=True)

        self._embed_model = None
        self._lock = threading.Lock()

        self._init_db()

    def _init_db(self):
        """Inicializar base de datos"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.executescript(self.SCHEMA)
            conn.commit()
            conn.close()

    @property
    def embed_model(self):
        """Modelo de embeddings (lazy loading)"""
        if self._embed_model is None and HAS_EMBEDDINGS:
            try:
                self._embed_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            except:
                pass
        return self._embed_model

    def _generate_id(self, task: str, plan: Dict) -> str:
        """Generar ID único para plan"""
        data = f"{task}:{json.dumps(plan, sort_keys=True)}"
        return hashlib.md5(data.encode()).hexdigest()[:12]

    def _get_embedding(self, text: str) -> Optional[bytes]:
        """Obtener embedding"""
        if self.embed_model:
            try:
                emb = self.embed_model.encode(text, convert_to_numpy=True)
                return emb.tobytes()
            except:
                pass
        return None

    def cache_plan(
        self,
        task_description: str,
        plan: Dict,
        task_type: str = None,
        success: bool = True,
        execution_time: float = None
    ) -> str:
        """
        Cachear un plan ejecutado.

        Args:
            task_description: Descripción de la tarea
            plan: Plan ejecutado (dict con steps, etc.)
            task_type: Tipo de tarea (categoría)
            success: Si fue exitoso
            execution_time: Tiempo de ejecución

        Returns:
            ID del plan
        """
        plan_id = self._generate_id(task_description, plan)
        timestamp = time.time()
        execution_time = execution_time or 0.0

        embedding = self._get_embedding(task_description)

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Verificar si ya existe
            cursor.execute("SELECT id FROM plans WHERE id = ?", (plan_id,))
            exists = cursor.fetchone()

            if exists:
                # Actualizar estadísticas
                if success:
                    cursor.execute("""
                        UPDATE plans SET
                            success_count = success_count + 1,
                            execution_count = execution_count + 1,
                            total_execution_time = total_execution_time + ?,
                            last_used = ?
                        WHERE id = ?
                    """, (execution_time, timestamp, plan_id))
                else:
                    cursor.execute("""
                        UPDATE plans SET
                            failure_count = failure_count + 1,
                            execution_count = execution_count + 1,
                            total_execution_time = total_execution_time + ?,
                            last_used = ?
                        WHERE id = ?
                    """, (execution_time, timestamp, plan_id))

                logger.debug(f"[PlanCache] Actualizado: {plan_id}")
            else:
                # Crear nuevo
                cursor.execute("""
                    INSERT INTO plans
                    (id, task_description, task_type, plan, success_count, failure_count,
                     total_execution_time, execution_count, last_used, created, embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    plan_id,
                    task_description,
                    task_type or "general",
                    json.dumps(plan),
                    1 if success else 0,
                    0 if success else 1,
                    execution_time,
                    1,
                    timestamp,
                    timestamp,
                    embedding
                ))

                logger.info(f"[PlanCache] Nuevo plan cacheado: {plan_id}")

            conn.commit()
            conn.close()

        self._check_limits()
        return plan_id

    def get_similar_plans(
        self,
        task_description: str,
        task_type: str = None,
        k: int = 3,
        min_success_rate: float = None
    ) -> List[CachedPlan]:
        """
        Recuperar planes similares.

        Args:
            task_description: Descripción de la tarea
            task_type: Filtrar por tipo
            k: Número de planes a retornar
            min_success_rate: Mínimo success rate

        Returns:
            Lista de planes similares ordenados por relevancia
        """
        min_success_rate = min_success_rate or self.MIN_SUCCESS_RATE

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Query base
            if task_type:
                cursor.execute("""
                    SELECT id, task_description, task_type, plan,
                           success_count, failure_count, total_execution_time,
                           execution_count, last_used, created
                    FROM plans
                    WHERE task_type = ?
                      AND execution_count > 0
                    ORDER BY last_used DESC
                    LIMIT ?
                """, (task_type, k * 5))
            else:
                cursor.execute("""
                    SELECT id, task_description, task_type, plan,
                           success_count, failure_count, total_execution_time,
                           execution_count, last_used, created
                    FROM plans
                    WHERE execution_count > 0
                    ORDER BY last_used DESC
                    LIMIT ?
                """, (k * 5,))

            rows = cursor.fetchall()
            conn.close()

        plans = []
        for row in rows:
            success_count = row[4]
            failure_count = row[5]
            total_executions = success_count + failure_count
            success_rate = success_count / total_executions if total_executions > 0 else 0

            if success_rate < min_success_rate:
                continue

            avg_time = row[6] / row[7] if row[7] > 0 else 0

            plans.append(CachedPlan(
                id=row[0],
                task_description=row[1],
                task_type=row[2],
                plan=json.loads(row[3]),
                success_rate=success_rate,
                execution_count=row[7],
                avg_execution_time=avg_time,
                last_used=row[8],
                created=row[9]
            ))

        # Reordenar por similitud si hay embeddings
        if self.embed_model and plans:
            plans = self._rank_by_similarity(task_description, plans)

        return plans[:k]

    def _rank_by_similarity(self, query: str, plans: List[CachedPlan]) -> List[CachedPlan]:
        """Reordenar por similitud semántica"""
        try:
            query_emb = self.embed_model.encode(query, convert_to_numpy=True)

            scored = []
            for plan in plans:
                plan_emb = self.embed_model.encode(plan.task_description, convert_to_numpy=True)
                sim = np.dot(query_emb, plan_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(plan_emb))

                # Combinar similitud con success_rate
                score = sim * 0.6 + plan.success_rate * 0.4
                scored.append((plan, score))

            scored.sort(key=lambda x: x[1], reverse=True)
            return [p for p, _ in scored]
        except:
            return plans

    def suggest_plan(
        self,
        task_description: str,
        task_type: str = None
    ) -> Optional[CachedPlan]:
        """
        Sugerir el mejor plan para una tarea.

        Args:
            task_description: Descripción de la tarea
            task_type: Tipo de tarea

        Returns:
            Mejor plan o None si no hay suficiente historial
        """
        plans = self.get_similar_plans(task_description, task_type, k=1)
        return plans[0] if plans else None

    def update_result(
        self,
        plan_id: str,
        success: bool,
        execution_time: float = None
    ):
        """
        Actualizar resultado de ejecución de un plan.

        Args:
            plan_id: ID del plan
            success: Si fue exitoso
            execution_time: Tiempo de ejecución
        """
        timestamp = time.time()
        execution_time = execution_time or 0.0

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if success:
                cursor.execute("""
                    UPDATE plans SET
                        success_count = success_count + 1,
                        execution_count = execution_count + 1,
                        total_execution_time = total_execution_time + ?,
                        last_used = ?
                    WHERE id = ?
                """, (execution_time, timestamp, plan_id))
            else:
                cursor.execute("""
                    UPDATE plans SET
                        failure_count = failure_count + 1,
                        execution_count = execution_count + 1,
                        total_execution_time = total_execution_time + ?,
                        last_used = ?
                    WHERE id = ?
                """, (execution_time, timestamp, plan_id))

            conn.commit()
            conn.close()

    def _check_limits(self):
        """Verificar límites y limpiar si necesario"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM plans")
            count = cursor.fetchone()[0]

            if count > self.MAX_PLANS:
                # Eliminar planes antiguos con bajo success rate
                cursor.execute("""
                    DELETE FROM plans
                    WHERE id IN (
                        SELECT id FROM plans
                        WHERE (success_count * 1.0 / (success_count + failure_count + 0.1)) < 0.3
                        ORDER BY last_used ASC
                        LIMIT ?
                    )
                """, (count - self.MAX_PLANS + 50,))

                logger.info(f"[PlanCache] Limpieza: eliminados {cursor.rowcount} planes")

            conn.commit()
            conn.close()

    def get_stats(self) -> Dict:
        """Obtener estadísticas del cache"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    AVG(success_count * 1.0 / (success_count + failure_count + 0.1)) as avg_success_rate,
                    AVG(execution_count) as avg_executions,
                    SUM(execution_count) as total_executions
                FROM plans
            """)

            row = cursor.fetchone()

            cursor.execute("""
                SELECT task_type, COUNT(*) FROM plans GROUP BY task_type
            """)
            by_type = {r[0]: r[1] for r in cursor.fetchall()}

            conn.close()

        return {
            "total_plans": row[0],
            "avg_success_rate": round(row[1], 3) if row[1] else 0,
            "avg_executions": round(row[2], 2) if row[2] else 0,
            "total_executions": row[3] or 0,
            "by_task_type": by_type
        }

    def clear(self, task_type: str = None):
        """Limpiar cache"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if task_type:
                cursor.execute("DELETE FROM plans WHERE task_type = ?", (task_type,))
            else:
                cursor.execute("DELETE FROM plans")

            conn.commit()
            conn.close()


# === Factory ===
_cache: Optional[PlanCache] = None


def get_plan_cache() -> PlanCache:
    """Obtener instancia singleton"""
    global _cache
    if _cache is None:
        _cache = PlanCache()
    return _cache


# === CLI para pruebas ===
if __name__ == "__main__":
    print("=== Test Plan Cache ===\n")

    cache = PlanCache(db_path="/tmp/test_plans.db")

    # Cachear planes
    print("1. Cacheando planes:")

    plan1 = {
        "description": "Buscar y responder",
        "steps": [
            {"action": "SEARCH", "input": "query"},
            {"action": "GENERATE", "input": "context"},
            {"action": "EVALUATE", "input": "response"}
        ]
    }

    id1 = cache.cache_plan(
        "¿Qué es Python?",
        plan1,
        task_type="qa",
        success=True,
        execution_time=2.5
    )
    print(f"   Plan 1: {id1}")

    plan2 = {
        "description": "Análisis complejo",
        "steps": [
            {"action": "DECOMPOSE", "input": "query"},
            {"action": "SEARCH", "input": "subqueries"},
            {"action": "SYNTHESIZE", "input": "results"}
        ]
    }

    id2 = cache.cache_plan(
        "Analiza las diferencias entre Python y Java",
        plan2,
        task_type="analysis",
        success=True,
        execution_time=5.0
    )
    print(f"   Plan 2: {id2}")

    # Recuperar similares
    print("\n2. Recuperando planes similares:")
    similar = cache.get_similar_plans("¿Qué es Java?", k=2)
    for p in similar:
        print(f"   - {p.task_description[:40]}... (success: {p.success_rate:.2f})")

    # Sugerir plan
    print("\n3. Sugerencia de plan:")
    suggested = cache.suggest_plan("¿Cuál es la capital de España?", "qa")
    if suggested:
        print(f"   Sugerido: {suggested.plan['description']}")

    # Stats
    print("\n4. Estadísticas:")
    print(f"   {cache.get_stats()}")

    # Cleanup
    os.remove("/tmp/test_plans.db")
    print("\n✅ Test completado")
