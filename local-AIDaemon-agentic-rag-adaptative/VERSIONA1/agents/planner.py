#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    PLANNER - Planificador de Agentes
========================================
Genera planes de ejecución basados en la respuesta del daemon.
Cada plan contiene pasos que serán ejecutados por agentes.
"""

import re
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Planner")


class StepType(Enum):
    """Tipos de pasos en un plan"""
    SEARCH = "search"          # Búsqueda de información
    ANALYZE = "analyze"        # Análisis de datos
    CODE = "code"              # Generación/ejecución de código
    VALIDATE = "validate"      # Validación
    SYNTHESIZE = "synthesize"  # Síntesis de resultados
    QUERY_DAEMON = "query"     # Re-preguntar al daemon


@dataclass
class PlanStep:
    """Un paso en el plan"""
    id: int
    type: StepType
    description: str
    agent_type: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[int] = field(default_factory=list)  # IDs de pasos previos
    tools_required: List[str] = field(default_factory=list)
    timeout: int = 60
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[str] = None


@dataclass
class Plan:
    """Plan de ejecución"""
    id: str
    description: str
    original_query: str
    daemon_response: str
    steps: List[PlanStep] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    status: str = "created"  # created, validated, running, completed, failed

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "original_query": self.original_query,
            "daemon_response": self.daemon_response[:500],
            "steps": [
                {
                    "id": s.id,
                    "type": s.type.value,
                    "description": s.description,
                    "agent_type": s.agent_type,
                    "dependencies": s.dependencies,
                    "tools_required": s.tools_required,
                    "status": s.status
                }
                for s in self.steps
            ],
            "status": self.status
        }


class AgentPlanner:
    """
    Planificador de agentes.
    Analiza la respuesta del daemon y genera un plan de ejecución.
    """

    def __init__(self, max_steps: int = 5):
        """
        Inicializar planificador.

        Args:
            max_steps: Máximo número de pasos en un plan
        """
        # Importar config
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
        from config import config
        from daemon_interface import DaemonCLI

        self.max_steps = max_steps
        self.config = config
        self.llm = DaemonCLI()  # Para generar planes con IA
        self._plan_counter = 0

    def needs_agents(self, daemon_response: str) -> bool:
        """
        Determinar si la respuesta del daemon necesita agentes.

        Args:
            daemon_response: Respuesta del daemon

        Returns:
            True si necesita agentes adicionales
        """
        # Indicadores de que se necesitan agentes
        need_agents_patterns = [
            r'necesito más información',
            r'no tengo acceso',
            r'requiere búsqueda',
            r'código.*ejecutar',
            r'verificar.*fuente',
            r'PARCIAL',
            r'FALLA',
            r'no puedo confirmar',
            r'sería necesario',
        ]

        response_lower = daemon_response.lower()

        for pattern in need_agents_patterns:
            if re.search(pattern, response_lower, re.IGNORECASE):
                return True

        return False

    def create_plan(
        self,
        original_query: str,
        daemon_response: str,
        context: str = ""
    ) -> Plan:
        """
        Crear plan de ejecución.

        Args:
            original_query: Consulta original del usuario
            daemon_response: Respuesta del daemon
            context: Contexto adicional

        Returns:
            Plan de ejecución
        """
        self._plan_counter += 1
        plan_id = f"plan_{self._plan_counter}_{int(time.time())}"

        # Generar plan con IA
        plan_prompt = self._build_planning_prompt(original_query, daemon_response, context)
        plan_response = self.llm.query(plan_prompt, max_tokens=1000, temperature=0.3)

        # Parsear plan
        steps = self._parse_plan_response(plan_response)

        # Si no se pudo parsear, crear plan por defecto
        if not steps:
            steps = self._create_default_plan(original_query, daemon_response)

        # Limitar pasos
        steps = steps[:self.max_steps]

        plan = Plan(
            id=plan_id,
            description=f"Plan para: {original_query[:50]}...",
            original_query=original_query,
            daemon_response=daemon_response,
            steps=steps
        )

        logger.info(f"Plan creado: {plan_id} con {len(steps)} pasos")
        return plan

    def _build_planning_prompt(
        self,
        query: str,
        daemon_response: str,
        context: str
    ) -> str:
        """Construir prompt para generar plan"""
        return f"""Eres un planificador de tareas experto. Debes crear un plan de ejecución para completar una consulta.

CONSULTA ORIGINAL: {query}

RESPUESTA ACTUAL DEL SISTEMA:
{daemon_response[:500]}

CONTEXTO ADICIONAL:
{context[:300] if context else "Ninguno"}

TIPOS DE PASOS DISPONIBLES:
- search: Búsqueda de información adicional
- analyze: Análisis de datos o código
- code: Generación o ejecución de código
- validate: Validación de resultados
- synthesize: Síntesis de información
- query: Re-preguntar al sistema principal

TIPOS DE AGENTES:
- generic: Tareas generales
- search: Búsquedas especializadas
- code: Tareas de código
- validation: Validación y verificación

