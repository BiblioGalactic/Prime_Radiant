"""
VERSIONE5: Interfaz simple con llama-cli
Solo subprocess, sin daemons ni complejidad
"""

import subprocess
import json
from pathlib import Path
from config import MODEL_PATH, MAX_TOKENS, TEMPERATURE


class SimpleLLM:
    """Interfaz minimalista con un modelo GGUF via llama-cli"""

    def __init__(self):
        self.model_path = MODEL_PATH
        self._verify_llama_cli()

    def _verify_llama_cli(self):
        """Verifica que llama-cli esté disponible"""
        try:
            subprocess.run(
                ["llama-cli", "--version"],
                capture_output=True,
                timeout=5,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "llama-cli no encontrado. Instala: "
                "https://github.com/ggerganov/llama.cpp/releases"
            )
        except Exception as e:
            raise RuntimeError(f"Error al verificar llama-cli: {e}")

    def query(self, prompt: str) -> str:
        """
        Envía un prompt al modelo GGUF y retorna la respuesta.

        Args:
            prompt: String con el prompt

        Returns:
            Respuesta del modelo
        """
        try:
            cmd = [
                "llama-cli",
                "-m", self.model_path,
                "-p", prompt,
                "-n", str(MAX_TOKENS),
                "--temp", str(TEMPERATURE),
                "--no-display-prompt",
                "-e",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                raise RuntimeError(f"llama-cli error: {result.stderr}")

            response = result.stdout.strip()
            return response if response else "No se generó respuesta"

        except subprocess.TimeoutExpired:
            return "Error: Tiempo de espera agotado (timeout)"
        except Exception as e:
            return f"Error al consultar modelo: {e}"

    def stream_query(self, prompt: str):
        """
        Versión streaming del query (genera tokens uno a uno)
        """
        cmd = [
            "llama-cli",
            "-m", self.model_path,
            "-p", prompt,
            "-n", str(MAX_TOKENS),
            "--temp", str(TEMPERATURE),
            "--no-display-prompt",
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            for line in process.stdout:
                yield line.rstrip("\n")
        finally:
            process.terminate()
            process.wait()
