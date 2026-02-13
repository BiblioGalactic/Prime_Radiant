#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    REACT AGENT - Agente ReAct
========================================
Sistema de IA con Agentes y RAGs

Implementa el patrón ReAct (Reasoning + Acting):
- Thought: Razonamiento sobre la situación
- Action: Decisión de qué hacer
- Observation: Resultado de la acción
- Loop hasta respuesta final
"""

import os
import sys
import re
import subprocess
import json
import logging
from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config import config
from core.prompts import PromptBuilder, parse_react_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ReActAgent")


class ReActAction(Enum):
    """Acciones disponibles para el agente ReAct"""
    SEARCH = "search"       # Buscar en RAG
    LOOKUP = "lookup"       # Buscar término específico
    CALCULATE = "calculate"  # Cálculo matemático
    VERIFY = "verify"       # Verificar información
    ANSWER = "answer"       # Dar respuesta final
    REFINE = "refine"       # Refinar query
    UNKNOWN = "unknown"


@dataclass
class ReActStep:
    """Un paso del loop ReAct"""
    step_num: int
    thought: str
    action: ReActAction
    action_input: str
    observation: str = ""
    success: bool = True


@dataclass
class ReActResult:
    """Resultado final del agente ReAct"""
    answer: str
    steps: List[ReActStep]
    total_steps: int
    success: bool
    confidence: float
    reasoning_trace: str  # Resumen del razonamiento


class ReActAgent:
    """
    Agente que implementa el patrón ReAct.

    Ciclo:
    1. Thought - Razona sobre la situación actual
    2. Action - Decide qué acción tomar
    3. Observation - Ejecuta acción y observa resultado
    4. Repeat o Answer - Continúa o da respuesta final
    """

    # Máximo de iteraciones para evitar loops infinitos
    MAX_ITERATIONS = 5

    # Prompt del agente
    REACT_SYSTEM = """Eres un agente de razonamiento que resuelve problemas paso a paso.

Usa el formato Thought-Action-Observation para cada paso.

ACCIONES DISPONIBLES:
- SEARCH: Buscar información en la base de conocimiento
  Action Input: la consulta a buscar
- LOOKUP: Buscar un término específico en documentos actuales
  Action Input: el término a buscar
- CALCULATE: Realizar un cálculo matemático
  Action Input: la expresión a calcular
- VERIFY: Verificar si una afirmación es correcta
  Action Input: la afirmación a verificar
- ANSWER: Dar la respuesta final
  Action Input: tu respuesta completa

FORMATO DE RESPUESTA:
Thought: [tu razonamiento sobre qué hacer]
Action: [SEARCH|LOOKUP|CALCULATE|VERIFY|ANSWER]
Action Input: [input para la acción]

REGLAS:
1. Siempre comienza con Thought
2. Una sola acción por turno
3. Usa ANSWER cuando tengas información suficiente
4. Máximo {max_iter} iteraciones"""

    def __init__(
        self,
        search_fn: Callable[[str], str] = None,
        max_iterations: int = None
    ):
        """
        Inicializar agente ReAct.

        Args:
            search_fn: Función de búsqueda (recibe query, retorna contexto)
            max_iterations: Máximo de iteraciones
        """
        self.llama_cli = config.LLAMA_CLI
        self.model = config.MODEL_AGENTS  # Modelo para agentes
        self.max_iterations = max_iterations or self.MAX_ITERATIONS

        # Función de búsqueda (puede ser RAGManager.get_context)
        self._search_fn = search_fn

        # Historial de pasos
        self.steps: List[ReActStep] = []

    def set_search_function(self, fn: Callable[[str], str]):
        """Establecer función de búsqueda"""
        self._search_fn = fn

    def step(
        self,
        question: str,
        state: Dict = None
    ) -> Tuple[ReActStep, bool]:
        """
        Ejecutar un paso del loop ReAct.

        Args:
            question: Pregunta/tarea original
            state: Estado actual (contexto, pasos previos)

        Returns:
            (ReActStep, is_final) - Paso ejecutado y si es el final
        """
        state = state or {}
        step_num = len(self.steps) + 1

        # Construir prompt con historial
        prompt = self._build_prompt(question, self.steps)

        # Llamar al LLM
        response = self._call_llm(prompt)

        # Parsear respuesta
        parsed = parse_react_response(response)

        # Determinar acción
        action_str = parsed.get("action", "").upper()
        try:
            action = ReActAction[action_str]
        except KeyError:
            action = ReActAction.UNKNOWN

        action_input = parsed.get("action_input", "")
        thought = parsed.get("thought", "")

        # Ejecutar acción
        observation, success = self._execute_action(action, action_input)

        # Crear paso
        step = ReActStep(
            step_num=step_num,
            thought=thought,
            action=action,
            action_input=action_input,
            observation=observation,
            success=success
        )

        self.steps.append(step)

        # Verificar si es respuesta final
        is_final = (action == ReActAction.ANSWER or step_num >= self.max_iterations)

        return step, is_final

    def run(
        self,
        question: str,
        initial_context: str = ""
    ) -> ReActResult:
        """
        Ejecutar loop ReAct completo.

        Args:
            question: Pregunta a responder
            initial_context: Contexto inicial

        Returns:
            ReActResult con respuesta y trace
        """
        self.steps = []  # Reset
        answer = ""
        success = True

        logger.info(f"[ReAct] Iniciando para: {question[:50]}...")

        for i in range(self.max_iterations):
            step, is_final = self.step(question)

            logger.info(f"[ReAct] Step {step.step_num}: {step.action.value} → {step.observation[:50] if step.observation else 'N/A'}...")

            if is_final:
                if step.action == ReActAction.ANSWER:
                    answer = step.action_input
                else:
                    # Timeout - usar mejor respuesta disponible
                    answer = self._extract_best_answer()
                    success = False
                break

        # Calcular confianza
        confidence = self._calculate_confidence()

        # Generar trace de razonamiento
        trace = self._generate_trace()

        return ReActResult(
            answer=answer,
            steps=self.steps,
            total_steps=len(self.steps),
            success=success,
            confidence=confidence,
            reasoning_trace=trace
        )

    def _build_prompt(self, question: str, previous_steps: List[ReActStep]) -> str:
        """Construir prompt con historial"""
        system = self.REACT_SYSTEM.format(max_iter=self.max_iterations)

        # Historial de pasos
        history = ""
        for step in previous_steps:
            history += f"\nThought: {step.thought}\n"
            history += f"Action: {step.action.value.upper()}\n"
            history += f"Action Input: {step.action_input}\n"
            history += f"Observation: {step.observation}\n"

        prompt = f"""{system}

