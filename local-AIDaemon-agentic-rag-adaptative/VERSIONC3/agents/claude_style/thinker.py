#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
🧠 THINKER - Módulo de Pensamiento
========================================
Analiza la tarea y genera pensamientos estructurados
antes de planificar o actuar.

Similar a como Claude piensa antes de responder:
- Analiza qué se pide
- Identifica conceptos clave
- Considera diferentes enfoques
- Evalúa complejidad y riesgos
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Thinker")


class ThoughtType(Enum):
    """Tipos de pensamiento"""
    ANALYSIS = "analysis"           # Análisis de la tarea
    CLARIFICATION = "clarification" # Clarificación de requisitos
    APPROACH = "approach"           # Enfoque a seguir
    RISK = "risk"                   # Identificación de riesgos
    DEPENDENCY = "dependency"       # Dependencias identificadas
    CONSTRAINT = "constraint"       # Restricciones
    ASSUMPTION = "assumption"       # Suposiciones


@dataclass
class Thought:
    """Un pensamiento estructurado"""
    type: ThoughtType
    content: str
    confidence: float = 0.8  # 0.0 a 1.0
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "content": self.content,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "metadata": self.metadata
        }


@dataclass
class ThinkingResult:
    """Resultado del proceso de pensamiento"""
    task: str
    thoughts: List[Thought] = field(default_factory=list)
    summary: str = ""
    complexity: int = 1  # 1-5
    estimated_steps: int = 1
    key_concepts: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    approach: str = ""

    def to_dict(self) -> Dict:
        return {
            "task": self.task,
            "thoughts": [t.to_dict() for t in self.thoughts],
            "summary": self.summary,
            "complexity": self.complexity,
            "estimated_steps": self.estimated_steps,
            "key_concepts": self.key_concepts,
            "risks": self.risks,
            "approach": self.approach
        }


