#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    BASE AGENT - Clase Base de Agentes
========================================
Define la estructura base para todos los agentes del sistema.
Cada agente es una llamada única al CLI (no daemon).
"""

import os
import re
import time
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Agent")


class AgentStatus(Enum):
    """Estados de un agente"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentResult:
    """Resultado de ejecución de un agente"""
    agent_name: str
    status: AgentStatus
    output: str
    latency: float  # Segundos
    tool_calls: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class Tool:
    """Definición de una herramienta"""
    name: str
    description: str
    parameters: List[str]
    handler: Optional[callable] = None


class BaseAgent(ABC):
    """
    Clase base abstracta para agentes.

    Un agente:
    - Recibe un miniprompt con una tarea específica
    - Tiene acceso a herramientas (MCP)
    - Ejecuta una llamada al CLI de llama
    - Retorna un resultado estructurado
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        tools: List[Tool] = None,
        model_path: str = None,
        llama_cli: str = None,
        timeout: int = 60
    ):
        """
        Inicializar agente.

        Args:
            name: Nombre identificador del agente
            description: Descripción de las capacidades
            tools: Lista de herramientas disponibles
            model_path: Ruta al modelo GGUF
            llama_cli: Ruta al ejecutable llama-cli
            timeout: Timeout en segundos
        """
        # Importar config
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
        from config import config

        self.name = name
        self.description = description
        self.tools = tools or []
        self.timeout = timeout

        # Configuración del modelo
        self.model_path = model_path or config.MODEL_AGENTS.path
        self.llama_cli = llama_cli or config.LLAMA_CLI
        self.model_config = config.MODEL_AGENTS

        # Estado
        self.status = AgentStatus.PENDING
        self._tool_calls: List[Dict] = []

    @abstractmethod
    def build_prompt(self, task: str, context: str = "") -> str:
        """
        Construir el prompt para el agente.

        Args:
            task: Tarea a realizar
            context: Contexto adicional

        Returns:
            Prompt completo
        """
        pass

    @abstractmethod
    def parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parsear la respuesta del modelo.

        Args:
            response: Respuesta raw del modelo

        Returns:
            Diccionario con datos parseados
        """
        pass

    def execute(self, task: str, context: str = "") -> AgentResult:
        """
        Ejecutar el agente.

        Args:
            task: Tarea a realizar
            context: Contexto adicional

        Returns:
            AgentResult con el resultado
        """
        self.status = AgentStatus.RUNNING
        self._tool_calls = []
        start_time = time.time()

        try:
            # Construir prompt
            prompt = self.build_prompt(task, context)

            # Ejecutar modelo
            response = self._call_model(prompt)

            # Verificar si hay llamadas a herramientas
            tool_match = re.search(r'\[TOOL:(\w+):([^\]]*)\]', response)
            while tool_match:
                tool_name = tool_match.group(1)
                tool_params = tool_match.group(2)

                # Ejecutar herramienta
                tool_result = self._execute_tool(tool_name, tool_params)
                self._tool_calls.append({
                    "tool": tool_name,
                    "params": tool_params,
                    "result": tool_result
                })

                # Continuar con resultado de herramienta
                continuation_prompt = f"{prompt}\n\n{response}\n\n[TOOL_RESULT:{tool_name}]: {tool_result}\n\nContinúa:"
                response = self._call_model(continuation_prompt)
                tool_match = re.search(r'\[TOOL:(\w+):([^\]]*)\]', response)

            # Parsear respuesta final
            parsed = self.parse_response(response)
            latency = time.time() - start_time

            # Determinar status
            if parsed.get("error"):
                self.status = AgentStatus.FAILED
            elif parsed.get("partial"):
                self.status = AgentStatus.PARTIAL
            else:
                self.status = AgentStatus.SUCCESS

            return AgentResult(
                agent_name=self.name,
                status=self.status,
                output=parsed.get("output", response),
                latency=latency,
                tool_calls=self._tool_calls,
                metadata=parsed.get("metadata", {}),
                error=parsed.get("error")
            )

        except subprocess.TimeoutExpired:
            self.status = AgentStatus.TIMEOUT
            return AgentResult(
                agent_name=self.name,
                status=self.status,
                output="",
                latency=self.timeout,
                error="Timeout ejecutando agente"
            )

        except Exception as e:
            self.status = AgentStatus.FAILED
            return AgentResult(
                agent_name=self.name,
                status=self.status,
                output="",
                latency=time.time() - start_time,
                error=str(e)
            )

    def _call_model(self, prompt: str) -> str:
        """Ejecutar llamada al modelo vía CLI"""
        try:
            # Escribir prompt a archivo temporal
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(prompt)
                prompt_file = f.name

            # Construir comando
            cmd = [
                self.llama_cli,
                "--model", self.model_path,
                "--file", prompt_file,
                "--n-predict", str(self.model_config.n_predict),
                "--ctx-size", str(self.model_config.ctx_size),
                "--temp", str(self.model_config.temperature),
                "--repeat-penalty", str(self.model_config.repeat_penalty),
                "--threads", str(self.model_config.threads),
            ]

            # Ejecutar
            logger.debug(f"[{self.name}] Ejecutando modelo...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # Limpiar archivo temporal
            Path(prompt_file).unlink(missing_ok=True)

            if result.returncode == 0:
                return self._clean_response(result.stdout.strip())
            else:
                raise RuntimeError(f"Error llama-cli: {result.stderr}")

        except subprocess.TimeoutExpired:
            Path(prompt_file).unlink(missing_ok=True)
            raise

    def _clean_response(self, response: str) -> str:
        """Limpiar respuesta del modelo"""
        # Buscar marcador de respuesta
        markers = ["RESPUESTA:", "OUTPUT:", "RESULTADO:"]
        for marker in markers:
            if marker in response:
                response = response.split(marker)[-1].strip()
                break

        # Limpiar artifacts
        response = re.sub(r'\[end of text\]', '', response)
        response = re.sub(r'<\|.*?\|>', '', response)
        response = re.sub(r'^\s*Pregunta:.*?\n', '', response, flags=re.MULTILINE)

        return response.strip()

    def _execute_tool(self, tool_name: str, params: str) -> str:
        """Ejecutar una herramienta"""
        for tool in self.tools:
            if tool.name == tool_name and tool.handler:
                try:
                    # Parsear parámetros
                    param_list = [p.strip() for p in params.split(',')]
                    return tool.handler(*param_list)
                except Exception as e:
                    return f"Error en herramienta {tool_name}: {e}"

        return f"Herramienta no encontrada: {tool_name}"

    def can_handle(self, task_type: str) -> bool:
        """Verificar si el agente puede manejar un tipo de tarea"""
        return True  # Por defecto, acepta todo


class GenericAgent(BaseAgent):
    """
    Agente genérico para tareas generales.
    """

    def build_prompt(self, task: str, context: str = "") -> str:
        """Construir prompt genérico"""
        tools_desc = ""
        if self.tools:
            tools_desc = "\n\nHERRAMIENTAS DISPONIBLES:\n"
            for tool in self.tools:
                tools_desc += f"- {tool.name}: {tool.description}\n"
            tools_desc += "\nPara usar: [TOOL:nombre:parametros]\n"

        prompt = f"""Eres {self.name}, un agente especializado.
{self.description}
{tools_desc}

TAREA: {task}
"""
        if context:
            prompt += f"\nCONTEXTO:\n{context}\n"

        prompt += """
INSTRUCCIONES:
- Ejecuta la tarea de forma precisa
- Si necesitas una herramienta, usa [TOOL:nombre:param1,param2]
- Si no puedes completar la tarea, explica por qué
- Sé conciso y directo

RESPUESTA:"""

        return prompt

    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parsear respuesta genérica"""
        result = {
            "output": response,
            "metadata": {},
            "error": None,
            "partial": False
        }

        # Detectar errores
        error_patterns = [
            r"no puedo",
            r"error",
            r"imposible",
            r"no tengo acceso"
        ]
        for pattern in error_patterns:
            if re.search(pattern, response.lower()):
                result["partial"] = True
                break

        return result


class SearchAgent(BaseAgent):
    """
    Agente especializado en búsquedas.
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="SearchAgent",
            description="Agente especializado en búsquedas de información",
            **kwargs
        )

    def build_prompt(self, task: str, context: str = "") -> str:
        prompt = f"""Eres un agente de búsqueda experto.

TAREA DE BÚSQUEDA: {task}
"""
        if context:
            prompt += f"\nCONTEXTO DISPONIBLE:\n{context}\n"

        prompt += """
INSTRUCCIONES:
- Analiza la información disponible
- Extrae los datos relevantes
- Si necesitas buscar en web, usa [TOOL:web_search:query]
- Presenta los resultados de forma estructurada

RESULTADO DE BÚSQUEDA:"""

        return prompt

    def parse_response(self, response: str) -> Dict[str, Any]:
        return {
            "output": response,
            "metadata": {"type": "search"},
            "error": None,
            "partial": False
        }


