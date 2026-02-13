#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    PROMPTS - Templates de Prompts Avanzados
========================================
Sistema de IA con Agentes y RAGs

Templates para:
- Chain of Thought (CoT)
- ReAct (Reasoning + Acting)
- Planificación estructurada
- Evaluación
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class PromptStyle(Enum):
    """Estilos de prompt"""
    DIRECT = "direct"         # Respuesta directa
    COT = "cot"               # Chain of Thought
    REACT = "react"           # Reasoning + Acting
    STRUCTURED = "structured"  # Formato estructurado
    SOCRATIC = "socratic"     # Preguntas guiadas


@dataclass
class PromptTemplate:
    """Template de prompt con metadatos"""
    name: str
    style: PromptStyle
    template: str
    description: str
    expected_format: str = "text"  # text, json, steps


class PromptBuilder:
    """
    Generador de prompts avanzados.

    Soporta múltiples estilos:
    - Direct: Respuesta simple
    - CoT: Razonamiento paso a paso
    - ReAct: Thought → Action → Observation
    - Structured: Formato JSON/estructurado
    """

    # === TEMPLATES BASE ===

    # System prompts por rol
    SYSTEM_PROMPTS = {
        "assistant": """Eres un asistente de IA útil, preciso y conciso.
Respondes en el mismo idioma que la consulta.
Si no estás seguro de algo, lo indicas claramente.""",

        "expert": """Eres un experto en {domain}.
Proporcionas respuestas detalladas y precisas basadas en conocimiento especializado.
Citas fuentes cuando es posible.""",

        "teacher": """Eres un profesor paciente y claro.
Explicas conceptos de forma gradual, usando ejemplos cuando es útil.
Verificas la comprensión antes de avanzar.""",

        "analyst": """Eres un analista crítico.
Examinas información desde múltiples perspectivas.
Identificas fortalezas, debilidades y sesgos potenciales.""",

        "planner": """Eres un planificador estratégico.
Descompones problemas complejos en pasos manejables.
Consideras recursos, riesgos y alternativas.""",
    }

    # Chain of Thought template
    COT_TEMPLATE = """Piensa paso a paso para resolver esta consulta.

CONSULTA: {query}

{context_section}

Razona de forma estructurada:
1. Primero, identifica qué se está preguntando
2. Luego, analiza la información disponible
3. Desarrolla tu razonamiento paso a paso
4. Finalmente, presenta tu conclusión

RAZONAMIENTO:
"""

    # ReAct template
    REACT_TEMPLATE = """Usa el formato Thought-Action-Observation para resolver esta consulta.

CONSULTA: {query}

{context_section}

{previous_steps}

Formato a seguir:
Thought: [Tu razonamiento sobre qué hacer]
Action: [Acción a tomar: SEARCH, CALCULATE, LOOKUP, ANSWER]
Action Input: [Input para la acción]

Si tienes suficiente información, usa:
Thought: [Tu razonamiento final]
Action: ANSWER
Action Input: [Tu respuesta completa]

Continúa:
"""

    # Structured output template
    STRUCTURED_TEMPLATE = """Responde a la siguiente consulta en formato JSON estructurado.

CONSULTA: {query}

{context_section}

Tu respuesta debe seguir este formato JSON:
{{
  "answer": "respuesta principal",
  "confidence": 0.0-1.0,
  "sources": ["fuente1", "fuente2"],
  "key_points": ["punto1", "punto2"],
  "caveats": ["limitación1", "limitación2"]
}}

Responde SOLO con JSON válido:
"""

    # Planning template
    PLANNING_TEMPLATE = """Crea un plan detallado para resolver esta consulta.

CONSULTA: {query}

HERRAMIENTAS DISPONIBLES:
{tools}

{context_section}

Genera un plan con el siguiente formato JSON:
{{
  "goal": "objetivo principal",
  "complexity": 1-5,
  "steps": [
    {{
      "step": 1,
      "action": "descripción de la acción",
      "tool": "herramienta a usar",
      "expected_output": "qué se espera obtener"
    }}
  ],
  "fallback": "qué hacer si el plan falla"
}}

Plan:
"""

    # Evaluation template
    EVAL_TEMPLATE = """Evalúa la calidad de la siguiente respuesta.

CONSULTA: {query}
CONTEXTO: {context}
RESPUESTA: {response}

Criterios de evaluación:
1. PRECISIÓN (0-10): ¿Es correcta la información?
2. COMPLETITUD (0-10): ¿Responde toda la consulta?
3. CLARIDAD (0-10): ¿Es fácil de entender?
4. RELEVANCIA (0-10): ¿Se enfoca en lo preguntado?

Responde con JSON:
{{
  "scores": {{
    "precision": 0-10,
    "completitud": 0-10,
    "claridad": 0-10,
    "relevancia": 0-10
  }},
  "overall": 0-10,
  "issues": ["problema1", "problema2"],
  "verdict": "OK|PARCIAL|FALLA"
}}
"""

    @classmethod
    def chain_of_thought(
        cls,
        query: str,
        context: str = "",
        system_role: str = "assistant"
    ) -> str:
        """
        Generar prompt Chain of Thought.

        Args:
            query: Consulta del usuario
            context: Contexto RAG
            system_role: Rol del sistema

        Returns:
            Prompt completo
        """
        context_section = f"\nCONTEXTO DISPONIBLE:\n{context}\n" if context else ""

        system = cls.SYSTEM_PROMPTS.get(system_role, cls.SYSTEM_PROMPTS["assistant"])

        prompt = system + "\n\n" + cls.COT_TEMPLATE.format(
            query=query,
            context_section=context_section
        )

        return prompt

    @classmethod
    def react_prompt(
        cls,
        query: str,
        context: str = "",
        previous_steps: List[Dict] = None,
        available_actions: List[str] = None
    ) -> str:
        """
        Generar prompt ReAct.

        Args:
            query: Consulta
            context: Contexto
            previous_steps: Pasos previos del loop
            available_actions: Acciones disponibles

        Returns:
            Prompt ReAct
        """
        context_section = f"\nCONTEXTO:\n{context}\n" if context else ""

        # Formatear pasos previos
        steps_text = ""
        if previous_steps:
            for step in previous_steps:
                steps_text += f"\nThought: {step.get('thought', '')}\n"
                steps_text += f"Action: {step.get('action', '')}\n"
                steps_text += f"Action Input: {step.get('action_input', '')}\n"
                if 'observation' in step:
                    steps_text += f"Observation: {step['observation']}\n"

        prompt = cls.REACT_TEMPLATE.format(
            query=query,
            context_section=context_section,
            previous_steps=steps_text if steps_text else "Sin pasos previos."
        )

        return prompt

    @classmethod
    def structured_output(
        cls,
        query: str,
        context: str = "",
        output_schema: Dict = None
    ) -> str:
        """
        Generar prompt para output estructurado.

        Args:
            query: Consulta
            context: Contexto
            output_schema: Schema personalizado (opcional)

        Returns:
            Prompt con formato estructurado
        """
        context_section = f"\nCONTEXTO:\n{context}\n" if context else ""

        if output_schema:
            import json
            schema_str = json.dumps(output_schema, indent=2)
            template = f"""Responde a la siguiente consulta en formato JSON.

CONSULTA: {query}

{context_section}

Tu respuesta debe seguir este schema:
{schema_str}

Responde SOLO con JSON válido:
"""
            return template

        return cls.STRUCTURED_TEMPLATE.format(
            query=query,
            context_section=context_section
        )

    @classmethod
    def planning_prompt(
        cls,
        query: str,
        tools: List[str],
        context: str = ""
    ) -> str:
        """
        Generar prompt de planificación.

        Args:
            query: Consulta/tarea
            tools: Lista de herramientas disponibles
            context: Contexto

        Returns:
            Prompt de planificación
        """
        context_section = f"\nCONTEXTO:\n{context}\n" if context else ""
        tools_str = "\n".join(f"- {t}" for t in tools)

        return cls.PLANNING_TEMPLATE.format(
            query=query,
            tools=tools_str,
            context_section=context_section
        )

    @classmethod
    def evaluation_prompt(
        cls,
        query: str,
        response: str,
        context: str = ""
    ) -> str:
        """
        Generar prompt de evaluación.

        Args:
            query: Consulta original
            response: Respuesta a evaluar
            context: Contexto usado

        Returns:
            Prompt de evaluación
        """
        return cls.EVAL_TEMPLATE.format(
            query=query[:500],
            context=context[:1000] if context else "Sin contexto",
            response=response[:2000]
        )

    @classmethod
    def build_prompt(
        cls,
        style: PromptStyle,
        query: str,
        context: str = "",
        **kwargs
    ) -> str:
        """
        Construir prompt según estilo.

        Args:
            style: Estilo de prompt
            query: Consulta
            context: Contexto
            **kwargs: Argumentos adicionales

        Returns:
            Prompt construido
        """
        if style == PromptStyle.DIRECT:
            return cls._direct_prompt(query, context)
        elif style == PromptStyle.COT:
            return cls.chain_of_thought(query, context, kwargs.get('role', 'assistant'))
        elif style == PromptStyle.REACT:
            return cls.react_prompt(
                query, context,
                kwargs.get('previous_steps'),
                kwargs.get('available_actions')
            )
        elif style == PromptStyle.STRUCTURED:
            return cls.structured_output(query, context, kwargs.get('schema'))
        elif style == PromptStyle.SOCRATIC:
            return cls._socratic_prompt(query, context)
        else:
            return cls._direct_prompt(query, context)

    @classmethod
    def _direct_prompt(cls, query: str, context: str = "") -> str:
        """Prompt directo simple - máxima libertad al modelo"""
        if context:
            return f"""Información relevante:
{context}

{query}"""
        return query

    @classmethod
    def _socratic_prompt(cls, query: str, context: str = "") -> str:
        """Prompt estilo socrático (preguntas guiadas)"""
        return f"""Actúa como un profesor socrático que guía al estudiante hacia la respuesta.

Consulta del estudiante: {query}

{f"Información relevante: {context}" if context else ""}

En lugar de dar una respuesta directa:
1. Haz una pregunta que ayude a reflexionar sobre el tema
2. Guía el razonamiento con preguntas de seguimiento
3. Ayuda a llegar a la conclusión por cuenta propia

Comienza con una pregunta reflexiva:"""

    @classmethod
    def select_style(cls, query: str, complexity: int = None) -> PromptStyle:
        """
        Seleccionar estilo de prompt automáticamente.

        SIMPLIFICADO: Usar DIRECT para casi todo, solo CoT para explicaciones complejas.
        REACT solo se usa internamente por agentes, NO para consultas normales.
        """
        # Por defecto: DIRECTO (más libertad al modelo)
        # Solo usar CoT para explicaciones muy complejas explícitas
        query_lower = query.lower()

        # Solo CoT si explícitamente pide explicación detallada
        if any(kw in query_lower for kw in ['explica detalladamente', 'explain in detail', 'paso a paso', 'step by step']):
            return PromptStyle.COT

        # Default: DIRECTO - deja que el modelo responda libremente
        return PromptStyle.DIRECT


