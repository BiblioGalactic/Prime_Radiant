#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    DAEMON INTERFACE - Comunicación con Daemon IA
========================================
Interfaz para comunicarse con el daemon de IA que corre en otra terminal.
El daemon lee de un pipe y escribe su salida a un log.
"""

import os
import sys
import re
import time
import subprocess
import threading
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum
import logging

# === Setup paths para imports absolutos ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DaemonInterface")


class ResponseVerdict(Enum):
    """Veredictos de respuesta"""
    OK = "OK"
    PARTIAL = "PARCIAL"
    FAIL = "FALLA"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"


@dataclass
class DaemonResponse:
    """Respuesta del daemon"""
    content: str
    verdict: ResponseVerdict
    timestamp: float
    latency: float  # Tiempo de respuesta en segundos
    raw_output: str = ""


class DaemonInterface:
    """
    Interfaz para comunicarse con el daemon IA.

    El daemon es un proceso llama-cli corriendo en modo interactivo
    que lee de un pipe nombrado y escribe a stdout/log.

    Flujo:
    1. Escribir consulta al pipe de entrada
    2. Esperar respuesta en el log de salida
    3. Parsear respuesta y extraer veredicto
    """

    def __init__(
        self,
        pipe_entrada: str = None,
        log_salida: str = None,
        timeout: int = None
    ):
        """
        Inicializar interfaz con daemon.

        Args:
            pipe_entrada: Ruta al pipe de entrada
            log_salida: Ruta al log de salida del daemon
            timeout: Timeout para respuestas
        """
        from core.config import config

        self.pipe_entrada = pipe_entrada or config.PIPE_ENTRADA
        self.log_salida = log_salida or config.LOG_DAEMON
        self.timeout = timeout or config.DAEMON_TIMEOUT

        # Estado
        self._last_log_position = 0
        self._lock = threading.Lock()

        # Crear pipe si no existe
        self._ensure_pipe()

    def _ensure_pipe(self):
        """Crear pipe nombrado si no existe"""
        pipe_path = Path(self.pipe_entrada)
        pipe_path.parent.mkdir(parents=True, exist_ok=True)

        if not pipe_path.exists():
            os.mkfifo(str(pipe_path))
            logger.info(f"Pipe creado: {self.pipe_entrada}")
        elif not os.path.exists(self.pipe_entrada):
            # El archivo existe pero no es un pipe, recrear
            pipe_path.unlink()
            os.mkfifo(str(pipe_path))

    def is_daemon_running(self) -> bool:
        """Verificar si el daemon está corriendo"""
        try:
            # Verificar si hay un proceso leyendo del pipe
            result = subprocess.run(
                ["lsof", self.pipe_entrada],
                capture_output=True,
                text=True,
                timeout=5
            )
            return "llama" in result.stdout.lower()
        except Exception:
            return False

    def send_query(self, query: str, context: str = "") -> Optional[str]:
        """
        Enviar consulta al daemon.

        Args:
            query: Consulta del usuario
            context: Contexto adicional (de RAGs)

        Returns:
            ID del mensaje o None si falla
        """
        with self._lock:
            try:
                # Construir prompt
                if context:
                    full_prompt = f"""CONTEXTO:
{context}

CONSULTA: {query}

INSTRUCCIONES:
- Responde basándote en el contexto proporcionado
- Sé preciso y conciso
- Al final, evalúa tu respuesta: OK si es completa, PARCIAL si falta info, FALLA si no puedes responder

