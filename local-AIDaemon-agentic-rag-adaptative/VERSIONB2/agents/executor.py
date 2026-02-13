#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    EXECUTOR - Ejecutor de Agentes
========================================
Ejecuta planes de forma secuencial, controlando timeouts,
errores y agregando resultados.
"""

import os
import sys
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging

# === Setup paths para imports absolutos ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agents.planner import Plan, PlanStep, StepType, AgentPlanner
from agents.validator import PlanValidator, ValidationResult
from agents.base_agent import (
    BaseAgent, AgentResult, AgentStatus, AgentFactory,
    GenericAgent, SearchAgent, CodeAgent, ValidationAgent, Tool
)
from agents.tools.mcp_client import MCPToolWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Executor")


@dataclass
class ExecutionResult:
    """Resultado de ejecución de un plan"""
    plan_id: str
    success: bool
    total_steps: int
    completed_steps: int
    failed_steps: int
    total_time: float
    step_results: List[AgentResult] = field(default_factory=list)
    final_output: str = ""
    errors: List[str] = field(default_factory=list)


class AgentExecutor:
    """
    Ejecutor de planes de agentes.

    Características:
    - Ejecución secuencial de pasos
    - Respeto de dependencias
    - Control de timeouts
    - Agregación de resultados
    - Posibilidad de re-preguntar al daemon
    """

    def __init__(
        self,
        max_retries: int = 3,
        step_timeout: int = 60,
        total_timeout: int = 300,
        max_recursion: int = 3
    ):
        """
        Inicializar ejecutor.

        Args:
            max_retries: Reintentos por paso fallido
            step_timeout: Timeout por paso
            total_timeout: Timeout total del plan
            max_recursion: Máximo nivel de recursión daemon
        """
        from core.config import config
        from core.daemon_interface import DaemonInterface

        self.max_retries = max_retries
        self.step_timeout = step_timeout
        self.total_timeout = total_timeout
        self.max_recursion = max_recursion
        self.config = config

        # Componentes
        self.planner = AgentPlanner()
        self.validator = PlanValidator()
        self.daemon = DaemonInterface()

        # Herramientas MCP
        self.mcp_tools = MCPToolWrapper()

        # Cache de agentes
        self._agents: Dict[str, BaseAgent] = {}

    def execute_plan(
        self,
        plan: Plan,
        session_id: str = None,
        current_depth: int = 0
    ) -> ExecutionResult:
        """
        Ejecutar un plan completo.

        Args:
            plan: Plan a ejecutar
            session_id: ID de sesión para estado compartido
            current_depth: Profundidad actual de recursión

        Returns:
            ExecutionResult con todos los resultados
        """
        # Verificar límite de recursión
        if current_depth > self.max_recursion:
            logger.warning(f"Límite de recursión alcanzado en executor: depth={current_depth}")
            return ExecutionResult(
                plan_id=plan.id,
                success=False,
                total_steps=len(plan.steps),
                completed_steps=0,
                failed_steps=0,
                total_time=0,
                errors=["Límite de recursión alcanzado"],
                final_output="Error: Recursión máxima"
            )

        start_time = time.time()
        step_results = []
        errors = []

        # Validar plan primero
        validation = self.validator.validate(plan)
        if not validation.is_valid:
            logger.error(f"Plan {plan.id} no válido: {validation.errors}")
            plan = self.validator.fix_plan(plan)
            validation = self.validator.validate(plan)
            if not validation.is_valid:
                return ExecutionResult(
                    plan_id=plan.id,
                    success=False,
                    total_steps=len(plan.steps),
                    completed_steps=0,
                    failed_steps=0,
                    total_time=time.time() - start_time,
                    errors=validation.errors,
                    final_output="Plan no válido"
                )

        plan.status = "running"
        logger.info(f"Ejecutando plan {plan.id} con {len(plan.steps)} pasos")

        # Ejecutar pasos secuencialmente
        context = ""  # Contexto acumulado de pasos anteriores
        completed = 0
        failed = 0

        while True:
            # Verificar timeout total
            elapsed = time.time() - start_time
            if elapsed > self.total_timeout:
                errors.append(f"Timeout total excedido ({self.total_timeout}s)")
                break

            # Obtener siguiente paso
            step = self.planner.get_next_step(plan)
            if step is None:
                # No hay más pasos pendientes
                break

            logger.info(f"Ejecutando paso {step.id}: {step.description[:50]}...")

            # Ejecutar paso con reintentos
            result = self._execute_step_with_retry(step, context, plan)
            step_results.append(result)

            if result.status == AgentStatus.SUCCESS:
                self.planner.update_step_status(plan, step.id, "completed", result.output)
                completed += 1
                context += f"\n\n[Paso {step.id}]: {result.output[:500]}"
            elif result.status == AgentStatus.PARTIAL:
                self.planner.update_step_status(plan, step.id, "completed", result.output)
                completed += 1
                context += f"\n\n[Paso {step.id} (parcial)]: {result.output[:500]}"
            else:
                self.planner.update_step_status(plan, step.id, "failed", result.error)
                failed += 1
                errors.append(f"Paso {step.id} falló: {result.error}")

        # Determinar éxito
        success = completed > 0 and failed == 0
        total_time = time.time() - start_time

        # Generar output final
        final_output = self._synthesize_results(plan, step_results)

        plan.status = "completed" if success else "failed"

        result = ExecutionResult(
            plan_id=plan.id,
            success=success,
            total_steps=len(plan.steps),
            completed_steps=completed,
            failed_steps=failed,
            total_time=total_time,
            step_results=step_results,
            final_output=final_output,
            errors=errors
        )

        logger.info(
            f"Plan {plan.id} {'completado' if success else 'fallido'}: "
            f"{completed}/{len(plan.steps)} pasos, {total_time:.1f}s"
        )

        return result

    def _execute_step_with_retry(
        self,
        step: PlanStep,
        context: str,
        plan: Plan
    ) -> AgentResult:
        """Ejecutar paso con reintentos"""
        last_result = None

        for attempt in range(self.max_retries):
            if attempt > 0:
                logger.warning(f"Reintento {attempt + 1}/{self.max_retries} para paso {step.id}")

            result = self._execute_step(step, context, plan)
            last_result = result

            if result.status in [AgentStatus.SUCCESS, AgentStatus.PARTIAL]:
                return result

            # Si es timeout, no reintentar
            if result.status == AgentStatus.TIMEOUT:
                break

        return last_result

    def _execute_step(
        self,
        step: PlanStep,
        context: str,
        plan: Plan
    ) -> AgentResult:
        """Ejecutar un paso individual"""
        step.status = "running"

        # Obtener o crear agente
        agent = self._get_agent(step)

        # Construir tarea para el agente
        task = self._build_task(step, context, plan)

        # Ejecutar agente
        result = agent.execute(task, context)

        return result

    def _get_agent(self, step: PlanStep) -> BaseAgent:
        """Obtener agente para un paso"""
        agent_type = step.agent_type

        if agent_type not in self._agents:
            # Crear agente con herramientas
            tools = self._get_tools_for_step(step)

            if agent_type == "search":
                agent = SearchAgent(tools=tools, timeout=self.step_timeout)
            elif agent_type == "code":
                agent = CodeAgent(tools=tools, timeout=self.step_timeout)
            elif agent_type == "validation":
                agent = ValidationAgent(tools=tools, timeout=self.step_timeout)
            else:
                agent = GenericAgent(
                    name=f"Agent_{agent_type}",
                    description=f"Agente genérico para {agent_type}",
                    tools=tools,
                    timeout=self.step_timeout
                )

            self._agents[agent_type] = agent

        return self._agents[agent_type]

    def _get_tools_for_step(self, step: PlanStep) -> List[Tool]:
        """Obtener herramientas necesarias para un paso"""
        all_tools = self.mcp_tools.get_tools()
        tool_names = set(step.tools_required)

        if not tool_names:
            return all_tools  # Todas las herramientas

        # Filtrar herramientas solicitadas
        return [t for t in all_tools if t.name in tool_names]

    def _build_task(self, step: PlanStep, context: str, plan: Plan) -> str:
        """Construir tarea para agente"""
        task = f"""TAREA: {step.description}

