#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    CRITIC - Crítico de Respuestas
========================================
Sistema de IA con Agentes y RAGs

Agente crítico que evalúa y mejora respuestas:
- Detecta errores, inconsistencias y omisiones
- Sugiere mejoras específicas
- Puede regenerar respuestas mejoradas
"""

import os
import sys
import re
import subprocess
import json
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config import config
from core.evaluator import Verdict, ConfidenceCalculator, ConfidenceMetrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Critic")


class CriticVerdict(Enum):
    """Veredictos del crítico"""
    APPROVE = "approve"           # Respuesta aceptable
    NEEDS_REVISION = "revision"   # Necesita ajustes menores
    NEEDS_REWRITE = "rewrite"     # Necesita reescritura
    REJECT = "reject"             # Rechazar completamente


@dataclass
class CriticFeedback:
    """Feedback del crítico"""
    verdict: CriticVerdict
    issues: List[str]         # Problemas identificados
    suggestions: List[str]    # Sugerencias de mejora
    improved_response: Optional[str]  # Respuesta mejorada (si aplica)
    confidence: float
    metrics: Optional[ConfidenceMetrics]


class ResponseCritic:
    """
    Crítico de respuestas que evalúa y mejora outputs del LLM.

    Funciones:
    1. Evaluar calidad de respuestas
    2. Identificar problemas específicos
    3. Sugerir mejoras
    4. Generar versión mejorada si es necesario
    """

    # Prompt del crítico
    CRITIC_PROMPT = """Eres un crítico experto que evalúa respuestas de IA.

CONSULTA ORIGINAL:
{query}

CONTEXTO DISPONIBLE:
{context}

RESPUESTA A EVALUAR:
{response}

Evalúa la respuesta según estos criterios:
1. PRECISIÓN: ¿La información es correcta según el contexto?
2. COMPLETITUD: ¿Responde todos los aspectos de la consulta?
3. CLARIDAD: ¿Es fácil de entender?
4. RELEVANCIA: ¿Se enfoca en lo que se preguntó?
5. COHERENCIA: ¿Es internamente consistente?

Si encuentras problemas, sugiere mejoras específicas.

Responde SOLO con JSON:
{{
  "verdict": "approve|revision|rewrite|reject",
  "issues": ["problema 1", "problema 2"],
  "suggestions": ["sugerencia 1", "sugerencia 2"],
  "confidence": 0.0-1.0
}}"""

    IMPROVE_PROMPT = """Mejora la siguiente respuesta basándote en el feedback del crítico.

CONSULTA ORIGINAL:
{query}

CONTEXTO:
{context}

RESPUESTA ORIGINAL:
{response}

PROBLEMAS IDENTIFICADOS:
{issues}

SUGERENCIAS:
{suggestions}

Genera una versión mejorada de la respuesta que:
1. Corrija los problemas identificados
2. Implemente las sugerencias
3. Mantenga un tono natural y claro
4. Se base en el contexto disponible

