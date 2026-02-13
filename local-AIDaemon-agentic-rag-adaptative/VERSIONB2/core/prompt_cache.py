#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    PROMPT CACHE - Caché de Prompts y Respuestas
========================================
Sistema de caché para evitar recomputaciones costosas.
Cachea:
- Prompts completos → Respuestas
- Embeddings de queries
- Resultados de búsqueda RAG
========================================
"""

import os
import sys
import time
import json
import hashlib
import sqlite3
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import OrderedDict
import logging

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PromptCache")


@dataclass
class CacheEntry:
    """Entrada de caché"""
    key: str
    prompt_hash: str
    response: str
    model: str
    created_at: float
    accessed_at: float
    hit_count: int = 1
    ttl_seconds: int = 3600  # 1 hora por defecto
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Verificar si la entrada expiró"""
        return (time.time() - self.created_at) > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        """Edad de la entrada en segundos"""
        return time.time() - self.created_at


class MemoryCache:
    """
    Caché en memoria con LRU eviction.
    Rápido para acceso frecuente.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Args:
            max_size: Máximo número de entradas
            default_ttl: TTL por defecto en segundos
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def _compute_key(self, prompt: str, model: str = "") -> str:
        """Computar clave única para prompt"""
        content = f"{model}:{prompt}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:32]

    def get(self, prompt: str, model: str = "") -> Optional[str]:
        """
        Obtener respuesta cacheada.

        Args:
            prompt: Prompt original
            model: Nombre del modelo

        Returns:
            Respuesta cacheada o None
        """
        key = self._compute_key(prompt, model)

        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            entry = self._cache[key]

            # Verificar TTL
            if entry.is_expired:
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            # Actualizar acceso (LRU)
            entry.accessed_at = time.time()
            entry.hit_count += 1
            self._cache.move_to_end(key)

            self._stats["hits"] += 1
            return entry.response

    def put(
        self,
        prompt: str,
        response: str,
        model: str = "",
        ttl: int = None,
        metadata: Dict = None
    ):
        """
        Guardar respuesta en caché.

        Args:
            prompt: Prompt original
            response: Respuesta a cachear
            model: Nombre del modelo
            ttl: TTL personalizado
            metadata: Metadatos adicionales
        """
        key = self._compute_key(prompt, model)
        ttl = ttl or self.default_ttl
        now = time.time()

        entry = CacheEntry(
            key=key,
            prompt_hash=hashlib.sha256(prompt.encode()).hexdigest()[:16],
            response=response,
            model=model,
            created_at=now,
            accessed_at=now,
            ttl_seconds=ttl,
            metadata=metadata or {}
        )

        with self._lock:
            # Evict si es necesario
            while len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats["evictions"] += 1

            self._cache[key] = entry

    def invalidate(self, prompt: str = None, model: str = None, pattern: str = None):
        """
        Invalidar entradas del caché.

        Args:
            prompt: Prompt específico
            model: Invalidar todo de un modelo
            pattern: Patrón en la respuesta
        """
        with self._lock:
            if prompt:
                key = self._compute_key(prompt, model or "")
                if key in self._cache:
                    del self._cache[key]
                return

            keys_to_delete = []
            for key, entry in self._cache.items():
                if model and entry.model == model:
                    keys_to_delete.append(key)
                elif pattern and pattern.lower() in entry.response.lower():
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._cache[key]

    def clear(self):
        """Limpiar todo el caché"""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / max(1, total)

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": hit_rate,
                "evictions": self._stats["evictions"]
            }


class SQLiteCache:
    """
    Caché persistente en SQLite.
    Sobrevive reinicios, útil para respuestas costosas.
    """

    def __init__(
        self,
        db_path: str = None,
        max_entries: int = 10000,
        default_ttl: int = 86400  # 24 horas
    ):
        """
        Args:
            db_path: Ruta a la base de datos
            max_entries: Máximo número de entradas
            default_ttl: TTL por defecto en segundos
        """
        self.db_path = db_path or os.path.join(BASE_DIR, "data", "prompt_cache.db")
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self._lock = threading.Lock()

        # Crear directorio si no existe
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Inicializar DB
        self._init_db()

    def _init_db(self):
        """Inicializar estructura de la base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    prompt_hash TEXT NOT NULL,
                    response TEXT NOT NULL,
                    model TEXT DEFAULT '',
                    created_at REAL NOT NULL,
                    accessed_at REAL NOT NULL,
                    hit_count INTEGER DEFAULT 1,
                    ttl_seconds INTEGER DEFAULT 86400,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_accessed_at ON cache(accessed_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_model ON cache(model)")
            conn.commit()

    def _compute_key(self, prompt: str, model: str = "") -> str:
        """Computar clave única"""
        content = f"{model}:{prompt}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:32]

    def get(self, prompt: str, model: str = "") -> Optional[str]:
        """Obtener respuesta cacheada"""
        key = self._compute_key(prompt, model)
        now = time.time()

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """SELECT response, created_at, ttl_seconds
                       FROM cache WHERE key = ?""",
                    (key,)
                )
                row = cursor.fetchone()

                if not row:
                    return None

                response, created_at, ttl = row

                # Verificar TTL
                if (now - created_at) > ttl:
                    conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                    conn.commit()
                    return None

                # Actualizar stats
                conn.execute(
                    """UPDATE cache
                       SET accessed_at = ?, hit_count = hit_count + 1
                       WHERE key = ?""",
                    (now, key)
                )
                conn.commit()

                return response

    def put(
        self,
        prompt: str,
        response: str,
        model: str = "",
        ttl: int = None,
        metadata: Dict = None
    ):
        """Guardar respuesta en caché"""
        key = self._compute_key(prompt, model)
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        ttl = ttl or self.default_ttl
        now = time.time()
        meta_json = json.dumps(metadata or {})

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                # Verificar límite
                cursor = conn.execute("SELECT COUNT(*) FROM cache")
                count = cursor.fetchone()[0]

                if count >= self.max_entries:
                    # Eliminar las más antiguas
                    conn.execute("""
                        DELETE FROM cache WHERE key IN (
                            SELECT key FROM cache
                            ORDER BY accessed_at ASC
                            LIMIT ?
                        )
                    """, (count - self.max_entries + 100,))

                # Insertar o actualizar
                conn.execute("""
                    INSERT OR REPLACE INTO cache
                    (key, prompt_hash, response, model, created_at, accessed_at, ttl_seconds, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (key, prompt_hash, response, model, now, now, ttl, meta_json))

                conn.commit()

    def invalidate(self, prompt: str = None, model: str = None, older_than: int = None):
        """Invalidar entradas"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                if prompt:
                    key = self._compute_key(prompt, model or "")
                    conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                elif model:
                    conn.execute("DELETE FROM cache WHERE model = ?", (model,))
                elif older_than:
                    cutoff = time.time() - older_than
                    conn.execute("DELETE FROM cache WHERE created_at < ?", (cutoff,))

                conn.commit()

    def cleanup_expired(self):
        """Limpiar entradas expiradas"""
        now = time.time()
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "DELETE FROM cache WHERE (? - created_at) > ttl_seconds",
                    (now,)
                )
                conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*), SUM(hit_count) FROM cache")
            row = cursor.fetchone()
            count, total_hits = row[0], row[1] or 0

            cursor = conn.execute(
                "SELECT AVG(? - created_at) FROM cache",
                (time.time(),)
            )
            avg_age = cursor.fetchone()[0] or 0

            return {
                "entries": count,
                "max_entries": self.max_entries,
                "total_hits": total_hits,
                "average_age_seconds": avg_age
            }


