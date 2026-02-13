#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    AGENT RUNTIME - Loop Agentico Real
========================================
Implementa el loop Think→Act→Observe→Repeat.
El corazón del sistema agentico.
========================================
"""

import os
import sys
import re
import json
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# Setup path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.agentic.tool_registry import ToolRegistry, ToolResult, get_tool_registry
from core.agentic.agent_prompts import AgentPrompts, get_agent_prompts
from core.agentic.marker_protocol import (
    parse_markers, get_first_action, marker_to_tool_call,
    MarkerAction, MARKER_SYSTEM_PROMPT, get_marker_prompt
)

logger = logging.getLogger("AgentRuntime")


# ============================================================================
# PRE-PROCESSING PLANNER - Divide instrucciones compuestas en subtareas
# ============================================================================

# Conectores temporales en español que indican secuencia de tareas
TEMPORAL_CONNECTORS = [
    ", luego ", " luego ", " después ", " despues ", " entonces ",
    " a continuación", " seguidamente", " posteriormente",
    " finalmente ", " por último", " y después ", " y luego ",
    " una vez que ", " cuando termines", " al terminar",
    ", después ", ", y después "
]

# Patrones de secuencia implícita (verbo + objeto + "y" + verbo_referencia)
IMPLICIT_SEQUENCE_PATTERNS = [
    (r"busca\s+.+\s+y\s+(léelo|leelo|ábrelo|abrelo|muéstralo|muestralo|resúmelo|resumelo)", True),
    (r"encuentra\s+.+\s+y\s+(léelo|leelo|ábrelo|abrelo|muéstralo|muestralo|resúmelo|resumelo)", True),
    (r"localiza\s+.+\s+y\s+(léelo|leelo|resume|analiza|muéstralo|muestralo)", True),
    (r"lee\s+.+\s+y\s+(resume|resúmelo|resumelo|analiza|explica|detalla)", True),
    (r"abre\s+.+\s+y\s+(léelo|leelo|resume|resúmelo|resumelo|analiza)", True),
]

# Conectores de conjunción que pueden indicar tareas paralelas
CONJUNCTION_CONNECTORS = [
    " y ", ", y ", " e "
]


def parse_complex_intent(user_input: str) -> Dict[str, Any]:
    """
    Pre-Processing Planner: Analiza instrucciones compuestas y las divide en subtareas.

    Args:
        user_input: Instrucción del usuario

    Returns:
        Dict con:
        - is_complex: bool - Si es una instrucción compuesta
        - subtasks: List[str] - Lista de subtareas ordenadas
        - original: str - Instrucción original
        - suggested_plan: str - Plan sugerido para inyectar al agente
    """
    user_lower = user_input.lower().strip()
    subtasks = []
    is_complex = False

    # PRIMERO: Detectar patrones implícitos como "busca X y léelo"
    for pattern, _ in IMPLICIT_SEQUENCE_PATTERNS:
        match = re.search(pattern, user_lower)
        if match:
            is_complex = True
            # Dividir en: "busca X" y "léelo" (o similar)
            full_match = match.group(0)
            verb2 = match.group(1)  # léelo, resume, etc.

            # Extraer la primera parte (busca + objeto)
            idx = user_lower.find(full_match)
            if idx >= 0:
                # Buscar el " y " dentro del match
                y_pos = full_match.find(" y ")
                if y_pos > 0:
                    task1 = user_lower[:idx + y_pos].strip()
                    task2 = f"{verb2} el resultado anterior"
                    subtasks = [task1, task2]
            break

    # SEGUNDO: Detectar conectores temporales explícitos
    if not is_complex:
        for connector in TEMPORAL_CONNECTORS:
            if connector in user_lower:
                is_complex = True
                # Dividir por el conector
                parts = user_lower.split(connector, 1)
                if len(parts) == 2:
                    task1 = parts[0].strip().rstrip(",").strip()
                    task2 = parts[1].strip().lstrip(",").strip()
                    if task1 and task1 not in subtasks:
                        subtasks.append(task1)
                    if task2:
                        # Recursivamente analizar la segunda parte
                        sub_result = parse_complex_intent(task2)
                        if sub_result["subtasks"] and sub_result["is_complex"]:
                            subtasks.extend(sub_result["subtasks"])
                        elif task2 not in subtasks:
                            subtasks.append(task2)
                break

    # TERCERO: Detectar conjunciones con múltiples verbos de acción
    if not is_complex:
        for connector in CONJUNCTION_CONNECTORS:
            if connector in user_lower:
                parts = [p.strip() for p in user_lower.split(connector) if p.strip()]
                if len(parts) >= 2:
                    # Verificar si parecen tareas separadas (verbos diferentes)
                    action_verbs = ["busca", "lee", "escribe", "muestra", "lista",
                                   "ejecuta", "crea", "abre", "guarda", "resume",
                                   "analiza", "encuentra", "copia", "mueve", "borra",
                                   "localiza", "detalla", "explica"]
                    verb_count = sum(1 for p in parts if any(v in p for v in action_verbs))
                    if verb_count >= 2:
                        is_complex = True
                        subtasks = parts
                break

    # Si no se detectaron subtareas, la instrucción es simple
    if not subtasks:
        subtasks = [user_input]

    # Generar plan sugerido
    suggested_plan = ""
    if is_complex and len(subtasks) > 1:
        plan_lines = []
        for i, task in enumerate(subtasks, 1):
            # Inferir herramienta probable
            tool_hint = _infer_tool_for_task(task)
            plan_lines.append(f"Paso {i}: {task.capitalize()} → usar {tool_hint}")
        suggested_plan = "\n".join(plan_lines)

    return {
        "is_complex": is_complex,
        "subtasks": subtasks,
        "original": user_input,
        "suggested_plan": suggested_plan,
        "task_count": len(subtasks)
    }


def _infer_tool_for_task(task: str) -> str:
    """Inferir qué herramienta usar para una subtarea."""
    task_lower = task.lower()

    if any(w in task_lower for w in ["lee", "leer", "muestra contenido", "abre", "ver archivo"]):
        return "filesystem_read"
    elif any(w in task_lower for w in ["busca", "encuentra", "localiza", "dónde está"]):
        return "filesystem_search o grep_search"
    elif any(w in task_lower for w in ["lista", "muestra archivos", "qué hay en", "contenido de carpeta"]):
        return "filesystem_list"
    elif any(w in task_lower for w in ["escribe", "crea archivo", "guarda", "genera"]):
        return "filesystem_write"
    elif any(w in task_lower for w in ["git", "commit", "push", "estado repo"]):
        return "git_status/git_log"
    elif any(w in task_lower for w in ["ejecuta", "corre", "pip", "npm", "comando"]):
        return "bash_execute"
    elif any(w in task_lower for w in ["calcula", "suma", "python", "código"]):
        return "python_execute"
    elif any(w in task_lower for w in ["resume", "resumen", "analiza", "explica"]):
        return "filesystem_read (luego procesar)"
    else:
        return "herramienta apropiada"


# Mensaje de kickstart cuando el agente no ejecuta herramientas (formato JSON)
KICKSTART_MESSAGE_JSON = """ERROR: Responde SOLO con JSON.

