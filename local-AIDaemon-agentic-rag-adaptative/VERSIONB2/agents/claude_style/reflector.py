#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
💭 REFLECTOR - Módulo de Reflexión
========================================
Reflexiona sobre el resultado final del plan.
Evalúa calidad, identifica mejoras y genera aprendizajes.

Características:
- Evaluación de calidad del resultado
- Identificación de patrones de éxito/fallo
- Generación de insights para futuras ejecuciones
- Auto-mejora del agente
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from .planner import Plan
from .executor import ExecutionContext, StepResult
from .verifier import VerificationResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Reflector")


class ReflectionQuality(Enum):
    """Calidad general del resultado"""
    EXCELLENT = "excellent"   # Superó expectativas
    GOOD = "good"             # Cumplió completamente
    ACCEPTABLE = "acceptable" # Cumplió parcialmente
    POOR = "poor"             # No cumplió
    FAILED = "failed"         # Falló completamente


@dataclass
class Lesson:
    """Una lección aprendida"""
    category: str  # "success", "failure", "optimization"
    description: str
    applies_to: List[str] = field(default_factory=list)  # Tipos de tareas
    confidence: float = 0.7

    def to_dict(self) -> Dict:
        return {
            "category": self.category,
            "description": self.description,
            "applies_to": self.applies_to,
            "confidence": self.confidence
        }


@dataclass
class Reflection:
    """Reflexión sobre la ejecución del plan"""
    plan_task: str
    quality: ReflectionQuality
    summary: str

    # Métricas
    steps_completed: int = 0
    steps_failed: int = 0
    total_attempts: int = 0
    execution_time: float = 0

    # Análisis
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    lessons: List[Lesson] = field(default_factory=list)

    # Para el usuario
    final_response: str = ""
    confidence: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "plan_task": self.plan_task,
            "quality": self.quality.value,
            "summary": self.summary,
            "steps_completed": self.steps_completed,
            "steps_failed": self.steps_failed,
            "total_attempts": self.total_attempts,
            "execution_time": self.execution_time,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "improvements": self.improvements,
            "lessons": [l.to_dict() for l in self.lessons],
            "final_response": self.final_response,
            "confidence": self.confidence
        }

    @property
    def success_rate(self) -> float:
        """Tasa de éxito"""
        total = self.steps_completed + self.steps_failed
        if total == 0:
            return 0.0
        return self.steps_completed / total

    @property
    def is_successful(self) -> bool:
        """¿Fue exitosa la ejecución?"""
        return self.quality in [ReflectionQuality.EXCELLENT, ReflectionQuality.GOOD]