class HybridPromptCache:
    """
    Caché híbrido que combina memoria + SQLite.

    Arquitectura:
    - L1: Memoria (rápido, volátil, últimas queries)
    - L2: SQLite (persistente, histórico)
    """

    def __init__(
        self,
        memory_size: int = 500,
        memory_ttl: int = 1800,  # 30 min
        sqlite_path: str = None,
        sqlite_ttl: int = 86400  # 24 horas
    ):
        """
        Args:
            memory_size: Entradas en caché de memoria
            memory_ttl: TTL para memoria
            sqlite_path: Ruta para SQLite
            sqlite_ttl: TTL para SQLite
        """
        self.l1_cache = MemoryCache(max_size=memory_size, default_ttl=memory_ttl)
        self.l2_cache = SQLiteCache(db_path=sqlite_path, default_ttl=sqlite_ttl)

        self._stats = {"l1_hits": 0, "l2_hits": 0, "misses": 0}

    def get(self, prompt: str, model: str = "") -> Optional[str]:
        """
        Obtener respuesta cacheada.
        Primero L1, luego L2.
        """
        # Try L1
        response = self.l1_cache.get(prompt, model)
        if response:
            self._stats["l1_hits"] += 1
            return response

        # Try L2
        response = self.l2_cache.get(prompt, model)
        if response:
            self._stats["l2_hits"] += 1
            # Promover a L1
            self.l1_cache.put(prompt, response, model)
            return response

        self._stats["misses"] += 1
        return None

    def put(
        self,
        prompt: str,
        response: str,
        model: str = "",
        persist: bool = True,
        ttl: int = None,
        metadata: Dict = None
    ):
        """
        Guardar respuesta en caché.

        Args:
            prompt: Prompt
            response: Respuesta
            model: Modelo
            persist: Si guardar en SQLite
            ttl: TTL personalizado
            metadata: Metadatos
        """
        # Siempre guardar en L1
        self.l1_cache.put(prompt, response, model, ttl, metadata)

        # Guardar en L2 si persist=True
        if persist:
            self.l2_cache.put(prompt, response, model, ttl, metadata)

    def invalidate(self, prompt: str = None, model: str = None):
        """Invalidar en ambos niveles"""
        self.l1_cache.invalidate(prompt, model)
        self.l2_cache.invalidate(prompt, model)

    def clear_memory(self):
        """Limpiar solo caché de memoria"""
        self.l1_cache.clear()

    def cleanup(self):
        """Limpiar entradas expiradas"""
        self.l2_cache.cleanup_expired()

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas completas"""
        l1_stats = self.l1_cache.get_stats()
        l2_stats = self.l2_cache.get_stats()

        total = self._stats["l1_hits"] + self._stats["l2_hits"] + self._stats["misses"]
        total_hits = self._stats["l1_hits"] + self._stats["l2_hits"]

        return {
            "total_requests": total,
            "total_hits": total_hits,
            "hit_rate": total_hits / max(1, total),
            "l1_hit_rate": self._stats["l1_hits"] / max(1, total),
            "l2_hit_rate": self._stats["l2_hits"] / max(1, total),
            "l1": l1_stats,
            "l2": l2_stats
        }


# === Decorador para cachear funciones ===
def cached_response(
    cache: HybridPromptCache,
    ttl: int = None,
    persist: bool = True,
    key_fn: callable = None
):
    """
    Decorador para cachear respuestas de funciones LLM.

    Uso:
        @cached_response(cache, ttl=3600)
        def generate(prompt: str) -> str:
            return llm.query(prompt)
    """
    def decorator(func):
        def wrapper(prompt: str, *args, **kwargs):
            # Computar clave
            model = kwargs.get('model', '')
            if key_fn:
                cache_key = key_fn(prompt, *args, **kwargs)
            else:
                cache_key = prompt

            # Buscar en caché
            cached = cache.get(cache_key, model)
            if cached:
                logger.debug(f"Cache hit for: {prompt[:30]}...")
                return cached

            # Ejecutar función
            response = func(prompt, *args, **kwargs)

            # Guardar en caché
            if response and not response.startswith("Error"):
                cache.put(
                    cache_key, response, model,
                    persist=persist,
                    ttl=ttl
                )

            return response

        return wrapper
    return decorator


# === SINGLETON ===
_cache_instance: Optional[HybridPromptCache] = None


def get_prompt_cache() -> HybridPromptCache:
    """Obtener instancia singleton del caché"""
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = HybridPromptCache()

    return _cache_instance


# === CLI para pruebas ===
if __name__ == "__main__":
    cache = get_prompt_cache()

    # Test básico
    print("Testing PromptCache...")

    # Put
    cache.put("¿Qué es Python?", "Python es un lenguaje de programación.", model="test")
    print("✅ Put completado")

    # Get
    response = cache.get("¿Qué es Python?", model="test")
    print(f"✅ Get: {response}")

    # Stats
    stats = cache.get_stats()
    print(f"📊 Stats: {json.dumps(stats, indent=2)}")

    # Miss
    miss = cache.get("Pregunta inexistente")
    print(f"✅ Miss: {miss}")

    # Final stats
    stats = cache.get_stats()
    print(f"📊 Final Stats: {json.dumps(stats, indent=2)}")
