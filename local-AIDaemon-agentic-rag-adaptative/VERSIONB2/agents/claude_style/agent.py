#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
🤖 CLAUDE STYLE AGENT - Agente Principal
========================================
Agente inteligente que emula el comportamiento de Claude:

1. PENSAR: Analiza la tarea antes de actuar
2. PLANIFICAR: Crea un plan de ejecución estructurado
3. EJECUTAR: Ejecuta cada paso del plan
4. VERIFICAR: Verifica que cada paso fue exitoso
5. CORREGIR: Corrige automáticamente si algo falla
6. REFLEXIONAR: Evalúa el resultado y aprende

Arquitectura:
┌─────────────────────────────────────────────────┐
│                ClaudeStyleAgent                 │
├─────────────────────────────────────────────────┤
│  🧠 Thinker  →  📋 Planner  →  ⚡ Executor      │
│       ↑                              ↓         │
│  💭 Reflector ← 🔧 Corrector ← 🔍 Verifier     │
└─────────────────────────────────────────────────┘

Uso:
    agent = ClaudeStyleAgent(llm_interface)
    result = agent.run("Implementa un sistema de caché")
"""

import os
import sys
import time
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

# Importar módulos del agente
from .thinker import Thinker, ThinkingResult, QuickThinker
from .planner import Planner, Plan, PlanStep, StepStatus, QuickPlanner
from .executor import Executor, ExecutionContext, StepResult, SimpleExecutor
from .verifier import Verifier, VerificationResult, VerificationStatus, QuickVerifier
from .corrector import Corrector, CorrectionResult, CorrectionStrategy
from .reflector import Reflector, Reflection, ReflectionQuality

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ClaudeStyleAgent")


class AgentMode(Enum):
    """Modos de operación del agente"""
    FULL = "full"           # Pipeline completo
    FAST = "fast"           # Pipeline rápido sin LLM en componentes intermedios
    MINIMAL = "minimal"     # Solo ejecutar sin verificación
    INTERACTIVE = "interactive"  # Pedir confirmación en cada paso


@dataclass
class AgentConfig:
    """Configuración del agente"""
    mode: AgentMode = AgentMode.FULL
    max_plan_steps: int = 10
    max_retries_per_step: int = 3
    max_total_retries: int = 15
    timeout_per_step: float = 60.0
    verbose: bool = True
    auto_correct: bool = True
    verify_all_steps: bool = True
    reflect_on_completion: bool = True
    use_lessons_learned: bool = True

    def to_dict(self) -> Dict:
        return {
            "mode": self.mode.value,
            "max_plan_steps": self.max_plan_steps,
            "max_retries_per_step": self.max_retries_per_step,
            "verbose": self.verbose,
            "auto_correct": self.auto_correct,
            "verify_all_steps": self.verify_all_steps
        }


@dataclass
class AgentResult:
    """Resultado final de la ejecución del agente"""
    task: str
    success: bool
    response: str

    # Detalles de ejecución
    thinking: Optional[ThinkingResult] = None
    plan: Optional[Plan] = None
    execution_context: Optional[ExecutionContext] = None
    reflection: Optional[Reflection] = None

    # Métricas
    total_time: float = 0
    steps_completed: int = 0
    steps_failed: int = 0
    corrections_made: int = 0

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "task": self.task,
            "success": self.success,
            "response": self.response,
            "total_time": self.total_time,
            "steps_completed": self.steps_completed,
            "steps_failed": self.steps_failed,
            "corrections_made": self.corrections_made,
            "metadata": self.metadata
        }


class ClaudeStyleAgent:
    """
    Agente que emula el comportamiento de Claude.

    Pipeline completo:
    1. Pensar sobre la tarea
    2. Crear plan de ejecución
    3. Ejecutar paso a paso
    4. Verificar cada paso
    5. Corregir si es necesario
    6. Reflexionar sobre el resultado

    Ejemplo:
        agent = ClaudeStyleAgent(llm)
        result = agent.run("Crea un archivo de configuración")
        print(result.response)
    """

    def __init__(
        self,
        llm_interface: Any,
        tool_executor: Callable = None,
        available_tools: List[str] = None,
        config: AgentConfig = None
    ):
        """
        Inicializar agente.

        Args:
            llm_interface: Interfaz al modelo de lenguaje
            tool_executor: Función para ejecutar herramientas
            available_tools: Lista de herramientas disponibles
            config: Configuración del agente
        """
        self.llm = llm_interface
        self.tool_executor = tool_executor
        self.available_tools = available_tools or []
        self.config = config or AgentConfig()

        # Inicializar componentes según el modo
        self._init_components()

        # Historial de ejecuciones
        self.execution_history: List[AgentResult] = []

        logger.info(f"🤖 ClaudeStyleAgent inicializado (modo={self.config.mode.value})")

    def _init_components(self):
        """Inicializar componentes del agente según el modo"""
        mode = self.config.mode
        verbose = self.config.verbose

        # Thinker
        if mode == AgentMode.FULL:
            self.thinker = Thinker(self.llm, verbose=verbose)
        else:
            self.thinker = QuickThinker(self.llm, verbose=verbose)

        # Planner
        if mode in [AgentMode.FULL, AgentMode.INTERACTIVE]:
            self.planner = Planner(self.llm, self.available_tools, verbose=verbose)
        else:
            self.planner = QuickPlanner(self.llm, self.available_tools, verbose=verbose)

        # Executor
        if mode == AgentMode.MINIMAL:
            self.executor = SimpleExecutor(
                self.llm, self.tool_executor, self.available_tools, verbose=verbose
            )
        else:
            self.executor = Executor(
                self.llm, self.tool_executor, self.available_tools, verbose=verbose
            )

        # Verifier
        if mode == AgentMode.FULL:
            self.verifier = Verifier(self.llm, verbose=verbose)
        elif mode == AgentMode.MINIMAL:
            self.verifier = None
        else:
            self.verifier = QuickVerifier(verbose=verbose)

        # Corrector
        if self.config.auto_correct and mode != AgentMode.MINIMAL:
            self.corrector = Corrector(
                self.llm, self.executor, self.available_tools,
                max_retries=self.config.max_retries_per_step,
                verbose=verbose
            )
        else:
            self.corrector = None

        # Reflector
        if self.config.reflect_on_completion:
            self.reflector = Reflector(self.llm, verbose=verbose)
        else:
            self.reflector = None

    def run(self, task: str, context: str = "") -> AgentResult:
        """
        Ejecutar una tarea completa.

        Args:
            task: La tarea a ejecutar
            context: Contexto adicional

        Returns:
            AgentResult con el resultado completo
        """
        start_time = time.time()

        if self.config.verbose:
            print("\n" + "=" * 60)
            print(f"🤖 CLAUDE STYLE AGENT - Ejecutando tarea")
            print("=" * 60)
            print(f"📝 Tarea: {task[:100]}...")

        try:
            # PASO 1: PENSAR
            thinking = self.thinker.think(task, context)

            # Usar lecciones aprendidas si está habilitado
            if self.config.use_lessons_learned and self.reflector:
                lessons = self.reflector.get_applicable_lessons(task)
                if lessons:
                    context += f"\n\nLecciones previas: {[l.description for l in lessons[:3]]}"

            # PASO 2: PLANIFICAR
            plan = self.planner.create_plan(task, thinking, context)

            # PASO 3: EJECUTAR
            exec_context = self._execute_with_verification(plan)

            # PASO 4: REFLEXIONAR
            reflection = None
            if self.reflector:
                verifications = []
                if self.verifier and exec_context.results:
                    for step, result in zip(plan.steps, exec_context.results):
                        ver = self.verifier.verify_step(step, result)
                        verifications.append(ver)

                reflection = self.reflector.reflect(plan, exec_context, verifications)

            # Construir resultado final
            result = self._build_result(
                task, thinking, plan, exec_context, reflection, start_time
            )

            # Guardar en historial
            self.execution_history.append(result)

            if self.config.verbose:
                self._print_final_result(result)

            return result

        except Exception as e:
            logger.error(f"Error en ejecución: {e}")
            import traceback
            traceback.print_exc()

            return AgentResult(
                task=task,
                success=False,
                response=f"Error en ejecución: {str(e)}",
                total_time=time.time() - start_time,
                metadata={"error": str(e)}
            )

    def _execute_with_verification(self, plan: Plan) -> ExecutionContext:
        """Ejecutar plan con verificación y corrección"""
        corrections_made = 0

        def on_step_complete(step: PlanStep, result: StepResult):
            """Callback cuando un paso se completa"""
            if self.config.verify_all_steps and self.verifier:
                verification = self.verifier.verify_step(step, result)

                # Si la verificación falla pero el resultado fue exitoso,
                # podría necesitar corrección
                if verification.needs_correction and self.corrector:
                    if self.config.verbose:
                        print(f"      ⚠️ Verificación parcial, intentando corrección...")

        def on_step_failed(step: PlanStep, result: StepResult) -> bool:
            """Callback cuando un paso falla"""
            nonlocal corrections_made

            if not self.corrector:
                return False  # No hay corrector, detener

            if step.attempts >= self.config.max_retries_per_step:
                if self.config.verbose:
                    print(f"      ❌ Máximo de reintentos alcanzado para paso {step.id}")
                return False

            if corrections_made >= self.config.max_total_retries:
                if self.config.verbose:
                    print(f"      ❌ Máximo de correcciones totales alcanzado")
                return False

            # Verificar para obtener más contexto
            verification = VerificationResult(
                step_id=step.id,
                status=VerificationStatus.FAILED,
                message=result.error,
                issues=[result.error]
            )

            if self.verifier:
                verification = self.verifier.verify_step(step, result)

            # Intentar corrección
            correction = self.corrector.analyze_and_correct(
                step, result, verification, None  # context se pasaría aquí
            )

            corrections_made += 1

            if correction.success:
                # Actualizar el paso como completado
                if correction.new_result:
                    plan.mark_step_completed(step.id, correction.new_result.output)
                    # Remover de fallidos si estaba
                    if step.id in plan.failed_steps:
                        plan.failed_steps.remove(step.id)
                return True  # Continuar con el plan
            else:
                # La corrección falló
                if correction.action_taken.strategy == CorrectionStrategy.SKIP:
                    return True  # Continuar aunque se saltó
                elif correction.action_taken.strategy == CorrectionStrategy.ABORT:
                    return False  # Detener el plan
                else:
                    return False  # Detener por defecto

        # Ejecutar el plan
        context = self.executor.execute_plan(
            plan,
            on_step_complete=on_step_complete,
            on_step_failed=on_step_failed
        )

        # Guardar correcciones en metadata
        context.variables["corrections_made"] = corrections_made

        return context

    def _build_result(
        self,
        task: str,
        thinking: ThinkingResult,
        plan: Plan,
        context: ExecutionContext,
        reflection: Optional[Reflection],
        start_time: float
    ) -> AgentResult:
        """Construir resultado final"""
        total_time = time.time() - start_time

        # Determinar respuesta final
        if reflection and reflection.final_response:
            response = reflection.final_response
        elif context.results:
            # Usar último resultado exitoso
            successful = [r for r in context.results if r.success]
            if successful:
                response = successful[-1].output
            else:
                failed = [r for r in context.results if not r.success]
                response = f"No se pudo completar. Errores: {failed[0].error if failed else 'Desconocido'}"
        else:
            response = "No se generó respuesta."

        # Determinar éxito
        success = plan.is_complete or (
            reflection and reflection.is_successful if reflection else False
        )

        return AgentResult(
            task=task,
            success=success,
            response=response,
            thinking=thinking,
            plan=plan,
            execution_context=context,
            reflection=reflection,
            total_time=total_time,
            steps_completed=len(plan.completed_steps),
            steps_failed=len(plan.failed_steps),
            corrections_made=context.variables.get("corrections_made", 0),
            metadata={
                "thinking_complexity": thinking.complexity,
                "plan_strategy": plan.overall_strategy,
                "reflection_quality": reflection.quality.value if reflection else None
            }
        )

    def _print_final_result(self, result: AgentResult):
        """Imprimir resultado final"""
        print("\n" + "=" * 60)
        print("📊 RESULTADO FINAL")
        print("=" * 60)

        status = "✅ ÉXITO" if result.success else "❌ FALLO"
        print(f"   Estado: {status}")
        print(f"   Tiempo total: {result.total_time:.2f}s")
        print(f"   Pasos: {result.steps_completed} completados, {result.steps_failed} fallidos")
        print(f"   Correcciones: {result.corrections_made}")

        print(f"\n   📝 Respuesta:")
        # Mostrar respuesta con indentación
        for line in result.response[:500].split('\n'):
            print(f"      {line}")

        if len(result.response) > 500:
            print(f"      ... ({len(result.response) - 500} caracteres más)")

        print("\n" + "=" * 60)

    def run_interactive(self, task: str) -> AgentResult:
        """
        Ejecutar tarea en modo interactivo.
        Pide confirmación antes de cada paso.
        """
        original_mode = self.config.mode
        self.config.mode = AgentMode.INTERACTIVE
        self._init_components()

        # TODO: Implementar confirmación interactiva
        result = self.run(task)

        self.config.mode = original_mode
        self._init_components()

        return result

    def run_fast(self, task: str) -> AgentResult:
        """Ejecutar tarea en modo rápido"""
        original_mode = self.config.mode
        self.config.mode = AgentMode.FAST
        self._init_components()

        result = self.run(task)

        self.config.mode = original_mode
        self._init_components()

        return result

    def get_execution_summary(self) -> Dict[str, Any]:
        """Obtener resumen de todas las ejecuciones"""
        if not self.execution_history:
            return {"total": 0}

        successful = sum(1 for r in self.execution_history if r.success)
        total_time = sum(r.total_time for r in self.execution_history)
        total_corrections = sum(r.corrections_made for r in self.execution_history)

        return {
            "total": len(self.execution_history),
            "successful": successful,
            "failed": len(self.execution_history) - successful,
            "success_rate": successful / len(self.execution_history),
            "total_time": total_time,
            "avg_time": total_time / len(self.execution_history),
            "total_corrections": total_corrections
        }


# === AGENTE SIMPLE ===
class SimpleClaudeAgent(ClaudeStyleAgent):
    """
    Versión simplificada del agente para tareas simples.
    No usa planificación ni reflexión.
    """

    def __init__(self, llm_interface: Any, tool_executor: Callable = None, **kwargs):
        config = AgentConfig(
            mode=AgentMode.MINIMAL,
            verify_all_steps=False,
            reflect_on_completion=False,
            auto_correct=False,
            verbose=kwargs.get('verbose', True)
        )
        super().__init__(llm_interface, tool_executor, config=config, **kwargs)

    def run(self, task: str, context: str = "") -> AgentResult:
        """Ejecución simplificada"""
        start_time = time.time()

        if self.config.verbose:
            print(f"\n⚡ Ejecutando: {task[:50]}...")

        # Ejecutar directamente
        try:
            response = self._call_llm(task + ("\n\nContexto: " + context if context else ""))

            return AgentResult(
                task=task,
                success=True,
                response=response,
                total_time=time.time() - start_time
            )
        except Exception as e:
            return AgentResult(
                task=task,
                success=False,
                response=f"Error: {str(e)}",
                total_time=time.time() - start_time
            )

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


# === TEST ===
if __name__ == "__main__":
    print("🤖 Test de Claude Style Agent")
    print("=" * 60)

    # Mock LLM
    class MockLLM:
        def __init__(self):
            self.call_count = 0

        def generate_simple(self, prompt: str, max_tokens: int = 500) -> str:
            self.call_count += 1

            # Simular diferentes respuestas según el contenido del prompt
            if "analiza" in prompt.lower() or "tarea" in prompt.lower():
                return json.dumps({
                    "analysis": "Tarea de prueba",
                    "key_concepts": ["test", "prueba"],
                    "complexity": 2,
                    "estimated_steps": 3,
                    "approach": "Ejecutar directamente",
                    "risks": [],
                    "assumptions": []
                })
            elif "plan" in prompt.lower():
                return json.dumps({
                    "overall_strategy": "Test strategy",
                    "success_criteria": "Test completado",
                    "estimated_duration": "10s",
                    "steps": [
                        {
                            "id": 1,
                            "description": "Paso de prueba",
                            "type": "execute",
                            "action": "test",
                            "verification_criteria": "Completado"
                        }
                    ]
                })
            elif "ejecuta" in prompt.lower():
                return json.dumps({
                    "use_tool": False,
                    "direct_response": "Ejecución exitosa de prueba",
                    "reasoning": "Test"
                })
            elif "verifica" in prompt.lower():
                return json.dumps({
                    "status": "passed",
                    "confidence": 0.9,
                    "message": "Verificación exitosa"
                })
            elif "reflexiona" in prompt.lower():
                return json.dumps({
                    "quality": "good",
                    "summary": "Test completado",
                    "final_response": "Prueba ejecutada correctamente",
                    "confidence": 0.9,
                    "strengths": ["Ejecución rápida"],
                    "weaknesses": [],
                    "improvements": []
                })
            else:
                return "Respuesta de prueba"

    import json

    # Crear agente
    llm = MockLLM()
    config = AgentConfig(mode=AgentMode.FAST, verbose=True)
    agent = ClaudeStyleAgent(llm, config=config)

    # Test
    result = agent.run("Ejecuta una prueba simple")

    print(f"\n📊 Resultado del test:")
    print(f"   Éxito: {result.success}")
    print(f"   Respuesta: {result.response}")
    print(f"   Tiempo: {result.total_time:.2f}s")
    print(f"   Llamadas LLM: {llm.call_count}")