Ejemplo para leer un archivo:
{"tool": "filesystem_read", "params": {"path": "/ruta/al/archivo"}}

Ejemplo para listar directorio:
{"tool": "filesystem_list", "params": {"path": "~/directorio"}}

Responde AHORA con el JSON de la herramienta que necesitas usar:"""

# Mensaje de kickstart para protocolo de marcadores [[comando]]
KICKSTART_MESSAGE_MARKERS = """ERROR: Usa marcadores [[comando]].

Ejemplos:
- Para leer: [[leer ~/archivo.txt]]
- Para listar: [[listar ~/carpeta]]
- Para buscar texto: [[buscar error en ~/logs]]
- Para responder: [[RESPUESTA: Tu respuesta aquí]]

Responde AHORA con el marcador adecuado:"""


class AgentState(Enum):
    """Estado del agente"""
    IDLE = "idle"
    THINKING = "thinking"
    PLANNING = "planning"
    ACTING = "acting"
    OBSERVING = "observing"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    ERROR = "error"
    WAITING_INPUT = "waiting_input"


@dataclass
class AgentStep:
    """Un paso en la ejecución del agente"""
    step_number: int
    state: AgentState
    thought: Optional[str] = None
    plan: Optional[List[str]] = None
    action: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    reflection: Optional[str] = None
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    duration: float = 0.0


@dataclass
class AgentResult:
    """Resultado final del agente"""
    success: bool
    response: str
    steps: List[AgentStep] = field(default_factory=list)
    total_time: float = 0.0
    tools_used: List[str] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentRuntime:
    """
    Runtime del agente con loop agentico real.

    Implementa:
    1. THINK: Analizar la tarea
    2. PLAN: Crear plan de acción
    3. ACT: Ejecutar herramienta
    4. OBSERVE: Analizar resultado
    5. REPEAT: Continuar hasta completar
    6. REFLECT: Resumen final

    Uso:
        runtime = AgentRuntime(llm_interface)
        result = runtime.execute("lista los archivos de ~/proyecto")
    """

    def __init__(
        self,
        llm_interface: Callable[[str], str],
        tool_registry: ToolRegistry = None,
        prompts: AgentPrompts = None,
        max_iterations: int = 10,
        verbose: bool = True,
        use_markers: bool = True  # NUEVO: Usar protocolo de marcadores simple
    ):
        """
        Inicializar runtime.

        Args:
            llm_interface: Función que recibe prompt y devuelve respuesta del LLM
            tool_registry: Registro de herramientas
            prompts: Configuración de prompts
            max_iterations: Máximo de iteraciones del loop
            verbose: Mostrar progreso
            use_markers: Usar protocolo de marcadores [[comando]] (recomendado para modelos pequeños)
        """
        self.llm = llm_interface
        self.tools = tool_registry or get_tool_registry()
        self.prompts = prompts or get_agent_prompts()
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.use_markers = use_markers
        self.max_history_length = 20  # FIX: Límite de historial para evitar OOM

        # Estado
        self._current_state = AgentState.IDLE
        self._steps: List[AgentStep] = []
        self._conversation_history: List[Dict[str, str]] = []
        self._empty_response_count = 0  # FIX: Contador para detectar loops vacíos
        self._pending_subtasks: List[str] = []  # Subtareas pendientes para tareas compuestas
        self._last_failed_action: Optional[Dict[str, Any]] = None  # FIX: Tracking de errores
        self._repeated_error_count = 0  # Contador de errores repetidos

    def execute(self, user_query: str) -> AgentResult:
        """
        Ejecutar tarea del usuario.

        Args:
            user_query: Consulta/tarea del usuario

        Returns:
            AgentResult con el resultado
        """
        start_time = time.time()
        self._steps = []
        self._conversation_history = []
        tools_used = []
        self._last_failed_action = None  # Reset error tracking
        self._repeated_error_count = 0

        # ============================================================
        # PRE-PROCESSING: Analizar si es instrucción compuesta
        # ============================================================
        intent_analysis = parse_complex_intent(user_query)

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"🤖 AGENTE INICIANDO")
            print(f"{'='*60}")
            print(f"📝 Tarea: {user_query}")
            if intent_analysis["is_complex"]:
                print(f"🔀 Tarea compuesta detectada: {intent_analysis['task_count']} subtareas")
                for i, st in enumerate(intent_analysis["subtasks"], 1):
                    print(f"   {i}. {st[:50]}...")
            print(f"{'='*60}\n")

        # Construir system prompt
        if self.use_markers:
            # Usar protocolo de marcadores simple [[comando]] con PWD
            pwd = os.getcwd()
            system_prompt = get_marker_prompt(pwd)
            if self.verbose:
                print(f"📋 Usando protocolo de MARCADORES [[comando]]")
                print(f"📂 PWD: {pwd}")
        else:
            # Usar formato JSON/XML tradicional
            tools_desc = self.tools.to_prompt_text()
            system_prompt = self.prompts.get_system_prompt(tools_desc)
            if self.verbose:
                print("📋 Usando protocolo JSON/XML")

        # Iniciar conversación
        self._conversation_history.append({
            "role": "system",
            "content": system_prompt
        })

        # Si es tarea compuesta, simplificar a la primera subtarea
        if intent_analysis["is_complex"] and len(intent_analysis["subtasks"]) > 1:
            first_task = intent_analysis["subtasks"][0]
            enhanced_query = f"""{first_task}

