#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
📋 PLANNER - Módulo de Planificación
========================================
Crea planes de ejecución estructurados basándose
en el análisis del Thinker.

Genera:
- Lista ordenada de pasos
- Dependencias entre pasos
- Criterios de verificación por paso
- Estrategias de rollback si falla
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Planner")


class StepStatus(Enum):
    """Estado de un paso del plan"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CORRECTED = "corrected"


class StepType(Enum):
    """Tipo de paso"""
    ANALYSIS = "analysis"       # Analizar algo
    SEARCH = "search"           # Buscar información
    CREATE = "create"           # Crear algo nuevo
    MODIFY = "modify"           # Modificar existente
    EXECUTE = "execute"         # Ejecutar comando/acción
    VERIFY = "verify"           # Verificar resultado
    COMMUNICATE = "communicate" # Comunicar al usuario


@dataclass
class PlanStep:
    """Un paso del plan de ejecución"""
    id: int
    description: str
    type: StepType = StepType.EXECUTE
    status: StepStatus = StepStatus.PENDING

    # Dependencias
    depends_on: List[int] = field(default_factory=list)

    # Ejecución
    action: str = ""
    action_params: Dict[str, Any] = field(default_factory=dict)
    tool_hint: str = ""  # Herramienta sugerida

    # Verificación
    verification_criteria: str = ""
    expected_output: str = ""

    # Resultado
    result: str = ""
    error: str = ""
    attempts: int = 0
    max_attempts: int = 3

    # Corrección
    correction_strategy: str = ""
    rollback_action: str = ""

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "description": self.description,
            "type": self.type.value,
            "status": self.status.value,
            "depends_on": self.depends_on,
            "action": self.action,
            "action_params": self.action_params,
            "tool_hint": self.tool_hint,
            "verification_criteria": self.verification_criteria,
            "expected_output": self.expected_output,
            "result": self.result,
            "error": self.error,
            "attempts": self.attempts,
            "correction_strategy": self.correction_strategy
        }

    def can_execute(self, completed_steps: List[int]) -> bool:
        """Verificar si el paso puede ejecutarse (dependencias cumplidas)"""
        return all(dep in completed_steps for dep in self.depends_on)

    def mark_completed(self, result: str):
        """Marcar como completado"""
        self.status = StepStatus.COMPLETED
        self.result = result

    def mark_failed(self, error: str):
        """Marcar como fallido"""
        self.status = StepStatus.FAILED
        self.error = error
        self.attempts += 1


@dataclass
class Plan:
    """Plan de ejecución completo"""
    task: str
    steps: List[PlanStep] = field(default_factory=list)
    created_at: float = 0
    estimated_duration: str = ""
    overall_strategy: str = ""
    success_criteria: str = ""

    # Estado
    current_step: int = 0
    completed_steps: List[int] = field(default_factory=list)
    failed_steps: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "task": self.task,
            "steps": [s.to_dict() for s in self.steps],
            "overall_strategy": self.overall_strategy,
            "success_criteria": self.success_criteria,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "progress": self.progress
        }

    @property
    def progress(self) -> float:
        """Progreso del plan (0.0 a 1.0)"""
        if not self.steps:
            return 0.0
        return len(self.completed_steps) / len(self.steps)

    @property
    def is_complete(self) -> bool:
        """¿Se completó el plan?"""
        return len(self.completed_steps) == len(self.steps)

    @property
    def has_failures(self) -> bool:
        """¿Hay pasos fallidos?"""
        return len(self.failed_steps) > 0

    def get_next_step(self) -> Optional[PlanStep]:
        """Obtener siguiente paso ejecutable"""
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                if step.can_execute(self.completed_steps):
                    return step
        return None

    def mark_step_completed(self, step_id: int, result: str):
        """Marcar paso como completado"""
        for step in self.steps:
            if step.id == step_id:
                step.mark_completed(result)
                if step_id not in self.completed_steps:
                    self.completed_steps.append(step_id)
                break

    def mark_step_failed(self, step_id: int, error: str):
        """Marcar paso como fallido"""
        for step in self.steps:
            if step.id == step_id:
                step.mark_failed(error)
                if step_id not in self.failed_steps:
                    self.failed_steps.append(step_id)
                break


class Planner:
    """
    Módulo de planificación del agente.

    Crea planes de ejecución basándose en:
    - El análisis del Thinker
    - Las herramientas disponibles
    - El contexto del proyecto
    """

    PLANNING_PROMPT = """Eres un planificador experto que crea planes de ejecución detallados.