class Thinker:
    """
    Módulo de pensamiento del agente.

    Analiza la tarea antes de planificar, identificando:
    - Qué se está pidiendo exactamente
    - Conceptos clave involucrados
    - Posibles enfoques
    - Riesgos y restricciones
    - Complejidad estimada
    """

    THINKING_PROMPT = """Eres un asistente inteligente que analiza tareas antes de ejecutarlas.

TAREA DEL USUARIO:
{task}

CONTEXTO ADICIONAL:
{context}

Analiza esta tarea y responde en JSON con el siguiente formato:
```json
{{
  "analysis": "Análisis detallado de qué se está pidiendo",
  "key_concepts": ["concepto1", "concepto2"],
  "complexity": 1-5,
  "estimated_steps": número de pasos estimados,
  "approach": "Mejor enfoque para resolver esta tarea",
  "risks": ["riesgo1", "riesgo2"],
  "assumptions": ["suposición1", "suposición2"],
  "clarifications_needed": ["pregunta1", "pregunta2"] o [],
  "dependencies": ["dependencia1", "dependencia2"] o []
}}
```

Sé conciso pero completo. Responde SOLO con el JSON."""

    def __init__(self, llm_interface: Any, verbose: bool = True):
        """
        Args:
            llm_interface: Interfaz al LLM
            verbose: Mostrar pensamientos en consola
        """
        self.llm = llm_interface
        self.verbose = verbose

    def think(self, task: str, context: str = "") -> ThinkingResult:
        """
        Pensar sobre una tarea.

        Args:
            task: La tarea a analizar
            context: Contexto adicional

        Returns:
            ThinkingResult con análisis completo
        """
        if self.verbose:
            print("\n🧠 PENSANDO...")
            print(f"   Tarea: {task[:100]}...")

        # Construir prompt
        prompt = self.THINKING_PROMPT.format(
            task=task,
            context=context or "(Sin contexto adicional)"
        )

        # Llamar al LLM
        try:
            response = self._call_llm(prompt)
            parsed = self._parse_response(response)
        except Exception as e:
            logger.error(f"Error en pensamiento: {e}")
            parsed = self._default_analysis(task)

        # Construir resultado
        result = ThinkingResult(
            task=task,
            complexity=parsed.get("complexity", 2),
            estimated_steps=parsed.get("estimated_steps", 3),
            key_concepts=parsed.get("key_concepts", []),
            risks=parsed.get("risks", []),
            approach=parsed.get("approach", "Ejecutar directamente"),
            summary=parsed.get("analysis", "")
        )

        # Crear pensamientos estructurados
        result.thoughts = self._create_thoughts(parsed)

        if self.verbose:
            self._print_thinking(result)

        return result

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
        # Intentar extraer JSON
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Intentar parsear directamente
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Parsing heurístico
        return self._heuristic_parse(response)

    def _heuristic_parse(self, response: str) -> Dict:
        """Parsing heurístico cuando JSON falla"""
        result = {
            "analysis": response[:500],
            "key_concepts": [],
            "complexity": 2,
            "estimated_steps": 3,
            "approach": "Enfoque estándar",
            "risks": [],
            "assumptions": [],
            "clarifications_needed": [],
            "dependencies": []
        }

        # Extraer complejidad si se menciona
        complexity_match = re.search(r'complejidad[:\s]*(\d)', response.lower())
        if complexity_match:
            result["complexity"] = int(complexity_match.group(1))

        return result

    def _default_analysis(self, task: str) -> Dict:
        """Análisis por defecto cuando falla el LLM"""
        # Estimar complejidad por longitud y palabras clave
        complexity = 2
        if len(task) > 200:
            complexity = 3
        if any(kw in task.lower() for kw in ['sistema', 'arquitectura', 'implementa', 'completo']):
            complexity = 4
        if any(kw in task.lower() for kw in ['simple', 'básico', 'rápido']):
            complexity = 1

        return {
            "analysis": f"Tarea: {task}",
            "key_concepts": self._extract_concepts(task),
            "complexity": complexity,
            "estimated_steps": complexity + 1,
            "approach": "Análisis → Planificación → Ejecución → Verificación",
            "risks": ["Posibles errores de implementación"],
            "assumptions": ["El contexto es suficiente"],
            "clarifications_needed": [],
            "dependencies": []
        }

    def _extract_concepts(self, task: str) -> List[str]:
        """Extraer conceptos clave de la tarea"""
        # Palabras clave técnicas comunes
        tech_keywords = [
            'api', 'base de datos', 'cache', 'servidor', 'cliente',
            'función', 'clase', 'módulo', 'test', 'error', 'bug',
            'optimizar', 'refactorizar', 'implementar', 'crear',
            'archivo', 'código', 'python', 'javascript', 'sistema'
        ]

        concepts = []
        task_lower = task.lower()

        for kw in tech_keywords:
            if kw in task_lower:
                concepts.append(kw)

        return concepts[:5]  # Máximo 5

    def _create_thoughts(self, parsed: Dict) -> List[Thought]:
        """Crear lista de pensamientos estructurados"""
        thoughts = []

        # Pensamiento de análisis
        if parsed.get("analysis"):
            thoughts.append(Thought(
                type=ThoughtType.ANALYSIS,
                content=parsed["analysis"],
                confidence=0.9,
                reasoning="Análisis inicial de la tarea"
            ))

        # Pensamiento de enfoque
        if parsed.get("approach"):
            thoughts.append(Thought(
                type=ThoughtType.APPROACH,
                content=parsed["approach"],
                confidence=0.85,
                reasoning="Mejor estrategia identificada"
            ))

        # Pensamientos de riesgo
        for risk in parsed.get("risks", []):
            thoughts.append(Thought(
                type=ThoughtType.RISK,
                content=risk,
                confidence=0.7,
                reasoning="Riesgo potencial identificado"
            ))

        # Pensamientos de dependencia
        for dep in parsed.get("dependencies", []):
            thoughts.append(Thought(
                type=ThoughtType.DEPENDENCY,
                content=dep,
                confidence=0.8,
                reasoning="Dependencia necesaria"
            ))

        # Pensamientos de suposición
        for assumption in parsed.get("assumptions", []):
            thoughts.append(Thought(
                type=ThoughtType.ASSUMPTION,
                content=assumption,
                confidence=0.6,
                reasoning="Suposición que debe verificarse"
            ))

        # Clarificaciones necesarias
        for clarification in parsed.get("clarifications_needed", []):
            thoughts.append(Thought(
                type=ThoughtType.CLARIFICATION,
                content=clarification,
                confidence=0.5,
                reasoning="Necesita clarificación del usuario"
            ))

        return thoughts

    def _print_thinking(self, result: ThinkingResult):
        """Imprimir pensamientos en consola"""
        print(f"\n   📊 Complejidad: {result.complexity}/5")
        print(f"   📝 Pasos estimados: {result.estimated_steps}")
        print(f"   🎯 Enfoque: {result.approach[:80]}...")

        if result.key_concepts:
            print(f"   🔑 Conceptos: {', '.join(result.key_concepts[:5])}")

        if result.risks:
            print(f"   ⚠️ Riesgos: {len(result.risks)}")
            for risk in result.risks[:2]:
                print(f"      - {risk[:60]}...")

        print()


# === QUICK THINKER ===
class QuickThinker(Thinker):
    """
    Versión rápida del Thinker para tareas simples.
    No usa LLM, solo análisis heurístico.
    """

    def think(self, task: str, context: str = "") -> ThinkingResult:
        """Pensamiento rápido sin LLM"""
        parsed = self._default_analysis(task)

        result = ThinkingResult(
            task=task,
            complexity=parsed["complexity"],
            estimated_steps=parsed["estimated_steps"],
            key_concepts=parsed["key_concepts"],
            risks=parsed["risks"],
            approach=parsed["approach"],
            summary=f"Análisis rápido de: {task[:100]}"
        )

        result.thoughts = self._create_thoughts(parsed)

        if self.verbose:
            print("\n⚡ PENSAMIENTO RÁPIDO:")
            self._print_thinking(result)

        return result
