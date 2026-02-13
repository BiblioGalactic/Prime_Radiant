#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    EVALUATOR - Evaluador de Respuestas
========================================
Sistema de IA con Agentes y RAGs

Modelo evaluador separado que determina si una respuesta es:
- OK: Completa y correcta
- PARCIAL: Útil pero incompleta
- FALLA: Incorrecta o inútil
"""

import os
import sys
import subprocess
import json
import re
import logging
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict
from enum import Enum
import re

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Verdict(Enum):
    """Veredictos de evaluación"""
    OK = "OK"
    PARCIAL = "PARCIAL"
    FALLA = "FALLA"
    ERROR = "ERROR"


@dataclass
class ConfidenceMetrics:
    """Métricas detalladas de confianza"""
    length_score: float      # Score basado en longitud
    overlap_score: float     # Overlap semántico query-answer
    coverage_score: float    # Cobertura del contexto
    uncertainty_score: float # Ausencia de incertidumbre
    overall: float           # Score combinado

    def to_dict(self) -> dict:
        return {
            "length": self.length_score,
            "overlap": self.overlap_score,
            "coverage": self.coverage_score,
            "uncertainty": self.uncertainty_score,
            "overall": self.overall
        }


@dataclass
class EvaluationResult:
    """Resultado de evaluación"""
    verdict: Verdict
    confidence: float  # 0.0 - 1.0
    reason: str
    suggestions: list  # Sugerencias para mejorar
    metrics: Optional[ConfidenceMetrics] = None  # Métricas detalladas

    def is_acceptable(self) -> bool:
        """¿La respuesta es aceptable?"""
        return self.verdict in (Verdict.OK, Verdict.PARCIAL)

    def needs_agents(self) -> bool:
        """¿Necesita activar agentes?"""
        return self.verdict in (Verdict.PARCIAL, Verdict.FALLA)

    def needs_refinement(self) -> bool:
        """¿Necesita refinamiento de query?"""
        return self.confidence < 0.6 or self.verdict == Verdict.PARCIAL

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "suggestions": self.suggestions,
            "metrics": self.metrics.to_dict() if self.metrics else None
        }


EVALUATOR_SYSTEM = """Eres un evaluador experto de respuestas de IA.

Tu trabajo es evaluar si una respuesta es adecuada para la consulta del usuario.

CRITERIOS DE EVALUACIÓN:

1. COMPLETITUD: ¿La respuesta cubre todos los aspectos de la pregunta?
2. PRECISIÓN: ¿La información es correcta y verificable?
3. RELEVANCIA: ¿La respuesta está enfocada en lo que se preguntó?
4. CLARIDAD: ¿La respuesta es clara y comprensible?

VEREDICTOS:

- OK: Respuesta completa, precisa, relevante y clara. No necesita mejoras.
- PARCIAL: Respuesta útil pero incompleta. Falta información o contexto.
- FALLA: Respuesta incorrecta, irrelevante, confusa o evasiva.

FORMATO DE RESPUESTA (JSON):
{
  "veredicto": "OK|PARCIAL|FALLA",
  "confianza": 0.0-1.0,
  "razon": "Explicación breve del veredicto",
  "sugerencias": ["lista", "de", "mejoras"]
}

Responde SOLO con el JSON, sin texto adicional."""


EVALUATOR_TEMPLATE = """CONSULTA DEL USUARIO:
{query}

CONTEXTO DISPONIBLE (RAG):
{context}

RESPUESTA A EVALUAR:
{response}

