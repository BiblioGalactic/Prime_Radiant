#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
⚡ EXECUTOR - Módulo de Ejecución
========================================
Ejecuta los pasos del plan, usando las herramientas
disponibles y el LLM cuando es necesario.

Características:
- Ejecución paso a paso
- Uso de herramientas MCP
- Manejo de errores
- Registro de resultados
"""

import re
import json
import logging
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from .planner import Plan, PlanStep, StepStatus, StepType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Executor")


@dataclass
class StepResult:
    """Resultado de ejecutar un paso"""
    step_id: int
    success: bool
    output: str
    error: str = ""
    execution_time: float = 0
    tool_used: str = ""
    attempts: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "step_id": self.step_id,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "tool_used": self.tool_used,
            "attempts": self.attempts,
            "metadata": self.metadata
        }


@dataclass
class ExecutionContext:
    """Contexto de ejecución"""
    plan: Plan
    results: List[StepResult] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)  # Variables compartidas
    start_time: float = 0
    current_step_id: int = 0
    total_attempts: int = 0


class Executor:
    """
    Módulo de ejecución del agente.

    Ejecuta los pasos del plan usando:
    - LLM para razonamiento
    - Herramientas MCP para acciones
    - Código Python para operaciones específicas
    """

    EXECUTION_PROMPT = """Ejecuta el siguiente paso del plan.

PASO A EJECUTAR:
- ID: {step_id}
- Descripción: {description}
- Tipo: {step_type}
- Acción: {action}
- Herramienta sugerida: {tool_hint}

CONTEXTO:
- Tarea original: {task}
- Resultados anteriores: {previous_results}
- Variables disponibles: {variables}

HERRAMIENTAS DISPONIBLES:
{tools}

Para usar una herramienta, responde:
```json
{{
  "use_tool": true,
  "tool_name": "nombre_herramienta",
  "tool_params": {{"param": "valor"}},
  "reasoning": "Por qué uso esta herramienta"
}}
```

Para responder directamente sin herramienta:
```json
{{
  "use_tool": false,
  "direct_response": "Tu respuesta o resultado",
  "reasoning": "Tu razonamiento"
}}
```