Responde con JSON: {{"tool": "nombre", "params": {{...}}}}"""
            self._conversation_history.append({
                "role": "user",
                "content": enhanced_query
            })
            # Guardar subtareas restantes para después
            self._pending_subtasks = intent_analysis["subtasks"][1:]
        else:
            self._conversation_history.append({
                "role": "user",
                "content": user_query
            })
            self._pending_subtasks = []

        # Loop principal
        iteration = 0
        final_response = ""
        empty_iterations = 0  # FIX: Contador de iteraciones vacías

        while iteration < self.max_iterations:
            iteration += 1
            step_start = time.time()

            if self.verbose:
                print(f"\n--- Iteración {iteration}/{self.max_iterations} ---")

            # 1. Obtener respuesta del LLM
            self._current_state = AgentState.THINKING
            prompt = self._build_prompt()

            if self.verbose:
                print("🧠 Pensando...")

            try:
                llm_response = self.llm(prompt)
            except Exception as e:
                logger.error(f"Error llamando LLM: {e}")
                return AgentResult(
                    success=False,
                    response="Error comunicándose con el modelo",
                    error=str(e),
                    total_time=time.time() - start_time
                )

            # FIX: Detectar respuesta vacía
            if not llm_response or not llm_response.strip():
                empty_iterations += 1
                logger.warning(f"Respuesta vacía del LLM (#{empty_iterations})")
                if empty_iterations >= 3:
                    logger.error("Demasiadas respuestas vacías, abortando")
                    return AgentResult(
                        success=False,
                        response="El modelo no está generando respuestas válidas.",
                        error="Too many empty responses",
                        total_time=time.time() - start_time
                    )
                # Continuar intentando
                self._conversation_history.append({
                    "role": "user",
                    "content": "Por favor, continúa con la tarea. Usa <action> o <response>."
                })
                continue
            else:
                empty_iterations = 0  # Reset si hay respuesta válida

            # DEBUG: Ver qué está respondiendo el modelo
            if self.verbose:
                print(f"📄 Respuesta LLM (primeros 500 chars):")
                print("-" * 40)
                print(llm_response[:500] if llm_response else "(vacío)")
                print("-" * 40)

            # 2. Parsear respuesta
            parsed = self._parse_response(llm_response)

            step = AgentStep(
                step_number=iteration,
                state=self._current_state,
                thought=parsed.get("think"),
                plan=parsed.get("plan"),
                action=parsed.get("action"),
                reflection=parsed.get("reflect"),
                timestamp=time.time()
            )

            # 3. Si hay respuesta final, terminar
            if parsed.get("response"):
                self._current_state = AgentState.COMPLETED
                final_response = parsed["response"]
                step.state = AgentState.COMPLETED
                step.duration = time.time() - step_start
                self._steps.append(step)

                if self.verbose:
                    print(f"✅ Tarea completada")
                break

            # 4. Si hay acción, ejecutarla
            if parsed.get("action"):
                self._current_state = AgentState.ACTING
                action = parsed["action"]
                tool_name = action.get("tool", "")
                params = action.get("params", {})

                if self.verbose:
                    print(f"🔧 Ejecutando: {tool_name}")
                    print(f"   Params: {json.dumps(params, ensure_ascii=False)[:100]}...")

                # Ejecutar herramienta
                result = self.tools.execute(tool_name, params)
                tools_used.append(tool_name)

                # 5. Observar resultado
                self._current_state = AgentState.OBSERVING

                if result.success:
                    observation = f"✅ Éxito:\n{result.output[:2000]}"
                    if len(result.output) > 2000:
                        observation += "\n... (truncado)"
                    # Reset error tracking on success
                    self._last_failed_action = None
                    self._repeated_error_count = 0
                else:
                    observation = f"❌ Error: {result.error}"

                    # FIX: Detectar si se repite la misma acción fallida
                    current_action_sig = f"{tool_name}:{json.dumps(params, sort_keys=True)}"
                    if self._last_failed_action == current_action_sig:
                        self._repeated_error_count += 1
                        if self.verbose:
                            print(f"⚠️ Acción repetida fallida #{self._repeated_error_count}")
                    else:
                        self._last_failed_action = current_action_sig
                        self._repeated_error_count = 1

                step.observation = observation

                if self.verbose:
                    print(f"👁️ Observación: {observation[:200]}...")

                # Agregar resultado a la conversación
                self._conversation_history.append({
                    "role": "assistant",
                    "content": llm_response
                })

                # FIX: Mensaje diferente si hay error repetido
                if not result.success and self._repeated_error_count >= 2:
                    error_msg = f"""<tool_result>
{observation}
</tool_result>