# === Helpers ===

def format_context(docs: List[str], max_chars: int = 2000) -> str:
    """Formatear lista de documentos como contexto"""
    context_parts = []
    total = 0

    for i, doc in enumerate(docs, 1):
        part = f"[Doc {i}]: {doc[:500]}"
        if total + len(part) > max_chars:
            break
        context_parts.append(part)
        total += len(part)

    return "\n\n".join(context_parts)


def extract_json_from_response(response: str) -> Optional[Dict]:
    """Extraer JSON de una respuesta de texto"""
    import re
    import json

    # Buscar bloque JSON
    json_match = re.search(r'\{[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    return None


def parse_react_response(response: str) -> Dict:
    """Parsear respuesta en formato ReAct"""
    result = {
        "thought": "",
        "action": "",
        "action_input": ""
    }

    # Buscar Thought
    thought_match = re.search(r'Thought:\s*(.+?)(?=Action:|$)', response, re.DOTALL | re.IGNORECASE)
    if thought_match:
        result["thought"] = thought_match.group(1).strip()

    # Buscar Action
    action_match = re.search(r'Action:\s*(\w+)', response, re.IGNORECASE)
    if action_match:
        result["action"] = action_match.group(1).strip().upper()

    # Buscar Action Input
    input_match = re.search(r'Action Input:\s*(.+?)(?=Thought:|Action:|$)', response, re.DOTALL | re.IGNORECASE)
    if input_match:
        result["action_input"] = input_match.group(1).strip()

    return result


# === CLI para pruebas ===
if __name__ == "__main__":
    print("=== Test Prompt Builder ===\n")

    query = "¿Por qué el cielo es azul?"
    context = "La luz del sol contiene todos los colores. La atmósfera dispersa más la luz azul."

    print("1. Direct Prompt:")
    print(PromptBuilder.build_prompt(PromptStyle.DIRECT, query, context)[:200])
    print()

    print("2. Chain of Thought:")
    print(PromptBuilder.chain_of_thought(query, context)[:300])
    print()

    print("3. ReAct Prompt:")
    print(PromptBuilder.react_prompt(query, context)[:300])
    print()

    print("4. Planning Prompt:")
    tools = ["SEARCH", "CALCULATE", "LOOKUP"]
    print(PromptBuilder.planning_prompt("Buscar información sobre Python", tools)[:300])
    print()

    print("5. Auto-select style:")
    test_queries = [
        "¿Qué es Python?",
        "Explica detalladamente cómo funciona TCP/IP",
        "Busca información sobre machine learning",
        "¿Qué opinas sobre la IA?",
    ]
    for q in test_queries:
        style = PromptBuilder.select_style(q)
        print(f"   '{q[:40]}...' → {style.value}")
