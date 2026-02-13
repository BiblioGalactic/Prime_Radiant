#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
📡 STREAMING - Respuestas en Tiempo Real
========================================
Sistema de streaming para mostrar respuestas del LLM token por token.

Ventajas:
- Mejor UX: El usuario ve la respuesta mientras se genera
- Menor latencia percibida
- Permite cancelar generación temprana

Modos:
- Console: Imprime directamente a stdout
- Callback: Llama función con cada chunk
- Buffer: Acumula en buffer para procesamiento posterior
"""

import os
import sys
import logging
import time
import threading
import queue
from typing import Callable, Optional, Generator, Any, Dict
from dataclasses import dataclass, field
from enum import Enum

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Streaming")


class StreamMode(Enum):
    """Modos de streaming"""
    CONSOLE = "console"     # Imprimir a stdout
    CALLBACK = "callback"   # Llamar función callback
    BUFFER = "buffer"       # Acumular en buffer
    QUEUE = "queue"         # Poner en cola thread-safe


@dataclass
class StreamChunk:
    """Chunk de stream"""
    content: str
    is_final: bool = False
    token_count: int = 0
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamResult:
    """Resultado completo de streaming"""
    full_response: str
    total_tokens: int
    total_time: float
    chunks_count: int
    was_cancelled: bool = False
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        """Indicador de éxito"""
        return self.error is None and not self.was_cancelled


class StreamingHandler:
    """
    Manejador de streaming para respuestas del LLM.

    Uso básico:
        handler = StreamingHandler(mode=StreamMode.CONSOLE)
        handler.start()
        for token in llm_response:
            handler.write(token)
        result = handler.finish()

    Uso con callback:
        def on_token(chunk):
            print(chunk.content, end='', flush=True)

        handler = StreamingHandler(mode=StreamMode.CALLBACK, callback=on_token)
        ...
    """

    def __init__(
        self,
        mode: StreamMode = StreamMode.CONSOLE,
        callback: Callable[[StreamChunk], None] = None,
        prefix: str = "",
        suffix: str = "\n",
        throttle_ms: int = 0
    ):
        """
        Inicializar handler de streaming.

        Args:
            mode: Modo de streaming
            callback: Función callback para modo CALLBACK
            prefix: Prefijo antes del primer chunk
            suffix: Sufijo después del último chunk
            throttle_ms: Delay entre chunks (ms)
        """
        self.mode = mode
        self.callback = callback
        self.prefix = prefix
        self.suffix = suffix
        self.throttle_ms = throttle_ms

        # Estado interno
        self._buffer = []
        self._queue = queue.Queue() if mode == StreamMode.QUEUE else None
        self._token_count = 0
        self._start_time = None
        self._is_started = False
        self._is_cancelled = False
        self._lock = threading.Lock()

    def start(self):
        """Iniciar streaming"""
        self._start_time = time.time()
        self._is_started = True
        self._buffer = []
        self._token_count = 0

        if self.prefix:
            self._output(self.prefix, is_prefix=True)

    def write(self, content: str) -> bool:
        """
        Escribir chunk al stream.

        Args:
            content: Contenido a escribir

        Returns:
            False si streaming fue cancelado
        """
        if not self._is_started:
            self.start()

        if self._is_cancelled:
            return False

        with self._lock:
            self._token_count += len(content.split())
            self._buffer.append(content)

        chunk = StreamChunk(
            content=content,
            token_count=self._token_count,
            metadata={"elapsed_ms": (time.time() - self._start_time) * 1000}
        )

        self._output_chunk(chunk)

        # Throttle si está configurado
        if self.throttle_ms > 0:
            time.sleep(self.throttle_ms / 1000)

        return True

    def write_line(self, content: str) -> bool:
        """Escribir línea completa"""
        return self.write(content + "\n")

    def cancel(self):
        """Cancelar streaming"""
        self._is_cancelled = True

    def finish(self) -> StreamResult:
        """
        Finalizar streaming y obtener resultado.

        Returns:
            StreamResult con respuesta completa y métricas
        """
        if self.suffix:
            self._output(self.suffix, is_suffix=True)

        elapsed = time.time() - self._start_time if self._start_time else 0

        result = StreamResult(
            full_response="".join(self._buffer),
            total_tokens=self._token_count,
            total_time=elapsed,
            chunks_count=len(self._buffer),
            was_cancelled=self._is_cancelled
        )

        self._is_started = False
        return result

    def _output_chunk(self, chunk: StreamChunk):
        """Enviar chunk según el modo"""
        if self.mode == StreamMode.CONSOLE:
            print(chunk.content, end='', flush=True)

        elif self.mode == StreamMode.CALLBACK and self.callback:
            try:
                self.callback(chunk)
            except Exception as e:
                logger.warning(f"Error en callback: {e}")

        elif self.mode == StreamMode.QUEUE and self._queue:
            self._queue.put(chunk)

        # BUFFER mode solo acumula (ya lo hacemos en write)

    def _output(self, content: str, is_prefix: bool = False, is_suffix: bool = False):
        """Output de prefix/suffix"""
        if self.mode == StreamMode.CONSOLE:
            print(content, end='', flush=True)
        elif self.mode == StreamMode.CALLBACK and self.callback:
            chunk = StreamChunk(
                content=content,
                metadata={"is_prefix": is_prefix, "is_suffix": is_suffix}
            )
            self.callback(chunk)

    def get_queue(self) -> Optional[queue.Queue]:
        """Obtener cola (solo modo QUEUE)"""
        return self._queue

    def get_buffer(self) -> str:
        """Obtener buffer acumulado"""
        return "".join(self._buffer)


class StreamingLLMWrapper:
    """
    Wrapper para hacer streaming de respuestas del DaemonInterface.

    Uso:
        wrapper = StreamingLLMWrapper(daemon_cli)
        for chunk in wrapper.generate_stream("¿Qué es Python?"):
            print(chunk.content, end='', flush=True)
    """

    def __init__(self, daemon_interface: Any):
        """
        Args:
            daemon_interface: DaemonCLI o DaemonInterface
        """
        self.daemon = daemon_interface

    def generate_stream(
        self,
        prompt: str,
        model_config: Dict = None,
        chunk_size: int = 1
    ) -> Generator[StreamChunk, None, None]:
        """
        Generar respuesta con streaming.

        Args:
            prompt: Prompt para el LLM
            model_config: Configuración del modelo
            chunk_size: Tamaño aproximado de chunks (palabras)

        Yields:
            StreamChunk con cada parte de la respuesta
        """
        start_time = time.time()
        token_count = 0

        try:
            # Llamar al daemon y obtener respuesta
            # Nota: DaemonCLI actual no soporta streaming real,
            # pero simulamos dividiendo la respuesta
            response = self.daemon.generate_simple(prompt)

            if not response:
                yield StreamChunk(
                    content="",
                    is_final=True,
                    metadata={"error": "Empty response"}
                )
                return

            # Simular streaming dividiendo en chunks
            words = response.split()
            buffer = []

            for i, word in enumerate(words):
                buffer.append(word)
                token_count += 1

                if len(buffer) >= chunk_size or i == len(words) - 1:
                    content = " ".join(buffer)
                    if i < len(words) - 1:
                        content += " "

                    is_final = (i == len(words) - 1)

                    yield StreamChunk(
                        content=content,
                        is_final=is_final,
                        token_count=token_count,
                        metadata={
                            "elapsed_ms": (time.time() - start_time) * 1000,
                            "progress": (i + 1) / len(words)
                        }
                    )

                    buffer = []

                    # Pequeño delay para simular streaming real
                    if not is_final:
                        time.sleep(0.01)

        except Exception as e:
            logger.error(f"Error en streaming: {e}")
            yield StreamChunk(
                content="",
                is_final=True,
                metadata={"error": str(e)}
            )


def stream_to_console(generator: Generator[StreamChunk, None, None], prefix: str = "💬 "):
    """
    Helper para imprimir stream a consola.

    Args:
        generator: Generador de chunks
        prefix: Prefijo inicial
    """
    print(prefix, end='', flush=True)

    full_response = []
    for chunk in generator:
        print(chunk.content, end='', flush=True)
        full_response.append(chunk.content)

        if chunk.is_final:
            print()  # Nueva línea al final

    return "".join(full_response)


def stream_with_spinner(
    generator: Generator[StreamChunk, None, None],
    spinner_chars: str = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
) -> str:
    """
    Stream con spinner mientras genera.

    Args:
        generator: Generador de chunks
        spinner_chars: Caracteres del spinner
    """
    import sys

    full_response = []
    spinner_idx = 0
    last_update = time.time()

    for chunk in generator:
        full_response.append(chunk.content)

        # Actualizar spinner cada 100ms
        now = time.time()
        if now - last_update > 0.1:
            spinner = spinner_chars[spinner_idx % len(spinner_chars)]
            sys.stdout.write(f"\r{spinner} Generando... ({chunk.token_count} tokens)")
            sys.stdout.flush()
            spinner_idx += 1
            last_update = now

        if chunk.is_final:
            # Limpiar línea del spinner
            sys.stdout.write("\r" + " " * 50 + "\r")
            sys.stdout.flush()

    return "".join(full_response)


# === TEST ===
if __name__ == "__main__":
    print("📡 Test de Streaming")
    print("=" * 50)

    # Test 1: Console mode
    print("\n1️⃣ Test Console Mode:")
    handler = StreamingHandler(mode=StreamMode.CONSOLE, prefix="   ")
    handler.start()
    for word in ["Hola,", " ", "esto", " ", "es", " ", "streaming!"]:
        handler.write(word)
        time.sleep(0.1)
    result = handler.finish()
    print(f"\n   Tokens: {result.total_tokens}, Tiempo: {result.total_time:.2f}s")

    # Test 2: Callback mode
    print("\n2️⃣ Test Callback Mode:")
    chunks_received = []

    def my_callback(chunk: StreamChunk):
        chunks_received.append(chunk.content)
        print(f"   Chunk: '{chunk.content}'")

    handler = StreamingHandler(mode=StreamMode.CALLBACK, callback=my_callback)
    handler.start()
    handler.write("Primera ")
    handler.write("parte. ")
    handler.write("Segunda parte.")
    result = handler.finish()
    print(f"   Total chunks: {len(chunks_received)}")

    # Test 3: Buffer mode
    print("\n3️⃣ Test Buffer Mode:")
    handler = StreamingHandler(mode=StreamMode.BUFFER)
    handler.start()
    handler.write("Acumulando ")
    handler.write("en ")
    handler.write("buffer...")
    result = handler.finish()
    print(f"   Buffer: '{result.full_response}'")

    print("\n✅ Tests completados")