INSTRUCCIONES:
1. Analiza qué falta en la respuesta actual
2. Crea un plan con máximo {self.max_steps} pasos
3. Cada paso debe ser específico y accionable
4. Indica dependencias entre pasos si las hay

FORMATO DE RESPUESTA (JSON):
{{
  "steps": [
    {{
      "type": "search",
      "description": "Descripción del paso",
      "agent_type": "search",
      "tools": ["web_search"],
      "depends_on": []
    }}
  ]
}}

PLAN:"""

    def _parse_plan_response(self, response: str) -> List[PlanStep]:
        """Parsear respuesta de plan"""
        steps = []

        try:
            # Buscar JSON en la respuesta
            json_match = re.search(r'\{[\s\S]*"steps"[\s\S]*\}', response)
            if json_match:
                plan_data = json.loads(json_match.group())

                for i, step_data in enumerate(plan_data.get("steps", [])):
                    step_type = StepType(step_data.get("type", "analyze"))
                    step = PlanStep(
                        id=i + 1,
                        type=step_type,
                        description=step_data.get("description", ""),
                        agent_type=step_data.get("agent_type", "generic"),
                        tools_required=step_data.get("tools", []),
                        dependencies=step_data.get("depends_on", [])
                    )
                    steps.append(step)

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Error parseando plan: {e}")

        return steps

    def _create_default_plan(
        self,
        query: str,
        daemon_response: str
    ) -> List[PlanStep]:
        """Crear plan por defecto cuando el parsing falla"""
        steps = []

        # Detectar tipo de tarea
        query_lower = query.lower()

        # Paso 1: Búsqueda si es necesario
        if any(kw in daemon_response.lower() for kw in ['no tengo', 'necesito', 'buscar']):
            steps.append(PlanStep(
                id=1,
                type=StepType.SEARCH,
                description=f"Buscar información adicional sobre: {query[:50]}",
                agent_type="search",
                tools_required=["web_search", "grep"]
            ))

        # Paso 2: Análisis
        if 'código' in query_lower or 'programa' in query_lower:
            steps.append(PlanStep(
                id=len(steps) + 1,
                type=StepType.CODE,
                description="Analizar o generar código requerido",
                agent_type="code",
                tools_required=["python_exec", "leer_archivo"],
                dependencies=[s.id for s in steps]
            ))
        else:
            steps.append(PlanStep(
                id=len(steps) + 1,
                type=StepType.ANALYZE,
                description="Analizar información recopilada",
                agent_type="generic",
                dependencies=[s.id for s in steps]
            ))

        # Paso 3: Validación
        steps.append(PlanStep(
            id=len(steps) + 1,
            type=StepType.VALIDATE,
            description="Validar resultados obtenidos",
            agent_type="validation",
            dependencies=[s.id for s in steps]
        ))

        # Paso 4: Síntesis
        steps.append(PlanStep(
            id=len(steps) + 1,
            type=StepType.SYNTHESIZE,
            description="Sintetizar respuesta final",
            agent_type="generic",
            dependencies=[s.id for s in steps]
        ))

        return steps

    def get_next_step(self, plan: Plan) -> Optional[PlanStep]:
        """
        Obtener siguiente paso a ejecutar.

        Args:
            plan: Plan de ejecución

        Returns:
            Siguiente paso o None si no hay más
        """
        for step in plan.steps:
            if step.status == "pending":
                # Verificar que las dependencias están completadas
                deps_completed = all(
                    plan.steps[dep_id - 1].status == "completed"
                    for dep_id in step.dependencies
                    if dep_id <= len(plan.steps)
                )
                if deps_completed:
                    return step

        return None

    def update_step_status(
        self,
        plan: Plan,
        step_id: int,
        status: str,
        result: str = None
    ):
        """
        Actualizar estado de un paso.

        Args:
            plan: Plan
            step_id: ID del paso
            status: Nuevo estado
            result: Resultado del paso
        """
        for step in plan.steps:
            if step.id == step_id:
                step.status = status
                step.result = result
                break

        # Actualizar estado general del plan
        all_completed = all(s.status == "completed" for s in plan.steps)
        any_failed = any(s.status == "failed" for s in plan.steps)

        if all_completed:
            plan.status = "completed"
        elif any_failed:
            plan.status = "failed"
        else:
            plan.status = "running"


# === CLI para pruebas ===
if __name__ == "__main__":
    import sys

    planner = AgentPlanner()

    if len(sys.argv) < 2:
        print("Uso: planner.py <consulta>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    daemon_response = "La información está incompleta, necesito más datos."

    print(f"📋 Creando plan para: {query}")
    print(f"🤖 Respuesta daemon: {daemon_response}")

    plan = planner.create_plan(query, daemon_response)

    print(f"\n📝 Plan: {plan.id}")
    print(f"   Estado: {plan.status}")
    print(f"   Pasos: {len(plan.steps)}")

    for step in plan.steps:
        deps = f" (depende de: {step.dependencies})" if step.dependencies else ""
        print(f"\n   {step.id}. [{step.type.value}] {step.description}")
        print(f"      Agente: {step.agent_type}{deps}")
        print(f"      Herramientas: {step.tools_required}")
