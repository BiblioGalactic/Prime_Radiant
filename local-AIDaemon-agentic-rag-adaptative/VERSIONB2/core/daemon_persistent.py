#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    DAEMON PERSISTENT - Modelo Siempre Cargado
========================================
Mantiene el modelo LLM cargado en memoria continuamente.
El orquestador puede usarlo para:
- Consultas rápidas sin tiempo de carga
- Autogestión y autocontrol
- Procesamiento de tareas en background
========================================
"""

import os
import sys
import re
import time
import json
import threading
import subprocess
import signal
import atexit
import socket
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Callable, List
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue, Empty
from datetime import datetime
import logging

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DaemonPersistent")


class DaemonStatus(Enum):
    """Estado del daemon"""
    STOPPED = "stopped"
    STARTING = "starting"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"


@dataclass
class DaemonRequest:
    """Solicitud al daemon"""
    id: str
    prompt: str
    max_tokens: int = 500
    temperature: float = 0.7
    callback: Optional[Callable] = None
    priority: int = 0  # 0=normal, 1=high, 2=urgent
    timestamp: float = field(default_factory=time.time)


@dataclass
class DaemonResult:
    """Resultado del daemon"""
    id: str
    response: str
    success: bool
    latency: float
    tokens_generated: int = 0
    error: Optional[str] = None


class PersistentDaemon:
    """
    Daemon persistente que mantiene el modelo cargado en memoria.

    Arquitectura:
    - Proceso llama-cli corriendo en modo interactivo
    - Cola de solicitudes con prioridad
    - Worker thread procesando solicitudes
    - Comunicación vía stdin/stdout del proceso
    """

    def __init__(
        self,
        model_path: str = None,
        llama_cli: str = None,
        ctx_size: int = 30096,
        threads: int = 4,
        n_predict: int = 500,
        auto_start: bool = False,
        system_prompt: str = None
    ):
        """
        Inicializar daemon persistente.

        Args:
            model_path: Ruta al modelo GGUF
            llama_cli: Ruta al ejecutable llama-cli
            ctx_size: Tamaño del contexto
            threads: Threads de CPU
            n_predict: Tokens máximos por respuesta
            auto_start: Iniciar automáticamente
            system_prompt: Prompt del sistema
        """
        from core.config import config

        self.model_path = model_path or config.MODEL_DAEMON.path
        self.llama_cli = llama_cli or config.LLAMA_CLI
        self.ctx_size = ctx_size
        self.threads = threads
        self.n_predict = n_predict

        # Sistema de prompts
        self.system_prompt = system_prompt or """Eres un asistente IA experto integrado en el sistema WikiRAG.
Puedes:
- Responder consultas sobre cualquier tema
- Ejecutar tareas de procesamiento
- Ayudar con la autogestión del sistema
- Analizar y mejorar respuestas

