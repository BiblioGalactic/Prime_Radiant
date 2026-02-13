#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
🔍 VERIFIER - Módulo de Verificación
========================================
Verifica que cada paso se completó correctamente
según los criterios definidos en el plan.

Características:
- Verificación automática de resultados
- Comparación con criterios esperados
- Detección de errores sutiles
- Evaluación de calidad
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from .planner import PlanStep, StepStatus
from .executor import StepResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Verifier")


class VerificationStatus(Enum):
    """Estado de verificación"""
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


@dataclass
class VerificationResult:
    """Resultado de verificación"""
    step_id: int
    status: VerificationStatus
    message: str
    confidence: float = 0.8  # 0.0 a 1.0
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "step_id": self.step_id,
            "status": self.status.value,
            "message": self.message,
            "confidence": self.confidence,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "metadata": self.metadata
        }

    @property
    def passed(self) -> bool:
        return self.status == VerificationStatus.PASSED

    @property
    def needs_correction(self) -> bool:
        return self.status in [VerificationStatus.FAILED, VerificationStatus.PARTIAL]


class Verifier:
    """
    Módulo de verificación del agente.

    Verifica que los pasos se completaron correctamente:
    - Compara resultado con criterios esperados
    - Detecta errores y problemas
    - Evalúa calidad del resultado
    - Sugiere correcciones si es necesario
    """

    VERIFICATION_PROMPT = """Verifica si el siguiente paso se completó correctamente.

PASO EJECUTADO:
- ID: {step_id}
- Descripción: {description}
- Acción: {action}

CRITERIO DE VERIFICACIÓN:
{verification_criteria}

RESULTADO ESPERADO:
{expected_output}

RESULTADO OBTENIDO:
{actual_output}

ERROR (si hubo):
{error}

Analiza y responde en JSON:
```json
{{
  "status": "passed|failed|partial",
  "confidence": 0.0-1.0,
  "message": "Explicación de la verificación",
  "issues": ["problema1", "problema2"] o [],
  "suggestions": ["sugerencia1", "sugerencia2"] o [],
  "reasoning": "Tu razonamiento detallado"
}}
```

REGLAS:
- "passed": El resultado cumple completamente el criterio
- "failed": El resultado no cumple el criterio o hubo error
- "partial": El resultado cumple parcialmente

Responde SOLO con el JSON."""

    def __init__(self, llm_interface: Any = None, verbose: bool = True):
        """
        Args:
            llm_interface: Interfaz al LLM (opcional para verificación avanzada)
            verbose: Mostrar verificación en consola
        """
        self.llm = llm_interface
        self.verbose = verbose

    def verify_step(self, step: PlanStep, result: StepResult) -> VerificationResult:
        """
        Verificar un paso ejecutado.

        Args:
            step: El paso del plan
            result: Resultado de la ejecución

        Returns:
            VerificationResult
        """
        if self.verbose:
            print(f"\n   🔍 Verificando paso {step.id}...")

        # Si no hay criterio de verificación, verificación básica
        if not step.verification_criteria:
            return self._basic_verification(step, result)

        # Si tenemos LLM, verificación avanzada
        if self.llm:
            return self._llm_verification(step, result)

        # Verificación heurística
        return self._heuristic_verification(step, result)

    def verify_plan(
        self,
        steps: List[PlanStep],
        results: List[StepResult]
    ) -> List[VerificationResult]:
        """
        Verificar todos los pasos de un plan.

        Args:
            steps: Lista de pasos
            results: Lista de resultados

        Returns:
            Lista de VerificationResult
        """
        verifications = []

        # Crear mapa de resultados por step_id
        result_map = {r.step_id: r for r in results}

        for step in steps:
            if step.id in result_map:
                ver = self.verify_step(step, result_map[step.id])
            else:
                ver = VerificationResult(
                    step_id=step.id,
                    status=VerificationStatus.SKIPPED,
                    message="Paso no ejecutado"
                )
            verifications.append(ver)

        return verifications

    def _basic_verification(self, step: PlanStep, result: StepResult) -> VerificationResult:
        """Verificación básica basada solo en éxito/fallo"""
        if result.success:
            return VerificationResult(
                step_id=step.id,
                status=VerificationStatus.PASSED,
                message="Paso ejecutado exitosamente",
                confidence=0.7  # Confianza moderada sin criterio específico
            )
        else:
            return VerificationResult(
                step_id=step.id,
                status=VerificationStatus.FAILED,
                message=f"Paso falló: {result.error}",
                confidence=0.9,
                issues=[result.error],
                suggestions=["Revisar el error y reintentar"]
            )

    def _heuristic_verification(self, step: PlanStep, result: StepResult) -> VerificationResult:
        """Verificación heurística sin LLM"""
        issues = []
        suggestions = []

        # Verificar si hubo error
        if not result.success:
            return VerificationResult(
                step_id=step.id,
                status=VerificationStatus.FAILED,
                message=f"Error en ejecución: {result.error}",
                confidence=0.9,
                issues=[result.error],
                suggestions=[step.correction_strategy] if step.correction_strategy else []
            )

        # Verificar si hay output
        if not result.output or result.output.strip() == "":
            issues.append("El resultado está vacío")
            suggestions.append("Verificar que la acción produjo output")

        # Verificar keywords del criterio en el output
        criteria_words = self._extract_keywords(step.verification_criteria)
        output_words = set(result.output.lower().split())

        matches = sum(1 for w in criteria_words if w in output_words)
        match_ratio = matches / len(criteria_words) if criteria_words else 0

        # Determinar estado
        if issues:
            status = VerificationStatus.PARTIAL if match_ratio > 0.3 else VerificationStatus.FAILED
            confidence = 0.6
        elif match_ratio >= 0.5:
            status = VerificationStatus.PASSED
            confidence = 0.7 + (match_ratio * 0.2)
        elif match_ratio >= 0.2:
            status = VerificationStatus.PARTIAL
            confidence = 0.6
            issues.append("El resultado cumple parcialmente los criterios")
        else:
            status = VerificationStatus.PARTIAL
            confidence = 0.5
            issues.append("No se pudo verificar completamente el resultado")

        return VerificationResult(
            step_id=step.id,
            status=status,
            message=f"Verificación heurística (coincidencia: {match_ratio:.0%})",
            confidence=confidence,
            issues=issues,
            suggestions=suggestions
        )

    def _llm_verification(self, step: PlanStep, result: StepResult) -> VerificationResult:
        """Verificación avanzada usando LLM"""
        prompt = self.VERIFICATION_PROMPT.format(
            step_id=step.id,
            description=step.description,
            action=step.action,
            verification_criteria=step.verification_criteria or "Ejecución exitosa",
            expected_output=step.expected_output or "No especificado",
            actual_output=result.output or "(Sin output)",
            error=result.error or "(Sin error)"
        )

        try:
            response = self._call_llm(prompt)
            parsed = self._parse_response(response)
        except Exception as e:
            logger.error(f"Error en verificación LLM: {e}")
            return self._heuristic_verification(step, result)

        # Mapear status
        status_map = {
            "passed": VerificationStatus.PASSED,
            "failed": VerificationStatus.FAILED,
            "partial": VerificationStatus.PARTIAL
        }
        status = status_map.get(parsed.get("status", "partial"), VerificationStatus.PARTIAL)

        ver_result = VerificationResult(
            step_id=step.id,
            status=status,
            message=parsed.get("message", "Verificación completada"),
            confidence=parsed.get("confidence", 0.7),
            issues=parsed.get("issues", []),
            suggestions=parsed.get("suggestions", []),
            metadata={"reasoning": parsed.get("reasoning", "")}
        )

        if self.verbose:
            icon = "✅" if ver_result.passed else ("⚠️" if status == VerificationStatus.PARTIAL else "❌")
            print(f"      {icon} {ver_result.message[:60]}... (confianza: {ver_result.confidence:.0%})")

        return ver_result

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

        return {"status": "partial", "message": response[:200]}

    def _extract_keywords(self, text: str) -> List[str]:
        """Extraer palabras clave de un texto"""
        if not text:
            return []

        # Limpiar y tokenizar
        words = re.findall(r'\b\w{3,}\b', text.lower())

        # Filtrar stopwords comunes
        stopwords = {'que', 'para', 'con', 'sin', 'por', 'los', 'las', 'del', 'una', 'uno'}
        keywords = [w for w in words if w not in stopwords]

        return keywords[:10]  # Máximo 10


# === QUICK VERIFIER ===
class QuickVerifier(Verifier):
    """
    Verificador rápido que solo comprueba éxito/fallo.
    No usa LLM.
    """

    def verify_step(self, step: PlanStep, result: StepResult) -> VerificationResult:
        """Verificación rápida basada solo en éxito"""
        if result.success:
            status = VerificationStatus.PASSED
            message = "Paso completado"
            confidence = 0.8
        else:
            status = VerificationStatus.FAILED
            message = f"Error: {result.error[:50]}..."
            confidence = 0.9

        if self.verbose:
            icon = "✅" if status == VerificationStatus.PASSED else "❌"
            print(f"      {icon} {message}")

        return VerificationResult(
            step_id=step.id,
            status=status,
            message=message,
            confidence=confidence,
            issues=[result.error] if result.error else []
        )