PREGUNTA: {question}

{history if history else "Sin pasos previos."}

Continúa con el siguiente paso:"""

        return prompt

    def _execute_action(self, action: ReActAction, action_input: str) -> Tuple[str, bool]:
        """
        Ejecutar una acción y obtener observación.

        Returns:
            (observation, success)
        """
        try:
            if action == ReActAction.SEARCH:
                return self._action_search(action_input)

            elif action == ReActAction.LOOKUP:
                return self._action_lookup(action_input)

            elif action == ReActAction.CALCULATE:
                return self._action_calculate(action_input)

            elif action == ReActAction.VERIFY:
                return self._action_verify(action_input)

            elif action == ReActAction.ANSWER:
                return (action_input, True)

            elif action == ReActAction.REFINE:
                return self._action_refine(action_input)

            else:
                return ("Acción no reconocida", False)

        except Exception as e:
            logger.error(f"[ReAct] Error ejecutando {action}: {e}")
            return (f"Error: {str(e)}", False)

    def _action_search(self, query: str) -> Tuple[str, bool]:
        """Ejecutar búsqueda"""
        if self._search_fn:
            try:
                result = self._search_fn(query)
                if result:
                    return (result[:1000], True)  # Limitar tamaño
                else:
                    return ("No se encontraron resultados", False)
            except Exception as e:
                return (f"Error en búsqueda: {e}", False)
        else:
            return ("Función de búsqueda no configurada", False)

    def _action_lookup(self, term: str) -> Tuple[str, bool]:
        """Buscar término en observaciones previas"""
        term_lower = term.lower()
        for step in reversed(self.steps):
            if term_lower in step.observation.lower():
                # Extraer contexto alrededor del término
                obs_lower = step.observation.lower()
                idx = obs_lower.find(term_lower)
                start = max(0, idx - 100)
                end = min(len(step.observation), idx + len(term) + 100)
                snippet = step.observation[start:end]
                return (f"...{snippet}...", True)

        return (f"Término '{term}' no encontrado en observaciones previas", False)

    def _action_calculate(self, expression: str) -> Tuple[str, bool]:
        """Evaluar expresión matemática"""
        try:
            # Limpiar expresión
            safe_expr = re.sub(r'[^0-9+\-*/().^ ]', '', expression)
            safe_expr = safe_expr.replace('^', '**')

            result = eval(safe_expr)
            return (f"Resultado: {result}", True)
        except Exception as e:
            return (f"Error de cálculo: {e}", False)

    def _action_verify(self, statement: str) -> Tuple[str, bool]:
        """Verificar afirmación (usando búsqueda)"""
        if self._search_fn:
            context = self._search_fn(statement)
            if context:
                # Simple heurística: verificar overlap
                statement_words = set(statement.lower().split())
                context_words = set(context.lower().split())
                overlap = len(statement_words & context_words) / len(statement_words) if statement_words else 0

                if overlap > 0.5:
                    return (f"La afirmación parece consistente con el contexto (overlap: {overlap:.2f})", True)
                else:
                    return (f"La afirmación no se puede verificar completamente (overlap: {overlap:.2f})", False)

        return ("No se puede verificar sin función de búsqueda", False)

    def _action_refine(self, query: str) -> Tuple[str, bool]:
        """Refinar query y buscar de nuevo"""
        # Importar refiner
        try:
            from core.query_refiner import get_refiner
            refiner = get_refiner(use_llm=False)
            result = refiner.refine(query)
            refined = result.refined

            # Buscar con query refinada
            if self._search_fn and refined != query:
                context = self._search_fn(refined)
                return (f"Query refinada: '{refined}'\n\nResultados: {context[:500]}", True)
            else:
                return (f"Query refinada: '{refined}'", True)
        except Exception as e:
            return (f"Error refinando: {e}", False)

    def _call_llm(self, prompt: str) -> str:
        """Llamar al LLM"""
        cmd = [
            self.llama_cli,
            "-m", self.model.path,
            "-c", str(self.model.ctx_size),
            "-t", str(self.model.threads),
            "-n", str(500),
            "--temp", str(self.model.temperature),
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
            logger.warning("[ReAct] LLM timeout")
            return "Thought: Timeout del modelo\nAction: ANSWER\nAction Input: No pude completar el razonamiento"
        except Exception as e:
            logger.error(f"[ReAct] LLM error: {e}")
            return f"Thought: Error del modelo\nAction: ANSWER\nAction Input: Error: {e}"

    def _extract_best_answer(self) -> str:
        """Extraer mejor respuesta de los pasos cuando hay timeout"""
        # Buscar en pasos previos alguna respuesta útil
        for step in reversed(self.steps):
            if step.action == ReActAction.SEARCH and step.success:
                return f"Basado en la búsqueda: {step.observation[:500]}"
            if step.action == ReActAction.VERIFY and step.success:
                return step.observation

        # Fallback: último pensamiento
        if self.steps:
            return f"Razonamiento parcial: {self.steps[-1].thought}"

        return "No se pudo completar el razonamiento"

    def _calculate_confidence(self) -> float:
        """Calcular confianza basada en los pasos"""
        if not self.steps:
            return 0.0

        # Factores
        success_rate = sum(1 for s in self.steps if s.success) / len(self.steps)
        answered = self.steps[-1].action == ReActAction.ANSWER
        few_steps = len(self.steps) <= 3

        confidence = 0.3  # Base
        confidence += success_rate * 0.3
        confidence += 0.2 if answered else 0.0
        confidence += 0.2 if few_steps else 0.0

        return min(confidence, 1.0)

    def _generate_trace(self) -> str:
        """Generar trace de razonamiento legible"""
        lines = []
        for step in self.steps:
            lines.append(f"[Step {step.step_num}]")
            lines.append(f"  Thought: {step.thought[:100]}...")
            lines.append(f"  Action: {step.action.value}")
            lines.append(f"  Result: {'✓' if step.success else '✗'} {step.observation[:50]}...")
            lines.append("")

        return "\n".join(lines)


# === Factory ===
_agent: Optional[ReActAgent] = None


def get_react_agent(search_fn: Callable = None) -> ReActAgent:
    """Obtener instancia singleton del agente ReAct"""
    global _agent
    if _agent is None:
        _agent = ReActAgent(search_fn=search_fn)
    elif search_fn:
        _agent.set_search_function(search_fn)
    return _agent


# === CLI para pruebas ===
if __name__ == "__main__":
    print("=== Test ReAct Agent ===\n")

    # Función de búsqueda mock
    def mock_search(query: str) -> str:
        responses = {
            "python": "Python es un lenguaje de programación interpretado, de alto nivel y propósito general.",
            "historia": "La historia es el estudio de eventos pasados.",
            "default": f"Búsqueda para: {query}"
        }
        for key, val in responses.items():
            if key in query.lower():
                return val
        return responses["default"]

    agent = ReActAgent(search_fn=mock_search, max_iterations=3)

    test_questions = [
        "¿Qué es Python y para qué se usa?",
        "Calcula 25 * 4 + 10",
    ]

    for q in test_questions:
        print(f"📝 Pregunta: {q}")
        result = agent.run(q)
        print(f"   ✅ Respuesta: {result.answer[:200]}...")
        print(f"   📊 Steps: {result.total_steps}, Confidence: {result.confidence:.2f}")
        print(f"   📋 Trace:\n{result.reasoning_trace[:300]}")
        print()