Responde SOLO con la respuesta mejorada, sin explicaciones adicionales."""

    # Patrones de problemas comunes
    ISSUE_PATTERNS = {
        "contradiction": [
            r'\b(pero|however|sin embargo)\b.*\b(contrario|opposite|diferente)\b',
            r'\b(sí|yes)\b.*\b(no|not)\b.*mismo',
        ],
        "uncertainty": [
            r'\b(no estoy seguro|not sure|quizás|maybe|posiblemente)\b',
            r'\b(podría ser|could be|tal vez|perhaps)\b',
        ],
        "incompleteness": [
            r'\b(etc\.|etcétera|and so on|entre otros)\b',
            r'\b(más información|more information|ver más)\b',
        ],
        "vagueness": [
            r'\b(algo|something|algunas|some|varios|various)\b',
            r'\b(generalmente|generally|normalmente|usually)\b',
        ],
        "off_topic": [
            r'\b(por cierto|by the way|hablando de|speaking of)\b',
        ]
    }

    def __init__(self, use_llm: bool = True):
        """
        Inicializar crítico.

        Args:
            use_llm: Si usar LLM para crítica avanzada
        """
        self.use_llm = use_llm
        self.llama_cli = config.LLAMA_CLI
        self.model = config.MODEL_FAST

    def evaluate_and_improve(
        self,
        response: str,
        query: str,
        context_docs: List[str] = None,
        auto_improve: bool = True
    ) -> CriticFeedback:
        """
        Evaluar respuesta y mejorarla si es necesario.

        Args:
            response: Respuesta a evaluar
            query: Consulta original
            context_docs: Documentos de contexto
            auto_improve: Si generar mejora automáticamente

        Returns:
            CriticFeedback con evaluación y mejora
        """
        context = "\n".join(context_docs[:3]) if context_docs else ""

        # 1. Evaluación heurística rápida
        heuristic_issues = self._heuristic_check(response, query, context)

        # 2. Calcular métricas de confianza
        is_ok, metrics = ConfidenceCalculator.quality_ok(response, query, context)

        # 3. Evaluación LLM si está disponible y hay problemas
        llm_feedback = None
        if self.use_llm and (heuristic_issues or not is_ok):
            try:
                llm_feedback = self._llm_evaluate(response, query, context)
            except Exception as e:
                logger.warning(f"[Critic] LLM evaluation failed: {e}")

        # 4. Combinar resultados
        all_issues = heuristic_issues.copy()
        suggestions = []

        if llm_feedback:
            all_issues.extend(llm_feedback.get("issues", []))
            suggestions = llm_feedback.get("suggestions", [])
            llm_confidence = llm_feedback.get("confidence", 0.5)
        else:
            llm_confidence = 0.5

        # Eliminar duplicados
        all_issues = list(dict.fromkeys(all_issues))
        suggestions = list(dict.fromkeys(suggestions))

        # 5. Determinar veredicto
        verdict = self._determine_verdict(all_issues, metrics, llm_feedback)

        # 6. Generar mejora si es necesario
        improved = None
        if auto_improve and verdict in (CriticVerdict.NEEDS_REVISION, CriticVerdict.NEEDS_REWRITE):
            improved = self._generate_improvement(
                response, query, context, all_issues, suggestions
            )

        # Calcular confianza combinada
        combined_confidence = (metrics.overall * 0.6 + llm_confidence * 0.4)

        return CriticFeedback(
            verdict=verdict,
            issues=all_issues,
            suggestions=suggestions,
            improved_response=improved,
            confidence=combined_confidence,
            metrics=metrics
        )

    def _heuristic_check(self, response: str, query: str, context: str) -> List[str]:
        """Verificación heurística rápida de problemas"""
        issues = []
        response_lower = response.lower()

        # Verificar patrones de problemas
        for issue_type, patterns in self.ISSUE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, response_lower, re.IGNORECASE):
                    if issue_type == "contradiction":
                        issues.append("Posible contradicción interna")
                    elif issue_type == "uncertainty":
                        issues.append("Alta incertidumbre en la respuesta")
                    elif issue_type == "incompleteness":
                        issues.append("Respuesta incompleta")
                    elif issue_type == "vagueness":
                        issues.append("Respuesta demasiado vaga")
                    elif issue_type == "off_topic":
                        issues.append("Contiene información fuera de tema")
                    break  # Solo un issue por tipo

        # Verificar longitud
        if len(response) < 50:
            issues.append("Respuesta demasiado corta")
        elif len(response) > 3000:
            issues.append("Respuesta excesivamente larga")

        # Verificar cobertura de query
        query_words = set(re.findall(r'\b\w{4,}\b', query.lower()))
        response_words = set(re.findall(r'\b\w{4,}\b', response_lower))
        stopwords = {'the', 'and', 'that', 'this', 'with', 'for', 'are', 'que', 'para', 'con', 'los', 'las'}
        query_words -= stopwords
        response_words -= stopwords

        if query_words:
            coverage = len(query_words & response_words) / len(query_words)
            if coverage < 0.3:
                issues.append("La respuesta no cubre los términos de la consulta")

        # Verificar uso del contexto
        if context:
            context_words = set(re.findall(r'\b\w{5,}\b', context.lower()))
            context_words -= stopwords
            if context_words:
                context_usage = len(context_words & response_words) / len(context_words)
                if context_usage < 0.1:
                    issues.append("No utiliza el contexto disponible")

        return issues

    def _llm_evaluate(self, response: str, query: str, context: str) -> Optional[Dict]:
        """Evaluación con LLM"""
        prompt = self.CRITIC_PROMPT.format(
            query=query[:500],
            context=context[:1000] if context else "Sin contexto adicional",
            response=response[:2000]
        )

        result = self._call_llm(prompt, max_tokens=300)

        try:
            json_match = re.search(r'\{[^{}]*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"[Critic] JSON parse failed: {e}")

        return None

    def _determine_verdict(
        self,
        issues: List[str],
        metrics: ConfidenceMetrics,
        llm_feedback: Optional[Dict]
    ) -> CriticVerdict:
        """Determinar veredicto basado en toda la información"""
        # Veredicto del LLM
        llm_verdict = None
        if llm_feedback:
            verdict_str = llm_feedback.get("verdict", "").lower()
            if verdict_str == "approve":
                llm_verdict = CriticVerdict.APPROVE
            elif verdict_str == "revision":
                llm_verdict = CriticVerdict.NEEDS_REVISION
            elif verdict_str == "rewrite":
                llm_verdict = CriticVerdict.NEEDS_REWRITE
            elif verdict_str == "reject":
                llm_verdict = CriticVerdict.REJECT

        # Reglas heurísticas
        if len(issues) == 0 and metrics.overall >= 0.7:
            return CriticVerdict.APPROVE
        elif len(issues) <= 2 and metrics.overall >= 0.5:
            return llm_verdict or CriticVerdict.NEEDS_REVISION
        elif len(issues) <= 4 and metrics.overall >= 0.3:
            return llm_verdict or CriticVerdict.NEEDS_REWRITE
        else:
            return CriticVerdict.REJECT

    def _generate_improvement(
        self,
        response: str,
        query: str,
        context: str,
        issues: List[str],
        suggestions: List[str]
    ) -> Optional[str]:
        """Generar versión mejorada de la respuesta"""
        if not self.use_llm:
            return None

        prompt = self.IMPROVE_PROMPT.format(
            query=query[:500],
            context=context[:1000] if context else "Sin contexto adicional",
            response=response[:1500],
            issues="\n".join(f"- {i}" for i in issues),
            suggestions="\n".join(f"- {s}" for s in suggestions)
        )

        try:
            improved = self._call_llm(prompt, max_tokens=1000)
            # Limpiar respuesta
            improved = improved.strip()
            if improved and len(improved) > 50:
                return improved
        except Exception as e:
            logger.warning(f"[Critic] Improvement generation failed: {e}")

        return None

    def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """Llamar al LLM"""
        cmd = [
            self.llama_cli,
            "-m", self.model.path,
            "-c", str(4096),
            "-t", str(4),
            "-n", str(max_tokens),
            "--temp", "0.3",
            "-p", prompt,
            "--no-display-prompt"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=45,
                stdin=subprocess.DEVNULL
            )

            output = result.stdout
            try:
                return output.decode('utf-8')
            except:
                return output.decode('latin-1', errors='replace')

        except subprocess.TimeoutExpired:
            logger.warning("[Critic] LLM timeout")
            return ""
        except Exception as e:
            logger.error(f"[Critic] LLM error: {e}")
            return ""

    def quick_check(self, response: str, query: str) -> Tuple[CriticVerdict, List[str]]:
        """
        Verificación rápida sin LLM.

        Returns:
            (veredicto, lista_de_issues)
        """
        issues = self._heuristic_check(response, query, "")
        is_ok, metrics = ConfidenceCalculator.quality_ok(response, query)

        if len(issues) == 0 and is_ok:
            return CriticVerdict.APPROVE, []
        elif len(issues) <= 2:
            return CriticVerdict.NEEDS_REVISION, issues
        else:
            return CriticVerdict.NEEDS_REWRITE, issues


# === Factory ===
_critic: Optional[ResponseCritic] = None


def get_critic(use_llm: bool = True) -> ResponseCritic:
    """Obtener instancia singleton del crítico"""
    global _critic
    if _critic is None:
        _critic = ResponseCritic(use_llm=use_llm)
    return _critic


# === CLI para pruebas ===
if __name__ == "__main__":
    print("=== Test Response Critic ===\n")

    critic = ResponseCritic(use_llm=False)  # Sin LLM para test rápido

    test_cases = [
        {
            "query": "¿Qué es Python?",
            "response": "Python es un lenguaje de programación interpretado de alto nivel, creado por Guido van Rossum en 1991. Es conocido por su sintaxis clara y legible, y se usa ampliamente en ciencia de datos, web development y automatización.",
            "context": "Python fue creado en 1991 por Guido van Rossum."
        },
        {
            "query": "¿Cómo instalar Docker?",
            "response": "No estoy seguro, pero quizás podrías buscar en Google. Algo sobre contenedores...",
            "context": "Docker se instala con apt install docker-ce en Ubuntu."
        },
        {
            "query": "Historia de la Segunda Guerra Mundial",
            "response": "Fue una guerra. Hubo batallas.",
            "context": "La Segunda Guerra Mundial (1939-1945) fue un conflicto global que involucró a la mayoría de las naciones del mundo."
        },
    ]

    for tc in test_cases:
        print(f"📝 Query: {tc['query']}")
        print(f"📄 Response: {tc['response'][:100]}...")

        feedback = critic.evaluate_and_improve(
            tc['response'],
            tc['query'],
            [tc['context']],
            auto_improve=False
        )

        print(f"   ⚖️ Verdict: {feedback.verdict.value}")
        print(f"   📊 Confidence: {feedback.confidence:.2f}")
        if feedback.issues:
            print(f"   ⚠️ Issues: {feedback.issues}")
        if feedback.suggestions:
            print(f"   💡 Suggestions: {feedback.suggestions[:2]}")
        print()