⚠️ ERROR REPETIDO: Esta acción ya falló antes.
NO la repitas. Opciones:
1. Usa una ruta diferente (la actual no existe)
2. Usa [[listar .]] para ver qué archivos hay
3. Usa [[RESPUESTA: explicación del error]] si no puedes continuar"""
                    self._conversation_history.append({
                        "role": "user",
                        "content": error_msg
                    })
                else:
                    self._conversation_history.append({
                        "role": "user",
                        "content": f"<tool_result>\n{observation}\n</tool_result>\n\nContinúa con el siguiente paso."
                    })

            else:
                # Sin acción ni respuesta - KICKSTART MECHANISM
                if self.verbose:
                    print("⚠️ Sin acción definida...")

                self._conversation_history.append({
                    "role": "assistant",
                    "content": llm_response
                })

                # KICKSTART: En las primeras iteraciones, forzar uso de herramienta
                if iteration <= 2:
                    if self.verbose:
                        print("🔄 KICKSTART: Forzando uso de herramienta...")

                    # Usar mensaje apropiado según el protocolo
                    kickstart_msg = KICKSTART_MESSAGE_MARKERS if self.use_markers else KICKSTART_MESSAGE_JSON
                    self._conversation_history.append({
                        "role": "user",
                        "content": kickstart_msg
                    })
                else:
                    # Después de 2 intentos, mensaje más suave
                    self._conversation_history.append({
                        "role": "user",
                        "content": "Continúa. Usa <action> para ejecutar una herramienta o <response> si terminaste."
                    })

            step.duration = time.time() - step_start
            self._steps.append(step)

            # FIX: Limitar historial de conversación para evitar OOM
            if len(self._conversation_history) > self.max_history_length:
                # Mantener system prompt (primer mensaje) y los últimos N-1 mensajes
                system_msg = self._conversation_history[0] if self._conversation_history else None
                recent = self._conversation_history[-(self.max_history_length - 1):]
                self._conversation_history = [system_msg] + recent if system_msg else recent
                logger.debug(f"Historial truncado a {len(self._conversation_history)} mensajes")

        # Si llegamos al máximo de iteraciones
        if iteration >= self.max_iterations and not final_response:
            self._current_state = AgentState.ERROR
            final_response = "Se alcanzó el límite de iteraciones sin completar la tarea."

        total_time = time.time() - start_time

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"📊 RESUMEN")
            print(f"{'='*60}")
            print(f"⏱️ Tiempo total: {total_time:.1f}s")
            print(f"🔄 Iteraciones: {iteration}")
            print(f"🔧 Herramientas: {', '.join(set(tools_used)) or 'ninguna'}")
            print(f"{'='*60}\n")

        return AgentResult(
            success=self._current_state == AgentState.COMPLETED,
            response=final_response,
            steps=self._steps,
            total_time=total_time,
            tools_used=list(set(tools_used)),
            metadata={
                "iterations": iteration,
                "max_iterations": self.max_iterations
            }
        )

    def _build_prompt(self) -> str:
        """Construir prompt para el LLM"""
        # Combinar historial de conversación
        parts = []
        for msg in self._conversation_history:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                parts.append(f"[SISTEMA]\n{content}")
            elif role == "user":
                parts.append(f"[USUARIO]\n{content}")
            elif role == "assistant":
                parts.append(f"[ASISTENTE]\n{content}")

        return "\n\n".join(parts)

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parsear respuesta del LLM.

        Soporta múltiples formatos (en orden de prioridad):
        1. MARCADORES [[comando]] - Formato más simple y robusto
        2. JSON puro: {"tool": "...", "params": {...}}
        3. JSON con done: {"done": true, "result": "..."}
        4. XML tags: <action>...</action>, <response>...</response>
        5. Texto con herramientas mencionadas
        """
        result = {}

        # Validar input
        if not response or not isinstance(response, str):
            logger.warning("Respuesta vacía o inválida para parsear")
            return result

        response = response.strip()
        if not response:
            return result

        # ============================================================
        # PRIORIDAD 0: MARCADORES [[comando]] - Formato simple
        # ============================================================
        marker_action = get_first_action(response)
        if marker_action:
            if marker_action.marker_type == 'response':
                # Marcador [[RESPUESTA: texto]]
                result["response"] = marker_action.params.get("text", "")
                logger.debug(f"Parseado marcador RESPUESTA: {result['response'][:100]}...")
                return result
            else:
                # Marcador de acción [[leer /ruta]], [[listar /dir]], etc.
                tool_call = marker_to_tool_call(marker_action)
                if tool_call:
                    result["action"] = tool_call
                    logger.debug(f"Parseado marcador {marker_action.marker_type}: {tool_call}")
                    return result
                elif not marker_action.is_safe:
                    # Acción bloqueada por seguridad
                    logger.warning(f"Marcador bloqueado: {marker_action.raw_marker} - {marker_action.error}")
                    result["response"] = f"⚠️ Acción bloqueada por seguridad: {marker_action.error}"
                    return result

        # ============================================================
        # PRIORIDAD 1: JSON puro (formato anterior)
        # ============================================================

        # Buscar JSON con "tool"
        json_tool_match = re.search(r'\{[^{}]*"tool"\s*:\s*"[^"]+"[^{}]*\}', response, re.DOTALL)
        if json_tool_match:
            try:
                json_obj = json.loads(json_tool_match.group(0))
                if "tool" in json_obj:
                    result["action"] = {
                        "tool": json_obj["tool"],
                        "params": json_obj.get("params", {})
                    }
                    logger.debug(f"Parseado JSON puro: {result['action']}")
                    return result
            except json.JSONDecodeError:
                pass

        # Buscar JSON con "done" (respuesta final)
        json_done_match = re.search(r'\{[^{}]*"done"\s*:\s*true[^{}]*\}', response, re.DOTALL | re.IGNORECASE)
        if json_done_match:
            try:
                json_obj = json.loads(json_done_match.group(0))
                if json_obj.get("done"):
                    result["response"] = json_obj.get("result", json_obj.get("message", "Tarea completada"))
                    return result
            except json.JSONDecodeError:
                pass

        # ============================================================
        # PRIORIDAD 2: Tags XML (formato anterior)
        # ============================================================

        # Extraer think
        think_match = re.search(r'<think>(.*?)</think>', response, re.DOTALL)
        if think_match:
            result["think"] = think_match.group(1).strip()

        # Extraer action con XML
        action_match = re.search(r'<action>(.*?)</action>', response, re.DOTALL)
        if action_match:
            action_text = action_match.group(1).strip()
            if action_text:
                try:
                    result["action"] = json.loads(action_text)
                except json.JSONDecodeError:
                    tool_match = re.search(r'"tool"\s*:\s*"([^"]+)"', action_text)
                    if tool_match:
                        result["action"] = {"tool": tool_match.group(1), "params": {}}
                        # Extraer params
                        params_match = re.search(r'"params"\s*:\s*(\{[^{}]*\})', action_text)
                        if params_match:
                            try:
                                result["action"]["params"] = json.loads(params_match.group(1))
                            except:
                                pass

        # Extraer response XML
        response_match = re.search(r'<response>(.*?)</response>', response, re.DOTALL)
        if response_match:
            result["response"] = response_match.group(1).strip()

        # FIX: Si no hay tags reconocidos, intentar detectar acciones de otras formas
        if "action" not in result and response:
            # INTENTO 1: Buscar JSON suelto con "tool"
            json_match = re.search(r'\{[^{}]*"tool"\s*:\s*"([^"]+)"[^{}]*\}', response, re.DOTALL)
            if json_match:
                try:
                    # Extraer el JSON completo
                    json_str = json_match.group(0)
                    result["action"] = json.loads(json_str)
                    logger.debug(f"Detectado JSON suelto: {result['action']}")
                except:
                    # Al menos extraer el nombre de la herramienta
                    result["action"] = {"tool": json_match.group(1), "params": {}}

            # INTENTO 2: Buscar patrones de texto como "Usaré filesystem_read"
            if "action" not in result:
                tool_names = ["filesystem_list", "filesystem_read", "filesystem_write",
                             "filesystem_search", "bash_execute", "git_status",
                             "git_log", "git_diff", "grep_search", "python_execute"]
                for tool in tool_names:
                    if tool in response.lower():
                        # Buscar si hay una ruta o parámetro cercano
                        path_match = re.search(r'["\']?(/[^\s"\']+|~/[^\s"\']+)["\']?', response)
                        params = {}
                        if path_match:
                            params["path"] = path_match.group(1).strip("\"'")
                        result["action"] = {"tool": tool, "params": params}
                        logger.debug(f"Inferido de texto: {tool} con params {params}")
                        break

            # INTENTO 3: Si no hay action ni response, y parece texto final, tratarlo como respuesta
            if "action" not in result and "response" not in result:
                if not any(tag in response for tag in ['<think>', '<action>', '<plan>']):
                    # Verificar si parece una conclusión
                    conclusion_markers = ["resumen:", "conclusión:", "resultado:", "archivo contiene",
                                          "el contenido", "aquí está", "encontré"]
                    if any(marker in response.lower() for marker in conclusion_markers):
                        result["response"] = response

        return result

    def get_state(self) -> AgentState:
        """Obtener estado actual"""
        return self._current_state

    def get_steps(self) -> List[AgentStep]:
        """Obtener pasos ejecutados"""
        return self._steps.copy()