TAREA:
{task}

ANÁLISIS PREVIO:
- Complejidad: {complexity}/5
- Conceptos clave: {concepts}
- Enfoque sugerido: {approach}
- Riesgos identificados: {risks}

HERRAMIENTAS DISPONIBLES:
{tools}

Crea un plan de ejecución en JSON con el siguiente formato:
```json
{{
  "overall_strategy": "Estrategia general del plan",
  "success_criteria": "Cómo saber si el plan tuvo éxito",
  "estimated_duration": "Tiempo estimado",
  "steps": [
    {{
      "id": 1,
      "description": "Descripción clara del paso",
      "type": "analysis|search|create|modify|execute|verify|communicate",
      "action": "Acción específica a realizar",
      "tool_hint": "herramienta_sugerida",
      "depends_on": [],
      "verification_criteria": "Cómo verificar que el paso fue exitoso",
      "expected_output": "Qué se espera obtener",
      "correction_strategy": "Qué hacer si falla"
    }}
  ]
}}
```

REGLAS:
1. Cada paso debe ser atómico y verificable
2. Incluir pasos de verificación después de acciones críticas
3. Los pasos deben tener dependencias claras
4. Incluir estrategias de corrección para pasos críticos
5. Máximo 10 pasos

Responde SOLO con el JSON."""

    def __init__(
        self,
        llm_interface: Any,
        available_tools: List[str] = None,
        verbose: bool = True
    ):
        """
        Args:
            llm_interface: Interfaz al LLM
            available_tools: Lista de herramientas disponibles
            verbose: Mostrar plan en consola
        """
        self.llm = llm_interface
        self.available_tools = available_tools or []
        self.verbose = verbose

    def create_plan(
        self,
        task: str,
        thinking_result: Any = None,
        context: str = ""
    ) -> Plan:
        """
        Crear plan de ejecución.

        Args:
            task: La tarea a planificar
            thinking_result: Resultado del Thinker
            context: Contexto adicional

        Returns:
            Plan con pasos de ejecución
        """
        if self.verbose:
            print("\n📋 PLANIFICANDO...")

        # Extraer info del thinking
        complexity = 2
        concepts = []
        approach = "Ejecutar directamente"
        risks = []

        if thinking_result:
            complexity = getattr(thinking_result, 'complexity', 2)
            concepts = getattr(thinking_result, 'key_concepts', [])
            approach = getattr(thinking_result, 'approach', approach)
            risks = getattr(thinking_result, 'risks', [])

        # Construir prompt
        prompt = self.PLANNING_PROMPT.format(
            task=task,
            complexity=complexity,
            concepts=", ".join(concepts) or "No especificados",
            approach=approach,
            risks=", ".join(risks) or "Ninguno identificado",
            tools=self._format_tools()
        )

        # Llamar al LLM
        try:
            response = self._call_llm(prompt)
            parsed = self._parse_response(response)
        except Exception as e:
            logger.error(f"Error en planificación: {e}")
            parsed = self._create_default_plan(task, complexity)

        # Construir Plan
        import time
        plan = Plan(
            task=task,
            created_at=time.time(),
            overall_strategy=parsed.get("overall_strategy", ""),
            success_criteria=parsed.get("success_criteria", ""),
            estimated_duration=parsed.get("estimated_duration", "")
        )

        # Crear pasos
        for step_data in parsed.get("steps", []):
            step = self._create_step(step_data)
            plan.steps.append(step)

        # Si no hay pasos, crear plan mínimo
        if not plan.steps:
            plan.steps = self._create_minimal_steps(task)

        if self.verbose:
            self._print_plan(plan)

        return plan

    def _call_llm(self, prompt: str) -> str:
        """Llamar al LLM"""
        if hasattr(self.llm, 'generate_simple'):
            return self.llm.generate_simple(prompt, max_tokens=1000)
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
            # Buscar objeto JSON más grande
            start = response.find('{')
            if start >= 0:
                depth = 0
                end = start
                for i, char in enumerate(response[start:], start):
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            break
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass

        return {}

    def _format_tools(self) -> str:
        """Formatear herramientas disponibles"""
        if not self.available_tools:
            return "- Herramientas estándar de sistema\n- Acceso a archivos\n- Ejecución de código"

        return "\n".join([f"- {tool}" for tool in self.available_tools])

    def _create_step(self, data: Dict) -> PlanStep:
        """Crear PlanStep desde diccionario"""
        # Mapear tipo
        type_map = {
            "analysis": StepType.ANALYSIS,
            "search": StepType.SEARCH,
            "create": StepType.CREATE,
            "modify": StepType.MODIFY,
            "execute": StepType.EXECUTE,
            "verify": StepType.VERIFY,
            "communicate": StepType.COMMUNICATE
        }

        step_type = type_map.get(data.get("type", "execute"), StepType.EXECUTE)

        return PlanStep(
            id=data.get("id", 1),
            description=data.get("description", ""),
            type=step_type,
            action=data.get("action", ""),
            action_params=data.get("action_params", {}),
            tool_hint=data.get("tool_hint", ""),
            depends_on=data.get("depends_on", []),
            verification_criteria=data.get("verification_criteria", ""),
            expected_output=data.get("expected_output", ""),
            correction_strategy=data.get("correction_strategy", "")
        )

    def _create_default_plan(self, task: str, complexity: int) -> Dict:
        """Crear plan por defecto"""
        steps = [
            {
                "id": 1,
                "description": "Analizar requisitos de la tarea",
                "type": "analysis",
                "action": "Revisar y entender qué se necesita",
                "verification_criteria": "Requisitos claros identificados",
                "correction_strategy": "Pedir clarificación"
            },
            {
                "id": 2,
                "description": "Ejecutar la tarea principal",
                "type": "execute",
                "action": task,
                "depends_on": [1],
                "verification_criteria": "Tarea completada sin errores",
                "correction_strategy": "Revisar errores y reintentar"
            },
            {
                "id": 3,
                "description": "Verificar resultado",
                "type": "verify",
                "action": "Verificar que el resultado es correcto",
                "depends_on": [2],
                "verification_criteria": "Resultado cumple expectativas",
                "correction_strategy": "Ajustar y repetir paso 2"
            }
        ]

        return {
            "overall_strategy": "Análisis → Ejecución → Verificación",
            "success_criteria": "Tarea completada y verificada",
            "estimated_duration": f"{complexity * 30} segundos",
            "steps": steps
        }

    def _create_minimal_steps(self, task: str) -> List[PlanStep]:
        """Crear pasos mínimos"""
        return [
            PlanStep(
                id=1,
                description="Ejecutar tarea",
                type=StepType.EXECUTE,
                action=task,
                verification_criteria="Completado sin errores"
            ),
            PlanStep(
                id=2,
                description="Verificar resultado",
                type=StepType.VERIFY,
                action="Verificar ejecución",
                depends_on=[1],
                verification_criteria="Resultado correcto"
            )
        ]

    def _print_plan(self, plan: Plan):
        """Imprimir plan en consola"""
        print(f"\n   📊 Estrategia: {plan.overall_strategy[:60]}...")
        print(f"   ✅ Éxito si: {plan.success_criteria[:60]}...")
        print(f"   ⏱️ Duración estimada: {plan.estimated_duration}")
        print(f"\n   📝 PASOS ({len(plan.steps)}):")

        for step in plan.steps:
            deps = f" (depende de: {step.depends_on})" if step.depends_on else ""
            print(f"      {step.id}. [{step.type.value}] {step.description[:50]}...{deps}")

        print()


# === QUICK PLANNER ===
class QuickPlanner(Planner):
    """
    Versión rápida del Planner para tareas simples.
    No usa LLM, solo crea plan básico.
    """

    def create_plan(
        self,
        task: str,
        thinking_result: Any = None,
        context: str = ""
    ) -> Plan:
        """Crear plan rápido sin LLM"""
        complexity = 2
        if thinking_result:
            complexity = getattr(thinking_result, 'complexity', 2)

        parsed = self._create_default_plan(task, complexity)

        import time
        plan = Plan(
            task=task,
            created_at=time.time(),
            overall_strategy=parsed["overall_strategy"],
            success_criteria=parsed["success_criteria"],
            estimated_duration=parsed["estimated_duration"]
        )

        for step_data in parsed["steps"]:
            plan.steps.append(self._create_step(step_data))

        if self.verbose:
            print("\n⚡ PLAN RÁPIDO:")
            self._print_plan(plan)

        return plan
