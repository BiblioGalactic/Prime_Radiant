#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
🔧 CORRECTOR - Módulo de Autocorrección
========================================
Corrige pasos fallidos o parcialmente completados.
Implementa estrategias de recuperación automática.

Características:
- Análisis de errores
- Estrategias de corrección múltiples
- Reintentos inteligentes
- Modificación dinámica del plan
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .planner import Plan, PlanStep, StepStatus
from .executor import StepResult
from .verifier import VerificationResult, VerificationStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Corrector")


class CorrectionStrategy(Enum):
    """Estrategias de corrección disponibles"""
    RETRY = "retry"                     # Reintentar el mismo paso
    MODIFY_PARAMS = "modify_params"     # Modificar parámetros
    ALTERNATIVE_TOOL = "alternative_tool"  # Usar herramienta alternativa
    DECOMPOSE = "decompose"             # Descomponer en subpasos
    SKIP = "skip"                       # Saltar el paso
    ROLLBACK = "rollback"               # Revertir y reintentar desde antes
    MANUAL = "manual"                   # Requiere intervención manual
    ABORT = "abort"                     # Abortar el plan


@dataclass
class CorrectionAction:
    """Acción de corrección a tomar"""
    strategy: CorrectionStrategy
    description: str
    modified_step: Optional[PlanStep] = None
    new_params: Dict[str, Any] = field(default_factory=dict)
    alternative_tool: str = ""
    sub_steps: List[PlanStep] = field(default_factory=list)
    confidence: float = 0.7
    reasoning: str = ""

    def to_dict(self) -> Dict:
        return {
            "strategy": self.strategy.value,
            "description": self.description,
            "new_params": self.new_params,
            "alternative_tool": self.alternative_tool,
            "confidence": self.confidence,
            "reasoning": self.reasoning
        }


@dataclass
class CorrectionResult:
    """Resultado de aplicar una corrección"""
    success: bool
    action_taken: CorrectionAction
    new_result: Optional[StepResult] = None
    message: str = ""
    attempts: int = 1

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "action": self.action_taken.to_dict(),
            "message": self.message,
            "attempts": self.attempts
        }