# === SINGLETON Y FACTORY (thread-safe) ===

import threading
_runtime_instance: Optional[AgentRuntime] = None
_runtime_lock = threading.Lock()  # FIX: Proteger singleton


def get_agent_runtime(
    llm_interface: Callable[[str], str] = None,
    use_markers: bool = True,  # Por defecto usar marcadores
    **kwargs
) -> AgentRuntime:
    """
    Obtener instancia del runtime (thread-safe).

    Args:
        llm_interface: Función LLM (requerida la primera vez)
        use_markers: Usar protocolo de marcadores [[comando]] (recomendado)
        **kwargs: Argumentos adicionales para AgentRuntime
    """
    global _runtime_instance

    with _runtime_lock:
        if _runtime_instance is None:
            if llm_interface is None:
                raise ValueError("llm_interface es requerido la primera vez")
            _runtime_instance = AgentRuntime(llm_interface, use_markers=use_markers, **kwargs)
        elif llm_interface is not None:
            # Actualizar LLM si se proporciona
            _runtime_instance.llm = llm_interface

        return _runtime_instance


def create_agent_runtime(
    llm_interface: Callable[[str], str],
    **kwargs
) -> AgentRuntime:
    """Crear nueva instancia del runtime (no singleton)"""
    return AgentRuntime(llm_interface, **kwargs)