RESPUESTA:"""
                else:
                    full_prompt = f"CONSULTA: {query}\n\nRESPUESTA:"

                # Registrar posición actual del log antes de escribir
                self._last_log_position = self._get_log_size()

                # Escribir al pipe (no bloqueante)
                with open(self.pipe_entrada, 'w') as pipe:
                    pipe.write(full_prompt + "\n")
                    pipe.flush()

                logger.info(f"Consulta enviada al daemon: {query[:50]}...")
                return True

            except Exception as e:
                logger.error(f"Error enviando al daemon: {e}")
                return None

    def _get_log_size(self) -> int:
        """Obtener tamaño actual del log"""
        try:
            if os.path.exists(self.log_salida):
                return os.path.getsize(self.log_salida)
        except Exception:
            pass
        return 0

    def wait_response(self, timeout: int = None) -> DaemonResponse:
        """
        Esperar respuesta del daemon.

        Args:
            timeout: Timeout en segundos

        Returns:
            DaemonResponse con contenido y veredicto
        """
        timeout = timeout or self.timeout
        start_time = time.time()
        last_content = ""
        stable_count = 0

        while (time.time() - start_time) < timeout:
            try:
                # Leer nuevas líneas del log
                new_content = self._read_new_log_content()

                if new_content:
                    # Verificar si la respuesta parece completa
                    if self._is_response_complete(new_content):
                        latency = time.time() - start_time

                        # Parsear respuesta
                        content, verdict = self._parse_response(new_content)

                        return DaemonResponse(
                            content=content,
                            verdict=verdict,
                            timestamp=time.time(),
                            latency=latency,
                            raw_output=new_content
                        )

                    # Verificar estabilidad (contenido no cambia)
                    if new_content == last_content:
                        stable_count += 1
                        if stable_count > 5:  # 5 polls sin cambio = respuesta completa
                            latency = time.time() - start_time
                            content, verdict = self._parse_response(new_content)
                            return DaemonResponse(
                                content=content,
                                verdict=verdict,
                                timestamp=time.time(),
                                latency=latency,
                                raw_output=new_content
                            )
                    else:
                        stable_count = 0
                        last_content = new_content

                time.sleep(0.3)  # Poll cada 300ms

            except Exception as e:
                logger.error(f"Error leyendo respuesta: {e}")
                time.sleep(0.5)

        # Timeout
        return DaemonResponse(
            content="",
            verdict=ResponseVerdict.TIMEOUT,
            timestamp=time.time(),
            latency=timeout,
            raw_output=last_content
        )

    def _read_new_log_content(self) -> str:
        """Leer contenido nuevo del log desde última posición"""
        try:
            if not os.path.exists(self.log_salida):
                return ""

            with open(self.log_salida, 'r', encoding='utf-8', errors='replace') as f:
                f.seek(self._last_log_position)
                content = f.read()

            return content.strip()

        except Exception as e:
            logger.error(f"Error leyendo log: {e}")
            return ""

    def _is_response_complete(self, content: str) -> bool:
        """Verificar si la respuesta parece completa"""
        # Indicadores de fin de respuesta
        end_markers = [
            r'\[end of text\]',
            r'<\|endoftext\|>',
            r'\n\n\n',  # Triple salto de línea
            r'(OK|PARCIAL|FALLA)\s*$',  # Veredicto al final
            r'RESPUESTA FINAL:.*\n',
        ]

        for marker in end_markers:
            if re.search(marker, content, re.IGNORECASE):
                return True

        return False

    def _parse_response(self, raw_output: str) -> Tuple[str, ResponseVerdict]:
        """
        Parsear respuesta y extraer veredicto.

        Returns:
            Tupla (contenido_limpio, veredicto)
        """
        content = raw_output

        # Limpiar artifacts comunes
        cleanup_patterns = [
            r'\[end of text\]',
            r'<\|endoftext\|>',
            r'<\|im_end\|>',
            r'^\s*RESPUESTA:\s*',
            r'^\s*CONSULTA:.*?\n',
            r'^\s*CONTEXTO:.*?\n(?:.*?\n)*?CONSULTA:',
        ]

        for pattern in cleanup_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)

        content = content.strip()

        # Extraer veredicto
        verdict = ResponseVerdict.OK  # Default

        verdict_patterns = [
            (r'\b(FALLA|FALLIDO|NO PUEDO|ERROR)\b', ResponseVerdict.FAIL),
            (r'\b(PARCIAL|INCOMPLETO|FALTA INFO)\b', ResponseVerdict.PARTIAL),
            (r'\b(OK|COMPLETO|CORRECTO)\b', ResponseVerdict.OK),
        ]

        for pattern, v in verdict_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                verdict = v
                break

        # Eliminar líneas de veredicto del contenido
        content = re.sub(r'\n.*?(OK|PARCIAL|FALLA).*?$', '', content, flags=re.IGNORECASE)
        content = content.strip()

        return content, verdict

    def query_and_wait(
        self,
        query: str,
        context: str = "",
        timeout: int = None
    ) -> DaemonResponse:
        """
        Enviar consulta y esperar respuesta (método combinado).

        Args:
            query: Consulta
            context: Contexto
            timeout: Timeout

        Returns:
            DaemonResponse
        """
        if not self.send_query(query, context):
            return DaemonResponse(
                content="",
                verdict=ResponseVerdict.ERROR,
                timestamp=time.time(),
                latency=0,
                raw_output="Error enviando consulta"
            )

        return self.wait_response(timeout)


class DaemonCLI:
    """
    Ejecutor de modelos LLM con selección inteligente.
    Usa ModelRouter para elegir el mejor modelo según la tarea.
    """

    def __init__(
        self,
        model_path: str = None,
        llama_cli: str = None,
        use_daemon_model: bool = True,
        use_router: bool = False
    ):
        """
        Inicializar CLI.

        Args:
            model_path: Ruta al modelo GGUF (fija el modelo)
            llama_cli: Ruta al ejecutable llama-cli
            use_daemon_model: Si usar el modelo del daemon o agentes
            use_router: Si usar el ModelRouter para selección dinámica
        """
        from core.config import config

        self.config = config
        self.use_router = use_router
        self._router = None

        if model_path:
            # Modelo específico
            self.model_path = model_path
            self.model_config = config.MODEL_DAEMON
        elif use_router:
            # Se seleccionará dinámicamente
            self.model_path = None
            self.model_config = None
        elif use_daemon_model:
            # Verificar si existe el modelo principal, sino usar fallback
            if os.path.exists(config.MODEL_DAEMON.path):
                self.model_path = config.MODEL_DAEMON.path
                self.model_config = config.MODEL_DAEMON
            elif os.path.exists(config.MODEL_DAEMON_FALLBACK.path):
                self.model_path = config.MODEL_DAEMON_FALLBACK.path
                self.model_config = config.MODEL_DAEMON_FALLBACK
                logger.info("Usando modelo fallback")
            else:
                self.model_path = config.MODEL_FAST.path
                self.model_config = config.MODEL_FAST
        else:
            self.model_path = config.MODEL_AGENTS.path
            self.model_config = config.MODEL_AGENTS

        self.llama_cli = llama_cli or config.LLAMA_CLI
        self.default_timeout = config.LLM_TIMEOUT

    @property
    def router(self):
        """Lazy load del router"""
        if self._router is None:
            from core.model_router import get_router
            self._router = get_router()
        return self._router

    def select_model_for_query(self, query: str, task_hint: str = None, previous_failures: int = 0):
        """Seleccionar modelo óptimo para una consulta con sistema de triaje"""
        if not self.use_router:
            return self.model_path, self.model_config, 0.0

        from core.model_router import TaskType

        task_type = None
        if task_hint:
            task_type = TaskType(task_hint) if task_hint in [t.value for t in TaskType] else None

        selection = self.router.select_model(
            query,
            task_type=task_type,
            previous_failures=previous_failures,
            is_retry=(previous_failures > 0)
        )

        # Crear ModelConfig desde ModelSpec
        from core.config import ModelConfig
        model_config = ModelConfig(
            path=selection.model.path,
            ctx_size=selection.model.ctx_size,
            threads=selection.model.threads,
            n_predict=selection.model.n_predict,
            temperature=selection.model.temperature,
            repeat_penalty=selection.model.repeat_penalty
        )

        # Obtener throttle_delay del modelo (para modelos grandes)
        throttle_delay = getattr(selection.model, 'throttle_delay', 0.0)

        return selection.model.path, model_config, throttle_delay

    def query(
        self,
        prompt: str,
        max_tokens: int = None,
        temperature: float = None,
        timeout: int = None,
        stream: bool = True,
        task_hint: str = None,
        previous_failures: int = 0
    ) -> str:
        """
        Ejecutar consulta directa al modelo.

        Args:
            prompt: Prompt completo
            max_tokens: Máximo tokens a generar
            temperature: Temperatura de generación
            timeout: Timeout en segundos
            stream: Si mostrar output en tiempo real
            task_hint: Pista sobre tipo de tarea (code, medical, etc.)
            previous_failures: Fallos previos (para escalar a modelos grandes)

        Returns:
            Respuesta del modelo
        """
        import tempfile

        # Selección dinámica de modelo si router está activo
        throttle_delay = 0.0
        if self.use_router:
            model_path, model_config, throttle_delay = self.select_model_for_query(
                prompt, task_hint, previous_failures
            )
        else:
            model_path = self.model_path
            model_config = self.model_config

        max_tokens = max_tokens or model_config.n_predict
        temperature = temperature or model_config.temperature
        timeout = timeout or self.default_timeout

        try:
            # Escribir prompt a archivo temporal con encoding explícito
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(prompt)
                prompt_file = f.name

            # Construir comando
            cmd = [
                self.llama_cli,
                "--model", model_path,
                "--file", prompt_file,
                "--n-predict", str(max_tokens),
                "--ctx-size", str(model_config.ctx_size),
                "--temp", str(temperature),
                "--repeat-penalty", str(model_config.repeat_penalty),
                "--threads", str(model_config.threads),
            ]

            # === LOGGING DEL COMANDO ===
            logger.info(f"🔧 Comando: {' '.join(cmd[:4])}...")
            logger.info(f"   Modelo: {Path(model_path).name}")
            logger.info(f"   ctx_size: {model_config.ctx_size}, n_predict: {max_tokens}")
            logger.info(f"   Prompt length: {len(prompt)} chars")

            if stream:
                # === EJECUTAR CON STREAM EN TIEMPO REAL ===
                return self._run_with_stream(cmd, prompt_file, timeout, throttle_delay)
            else:
                # Ejecutar sin stream
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )

                Path(prompt_file).unlink(missing_ok=True)

                if result.returncode == 0:
                    return self._clean_response(result.stdout.strip())
                else:
                    logger.error(f"Error llama-cli: {result.stderr}")
                    return f"Error: {result.stderr}"

        except subprocess.TimeoutExpired:
            logger.error(f"⏱️ Timeout después de {timeout}s")
            return "Error: Timeout ejecutando modelo"
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return f"Error: {str(e)}"

    def _run_with_stream(self, cmd: list, prompt_file: str, timeout: int, throttle_delay: float = 0.0) -> str:
        """Ejecutar con stream de output en tiempo real"""
        import io
        import select
        import os as _os

        output_chunks = []
        start_time = time.time()

        # Mostrar warning si es modelo grande con throttle
        if throttle_delay > 0:
            logger.warning(f"⚠️ Modelo grande: throttle={throttle_delay*1000:.0f}ms por línea")

        try:
            # === FIX CRÍTICO: stdin=DEVNULL y start_new_session=True ===
            # Esto evita que el modelo entre en modo interactivo y corrompa el TTY
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Separar stderr
                stdin=subprocess.DEVNULL,  # NO esperar input
                bufsize=1,
                start_new_session=True  # Nuevo grupo de procesos (evita TTY)
            )

            print("   [LLM] ", end="", flush=True)
            char_count = 0
            empty_reads = 0
            max_empty_reads = 10  # Si no hay output por X reads, terminar

            # Leer con timeout por línea usando select
            while True:
                # Verificar timeout global
                if time.time() - start_time > timeout:
                    self._force_kill_process(process)
                    logger.error(f"⏱️ Timeout después de {timeout}s")
                    break

                # Verificar si proceso terminó
                if process.poll() is not None:
                    # Proceso terminó, leer lo que queda
                    remaining = process.stdout.read()
                    if remaining:
                        try:
                            text = remaining.decode('utf-8', errors='replace')
                            for line in text.split('\n'):
                                if not self._is_metal_log_line(line) and line.strip():
                                    output_chunks.append(line + '\n')
                                    print(line)
                        except:
                            pass
                    break

                # Usar select para no bloquear indefinidamente
                try:
                    readable, _, _ = select.select([process.stdout], [], [], 0.5)
                except:
                    readable = []

                if not readable:
                    empty_reads += 1
                    if empty_reads >= max_empty_reads:
                        # Sin output por mucho tiempo, terminar
                        logger.info("Sin output, terminando proceso...")
                        self._force_kill_process(process)
                        break
                    continue

                empty_reads = 0  # Reset contador

                # Leer línea en bytes
                line_bytes = process.stdout.readline()
                if not line_bytes:
                    continue

                # Decodificar con manejo de errores
                try:
                    line = line_bytes.decode('utf-8', errors='replace')
                except Exception:
                    line = line_bytes.decode('latin-1', errors='replace')

                # Detectar y filtrar logs de Metal/GPU
                if self._is_metal_log_line(line):
                    continue

                # Detectar tokens de fin de generación
                if self._is_end_token(line):
                    logger.info("Detectado fin de generación")
                    self._force_kill_process(process)
                    break

                # Detectar prompt interactivo y terminar INMEDIATAMENTE
                stripped = line.strip()
                if stripped == '>' or stripped.startswith('> ') or stripped == '>>':
                    logger.info("Detectado prompt interactivo, forzando cierre...")
                    self._force_kill_process(process)
                    break

                # Añadir al output
                output_chunks.append(line)
                char_count += len(line)

                # Mostrar en tiempo real
                print(line, end="", flush=True)

                # === THROTTLE para modelos grandes ===
                if throttle_delay > 0:
                    time.sleep(throttle_delay)

            print()  # Nueva línea al final

            # Limpiar archivo temporal
            Path(prompt_file).unlink(missing_ok=True)

            elapsed = time.time() - start_time
            logger.info(f"✅ Generación completada: {char_count} chars en {elapsed:.1f}s")

            output = "".join(output_chunks)
            return self._clean_response(output.strip())

        except Exception as e:
            logger.error(f"Error en stream: {e}")
            # Asegurar que el proceso muere
            try:
                self._force_kill_process(process)
            except:
                pass
            Path(prompt_file).unlink(missing_ok=True)
            return f"Error: {str(e)}"
        finally:
            # === FIX TTY: Restaurar terminal ===
            self._restore_terminal()

    def _force_kill_process(self, process):
        """Forzar cierre del proceso de forma segura"""
        import signal
        import os as _os

        if process.poll() is not None:
            return  # Ya terminó

        try:
            # Primero intentar terminar el grupo de procesos
            pgid = _os.getpgid(process.pid)
            _os.killpg(pgid, signal.SIGTERM)
        except:
            pass

        try:
            process.terminate()
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
                process.wait(timeout=1)
            except:
                pass
        except:
            pass

    def _restore_terminal(self):
        """Restaurar configuración del terminal"""
        import sys
        try:
            # Restaurar echo y modo canónico del terminal
            if sys.stdin.isatty():
                import termios
                import tty
                fd = sys.stdin.fileno()
                # Obtener configuración actual y restaurar defaults
                attrs = termios.tcgetattr(fd)
                attrs[3] = attrs[3] | termios.ECHO | termios.ICANON
                termios.tcsetattr(fd, termios.TCSADRAIN, attrs)
        except:
            pass  # No es un TTY o no tiene termios

    def _is_end_token(self, line: str) -> bool:
        """Detectar tokens que indican fin de generación"""
        end_patterns = [
            '[end of text]',
            '<|endoftext|>',
            '<|im_end|>',
            '<|eot_id|>',
            '</s>',
            '<|end|>',
        ]
        line_lower = line.lower().strip()
        return any(p.lower() in line_lower for p in end_patterns)

    def _is_metal_log_line(self, line: str) -> bool:
        """Detectar si una línea es un log de Metal/GPU/llama.cpp"""
        # Patrones de logs de arranque y sistema
        metal_patterns = [
            # Metal/GPU
            'ggml_metal', 'ggml_backend', 'ggml_cuda', 'ggml_vulkan',
            'Main GPU', 'MTLGPUFamily', 'simdgroup', 'unified memory',
            'recommendedMaxWorkingSetSize', 'maxTransferRate',
            'Metal device:', 'GPU layers:',
            # llama.cpp internals
            'llama_', 'llm_load', 'load_tensors', 'loaded meta',
            'using device', 'offloading', 'kv_cache', 'compute_buffer',
            'model size:', 'model params:', 'total VRAM',
            'n_ctx_train', 'n_embd', 'n_head', 'n_layer', 'n_vocab',
            # Sampling info
            'sampling:', 'sampler chain', 'generate:', 'seed:',
            'repeat_penalty', 'frequency_penalty', 'presence_penalty',
            'top_k', 'top_p', 'min_p', 'tfs_z', 'typical_p', 'temp',
            # System info
            'system_info:', 'n_threads', 'AVX', 'AVX2', 'AVX512',
            'FMA', 'NEON', 'ARM_FMA', 'METAL', 'BLAS',
            # Progress indicators
            'llama_new_context', 'llama_kv_cache', 'eval time',
            'prompt eval time', 'sample time', 'total time',
            # Warnings comunes
            'warning:', 'warn:', 'note:',
        ]
        line_lower = line.lower()
        return any(p.lower() in line_lower for p in metal_patterns)

    def _clean_response(self, response: str) -> str:
        """Limpiar respuesta del modelo"""
        # === PRIMERO: Eliminar bloques <think>...</think> (Qwen3 thinking) ===
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE)
        # También eliminar tags de pensamiento incompletos
        response = re.sub(r'<think>.*$', '', response, flags=re.DOTALL | re.IGNORECASE)
        response = re.sub(r'^.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE)

        # Buscar marcador de respuesta
        markers = ["RESPUESTA:", "Respuesta:", "ANSWER:"]
        for marker in markers:
            if marker in response:
                response = response.split(marker)[-1].strip()
                break

        # Limpiar artifacts
        response = re.sub(r'\[end of text\]', '', response)
        response = re.sub(r'<\|.*?\|>', '', response)

        return response.strip()


# === CLI para pruebas ===
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: daemon_interface.py [status|send|cli] [args]")
        sys.exit(1)

    cmd = sys.argv[1]
    daemon = DaemonInterface()

    if cmd == "status":
        running = daemon.is_daemon_running()
        status = "🟢 Corriendo" if running else "🔴 No disponible"
        print(f"Estado del daemon: {status}")

    elif cmd == "send":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Hola, ¿cómo estás?"
        print(f"Enviando: {query}")
        if daemon.send_query(query):
            print("✅ Enviado, esperando respuesta...")
            response = daemon.wait_response()
            print(f"\n📤 Respuesta ({response.verdict.value}, {response.latency:.1f}s):")
            print(response.content)
        else:
            print("❌ Error enviando")

    elif cmd == "cli":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "¿Qué es Python?"
        cli = DaemonCLI()
        print(f"Ejecutando: {query}")
        response = cli.query(f"Pregunta: {query}\n\nRespuesta:")
        print(f"\n📤 Respuesta:")
        print(response)

    else:
        print(f"Comando desconocido: {cmd}")