Responde de forma precisa, útil y concisa."""

        # Estado
        self._status = DaemonStatus.STOPPED
        self._process: Optional[subprocess.Popen] = None
        self._request_queue: Queue = Queue()
        self._results: Dict[str, DaemonResult] = {}
        self._results_lock = threading.Lock()

        # Worker
        self._worker_thread: Optional[threading.Thread] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Métricas
        self._metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_latency": 0.0,
            "start_time": None
        }

        # Buffer de respuesta actual
        self._current_response_buffer = []
        self._current_request_id: Optional[str] = None
        self._response_ready = threading.Event()

        # Flag para evitar múltiples stops
        self._cleanup_registered = False

        if auto_start:
            self.start()

    @property
    def status(self) -> DaemonStatus:
        """Estado actual del daemon"""
        return self._status

    @property
    def is_ready(self) -> bool:
        """Daemon listo para recibir consultas"""
        return self._status == DaemonStatus.READY

    def start(self) -> bool:
        """
        Iniciar el daemon.

        Returns:
            True si inició correctamente
        """
        if self._status in [DaemonStatus.READY, DaemonStatus.STARTING]:
            logger.warning("Daemon ya está corriendo o iniciando")
            return True

        logger.info("🚀 Iniciando daemon persistente...")
        self._status = DaemonStatus.STARTING

        try:
            # Verificar modelo
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Modelo no encontrado: {self.model_path}")

            # Verificar llama-cli
            if not os.path.exists(self.llama_cli):
                raise FileNotFoundError(f"llama-cli no encontrado: {self.llama_cli}")

            # Construir comando
            cmd = [
                self.llama_cli,
                "--model", self.model_path,
                "--ctx-size", str(self.ctx_size),
                "--threads", str(self.threads),
                "--n-predict", str(self.n_predict),
                "--interactive",
                "--interactive-first",
                "--color",
                "--no-display-prompt",
                "-p", self.system_prompt
            ]

            logger.info(f"   Modelo: {Path(self.model_path).name}")
            logger.info(f"   ctx_size: {self.ctx_size}, threads: {self.threads}")

            # Iniciar proceso
            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,  # Sin buffer para respuesta inmediata
                start_new_session=True,
                env={**os.environ, 'TERM': 'dumb'}  # Evitar secuencias de escape
            )

            # Esperar a que el modelo se cargue
            logger.info("   Cargando modelo...")
            if not self._wait_for_ready(timeout=120):
                raise RuntimeError("Timeout esperando que el modelo se cargue")

            # Iniciar worker threads
            self._stop_event.clear()

            self._reader_thread = threading.Thread(
                target=self._output_reader_loop,
                name="DaemonReader",
                daemon=True
            )
            self._reader_thread.start()

            self._worker_thread = threading.Thread(
                target=self._request_worker_loop,
                name="DaemonWorker",
                daemon=True
            )
            self._worker_thread.start()

            self._status = DaemonStatus.READY
            self._metrics["start_time"] = time.time()

            logger.info("✅ Daemon persistente listo")
            return True

        except Exception as e:
            logger.error(f"❌ Error iniciando daemon: {e}")
            self._status = DaemonStatus.ERROR
            self.stop()
            return False

    def _wait_for_ready(self, timeout: int = 120) -> bool:
        """Esperar a que el modelo esté listo"""
        start = time.time()
        ready_indicators = [
            "interactive mode on",
            "sampling:",
            "> ",
            "system_info:"
        ]

        buffer = ""

        while (time.time() - start) < timeout:
            if self._process.poll() is not None:
                # Proceso terminó
                stderr = self._process.stderr.read()
                logger.error(f"Proceso terminó: {stderr}")
                return False

            try:
                # Leer stderr (logs de carga van ahí)
                import select
                readable, _, _ = select.select([self._process.stderr], [], [], 0.5)

                if readable:
                    chunk = self._process.stderr.read(4096)
                    if chunk:
                        try:
                            text = chunk.decode('utf-8', errors='replace')
                            buffer += text

                            # Mostrar progreso
                            if "loaded meta" in text.lower():
                                logger.info("      Metadata cargada...")
                            elif "load_tensors" in text.lower():
                                logger.info("      Cargando tensores...")
                            elif "warming up" in text.lower():
                                logger.info("      Calentando modelo...")

                            # Verificar si está listo
                            for indicator in ready_indicators:
                                if indicator.lower() in buffer.lower():
                                    return True
                        except:
                            pass

            except Exception as e:
                logger.warning(f"Error leyendo stderr: {e}")

            time.sleep(0.1)

        return False

    def _output_reader_loop(self):
        """Loop que lee output del proceso continuamente"""
        buffer = []
        end_markers = ['[end of text]', '<|endoftext|>', '<|im_end|>', '</s>']
        prompt_marker = '\n> '

        while not self._stop_event.is_set():
            if self._process is None or self._process.poll() is not None:
                break

            try:
                import select
                readable, _, _ = select.select([self._process.stdout], [], [], 0.5)

                if not readable:
                    continue

                chunk = self._process.stdout.read(1024)
                if not chunk:
                    continue

                try:
                    text = chunk.decode('utf-8', errors='replace')
                except:
                    text = chunk.decode('latin-1', errors='replace')

                # Filtrar logs de Metal/GPU
                lines = text.split('\n')
                clean_lines = []
                for line in lines:
                    if not self._is_system_log(line):
                        clean_lines.append(line)

                clean_text = '\n'.join(clean_lines)
                if clean_text.strip():
                    buffer.append(clean_text)

                # Verificar si respuesta completa
                full_text = ''.join(buffer)

                # Detectar fin de respuesta
                response_complete = False
                for marker in end_markers:
                    if marker.lower() in full_text.lower():
                        response_complete = True
                        break

                if prompt_marker in full_text:
                    response_complete = True

                if response_complete and self._current_request_id:
                    # Limpiar respuesta
                    response = self._clean_response(full_text)
                    self._current_response_buffer.append(response)
                    self._response_ready.set()
                    buffer.clear()

            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error(f"Error en reader: {e}")

    def _request_worker_loop(self):
        """Loop que procesa solicitudes de la cola"""
        while not self._stop_event.is_set():
            try:
                request = self._request_queue.get(timeout=1.0)

                if request is None:  # Señal de terminación
                    break

                self._process_request(request)

            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error en worker: {e}")

    def _process_request(self, request: DaemonRequest):
        """Procesar una solicitud"""
        start_time = time.time()
        self._status = DaemonStatus.BUSY
        self._current_request_id = request.id
        self._current_response_buffer.clear()
        self._response_ready.clear()

        logger.info(f"📝 Procesando: {request.prompt[:50]}...")

        try:
            # Enviar prompt al proceso
            prompt_bytes = (request.prompt + "\n").encode('utf-8')
            self._process.stdin.write(prompt_bytes)
            self._process.stdin.flush()

            # Esperar respuesta
            timeout = max(30, request.max_tokens // 10)  # Aprox 10 tokens/s
            if self._response_ready.wait(timeout=timeout):
                response = ''.join(self._current_response_buffer)
                success = True
                error = None
            else:
                response = ''.join(self._current_response_buffer) or ""
                success = len(response) > 10
                error = "Timeout parcial" if not success else None

            latency = time.time() - start_time
            tokens = len(response.split())

            result = DaemonResult(
                id=request.id,
                response=response,
                success=success,
                latency=latency,
                tokens_generated=tokens,
                error=error
            )

            # Guardar resultado
            with self._results_lock:
                self._results[request.id] = result

            # Actualizar métricas
            self._metrics["total_requests"] += 1
            self._metrics["total_latency"] += latency
            self._metrics["total_tokens"] += tokens
            if success:
                self._metrics["successful_requests"] += 1
            else:
                self._metrics["failed_requests"] += 1

            # Callback si existe
            if request.callback:
                try:
                    request.callback(result)
                except Exception as e:
                    logger.error(f"Error en callback: {e}")

            logger.info(f"✅ Respuesta: {tokens} tokens en {latency:.1f}s")

        except Exception as e:
            logger.error(f"❌ Error procesando: {e}")
            result = DaemonResult(
                id=request.id,
                response="",
                success=False,
                latency=time.time() - start_time,
                error=str(e)
            )
            with self._results_lock:
                self._results[request.id] = result

            if request.callback:
                try:
                    request.callback(result)
                except:
                    pass

        finally:
            self._current_request_id = None
            self._status = DaemonStatus.READY

    def _is_system_log(self, line: str) -> bool:
        """Detectar líneas de log del sistema"""
        patterns = [
            'ggml_', 'llama_', 'llm_load', 'Metal', 'GPU', 'CUDA',
            'sampling:', 'sampler', 'generate:', 'n_ctx', 'n_batch',
            'system_info', 'threads', 'AVX', 'NEON', 'FMA'
        ]
        line_lower = line.lower()
        return any(p.lower() in line_lower for p in patterns)

    def _clean_response(self, text: str) -> str:
        """Limpiar respuesta"""
        # Remover markers de fin
        markers = ['[end of text]', '<|endoftext|>', '<|im_end|>', '</s>', '\n> ']
        for marker in markers:
            text = text.replace(marker, '')

        # Limpiar espacios
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def query(
        self,
        prompt: str,
        max_tokens: int = None,
        temperature: float = None,
        timeout: int = 60,
        priority: int = 0
    ) -> str:
        """
        Enviar consulta al daemon y esperar respuesta.

        Args:
            prompt: Prompt a enviar
            max_tokens: Tokens máximos (usa default si None)
            temperature: Temperatura (no aplicable en modo interactivo)
            timeout: Timeout en segundos
            priority: Prioridad (0=normal, 1=high, 2=urgent)

        Returns:
            Respuesta del modelo
        """
        if not self.is_ready:
            if not self.start():
                return "Error: No se pudo iniciar el daemon"

        import uuid
        request_id = str(uuid.uuid4())[:8]

        request = DaemonRequest(
            id=request_id,
            prompt=prompt,
            max_tokens=max_tokens or self.n_predict,
            temperature=temperature or 0.7,
            priority=priority
        )

        # Encolar solicitud
        self._request_queue.put(request)

        # Esperar resultado
        start = time.time()
        while (time.time() - start) < timeout:
            with self._results_lock:
                if request_id in self._results:
                    result = self._results.pop(request_id)
                    if result.success:
                        return result.response
                    else:
                        return f"Error: {result.error or 'Fallo desconocido'}"
            time.sleep(0.1)

        return "Error: Timeout esperando respuesta"

    def query_async(
        self,
        prompt: str,
        callback: Callable[[DaemonResult], None],
        max_tokens: int = None,
        priority: int = 0
    ) -> str:
        """
        Enviar consulta asíncrona con callback.

        Args:
            prompt: Prompt
            callback: Función a llamar con el resultado
            max_tokens: Tokens máximos
            priority: Prioridad

        Returns:
            ID de la solicitud
        """
        if not self.is_ready:
            if not self.start():
                callback(DaemonResult(
                    id="error",
                    response="",
                    success=False,
                    latency=0,
                    error="No se pudo iniciar daemon"
                ))
                return "error"

        import uuid
        request_id = str(uuid.uuid4())[:8]

        request = DaemonRequest(
            id=request_id,
            prompt=prompt,
            max_tokens=max_tokens or self.n_predict,
            callback=callback,
            priority=priority
        )

        self._request_queue.put(request)
        return request_id

    def get_result(self, request_id: str) -> Optional[DaemonResult]:
        """Obtener resultado por ID"""
        with self._results_lock:
            return self._results.get(request_id)

    def stop(self):
        """Detener el daemon (solo una vez)"""
        # Evitar múltiples stops
        if self._status == DaemonStatus.STOPPED:
            return

        logger.info("🛑 Deteniendo daemon persistente...")
        self._status = DaemonStatus.STOPPED

        self._stop_event.set()
        self._request_queue.put(None)  # Señal de terminación

        # Esperar threads
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2)

        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=2)

        # Terminar proceso
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=2)
            except:
                pass
            finally:
                self._process = None

        self._status = DaemonStatus.STOPPED
        logger.info("✅ Daemon detenido")

    def restart(self) -> bool:
        """Reiniciar el daemon"""
        self.stop()
        time.sleep(1)
        return self.start()

    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del daemon"""
        uptime = 0.0
        if self._metrics["start_time"]:
            uptime = time.time() - self._metrics["start_time"]

        avg_latency = 0.0
        if self._metrics["total_requests"] > 0:
            avg_latency = self._metrics["total_latency"] / self._metrics["total_requests"]

        return {
            "status": self._status.value,
            "uptime_seconds": uptime,
            "total_requests": self._metrics["total_requests"],
            "successful_requests": self._metrics["successful_requests"],
            "failed_requests": self._metrics["failed_requests"],
            "success_rate": (
                self._metrics["successful_requests"] / max(1, self._metrics["total_requests"])
            ),
            "total_tokens": self._metrics["total_tokens"],
            "average_latency": avg_latency,
            "queue_size": self._request_queue.qsize()
        }