class Corrector:
    """
    Módulo de autocorrección del agente.

    Analiza fallos y aplica estrategias de corrección:
    - Reintentar con mismos/diferentes parámetros
    - Usar herramienta alternativa
    - Descomponer el paso
    - Rollback a estado anterior
    """

    CORRECTION_PROMPT = """Analiza el fallo y sugiere una estrategia de corrección.

PASO FALLIDO:
- ID: {step_id}
- Descripción: {description}
- Acción: {action}
- Herramienta: {tool_hint}

ERROR:
{error}

RESULTADO OBTENIDO:
{result}

VERIFICACIÓN:
- Estado: {verification_status}
- Problemas: {issues}

ESTRATEGIA ORIGINAL DE CORRECCIÓN:
{original_strategy}

INTENTOS PREVIOS: {attempts}/{max_attempts}

HERRAMIENTAS DISPONIBLES:
{available_tools}

Sugiere la mejor estrategia de corrección en JSON:
```json
{{
  "strategy": "retry|modify_params|alternative_tool|decompose|skip|rollback|manual|abort",
  "description": "Descripción de la corrección",
  "new_params": {{}},
  "alternative_tool": "",
  "sub_steps": [],
  "confidence": 0.0-1.0,
  "reasoning": "Por qué esta estrategia es la mejor"
}}
```

REGLAS:
- Si es el primer intento, preferir "retry" o "modify_params"
- Si hay herramienta alternativa viable, sugerirla
- Si el paso es complejo, considerar "decompose"
- Si ya hay varios intentos fallidos, considerar "skip" o "abort"
- "manual" solo si realmente se necesita intervención humana

Responde SOLO con el JSON."""

    def __init__(
        self,
        llm_interface: Any = None,
        executor: Any = None,
        available_tools: List[str] = None,
        max_retries: int = 3,
        verbose: bool = True
    ):
        """
        Args:
            llm_interface: Interfaz al LLM
            executor: Ejecutor para reintentos
            available_tools: Herramientas disponibles
            max_retries: Máximo de reintentos por paso
            verbose: Mostrar correcciones en consola
        """
        self.llm = llm_interface
        self.executor = executor
        self.available_tools = available_tools or []
        self.max_retries = max_retries
        self.verbose = verbose

    def analyze_and_correct(
        self,
        step: PlanStep,
        result: StepResult,
        verification: VerificationResult,
        context: Any = None
    ) -> CorrectionResult:
        """
        Analizar fallo y aplicar corrección.

        Args:
            step: Paso que falló
            result: Resultado de la ejecución
            verification: Resultado de la verificación
            context: Contexto de ejecución

        Returns:
            CorrectionResult
        """
        if self.verbose:
            print(f"\n   🔧 Analizando corrección para paso {step.id}...")

        # Determinar estrategia
        action = self._determine_strategy(step, result, verification)

        if self.verbose:
            print(f"      📋 Estrategia: {action.strategy.value}")
            print(f"      📝 {action.description[:60]}...")

        # Aplicar corrección
        correction_result = self._apply_correction(step, action, context)

        return correction_result

    def _determine_strategy(
        self,
        step: PlanStep,
        result: StepResult,
        verification: VerificationResult
    ) -> CorrectionAction:
        """Determinar la mejor estrategia de corrección"""
        # Si tenemos LLM, usar para análisis avanzado
        if self.llm:
            return self._llm_strategy(step, result, verification)

        # Estrategia heurística
        return self._heuristic_strategy(step, result, verification)

    def _heuristic_strategy(
        self,
        step: PlanStep,
        result: StepResult,
        verification: VerificationResult
    ) -> CorrectionAction:
        """Determinar estrategia usando heurísticas"""
        attempts = step.attempts

        # Si hay estrategia original definida
        if step.correction_strategy and attempts == 1:
            return CorrectionAction(
                strategy=CorrectionStrategy.RETRY,
                description=f"Aplicar estrategia original: {step.correction_strategy}",
                reasoning="Primera corrección usando estrategia predefinida",
                confidence=0.7
            )

        # Primer intento: reintentar
        if attempts < 2:
            return CorrectionAction(
                strategy=CorrectionStrategy.RETRY,
                description="Reintentar la ejecución del paso",
                reasoning="Primer intento de corrección",
                confidence=0.6
            )

        # Segundo intento: modificar parámetros
        if attempts < 3:
            return CorrectionAction(
                strategy=CorrectionStrategy.MODIFY_PARAMS,
                description="Intentar con parámetros modificados",
                new_params=self._suggest_param_modifications(step, result),
                reasoning="Segundo intento con parámetros ajustados",
                confidence=0.5
            )

        # Tercer intento: buscar alternativa
        if attempts < 4 and self.available_tools:
            alt_tool = self._find_alternative_tool(step)
            if alt_tool:
                return CorrectionAction(
                    strategy=CorrectionStrategy.ALTERNATIVE_TOOL,
                    description=f"Usar herramienta alternativa: {alt_tool}",
                    alternative_tool=alt_tool,
                    reasoning="Intentar con herramienta alternativa",
                    confidence=0.5
                )

        # Muchos intentos: saltar
        if attempts >= self.max_retries:
            return CorrectionAction(
                strategy=CorrectionStrategy.SKIP,
                description="Saltar este paso después de múltiples intentos fallidos",
                reasoning=f"Máximo de intentos ({self.max_retries}) alcanzado",
                confidence=0.8
            )

        # Default: abortar
        return CorrectionAction(
            strategy=CorrectionStrategy.ABORT,
            description="Abortar el plan debido a fallos persistentes",
            reasoning="No se encontró estrategia de corrección viable",
            confidence=0.9
        )

    def _llm_strategy(
        self,
        step: PlanStep,
        result: StepResult,
        verification: VerificationResult
    ) -> CorrectionAction:
        """Determinar estrategia usando LLM"""
        prompt = self.CORRECTION_PROMPT.format(
            step_id=step.id,
            description=step.description,
            action=step.action,
            tool_hint=step.tool_hint or "Ninguna",
            error=result.error or "(Sin error explícito)",
            result=result.output[:500] if result.output else "(Sin output)",
            verification_status=verification.status.value,
            issues=", ".join(verification.issues) if verification.issues else "Ninguno",
            original_strategy=step.correction_strategy or "No definida",
            attempts=step.attempts,
            max_attempts=step.max_attempts,
            available_tools=", ".join(self.available_tools[:10]) or "Ninguna específica"
        )

        try:
            response = self._call_llm(prompt)
            parsed = self._parse_response(response)
        except Exception as e:
            logger.error(f"Error en LLM: {e}")
            return self._heuristic_strategy(step, result, verification)

        # Mapear estrategia
        strategy_map = {
            "retry": CorrectionStrategy.RETRY,
            "modify_params": CorrectionStrategy.MODIFY_PARAMS,
            "alternative_tool": CorrectionStrategy.ALTERNATIVE_TOOL,
            "decompose": CorrectionStrategy.DECOMPOSE,
            "skip": CorrectionStrategy.SKIP,
            "rollback": CorrectionStrategy.ROLLBACK,
            "manual": CorrectionStrategy.MANUAL,
            "abort": CorrectionStrategy.ABORT
        }

        strategy = strategy_map.get(
            parsed.get("strategy", "retry"),
            CorrectionStrategy.RETRY
        )

        return CorrectionAction(
            strategy=strategy,
            description=parsed.get("description", "Corrección automática"),
            new_params=parsed.get("new_params", {}),
            alternative_tool=parsed.get("alternative_tool", ""),
            confidence=parsed.get("confidence", 0.6),
            reasoning=parsed.get("reasoning", "")
        )

    def _apply_correction(
        self,
        step: PlanStep,
        action: CorrectionAction,
        context: Any
    ) -> CorrectionResult:
        """Aplicar la estrategia de corrección"""
        step.attempts += 1

        if action.strategy == CorrectionStrategy.RETRY:
            return self._apply_retry(step, action, context)

        elif action.strategy == CorrectionStrategy.MODIFY_PARAMS:
            return self._apply_modify_params(step, action, context)

        elif action.strategy == CorrectionStrategy.ALTERNATIVE_TOOL:
            return self._apply_alternative_tool(step, action, context)

        elif action.strategy == CorrectionStrategy.SKIP:
            return self._apply_skip(step, action)

        elif action.strategy == CorrectionStrategy.DECOMPOSE:
            return self._apply_decompose(step, action, context)

        elif action.strategy == CorrectionStrategy.ROLLBACK:
            return self._apply_rollback(step, action, context)

        elif action.strategy == CorrectionStrategy.MANUAL:
            return CorrectionResult(
                success=False,
                action_taken=action,
                message="Se requiere intervención manual",
                attempts=step.attempts
            )

        else:  # ABORT
            return CorrectionResult(
                success=False,
                action_taken=action,
                message="Plan abortado",
                attempts=step.attempts
            )

    def _apply_retry(
        self,
        step: PlanStep,
        action: CorrectionAction,
        context: Any
    ) -> CorrectionResult:
        """Aplicar estrategia de reintento"""
        if not self.executor:
            return CorrectionResult(
                success=False,
                action_taken=action,
                message="No hay ejecutor disponible para reintentar"
            )

        try:
            new_result = self.executor.execute_step(step, context)

            return CorrectionResult(
                success=new_result.success,
                action_taken=action,
                new_result=new_result,
                message="Reintento " + ("exitoso" if new_result.success else "fallido"),
                attempts=step.attempts
            )
        except Exception as e:
            return CorrectionResult(
                success=False,
                action_taken=action,
                message=f"Error en reintento: {str(e)}",
                attempts=step.attempts
            )

    def _apply_modify_params(
        self,
        step: PlanStep,
        action: CorrectionAction,
        context: Any
    ) -> CorrectionResult:
        """Aplicar modificación de parámetros"""
        # Actualizar parámetros del paso
        original_params = step.action_params.copy()
        step.action_params.update(action.new_params)

        if self.verbose:
            print(f"      🔄 Parámetros modificados: {action.new_params}")

        # Reintentar con nuevos parámetros
        result = self._apply_retry(step, action, context)

        # Restaurar parámetros originales si falló
        if not result.success:
            step.action_params = original_params

        return result

    def _apply_alternative_tool(
        self,
        step: PlanStep,
        action: CorrectionAction,
        context: Any
    ) -> CorrectionResult:
        """Aplicar herramienta alternativa"""
        original_tool = step.tool_hint
        step.tool_hint = action.alternative_tool

        if self.verbose:
            print(f"      🔧 Cambiando herramienta: {original_tool} → {action.alternative_tool}")

        result = self._apply_retry(step, action, context)

        if not result.success:
            step.tool_hint = original_tool

        return result

    def _apply_skip(
        self,
        step: PlanStep,
        action: CorrectionAction
    ) -> CorrectionResult:
        """Saltar el paso"""
        step.status = StepStatus.SKIPPED

        if self.verbose:
            print(f"      ⏭️ Paso {step.id} saltado")

        return CorrectionResult(
            success=True,  # Éxito en el sentido de que continuamos
            action_taken=action,
            message=f"Paso {step.id} saltado",
            attempts=step.attempts
        )

    def _apply_decompose(
        self,
        step: PlanStep,
        action: CorrectionAction,
        context: Any
    ) -> CorrectionResult:
        """Descomponer paso en subpasos"""
        # Esta estrategia requiere modificar el plan
        # Por ahora, simplemente reportamos que se necesita
        return CorrectionResult(
            success=False,
            action_taken=action,
            message="Descomposición de paso pendiente de implementar",
            attempts=step.attempts
        )

    def _apply_rollback(
        self,
        step: PlanStep,
        action: CorrectionAction,
        context: Any
    ) -> CorrectionResult:
        """Rollback y reintentar desde un punto anterior"""
        if step.rollback_action:
            if self.verbose:
                print(f"      ↩️ Ejecutando rollback: {step.rollback_action[:50]}...")
            # Aquí se ejecutaría la acción de rollback
            pass

        return CorrectionResult(
            success=False,
            action_taken=action,
            message="Rollback ejecutado, requiere replanificación",
            attempts=step.attempts
        )

    def _suggest_param_modifications(
        self,
        step: PlanStep,
        result: StepResult
    ) -> Dict[str, Any]:
        """Sugerir modificaciones a los parámetros"""
        suggestions = {}

        # Análisis heurístico del error
        error = result.error.lower() if result.error else ""

        if "timeout" in error:
            suggestions["timeout"] = step.action_params.get("timeout", 30) * 2

        if "not found" in error or "no existe" in error:
            # Posiblemente ruta incorrecta
            pass

        if "permission" in error or "denied" in error:
            # Problema de permisos
            pass

        return suggestions

    def _find_alternative_tool(self, step: PlanStep) -> Optional[str]:
        """Encontrar herramienta alternativa"""
        if not self.available_tools:
            return None

        # Mapa de herramientas relacionadas
        alternatives = {
            "leer_archivo": ["buscar_archivos", "grep"],
            "ejecutar_comando": ["claudia_cmd"],
            "buscar": ["grep", "listar_directorio"],
            "claudia": ["claudia_analyze", "claudia_project"],
        }

        current_tool = step.tool_hint or ""

        for alt in alternatives.get(current_tool, []):
            if alt in self.available_tools and alt != current_tool:
                return alt

        return None

    def _call_llm(self, prompt: str) -> str:
        """Llamar al LLM"""
        if hasattr(self.llm, 'generate_simple'):
            return self.llm.generate_simple(prompt, max_tokens=500)
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

        return {"strategy": "retry", "description": "Reintento automático"}