Evalúa esta respuesta según los criterios establecidos.
Responde SOLO con JSON válido."""


class ResponseEvaluator:
    """
    Evaluador de respuestas usando modelo LLM separado.

    Usa llama-cli con modelo ligero para evaluaciones rápidas.
    """

    def __init__(self):
        self.llama_cli = config.LLAMA_CLI
        self.model = config.MODEL_EVALUATOR
        self._validate_setup()

    def _validate_setup(self):
        """Validar que el setup es correcto"""
        if not os.path.isfile(self.llama_cli):
            raise FileNotFoundError(f"llama-cli no encontrado: {self.llama_cli}")
        if not os.path.isfile(self.model.path):
            raise FileNotFoundError(f"Modelo no encontrado: {self.model.path}")

    def evaluate(
        self,
        query: str,
        response: str,
        context: str = ""
    ) -> EvaluationResult:
        """
        Evaluar una respuesta.

        Args:
            query: Consulta original del usuario
            response: Respuesta a evaluar
            context: Contexto RAG disponible

        Returns:
            EvaluationResult con veredicto
        """
        # Construir prompt
        prompt = EVALUATOR_TEMPLATE.format(
            query=query[:500],  # Limitar tamaño
            context=context[:1000] if context else "Sin contexto adicional",
            response=response[:2000]
        )

        # Llamar a llama-cli
        try:
            result = self._call_llm(prompt)
            return self._parse_result(result)
        except Exception as e:
            logger.error(f"Error en evaluación: {e}")
            return EvaluationResult(
                verdict=Verdict.ERROR,
                confidence=0.0,
                reason=str(e),
                suggestions=[]
            )

    def _call_llm(self, prompt: str) -> str:
        """Llamar al modelo LLM"""
        cmd = [
            self.llama_cli,
            "-m", self.model.path,
            "-c", str(self.model.ctx_size),
            "-t", str(self.model.threads),
            "-n", str(self.model.n_predict),
            "--temp", str(self.model.temperature),
            "-p", f"{EVALUATOR_SYSTEM}\n\n{prompt}",
            "--no-display-prompt"
        ]

        logger.debug(f"Evaluator command: {' '.join(cmd[:5])}...")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            raise RuntimeError(f"llama-cli error: {result.stderr}")

        return result.stdout.strip()

    def _parse_result(self, raw: str) -> EvaluationResult:
        """Parsear resultado del LLM"""
        # Buscar JSON en la respuesta
        json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)

        if not json_match:
            # Intentar parsear toda la respuesta
            try:
                data = json.loads(raw)
            except:
                # Fallback: buscar palabras clave
                return self._fallback_parse(raw)
        else:
            try:
                data = json.loads(json_match.group())
            except:
                return self._fallback_parse(raw)

        # Extraer campos
        verdict_str = data.get("veredicto", "FALLA").upper()
        try:
            verdict = Verdict[verdict_str]
        except KeyError:
            verdict = Verdict.FALLA

        return EvaluationResult(
            verdict=verdict,
            confidence=float(data.get("confianza", 0.5)),
            reason=data.get("razon", "Sin razón especificada"),
            suggestions=data.get("sugerencias", [])
        )

    def _fallback_parse(self, raw: str) -> EvaluationResult:
        """Parseo de emergencia basado en keywords"""
        raw_lower = raw.lower()

        if "ok" in raw_lower and "completa" in raw_lower:
            verdict = Verdict.OK
            confidence = 0.7
        elif "parcial" in raw_lower or "incompleta" in raw_lower:
            verdict = Verdict.PARCIAL
            confidence = 0.6
        elif "falla" in raw_lower or "incorrecta" in raw_lower or "error" in raw_lower:
            verdict = Verdict.FALLA
            confidence = 0.6
        else:
            # Por defecto, asumir parcial para no perder consultas
            verdict = Verdict.PARCIAL
            confidence = 0.4

        return EvaluationResult(
            verdict=verdict,
            confidence=confidence,
            reason=f"Parseo fallback: {raw[:100]}...",
            suggestions=["Revisar respuesta manualmente"]
        )

    def quick_evaluate(self, query: str, response: str) -> Verdict:
        """Evaluación rápida sin contexto"""
        result = self.evaluate(query, response)
        return result.verdict


# === Calculador de Confianza Sofisticado ===

class ConfidenceCalculator:
    """
    Calcula métricas de confianza sofisticadas para respuestas.

    Métricas combinadas:
    1. Longitud normalizada
    2. Overlap semántico query-answer
    3. Coverage del contexto
    4. Ausencia de incertidumbre
    """

    # Palabras de incertidumbre con pesos
    UNCERTAINTY_WORDS = {
        "no sé": 0.8, "no estoy seguro": 0.7, "quizás": 0.5,
        "tal vez": 0.5, "posiblemente": 0.4, "podría ser": 0.4,
        "no tengo información": 0.8, "desconozco": 0.7,
        "no puedo": 0.6, "i don't know": 0.8, "maybe": 0.5,
        "perhaps": 0.5, "possibly": 0.4, "uncertain": 0.6
    }

    # Longitudes esperadas por tipo de respuesta
    LENGTH_TARGETS = {
        "short": (50, 150),    # Respuestas cortas
        "medium": (150, 500),  # Respuestas medias
        "long": (500, 2000),   # Respuestas largas
        "default": (100, 800)  # Default
    }

    @classmethod
    def compute(
        cls,
        answer: str,
        query: str,
        context: str = "",
        expected_length: str = "default"
    ) -> ConfidenceMetrics:
        """
        Calcular métricas de confianza.

        Args:
            answer: Respuesta a evaluar
            query: Consulta original
            context: Contexto usado para generar la respuesta
            expected_length: Tipo de longitud esperada

        Returns:
            ConfidenceMetrics con todas las métricas
        """
        # 1. Score de longitud
        length_score = cls._compute_length_score(answer, expected_length)

        # 2. Score de overlap semántico
        overlap_score = cls._compute_overlap_score(answer, query)

        # 3. Score de cobertura del contexto
        coverage_score = cls._compute_coverage_score(answer, context) if context else 0.5

        # 4. Score de incertidumbre (invertido - menos incertidumbre = mejor)
        uncertainty_score = cls._compute_uncertainty_score(answer)

        # Calcular overall con pesos
        weights = {
            "length": 0.15,
            "overlap": 0.35,
            "coverage": 0.25,
            "uncertainty": 0.25
        }

        overall = (
            weights["length"] * length_score +
            weights["overlap"] * overlap_score +
            weights["coverage"] * coverage_score +
            weights["uncertainty"] * uncertainty_score
        )

        return ConfidenceMetrics(
            length_score=round(length_score, 3),
            overlap_score=round(overlap_score, 3),
            coverage_score=round(coverage_score, 3),
            uncertainty_score=round(uncertainty_score, 3),
            overall=round(overall, 3)
        )

    @classmethod
    def _compute_length_score(cls, answer: str, expected_length: str) -> float:
        """Calcular score basado en longitud"""
        min_len, max_len = cls.LENGTH_TARGETS.get(expected_length, cls.LENGTH_TARGETS["default"])
        actual_len = len(answer)

        if actual_len < min_len:
            # Muy corta - penalizar
            return max(0.1, actual_len / min_len)
        elif actual_len <= max_len:
            # Dentro del rango ideal
            return 1.0
        else:
            # Muy larga - penalizar ligeramente
            return max(0.6, 1.0 - (actual_len - max_len) / (max_len * 2))

    @classmethod
    def _compute_overlap_score(cls, answer: str, query: str) -> float:
        """Calcular overlap semántico entre query y answer"""
        # Tokenizar
        query_words = set(re.findall(r'\b\w{3,}\b', query.lower()))
        answer_words = set(re.findall(r'\b\w{3,}\b', answer.lower()))

        # Eliminar stopwords comunes
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                    'el', 'la', 'los', 'las', 'un', 'una', 'es', 'son', 'que',
                    'de', 'en', 'por', 'para', 'con', 'sin', 'and', 'or', 'but'}
        query_words -= stopwords
        answer_words -= stopwords

        if not query_words:
            return 0.5

        # Calcular Jaccard similarity
        intersection = len(query_words & answer_words)
        union = len(query_words | answer_words)

        jaccard = intersection / union if union > 0 else 0

        # Bonus si la respuesta cubre la mayoría de términos de la query
        coverage_bonus = intersection / len(query_words) if query_words else 0

        return min(1.0, jaccard * 0.5 + coverage_bonus * 0.5)

    @classmethod
    def _compute_coverage_score(cls, answer: str, context: str) -> float:
        """Calcular qué tanto del contexto se refleja en la respuesta"""
        if not context:
            return 0.5

        # Extraer términos clave del contexto
        context_words = set(re.findall(r'\b\w{4,}\b', context.lower()))
        answer_words = set(re.findall(r'\b\w{4,}\b', answer.lower()))

        # Eliminar stopwords
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'that', 'this',
                    'el', 'la', 'los', 'las', 'que', 'como', 'para', 'por'}
        context_words -= stopwords
        answer_words -= stopwords

        if not context_words:
            return 0.5

        # Qué porcentaje de términos del contexto aparecen en la respuesta
        overlap = len(context_words & answer_words)
        coverage = overlap / len(context_words)

        return min(1.0, coverage * 1.5)  # Bonus por buena cobertura

    @classmethod
    def _compute_uncertainty_score(cls, answer: str) -> float:
        """Calcular score de certeza (inverso de incertidumbre)"""
        answer_lower = answer.lower()
        total_uncertainty = 0.0

        for phrase, weight in cls.UNCERTAINTY_WORDS.items():
            if phrase in answer_lower:
                total_uncertainty += weight

        # Normalizar y invertir
        uncertainty_normalized = min(1.0, total_uncertainty)
        certainty_score = 1.0 - uncertainty_normalized

        return certainty_score

    @classmethod
    def quality_ok(
        cls,
        answer: str,
        query: str,
        context: str = "",
        threshold: float = 0.5
    ) -> Tuple[bool, ConfidenceMetrics]:
        """
        Verificar si la calidad es aceptable.

        Args:
            answer: Respuesta a evaluar
            query: Consulta original
            context: Contexto usado
            threshold: Umbral de aceptación

        Returns:
            Tupla (es_aceptable, métricas)
        """
        metrics = cls.compute(answer, query, context)
        is_ok = metrics.overall >= threshold
        return is_ok, metrics


# === Evaluación heurística (sin LLM) ===

class HeuristicEvaluator:
    """
    Evaluador heurístico rápido mejorado.

    Usa reglas simples + ConfidenceCalculator para evaluación instantánea.
    Útil como pre-filtro antes del evaluador LLM.
    """

    # Palabras que indican incertidumbre
    UNCERTAINTY_WORDS = [
        "no sé", "no estoy seguro", "quizás", "tal vez",
        "posiblemente", "podría ser", "no tengo información",
        "desconozco", "no puedo", "no tengo acceso"
    ]

    # Palabras que indican error
    ERROR_WORDS = [
        "error", "fallo", "no encontrado", "no disponible",
        "timeout", "exception", "traceback"
    ]

    # Longitud mínima esperada
    MIN_RESPONSE_LENGTH = 50

    # Umbrales de calidad
    QUALITY_THRESHOLD_OK = 0.6
    QUALITY_THRESHOLD_PARTIAL = 0.4

    @classmethod
    def evaluate(cls, query: str, response: str, context: str = "") -> Tuple[Verdict, str]:
        """
        Evaluación heurística rápida.

        Returns:
            (Verdict, razón)
        """
        response_lower = response.lower()

        # Respuesta vacía o muy corta
        if not response or len(response.strip()) < cls.MIN_RESPONSE_LENGTH:
            return Verdict.FALLA, "Respuesta demasiado corta"

        # Detectar errores técnicos
        for word in cls.ERROR_WORDS:
            if word in response_lower:
                return Verdict.FALLA, f"Detectado error: '{word}'"

        # Detectar incertidumbre alta
        uncertainty_count = sum(
            1 for word in cls.UNCERTAINTY_WORDS
            if word in response_lower
        )
        if uncertainty_count >= 2:
            return Verdict.PARCIAL, "Alta incertidumbre en respuesta"

        # Verificar que menciona términos de la query
        query_words = set(query.lower().split())
        response_words = set(response_lower.split())
        overlap = query_words & response_words

        # Filtrar palabras comunes
        common_words = {"el", "la", "de", "que", "en", "es", "un", "una", "y", "a", "por", "para"}
        meaningful_overlap = overlap - common_words

        if len(meaningful_overlap) < 2:
            return Verdict.PARCIAL, "Respuesta poco relacionada con la consulta"

        # Si pasa todos los filtros, asumir OK
        return Verdict.OK, "Respuesta parece adecuada"

    @classmethod
    def evaluate_with_metrics(
        cls,
        query: str,
        response: str,
        context: str = ""
    ) -> EvaluationResult:
        """
        Evaluación heurística con métricas de confianza.

        Returns:
            EvaluationResult completo
        """
        # Evaluación básica
        verdict, reason = cls.evaluate(query, response, context)

        # Calcular métricas de confianza
        is_ok, metrics = ConfidenceCalculator.quality_ok(response, query, context)

        # Ajustar veredicto basado en métricas si es necesario
        if verdict == Verdict.OK and metrics.overall < cls.QUALITY_THRESHOLD_PARTIAL:
            verdict = Verdict.PARCIAL
            reason = f"Métricas bajas: {metrics.overall:.2f}"
        elif verdict == Verdict.PARCIAL and metrics.overall >= cls.QUALITY_THRESHOLD_OK:
            verdict = Verdict.OK
            reason = f"Métricas aceptables: {metrics.overall:.2f}"

        # Generar sugerencias
        suggestions = cls._generate_suggestions(metrics, verdict)

        return EvaluationResult(
            verdict=verdict,
            confidence=metrics.overall,
            reason=reason,
            suggestions=suggestions,
            metrics=metrics
        )

    @classmethod
    def _generate_suggestions(cls, metrics: ConfidenceMetrics, verdict: Verdict) -> List[str]:
        """Generar sugerencias de mejora basadas en métricas"""
        suggestions = []

        if metrics.length_score < 0.5:
            suggestions.append("Respuesta muy corta, ampliar con más detalles")

        if metrics.overlap_score < 0.4:
            suggestions.append("Respuesta poco relacionada con la pregunta")

        if metrics.coverage_score < 0.4:
            suggestions.append("No utiliza suficiente información del contexto")

        if metrics.uncertainty_score < 0.5:
            suggestions.append("Reducir expresiones de incertidumbre")

        if verdict == Verdict.FALLA:
            suggestions.append("Considerar reformular la consulta")
            suggestions.append("Activar agentes para búsqueda adicional")

        return suggestions


# === Factory ===

def create_evaluator(use_llm: bool = True) -> ResponseEvaluator:
    """Crear evaluador"""
    if use_llm:
        try:
            return ResponseEvaluator()
        except FileNotFoundError as e:
            logger.warning(f"LLM evaluator no disponible: {e}")

    # Fallback: wrapper de heurístico
    class HeuristicWrapper:
        def evaluate(self, query, response, context=""):
            verdict, reason = HeuristicEvaluator.evaluate(query, response)
            return EvaluationResult(
                verdict=verdict,
                confidence=0.5,
                reason=reason,
                suggestions=[]
            )

    return HeuristicWrapper()


if __name__ == "__main__":
    print("=== Test Evaluator ===\n")

    # Test heurístico
    print("1. Evaluador Heurístico:")

    tests = [
        ("¿Qué es Python?", "Python es un lenguaje de programación interpretado, de alto nivel y propósito general."),
        ("¿Qué es Python?", "No sé, no estoy seguro de qué es eso."),
        ("¿Qué es Python?", "Error: timeout"),
        ("¿Qué es Python?", "ok"),
    ]

    for query, response in tests:
        verdict, reason = HeuristicEvaluator.evaluate(query, response)
        print(f"   Q: {query[:30]}...")
        print(f"   R: {response[:40]}...")
        print(f"   → {verdict.value}: {reason}\n")

    # Test LLM (si está disponible)
    print("2. Evaluador LLM:")
    try:
        evaluator = ResponseEvaluator()
        result = evaluator.evaluate(
            "¿Qué es Python?",
            "Python es un lenguaje de programación interpretado, de alto nivel y de propósito general, creado por Guido van Rossum.",
            "Python fue creado en 1991."
        )
        print(f"   Veredicto: {result.verdict.value}")
        print(f"   Confianza: {result.confidence}")
        print(f"   Razón: {result.reason}")
        print(f"   Sugerencias: {result.suggestions}")
    except FileNotFoundError as e:
        print(f"   ⚠️ LLM no disponible: {e}")

    print("\n✅ Test completado")