class Reflector:
    """
    Módulo de reflexión del agente.

    Analiza el resultado de la ejecución:
    - Evalúa calidad general
    - Identifica fortalezas y debilidades
    - Genera lecciones aprendidas
    - Sugiere mejoras para el futuro
    """

    REFLECTION_PROMPT = """Reflexiona sobre la ejecución del siguiente plan.

TAREA ORIGINAL:
{task}

PLAN EJECUTADO:
- Pasos totales: {total_steps}
- Pasos completados: {completed_steps}
- Pasos fallidos: {failed_steps}
- Intentos totales: {total_attempts}
- Tiempo total: {execution_time:.1f}s

RESULTADOS POR PASO:
{step_results}

CRITERIO DE ÉXITO ORIGINAL:
{success_criteria}

Reflexiona y responde en JSON:
```json
{{
  "quality": "excellent|good|acceptable|poor|failed",
  "summary": "Resumen de la ejecución",
  "final_response": "Respuesta final para el usuario",
  "confidence": 0.0-1.0,
  "strengths": ["fortaleza1", "fortaleza2"],
  "weaknesses": ["debilidad1", "debilidad2"],
  "improvements": ["mejora1", "mejora2"],
  "lessons": [
    {{
      "category": "success|failure|optimization",
      "description": "Lección aprendida",
      "applies_to": ["tipo_tarea1"]
    }}
  ]
}}
```

REGLAS:
- La respuesta final debe ser útil y directa para el usuario
- Identifica patrones de éxito y fallo
- Las lecciones deben ser aplicables a futuras ejecuciones

Responde SOLO con el JSON."""

    def __init__(self, llm_interface: Any = None, verbose: bool = True):
        """
        Args:
            llm_interface: Interfaz al LLM
            verbose: Mostrar reflexión en consola
        """
        self.llm = llm_interface
        self.verbose = verbose

        # Almacén de lecciones aprendidas
        self.lessons_learned: List[Lesson] = []

    def reflect(
        self,
        plan: Plan,
        context: ExecutionContext,
        verifications: List[VerificationResult] = None
    ) -> Reflection:
        """
        Reflexionar sobre la ejecución de un plan.

        Args:
            plan: El plan ejecutado
            context: Contexto de ejecución
            verifications: Resultados de verificación

        Returns:
            Reflection con análisis completo
        """
        if self.verbose:
            print("\n💭 REFLEXIONANDO...")

        # Calcular métricas básicas
        import time
        execution_time = time.time() - context.start_time if context.start_time else 0

        # Si tenemos LLM, reflexión profunda
        if self.llm:
            reflection = self._llm_reflection(plan, context, execution_time)
        else:
            reflection = self._heuristic_reflection(plan, context, execution_time)

        # Almacenar lecciones aprendidas
        self.lessons_learned.extend(reflection.lessons)

        if self.verbose:
            self._print_reflection(reflection)

        return reflection

    def _heuristic_reflection(
        self,
        plan: Plan,
        context: ExecutionContext,
        execution_time: float
    ) -> Reflection:
        """Reflexión basada en heurísticas"""
        completed = len(plan.completed_steps)
        failed = len(plan.failed_steps)
        total = len(plan.steps)

        # Determinar calidad
        success_rate = completed / total if total > 0 else 0

        if success_rate >= 0.95:
            quality = ReflectionQuality.EXCELLENT
        elif success_rate >= 0.8:
            quality = ReflectionQuality.GOOD
        elif success_rate >= 0.5:
            quality = ReflectionQuality.ACCEPTABLE
        elif success_rate >= 0.2:
            quality = ReflectionQuality.POOR
        else:
            quality = ReflectionQuality.FAILED

        # Construir resumen
        if quality in [ReflectionQuality.EXCELLENT, ReflectionQuality.GOOD]:
            summary = f"Plan ejecutado exitosamente ({completed}/{total} pasos)"
        elif quality == ReflectionQuality.ACCEPTABLE:
            summary = f"Plan parcialmente completado ({completed}/{total} pasos)"
        else:
            summary = f"Plan con dificultades ({failed}/{total} pasos fallidos)"

        # Identificar fortalezas y debilidades
        strengths = []
        weaknesses = []

        if success_rate >= 0.8:
            strengths.append("Alta tasa de éxito en ejecución")
        if execution_time < 30:
            strengths.append("Ejecución rápida")
        if context.total_attempts <= total * 1.2:
            strengths.append("Pocos reintentos necesarios")

        if failed > 0:
            weaknesses.append(f"{failed} pasos fallaron")
        if context.total_attempts > total * 2:
            weaknesses.append("Demasiados reintentos")
        if execution_time > 120:
            weaknesses.append("Ejecución lenta")

        # Construir respuesta final
        final_response = self._build_final_response(plan, context)

        # Generar lecciones
        lessons = self._generate_lessons(plan, context, quality)

        return Reflection(
            plan_task=plan.task,
            quality=quality,
            summary=summary,
            steps_completed=completed,
            steps_failed=failed,
            total_attempts=context.total_attempts,
            execution_time=execution_time,
            strengths=strengths,
            weaknesses=weaknesses,
            improvements=self._suggest_improvements(quality, weaknesses),
            lessons=lessons,
            final_response=final_response,
            confidence=success_rate * 0.8 + 0.2
        )

    def _llm_reflection(
        self,
        plan: Plan,
        context: ExecutionContext,
        execution_time: float
    ) -> Reflection:
        """Reflexión usando LLM"""
        # Formatear resultados de pasos
        step_results = self._format_step_results(context.results)

        prompt = self.REFLECTION_PROMPT.format(
            task=plan.task,
            total_steps=len(plan.steps),
            completed_steps=len(plan.completed_steps),
            failed_steps=len(plan.failed_steps),
            total_attempts=context.total_attempts,
            execution_time=execution_time,
            step_results=step_results,
            success_criteria=plan.success_criteria or "Completar todos los pasos"
        )

        try:
            response = self._call_llm(prompt)
            parsed = self._parse_response(response)
        except Exception as e:
            logger.error(f"Error en LLM: {e}")
            return self._heuristic_reflection(plan, context, execution_time)

        # Mapear calidad
        quality_map = {
            "excellent": ReflectionQuality.EXCELLENT,
            "good": ReflectionQuality.GOOD,
            "acceptable": ReflectionQuality.ACCEPTABLE,
            "poor": ReflectionQuality.POOR,
            "failed": ReflectionQuality.FAILED
        }
        quality = quality_map.get(
            parsed.get("quality", "acceptable"),
            ReflectionQuality.ACCEPTABLE
        )

        # Parsear lecciones
        lessons = []
        for l in parsed.get("lessons", []):
            lessons.append(Lesson(
                category=l.get("category", "optimization"),
                description=l.get("description", ""),
                applies_to=l.get("applies_to", []),
                confidence=0.7
            ))

        return Reflection(
            plan_task=plan.task,
            quality=quality,
            summary=parsed.get("summary", ""),
            steps_completed=len(plan.completed_steps),
            steps_failed=len(plan.failed_steps),
            total_attempts=context.total_attempts,
            execution_time=execution_time,
            strengths=parsed.get("strengths", []),
            weaknesses=parsed.get("weaknesses", []),
            improvements=parsed.get("improvements", []),
            lessons=lessons,
            final_response=parsed.get("final_response", ""),
            confidence=parsed.get("confidence", 0.7)
        )

    def _build_final_response(
        self,
        plan: Plan,
        context: ExecutionContext
    ) -> str:
        """Construir respuesta final para el usuario"""
        if not context.results:
            return "No se pudo completar la tarea."

        # Obtener resultados exitosos
        successful_results = [r for r in context.results if r.success]

        if not successful_results:
            failed_results = [r for r in context.results if not r.success]
            errors = [r.error for r in failed_results[:3]]
            return f"La tarea no pudo completarse. Errores: {'; '.join(errors)}"

        # Combinar outputs exitosos
        outputs = [r.output for r in successful_results if r.output]

        if len(outputs) == 1:
            return outputs[0]
        elif len(outputs) > 1:
            # Resumir múltiples outputs
            combined = "\n\n".join([f"• {o[:200]}" for o in outputs[:5]])
            return f"Tarea completada:\n{combined}"
        else:
            return "Tarea completada exitosamente."

    def _generate_lessons(
        self,
        plan: Plan,
        context: ExecutionContext,
        quality: ReflectionQuality
    ) -> List[Lesson]:
        """Generar lecciones aprendidas"""
        lessons = []

        # Lección de éxito
        if quality in [ReflectionQuality.EXCELLENT, ReflectionQuality.GOOD]:
            lessons.append(Lesson(
                category="success",
                description=f"Estrategia '{plan.overall_strategy}' efectiva para esta tarea",
                applies_to=["tareas similares"],
                confidence=0.8
            ))

        # Lección de fallo
        if quality in [ReflectionQuality.POOR, ReflectionQuality.FAILED]:
            failed_steps = [s for s in plan.steps if s.id in plan.failed_steps]
            if failed_steps:
                lessons.append(Lesson(
                    category="failure",
                    description=f"Paso '{failed_steps[0].description[:50]}...' requiere mejor manejo",
                    applies_to=["pasos similares"],
                    confidence=0.7
                ))

        # Lección de optimización
        if context.total_attempts > len(plan.steps) * 1.5:
            lessons.append(Lesson(
                category="optimization",
                description="Reducir reintentos mejorando validación previa",
                applies_to=["todas las tareas"],
                confidence=0.6
            ))

        return lessons

    def _suggest_improvements(
        self,
        quality: ReflectionQuality,
        weaknesses: List[str]
    ) -> List[str]:
        """Sugerir mejoras para futuras ejecuciones"""
        improvements = []

        if quality in [ReflectionQuality.POOR, ReflectionQuality.FAILED]:
            improvements.append("Mejorar análisis previo de la tarea")
            improvements.append("Agregar pasos de verificación intermedios")

        if "fallaron" in " ".join(weaknesses).lower():
            improvements.append("Implementar mejor manejo de errores")

        if "reintentos" in " ".join(weaknesses).lower():
            improvements.append("Optimizar estrategias de corrección")

        if "lenta" in " ".join(weaknesses).lower():
            improvements.append("Paralelizar pasos independientes")

        return improvements

    def _format_step_results(self, results: List[StepResult]) -> str:
        """Formatear resultados para el prompt"""
        if not results:
            return "(Sin resultados)"

        lines = []
        for r in results[:10]:  # Máximo 10
            status = "✅" if r.success else "❌"
            output = r.output[:100] if r.output else r.error[:100] if r.error else "N/A"
            lines.append(f"- Paso {r.step_id} {status}: {output}")

        return "\n".join(lines)

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
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        return {"summary": response[:500], "quality": "acceptable"}

    def _print_reflection(self, reflection: Reflection):
        """Imprimir reflexión en consola"""
        quality_icons = {
            ReflectionQuality.EXCELLENT: "🌟",
            ReflectionQuality.GOOD: "✅",
            ReflectionQuality.ACCEPTABLE: "⚠️",
            ReflectionQuality.POOR: "❌",
            ReflectionQuality.FAILED: "💔"
        }

        icon = quality_icons.get(reflection.quality, "❓")

        print(f"\n   {icon} Calidad: {reflection.quality.value.upper()}")
        print(f"   📊 Éxito: {reflection.success_rate:.0%} ({reflection.steps_completed}/{reflection.steps_completed + reflection.steps_failed})")
        print(f"   ⏱️ Tiempo: {reflection.execution_time:.1f}s")
        print(f"   🎯 Confianza: {reflection.confidence:.0%}")

        if reflection.strengths:
            print(f"\n   💪 Fortalezas:")
            for s in reflection.strengths[:3]:
                print(f"      • {s}")

        if reflection.weaknesses:
            print(f"\n   🔻 Debilidades:")
            for w in reflection.weaknesses[:3]:
                print(f"      • {w}")

        if reflection.lessons:
            print(f"\n   📚 Lecciones ({len(reflection.lessons)}):")
            for l in reflection.lessons[:3]:
                print(f"      [{l.category}] {l.description[:50]}...")

        print()

    def get_applicable_lessons(self, task_type: str) -> List[Lesson]:
        """Obtener lecciones aplicables a un tipo de tarea"""
        return [
            l for l in self.lessons_learned
            if not l.applies_to or task_type in l.applies_to
        ]