CONSULTA ORIGINAL: {plan.original_query}

RESPUESTA DEL SISTEMA:
{plan.daemon_response[:300]}

INSTRUCCIONES:
- Completa la tarea de forma precisa
- Usa las herramientas disponibles si es necesario
- Si no puedes completar la tarea, indica qué falta
"""
        if context:
            task += f"\n\nCONTEXTO DE PASOS ANTERIORES:\n{context[:500]}"

        return task

    def _synthesize_results(
        self,
        plan: Plan,
        results: List[AgentResult]
    ) -> str:
        """Sintetizar resultados de todos los pasos"""
        if not results:
            return "Sin resultados"

        successful_results = [r for r in results if r.status in [AgentStatus.SUCCESS, AgentStatus.PARTIAL]]

        if not successful_results:
            return "No se completaron pasos exitosamente"

        # Combinar outputs
        combined = []
        for r in successful_results:
            if r.output:
                combined.append(f"[{r.agent_name}]: {r.output[:300]}")

        # Si hay muchos resultados, sintetizar con IA
        if len(combined) > 3:
            # Usar daemon para sintetizar
            synthesis_prompt = f"""Sintetiza los siguientes resultados en una respuesta coherente:

CONSULTA ORIGINAL: {plan.original_query}

RESULTADOS:
{chr(10).join(combined)}

SÍNTESIS:"""

            response = self.daemon.query_and_wait(synthesis_prompt, timeout=30)
            if response.verdict.value != "TIMEOUT":
                return response.content

        return "\n\n".join(combined)

    def run_agents(self, plan: Plan) -> ExecutionResult:
        """Alias para execute_plan"""
        return self.execute_plan(plan)

    def query_daemon_from_agent(self, query: str, context: str = "") -> str:
        """
        Permitir que un agente re-pregunte al daemon.

        Args:
            query: Pregunta del agente
            context: Contexto

        Returns:
            Respuesta del daemon
        """
        logger.info(f"Agente consultando daemon: {query[:50]}...")
        response = self.daemon.query_and_wait(query, context, timeout=60)
        return response.content


# === CLI para pruebas ===
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: executor.py <consulta>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    # Crear plan
    planner = AgentPlanner()
    plan = planner.create_plan(
        query,
        "Necesito más información para responder completamente."
    )

    print(f"📋 Plan creado: {plan.id}")
    print(f"   Pasos: {len(plan.steps)}")
    for step in plan.steps:
        print(f"   - {step.id}. [{step.type.value}] {step.description[:40]}...")

    print("\n🚀 Ejecutando plan...")

    # Ejecutar
    executor = AgentExecutor()
    result = executor.execute_plan(plan)

    print(f"\n📊 Resultado:")
    print(f"   Éxito: {'✅' if result.success else '❌'}")
    print(f"   Completados: {result.completed_steps}/{result.total_steps}")
    print(f"   Tiempo: {result.total_time:.1f}s")

    if result.errors:
        print(f"\n❌ Errores:")
        for e in result.errors:
            print(f"   - {e}")

    print(f"\n📤 Output final:")
    print(result.final_output[:500])