class CodeAgent(BaseAgent):
    """
    Agente especializado en código.
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="CodeAgent",
            description="Agente especializado en análisis y generación de código",
            **kwargs
        )

    def build_prompt(self, task: str, context: str = "") -> str:
        prompt = f"""Eres un agente experto en programación.

TAREA DE CÓDIGO: {task}
"""
        if context:
            prompt += f"\nCÓDIGO/CONTEXTO:\n```\n{context}\n```\n"

        prompt += """
INSTRUCCIONES:
- Analiza el código si se proporciona
- Genera código limpio y documentado
- Si necesitas ejecutar Python, usa [TOOL:python_exec:codigo]
- Explica tu solución brevemente

CÓDIGO/SOLUCIÓN:"""

        return prompt

    def parse_response(self, response: str) -> Dict[str, Any]:
        # Extraer bloques de código
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', response, re.DOTALL)

        return {
            "output": response,
            "metadata": {
                "type": "code",
                "code_blocks": code_blocks
            },
            "error": None,
            "partial": False
        }


class ValidationAgent(BaseAgent):
    """
    Agente especializado en validación.
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="ValidationAgent",
            description="Agente especializado en validación y verificación",
            **kwargs
        )

    def build_prompt(self, task: str, context: str = "") -> str:
        prompt = f"""Eres un agente validador experto.

TAREA DE VALIDACIÓN: {task}
"""
        if context:
            prompt += f"\nCONTENIDO A VALIDAR:\n{context}\n"

        prompt += """
INSTRUCCIONES:
- Analiza el contenido proporcionado
- Verifica si cumple con los requisitos
- Identifica errores o inconsistencias
- Da un veredicto: OK, PARCIAL o FALLA

VEREDICTO:"""

        return prompt

    def parse_response(self, response: str) -> Dict[str, Any]:
        # Extraer veredicto
        verdict = "PARCIAL"  # Default
        if re.search(r'\bOK\b', response, re.IGNORECASE):
            verdict = "OK"
        elif re.search(r'\bFALLA\b', response, re.IGNORECASE):
            verdict = "FALLA"

        return {
            "output": response,
            "metadata": {
                "type": "validation",
                "verdict": verdict
            },
            "error": None if verdict != "FALLA" else "Validación fallida",
            "partial": verdict == "PARCIAL"
        }


