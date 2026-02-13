#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    CLAUDIA AGENT - Wrapper para asistente-ia
========================================
Integra Claudia (asistente de código local) como agente de WikiRAG.

Claudia aporta:
- Ejecución de comandos del sistema
- Análisis de archivos de código
- Modo agéntico (planificar → ejecutar → sintetizar)

Uso:
    from agents.claudia_agent import ClaudiaAgent, get_claudia_agent

    agent = get_claudia_agent()
    result = agent.execute("analiza el archivo main.py")
"""

import os
import sys
import subprocess
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ClaudiaAgent")

# Ruta a Claudia
CLAUDIA_PATH = os.path.expanduser("~/proyecto/asistente-ia")
CLAUDIA_SRC = os.path.join(CLAUDIA_PATH, "src")


@dataclass
class ClaudiaResult:
    """Resultado de ejecución de Claudia"""
    success: bool
    response: str
    mode: str  # "normal" o "agentic"
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class ClaudiaAgent:
    """
    Agente que envuelve a Claudia para tareas de código.

    Puede usarse de dos formas:
    1. Importando directamente los módulos de Claudia
    2. Llamando via subprocess (más aislado)
    """

    def __init__(
        self,
        claudia_path: str = None,
        use_subprocess: bool = True,
        agentic_by_default: bool = False,
        verbose: bool = False
    ):
        """
        Args:
            claudia_path: Ruta a asistente-ia
            use_subprocess: Si llamar via subprocess (más seguro) o importar
            agentic_by_default: Activar modo agéntico por defecto
            verbose: Modo verbose
        """
        self.claudia_path = claudia_path or CLAUDIA_PATH
        self.claudia_src = os.path.join(self.claudia_path, "src")
        self.use_subprocess = use_subprocess
        self.agentic_by_default = agentic_by_default
        self.verbose = verbose

        # Verificar que Claudia existe
        if not os.path.exists(self.claudia_src):
            logger.warning(f"⚠️ Claudia no encontrada en {self.claudia_path}")
            self._available = False
        else:
            self._available = True
            logger.info(f"✅ Claudia disponible en {self.claudia_path}")

        # Instancia interna (si no usamos subprocess)
        self._assistant = None

    @property
    def is_available(self) -> bool:
        """Verificar si Claudia está disponible"""
        return self._available

    def _init_assistant(self):
        """Inicializar asistente interno (lazy)"""
        if self._assistant is not None:
            return

        if not self._available:
            return

        try:
            # Añadir src de Claudia al path
            if self.claudia_src not in sys.path:
                sys.path.insert(0, self.claudia_src)

            from core.assistant import LocalAssistant
            from core.config import Config
            from core.agentic_extension import extend_assistant_with_agentic

            # Cargar configuración
            config_path = os.path.join(self.claudia_path, "config", "settings.json")
            config = Config(config_path)

            # Crear asistente con extensión agéntica
            AgenticAssistant = extend_assistant_with_agentic(LocalAssistant)
            self._assistant = AgenticAssistant(config, verbose=self.verbose)

            if self.agentic_by_default:
                self._assistant.toggle_agentic_mode(True)

            logger.info("✅ Claudia inicializada internamente")

        except Exception as e:
            logger.error(f"❌ Error inicializando Claudia: {e}")
            self._assistant = None

    def execute(self, task: str, agentic: bool = None, working_dir: str = None) -> ClaudiaResult:
        """
        Ejecutar tarea con Claudia.

        Args:
            task: Tarea a ejecutar (ej: "analiza main.py")
            agentic: Forzar modo agéntico (None = auto-detectar)
            working_dir: Directorio de trabajo

        Returns:
            ClaudiaResult con respuesta
        """
        if not self._available:
            return ClaudiaResult(
                success=False,
                response="",
                mode="none",
                error="Claudia no disponible"
            )

        # Determinar modo
        use_agentic = agentic if agentic is not None else self._should_use_agentic(task)
        mode = "agentic" if use_agentic else "normal"

        if self.use_subprocess:
            return self._execute_subprocess(task, use_agentic, working_dir)
        else:
            return self._execute_internal(task, use_agentic, working_dir)

    def _should_use_agentic(self, task: str) -> bool:
        """Determinar si usar modo agéntico"""
        if self.agentic_by_default:
            return True

        # Triggers para modo agéntico
        agentic_triggers = [
            'analiza completamente', 'investigación profunda', 'análisis exhaustivo',
            'modo agéntico', 'revisa todo', 'examina detalladamente',
            'analiza el proyecto', 'audita', 'refactoriza todo'
        ]

        task_lower = task.lower()
        return any(trigger in task_lower for trigger in agentic_triggers)

    def _execute_subprocess(self, task: str, agentic: bool, working_dir: str) -> ClaudiaResult:
        """Ejecutar via subprocess (aislado)"""
        try:
            cmd = [
                sys.executable,
                os.path.join(self.claudia_src, "main.py"),
            ]

            if agentic:
                cmd.append("--agentic")

            if self.verbose:
                cmd.append("--verbose")

            cmd.append(task)

            # Ejecutar
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutos máximo
                cwd=working_dir or self.claudia_path
            )

            if result.returncode == 0:
                return ClaudiaResult(
                    success=True,
                    response=result.stdout.strip(),
                    mode="agentic" if agentic else "normal",
                    metadata={"exit_code": result.returncode}
                )
            else:
                return ClaudiaResult(
                    success=False,
                    response=result.stdout.strip(),
                    mode="agentic" if agentic else "normal",
                    error=result.stderr.strip(),
                    metadata={"exit_code": result.returncode}
                )

        except subprocess.TimeoutExpired:
            return ClaudiaResult(
                success=False,
                response="",
                mode="agentic" if agentic else "normal",
                error="Timeout: Claudia tardó más de 5 minutos"
            )
        except Exception as e:
            return ClaudiaResult(
                success=False,
                response="",
                mode="agentic" if agentic else "normal",
                error=str(e)
            )

    def _execute_internal(self, task: str, agentic: bool, working_dir: str) -> ClaudiaResult:
        """Ejecutar internamente (importando módulos)"""
        try:
            self._init_assistant()

            if self._assistant is None:
                return ClaudiaResult(
                    success=False,
                    response="",
                    mode="none",
                    error="Claudia no pudo inicializarse"
                )

            # Cambiar directorio si se especifica
            original_dir = os.getcwd()
            if working_dir:
                os.chdir(working_dir)

            try:
                # Activar/desactivar modo agéntico
                self._assistant.toggle_agentic_mode(agentic)

                # Ejecutar
                response = self._assistant.execute(task)

                return ClaudiaResult(
                    success=True,
                    response=response,
                    mode="agentic" if agentic else "normal"
                )

            finally:
                os.chdir(original_dir)

        except Exception as e:
            return ClaudiaResult(
                success=False,
                response="",
                mode="agentic" if agentic else "normal",
                error=str(e)
            )

    def analyze_file(self, file_path: str, question: str = None) -> ClaudiaResult:
        """
        Analizar un archivo específico.

        Args:
            file_path: Ruta al archivo
            question: Pregunta específica sobre el archivo

        Returns:
            ClaudiaResult
        """
        if question:
            task = f"analiza el archivo {file_path} y responde: {question}"
        else:
            task = f"explica el archivo {file_path}"

        return self.execute(task)

    def run_command(self, command: str, working_dir: str = None) -> ClaudiaResult:
        """
        Ejecutar un comando del sistema via Claudia.

        Args:
            command: Comando a ejecutar
            working_dir: Directorio de trabajo

        Returns:
            ClaudiaResult
        """
        task = f"ejecuta el comando: {command}"
        return self.execute(task, agentic=False, working_dir=working_dir)

    def analyze_project(self, project_path: str = None) -> ClaudiaResult:
        """
        Análisis completo del proyecto (modo agéntico).

        Args:
            project_path: Ruta al proyecto

        Returns:
            ClaudiaResult
        """
        task = "analiza completamente la arquitectura del proyecto"
        return self.execute(task, agentic=True, working_dir=project_path)


# === SINGLETON ===
_claudia_instance: Optional[ClaudiaAgent] = None


def get_claudia_agent(
    use_subprocess: bool = True,
    agentic_by_default: bool = False,
    verbose: bool = False
) -> ClaudiaAgent:
    """Obtener instancia singleton de ClaudiaAgent"""
    global _claudia_instance

    if _claudia_instance is None:
        _claudia_instance = ClaudiaAgent(
            use_subprocess=use_subprocess,
            agentic_by_default=agentic_by_default,
            verbose=verbose
        )

    return _claudia_instance


# === CLI para pruebas ===
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ClaudiaAgent - Wrapper para asistente-ia")
    parser.add_argument("task", nargs="*", help="Tarea a ejecutar")
    parser.add_argument("--agentic", "-a", action="store_true", help="Forzar modo agéntico")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verbose")

    args = parser.parse_args()

    agent = ClaudiaAgent(verbose=args.verbose)

    if not agent.is_available:
        print("❌ Claudia no está disponible")
        sys.exit(1)

    if args.task:
        task = " ".join(args.task)
        print(f"🤖 Ejecutando: {task}")
        result = agent.execute(task, agentic=args.agentic)

        if result.success:
            print(f"✅ Modo: {result.mode}")
            print(result.response)
        else:
            print(f"❌ Error: {result.error}")
    else:
        print("Uso: claudia_agent.py <tarea>")
        print("Ejemplo: claudia_agent.py 'analiza el archivo main.py'")