Responde SOLO con el JSON."""

    def __init__(
        self,
        llm_interface: Any,
        tool_executor: Callable = None,
        available_tools: List[Dict] = None,
        verbose: bool = True
    ):
        """
        Args:
            llm_interface: Interfaz al LLM
            tool_executor: Función para ejecutar herramientas
            available_tools: Lista de herramientas disponibles
            verbose: Mostrar ejecución en consola
        """
        self.llm = llm_interface
        self.tool_executor = tool_executor
        self.available_tools = available_tools or []
        self.verbose = verbose

    def execute_plan(
        self,
        plan: Plan,
        on_step_complete: Callable = None,
        on_step_failed: Callable = None
    ) -> ExecutionContext:
        """
        Ejecutar todo el plan.

        Args:
            plan: Plan a ejecutar
            on_step_complete: Callback cuando paso completa
            on_step_failed: Callback cuando paso falla

        Returns:
            ExecutionContext con resultados
        """
        context = ExecutionContext(
            plan=plan,
            start_time=time.time()
        )

        if self.verbose:
            print("\n⚡ EJECUTANDO PLAN...")
            print(f"   📋 Total pasos: {len(plan.steps)}")

        while True:
            # Obtener siguiente paso
            step = plan.get_next_step()

            if step is None:
                # No hay más pasos o no se pueden ejecutar
                if plan.is_complete:
                    if self.verbose:
                        print("\n   ✅ PLAN COMPLETADO")
                    break
                elif plan.has_failures:
                    if self.verbose:
                        print("\n   ❌ PLAN TIENE FALLOS NO RECUPERABLES")
                    break
                else:
                    # Posible deadlock en dependencias
                    if self.verbose:
                        print("\n   ⚠️ No hay pasos ejecutables (posible deadlock)")
                    break

            # Ejecutar paso
            context.current_step_id = step.id
            result = self.execute_step(step, context)
            context.results.append(result)
            context.total_attempts += result.attempts

            if result.success:
                plan.mark_step_completed(step.id, result.output)
                if on_step_complete:
                    on_step_complete(step, result)
            else:
                plan.mark_step_failed(step.id, result.error)
                if on_step_failed:
                    should_continue = on_step_failed(step, result)
                    if not should_continue:
                        break

        return context

    def execute_step(self, step: PlanStep, context: ExecutionContext) -> StepResult:
        """
        Ejecutar un solo paso.

        Args:
            step: Paso a ejecutar
            context: Contexto de ejecución

        Returns:
            StepResult con resultado
        """
        start_time = time.time()
        step.status = StepStatus.IN_PROGRESS

        if self.verbose:
            print(f"\n   ▶️ Paso {step.id}: {step.description[:50]}...")

        # Preparar contexto para el prompt
        previous_results = self._format_previous_results(context.results[-3:])  # Últimos 3

        # Construir prompt
        prompt = self.EXECUTION_PROMPT.format(
            step_id=step.id,
            description=step.description,
            step_type=step.type.value,
            action=step.action,
            tool_hint=step.tool_hint or "Ninguna específica",
            task=context.plan.task,
            previous_results=previous_results,
            variables=json.dumps(context.variables, ensure_ascii=False),
            tools=self._format_tools()
        )

        # Llamar al LLM para decidir cómo ejecutar
        try:
            response = self._call_llm(prompt)
            parsed = self._parse_response(response)
        except Exception as e:
            logger.error(f"Error en LLM: {e}")
            return StepResult(
                step_id=step.id,
                success=False,
                output="",
                error=f"Error en LLM: {str(e)}",
                execution_time=time.time() - start_time
            )

        # Ejecutar según la respuesta
        if parsed.get("use_tool", False):
            result = self._execute_with_tool(step, parsed, context)
        else:
            result = self._execute_direct(step, parsed, context)

        result.execution_time = time.time() - start_time

        if self.verbose:
            status = "✅" if result.success else "❌"
            print(f"      {status} {result.output[:80] if result.success else result.error[:80]}...")

        return result

    def _execute_with_tool(
        self,
        step: PlanStep,
        parsed: Dict,
        context: ExecutionContext
    ) -> StepResult:
        """Ejecutar paso usando herramienta"""
        tool_name = parsed.get("tool_name", "")
        tool_params = parsed.get("tool_params", {})

        if self.verbose:
            print(f"      🔧 Usando herramienta: {tool_name}")

        if not self.tool_executor:
            return StepResult(
                step_id=step.id,
                success=False,
                output="",
                error="No hay ejecutor de herramientas configurado",
                tool_used=tool_name
            )

        try:
            # Ejecutar herramienta
            tool_result = self.tool_executor(tool_name, tool_params)

            # Procesar resultado
            if isinstance(tool_result, dict):
                if tool_result.get("error"):
                    return StepResult(
                        step_id=step.id,
                        success=False,
                        output="",
                        error=tool_result.get("error", "Error desconocido"),
                        tool_used=tool_name
                    )
                output = tool_result.get("result", str(tool_result))
            else:
                output = str(tool_result)

            # Guardar en variables si es necesario
            context.variables[f"step_{step.id}_result"] = output

            return StepResult(
                step_id=step.id,
                success=True,
                output=output,
                tool_used=tool_name
            )

        except Exception as e:
            return StepResult(
                step_id=step.id,
                success=False,
                output="",
                error=f"Error ejecutando {tool_name}: {str(e)}",
                tool_used=tool_name
            )

    def _execute_direct(
        self,
        step: PlanStep,
        parsed: Dict,
        context: ExecutionContext
    ) -> StepResult:
        """Ejecutar paso directamente (sin herramienta)"""
        direct_response = parsed.get("direct_response", "")
        reasoning = parsed.get("reasoning", "")

        if not direct_response:
            # Si no hay respuesta directa, usar el LLM para ejecutar
            return self._execute_with_llm(step, context)

        # Guardar en variables
        context.variables[f"step_{step.id}_result"] = direct_response

        return StepResult(
            step_id=step.id,
            success=True,
            output=direct_response,
            metadata={"reasoning": reasoning}
        )

    def _execute_with_llm(
        self,
        step: PlanStep,
        context: ExecutionContext
    ) -> StepResult:
        """Ejecutar paso usando LLM directamente"""
        prompt = f"""Ejecuta esta acción y proporciona el resultado:

ACCIÓN: {step.action}
DESCRIPCIÓN: {step.description}

CONTEXTO:
{json.dumps(context.variables, indent=2, ensure_ascii=False)}

Proporciona el resultado de forma clara y concisa."""

        try:
            result = self._call_llm(prompt)
            context.variables[f"step_{step.id}_result"] = result

            return StepResult(
                step_id=step.id,
                success=True,
                output=result
            )
        except Exception as e:
            return StepResult(
                step_id=step.id,
                success=False,
                output="",
                error=str(e)
            )

    def _call_llm(self, prompt: str) -> str:
        """Llamar al LLM"""
        if hasattr(self.llm, 'generate_simple'):
            return self.llm.generate_simple(prompt, max_tokens=800)
        elif hasattr(self.llm, 'generate'):
            return self.llm.generate(prompt)
        elif callable(self.llm):
            return self.llm(prompt)
        else:
            raise ValueError("Interfaz LLM no reconocida")

    def _parse_response(self, response: str) -> Dict:
        """Parsear respuesta del LLM"""
        # Intentar extraer JSON
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Intentar parsear directamente
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Respuesta directa si no es JSON
        return {
            "use_tool": False,
            "direct_response": response,
            "reasoning": "Respuesta directa del LLM"
        }

    def _format_previous_results(self, results: List[StepResult]) -> str:
        """Formatear resultados anteriores"""
        if not results:
            return "(Ninguno)"

        lines = []
        for r in results:
            status = "✅" if r.success else "❌"
            lines.append(f"- Paso {r.step_id} {status}: {r.output[:100] if r.output else r.error[:100]}")

        return "\n".join(lines)

    def _format_tools(self) -> str:
        """Formatear herramientas disponibles"""
        if not self.available_tools:
            return "- Sin herramientas específicas disponibles"

        lines = []
        for tool in self.available_tools[:10]:  # Máximo 10
            if isinstance(tool, dict):
                lines.append(f"- {tool.get('name', '?')}: {tool.get('description', '')[:50]}")
            else:
                lines.append(f"- {tool}")

        return "\n".join(lines)


# === SIMPLE EXECUTOR ===
class SimpleExecutor(Executor):
    """
    Ejecutor simple que no usa LLM para decisiones.
    Solo ejecuta herramientas directamente.
    """

    def execute_step(self, step: PlanStep, context: ExecutionContext) -> StepResult:
        """Ejecutar paso directamente"""
        start_time = time.time()
        step.status = StepStatus.IN_PROGRESS

        if self.verbose:
            print(f"\n   ▶️ Paso {step.id}: {step.description[:50]}...")

        # Si hay herramienta sugerida, usarla
        if step.tool_hint and self.tool_executor:
            result = self._execute_with_tool(
                step,
                {"tool_name": step.tool_hint, "tool_params": step.action_params},
                context
            )
        else:
            # Ejecutar acción como respuesta directa
            context.variables[f"step_{step.id}_result"] = step.action
            result = StepResult(
                step_id=step.id,
                success=True,
                output=f"Ejecutado: {step.action}"
            )

        result.execution_time = time.time() - start_time

        if self.verbose:
            status = "✅" if result.success else "❌"
            print(f"      {status} {result.output[:80] if result.success else result.error[:80]}...")

        return result