# === Factory de agentes ===
class AgentFactory:
    """Fábrica para crear agentes"""

    _registry: Dict[str, type] = {
        "generic": GenericAgent,
        "search": SearchAgent,
        "code": CodeAgent,
        "validation": ValidationAgent,
    }

    @classmethod
    def register(cls, agent_type: str, agent_class: type):
        """Registrar tipo de agente"""
        cls._registry[agent_type] = agent_class

    @classmethod
    def create(cls, agent_type: str, **kwargs) -> BaseAgent:
        """Crear agente por tipo"""
        if agent_type not in cls._registry:
            raise ValueError(f"Tipo de agente desconocido: {agent_type}")
        return cls._registry[agent_type](**kwargs)

    @classmethod
    def list_types(cls) -> List[str]:
        """Listar tipos disponibles"""
        return list(cls._registry.keys())


# === CLI para pruebas ===
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Uso: base_agent.py [generic|search|code|validation] <tarea>")
        print(f"Tipos disponibles: {AgentFactory.list_types()}")
        sys.exit(1)

    agent_type = sys.argv[1]
    task = " ".join(sys.argv[2:])

    print(f"🤖 Creando agente: {agent_type}")
    print(f"📋 Tarea: {task}")

    try:
        agent = AgentFactory.create(agent_type)
        result = agent.execute(task)

        print(f"\n📤 Resultado ({result.status.value}, {result.latency:.1f}s):")
        print(result.output)

        if result.tool_calls:
            print(f"\n🔧 Herramientas usadas: {len(result.tool_calls)}")
            for tc in result.tool_calls:
                print(f"   - {tc['tool']}: {tc['result'][:50]}...")

    except Exception as e:
        print(f"❌ Error: {e}")