# === TEST ===

if __name__ == "__main__":
    # Mock LLM para testing con MARCADORES
    call_count = [0]  # Contador mutable para tracking

    def mock_llm_markers(prompt: str) -> str:
        """LLM simulado para testing con protocolo de marcadores"""
        call_count[0] += 1

        # Primera llamada: ejecutar acción
        if call_count[0] == 1:
            return "Voy a listar los archivos. [[listar ~/wikirag]]"

        # Segunda llamada (después de tool_result): dar respuesta final
        if "<tool_result>" in prompt or "Éxito" in prompt:
            return """[[RESPUESTA: El directorio ~/wikirag contiene:
- core/ - Núcleo del sistema
- agents/ - Agentes de IA
- scripts/ - Scripts de utilidad
- tests/ - Pruebas automatizadas]]"""

        return "[[RESPUESTA: No entendí la solicitud.]]"

    # Mock LLM para testing con JSON/XML (formato anterior)
    def mock_llm_json(prompt: str) -> str:
        """LLM simulado para testing con JSON"""
        if "lista los archivos" in prompt.lower():
            return '{"tool": "filesystem_list", "params": {"path": "~/wikirag"}}'
        elif "tool_result" in prompt.lower():
            return '{"done": true, "result": "El directorio contiene core, agents, scripts."}'
        else:
            return '{"done": true, "result": "No entendí la solicitud."}'

    print("=== TEST AGENT RUNTIME CON MARCADORES ===\n")

    # Test con marcadores (recomendado para modelos pequeños)
    runtime = AgentRuntime(
        llm_interface=mock_llm_markers,
        max_iterations=5,
        verbose=True,
        use_markers=True  # Protocolo de marcadores
    )

    result = runtime.execute("lista los archivos de ~/wikirag")

    print(f"\n=== RESULTADO ===")
    print(f"Éxito: {result.success}")
    print(f"Respuesta: {result.response[:200]}...")
    print(f"Herramientas: {result.tools_used}")
    print(f"Tiempo: {result.total_time:.1f}s")

    print("\n\n=== TEST CON JSON (formato anterior) ===\n")

    runtime2 = AgentRuntime(
        llm_interface=mock_llm_json,
        max_iterations=5,
        verbose=True,
        use_markers=False  # Protocolo JSON
    )

    result2 = runtime2.execute("lista los archivos de ~/wikirag")

    print(f"\n=== RESULTADO ===")
    print(f"Éxito: {result2.success}")
    print(f"Respuesta: {result2.response}")
    print(f"Herramientas: {result2.tools_used}")