# === SINGLETON ESTRICTO ===
_daemon_instance: Optional[PersistentDaemon] = None
_daemon_lock = threading.Lock()


def get_persistent_daemon(auto_start: bool = False) -> PersistentDaemon:
    """
    Obtener instancia ÚNICA del daemon (singleton thread-safe).

    IMPORTANTE: Solo puede existir UN daemon en todo el sistema.
    Si ya existe, devuelve el existente ignorando auto_start.
    """
    global _daemon_instance

    with _daemon_lock:
        if _daemon_instance is None:
            logger.info("🔧 Creando instancia ÚNICA del daemon...")
            _daemon_instance = PersistentDaemon(auto_start=auto_start)
        else:
            logger.debug("♻️ Reutilizando daemon existente")

    return _daemon_instance


def stop_persistent_daemon():
    """Detener daemon singleton (solo una vez)"""
    global _daemon_instance

    with _daemon_lock:
        if _daemon_instance:
            _daemon_instance.stop()
            _daemon_instance = None


# === CLI para pruebas ===
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Daemon Persistente de WikiRAG")
    parser.add_argument("command", nargs="?", default="interactive",
                       choices=["start", "stop", "status", "query", "interactive"],
                       help="Comando a ejecutar")
    parser.add_argument("--query", "-q", help="Consulta a ejecutar")

    args = parser.parse_args()

    daemon = get_persistent_daemon(auto_start=False)

    if args.command == "start":
        if daemon.start():
            print("✅ Daemon iniciado")
            # Mantener corriendo
            print("Presiona Ctrl+C para detener...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            print("❌ Error iniciando daemon")

    elif args.command == "stop":
        daemon.stop()
        print("✅ Daemon detenido")

    elif args.command == "status":
        metrics = daemon.get_metrics()
        print(f"Estado: {metrics['status']}")
        print(f"Uptime: {metrics['uptime_seconds']:.1f}s")
        print(f"Requests: {metrics['total_requests']} ({metrics['success_rate']:.0%} éxito)")
        print(f"Latencia promedio: {metrics['average_latency']:.2f}s")

    elif args.command == "query":
        if not args.query:
            print("Error: Se requiere --query")
            sys.exit(1)

        daemon.start()
        response = daemon.query(args.query)
        print(f"\n📤 Respuesta:\n{response}")

    elif args.command == "interactive":
        daemon.start()
        print("\n🤖 Modo interactivo (escribe 'salir' para terminar)\n")

        while True:
            try:
                query = input("❓ Tu consulta: ").strip()

                if query.lower() in ['salir', 'exit', 'quit']:
                    break

                if query.lower() == 'status':
                    metrics = daemon.get_metrics()
                    print(f"   Estado: {metrics['status']}")
                    print(f"   Requests: {metrics['total_requests']}")
                    continue

                if not query:
                    continue

                print("🔄 Procesando...")
                response = daemon.query(query)
                print(f"\n💬 Respuesta:\n{response}\n")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")

        daemon.stop()
        print("👋 ¡Hasta luego!")
