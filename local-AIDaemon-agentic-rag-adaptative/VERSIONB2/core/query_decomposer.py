#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    QUERY DECOMPOSER - Descomposición Multi-paso
========================================
Sistema avanzado de descomposición de queries complejas.
Divide preguntas complejas en sub-preguntas más simples
que pueden ser respondidas secuencialmente.
========================================
"""

import os
import sys
import re
import json
import subprocess
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("QueryDecomposer")


class QueryType(Enum):
    """Tipos de query"""
    SIMPLE = "simple"           # Pregunta directa
    COMPARISON = "comparison"   # Comparación entre items
    MULTI_HOP = "multi_hop"     # Requiere razonamiento multi-paso
    AGGREGATION = "aggregation" # Requiere agregar información
    TEMPORAL = "temporal"       # Preguntas sobre tiempo/secuencia
    CAUSAL = "causal"           # Preguntas de causa-efecto


@dataclass
class SubQuery:
    """Sub-query descompuesta"""
    query: str
    order: int                  # Orden de ejecución
    depends_on: List[int]       # IDs de sub-queries de las que depende
    query_type: QueryType
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecomposedQuery:
    """Resultado de descomposición"""
    original: str
    sub_queries: List[SubQuery]
    query_type: QueryType
    is_decomposable: bool
    reasoning: str
    aggregation_strategy: str = "synthesize"  # synthesize, list, compare


class QueryDecomposer:
    """
    Descompositor avanzado de queries.

    Estrategias:
    1. Detección de tipo de query
    2. Descomposición basada en patrones
    3. Descomposición con LLM
    4. Ordenamiento de dependencias
    """

    # Patrones para detectar tipo de query
    COMPARISON_PATTERNS = [
        r'\b(vs\.?|versus|comparar?|diferencia|entre)\b',
        r'\b(mejor|peor|más|menos)\b.*\b(que|vs)\b',
        r'\b(similitud|parecido|distintos?)\b',
    ]

    MULTI_HOP_PATTERNS = [
        r'\b(quién|qué|cuál|dónde)\b.*\b(y|además|también)\b.*\b(quién|qué|cuál)\b',
        r'\b(por qué|cómo)\b.*\b(y|además)\b.*\b(qué|cuál)\b',
    ]

    TEMPORAL_PATTERNS = [
        r'\b(primero|luego|después|antes|cuando|mientras)\b',
        r'\b(historia|evolución|desarrollo|cambio)\b',
        r'\b(cronología|secuencia|orden)\b',
    ]

    CAUSAL_PATTERNS = [
        r'\b(por qué|causa|razón|motivo|consecuencia)\b',
        r'\b(debido a|gracias a|a causa de)\b',
        r'\b(efecto|resultado|impacto)\b',
    ]

    AGGREGATION_PATTERNS = [
        r'\b(todos?|cada|lista|enumera|cuántos)\b',
        r'\b(ejemplos?|casos?|tipos?)\b',
        r'\b(principales?|más importantes?)\b',
    ]

    DECOMPOSE_PROMPT = """Eres un experto en descomponer preguntas complejas.

PREGUNTA ORIGINAL: {query}

Tu tarea es descomponer esta pregunta en sub-preguntas más simples que se puedan responder secuencialmente.

Reglas:
1. Cada sub-pregunta debe ser auto-contenida
2. El orden debe permitir construir la respuesta final
3. Si una sub-pregunta depende de otra, indícalo

Responde SOLO con JSON:
{{
  "query_type": "simple|comparison|multi_hop|aggregation|temporal|causal",
  "is_decomposable": true/false,
  "sub_queries": [
    {{
      "query": "primera sub-pregunta",
      "order": 1,
      "depends_on": []
    }},
    {{
      "query": "segunda sub-pregunta",
      "order": 2,
      "depends_on": [1]
    }}
  ],
  "aggregation_strategy": "synthesize|list|compare",
  "reasoning": "explicación breve"
}}"""

    def __init__(self, use_llm: bool = True):
        """
        Args:
            use_llm: Si usar LLM para descomposición avanzada
        """
        self.use_llm = use_llm
        self.llama_cli = config.LLAMA_CLI
        self.model = config.MODEL_FAST

    def detect_query_type(self, query: str) -> QueryType:
        """Detectar tipo de query basado en patrones"""
        query_lower = query.lower()

        # Verificar patrones en orden de especificidad
        for pattern in self.COMPARISON_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return QueryType.COMPARISON

        for pattern in self.MULTI_HOP_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return QueryType.MULTI_HOP

        for pattern in self.TEMPORAL_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return QueryType.TEMPORAL

        for pattern in self.CAUSAL_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return QueryType.CAUSAL

        for pattern in self.AGGREGATION_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return QueryType.AGGREGATION

        return QueryType.SIMPLE

    def should_decompose(self, query: str) -> bool:
        """Determinar si una query debe ser descompuesta"""
        # Longitud significativa
        if len(query) > 100:
            return True

        # Múltiples signos de pregunta
        if query.count('?') > 1:
            return True

        # Conectores que sugieren complejidad
        connectors = [' y ', ' además ', ' también ', ' pero ', ' sin embargo ',
                     ' and ', ' also ', ' but ', ' however ']
        if any(c in query.lower() for c in connectors):
            query_type = self.detect_query_type(query)
            if query_type != QueryType.SIMPLE:
                return True

        # Tipo de query complejo
        query_type = self.detect_query_type(query)
        return query_type in [QueryType.COMPARISON, QueryType.MULTI_HOP,
                             QueryType.TEMPORAL, QueryType.CAUSAL]

    def decompose(self, query: str) -> DecomposedQuery:
        """
        Descomponer una query compleja.

        Args:
            query: Query original

        Returns:
            DecomposedQuery con sub-queries
        """
        query_type = self.detect_query_type(query)

        # Si es simple, no descomponer
        if not self.should_decompose(query):
            return DecomposedQuery(
                original=query,
                sub_queries=[SubQuery(
                    query=query,
                    order=1,
                    depends_on=[],
                    query_type=query_type
                )],
                query_type=query_type,
                is_decomposable=False,
                reasoning="Query simple, no requiere descomposición"
            )

        # Intentar descomposición con LLM
        if self.use_llm:
            try:
                result = self._decompose_with_llm(query)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"LLM decomposition failed: {e}")

        # Fallback: descomposición basada en reglas
        return self._decompose_rules_based(query, query_type)

    def _decompose_rules_based(self, query: str, query_type: QueryType) -> DecomposedQuery:
        """Descomposición basada en reglas/patrones"""
        sub_queries = []

        if query_type == QueryType.COMPARISON:
            # Extraer items a comparar
            items = self._extract_comparison_items(query)
            if len(items) >= 2:
                # Sub-query por cada item
                for i, item in enumerate(items):
                    sub_queries.append(SubQuery(
                        query=f"¿Qué es {item}? Características principales.",
                        order=i + 1,
                        depends_on=[],
                        query_type=QueryType.SIMPLE
                    ))
                # Sub-query de comparación final
                sub_queries.append(SubQuery(
                    query=f"Comparación entre {' y '.join(items)}",
                    order=len(items) + 1,
                    depends_on=list(range(1, len(items) + 1)),
                    query_type=QueryType.COMPARISON
                ))
                strategy = "compare"
            else:
                sub_queries.append(SubQuery(
                    query=query, order=1, depends_on=[],
                    query_type=query_type
                ))
                strategy = "synthesize"

        elif query_type == QueryType.MULTI_HOP:
            # Dividir en partes por conectores
            parts = self._split_by_connectors(query)
            for i, part in enumerate(parts):
                sub_queries.append(SubQuery(
                    query=part.strip(),
                    order=i + 1,
                    depends_on=list(range(1, i + 1)) if i > 0 else [],
                    query_type=QueryType.SIMPLE
                ))
            strategy = "synthesize"

        elif query_type == QueryType.TEMPORAL:
            # Preguntas temporales: primero contexto, luego secuencia
            sub_queries.append(SubQuery(
                query=f"Contexto general: {query}",
                order=1,
                depends_on=[],
                query_type=QueryType.SIMPLE
            ))
            sub_queries.append(SubQuery(
                query=f"Secuencia cronológica relacionada con: {query}",
                order=2,
                depends_on=[1],
                query_type=QueryType.TEMPORAL
            ))
            strategy = "list"

        elif query_type == QueryType.CAUSAL:
            # Causa → Efecto
            sub_queries.append(SubQuery(
                query=f"¿Cuál es la causa principal de {self._extract_topic(query)}?",
                order=1,
                depends_on=[],
                query_type=QueryType.SIMPLE
            ))
            sub_queries.append(SubQuery(
                query=f"¿Cuáles son los efectos o consecuencias?",
                order=2,
                depends_on=[1],
                query_type=QueryType.SIMPLE
            ))
            strategy = "synthesize"

        elif query_type == QueryType.AGGREGATION:
            # Lista/enumeración
            sub_queries.append(SubQuery(
                query=query,
                order=1,
                depends_on=[],
                query_type=QueryType.AGGREGATION
            ))
            strategy = "list"

        else:
            # Default: múltiples preguntas por '?'
            questions = [q.strip() + '?' for q in query.split('?') if q.strip()]
            for i, q in enumerate(questions):
                sub_queries.append(SubQuery(
                    query=q,
                    order=i + 1,
                    depends_on=[],
                    query_type=QueryType.SIMPLE
                ))
            strategy = "synthesize"

        return DecomposedQuery(
            original=query,
            sub_queries=sub_queries if sub_queries else [
                SubQuery(query=query, order=1, depends_on=[], query_type=query_type)
            ],
            query_type=query_type,
            is_decomposable=len(sub_queries) > 1,
            reasoning=f"Descomposición basada en reglas para tipo {query_type.value}",
            aggregation_strategy=strategy
        )

    def _decompose_with_llm(self, query: str) -> Optional[DecomposedQuery]:
        """Descomponer usando LLM"""
        prompt = self.DECOMPOSE_PROMPT.format(query=query)
        result = self._call_llm(prompt)

        try:
            # Buscar JSON en la respuesta
            json_match = re.search(r'\{[\s\S]*\}', result)
            if not json_match:
                return None

            data = json.loads(json_match.group())

            # Parsear tipo de query
            type_str = data.get("query_type", "simple").lower()
            try:
                query_type = QueryType(type_str)
            except ValueError:
                query_type = QueryType.SIMPLE

            # Parsear sub-queries
            sub_queries = []
            for sq in data.get("sub_queries", []):
                sub_queries.append(SubQuery(
                    query=sq.get("query", ""),
                    order=sq.get("order", 1),
                    depends_on=sq.get("depends_on", []),
                    query_type=QueryType.SIMPLE
                ))

            if not sub_queries:
                return None

            return DecomposedQuery(
                original=query,
                sub_queries=sub_queries,
                query_type=query_type,
                is_decomposable=data.get("is_decomposable", len(sub_queries) > 1),
                reasoning=data.get("reasoning", "Descomposición LLM"),
                aggregation_strategy=data.get("aggregation_strategy", "synthesize")
            )

        except json.JSONDecodeError:
            return None
        except Exception as e:
            logger.warning(f"Error parsing LLM decomposition: {e}")
            return None

    def _extract_comparison_items(self, query: str) -> List[str]:
        """Extraer items a comparar de una query"""
        # Patrones comunes de comparación
        patterns = [
            r'(\w+)\s+vs\.?\s+(\w+)',
            r'(\w+)\s+versus\s+(\w+)',
            r'diferencia\s+entre\s+(\w+)\s+y\s+(\w+)',
            r'comparar\s+(\w+)\s+(?:con|y)\s+(\w+)',
            r'(\w+)\s+o\s+(\w+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return list(match.groups())

        return []

    def _split_by_connectors(self, query: str) -> List[str]:
        """Dividir query por conectores"""
        connectors = [' y además ', ' además ', ' también ', ' y también ',
                     ' pero ', ' sin embargo ', ' and ', ' but ']

        parts = [query]
        for conn in connectors:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(conn))
            parts = new_parts

        return [p.strip() for p in parts if p.strip() and len(p.strip()) > 5]

    def _extract_topic(self, query: str) -> str:
        """Extraer tema principal de la query"""
        # Remover palabras interrogativas y artículos
        words_to_remove = [
            'por qué', 'cómo', 'qué', 'cuál', 'quién', 'cuándo', 'dónde',
            'el', 'la', 'los', 'las', 'un', 'una', 'es', 'son', 'fue'
        ]

        topic = query.lower()
        topic = re.sub(r'[¿?]', '', topic)

        for word in words_to_remove:
            topic = topic.replace(word, '')

        return topic.strip()[:50]

    def _call_llm(self, prompt: str) -> str:
        """Llamar al LLM"""
        cmd = [
            self.llama_cli,
            "-m", self.model.path,
            "-c", str(2048),
            "-t", str(4),
            "-n", str(500),
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
            return ""
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return ""


def execute_decomposed_query(
    decomposed: DecomposedQuery,
    query_fn: callable,
    synthesize_fn: callable = None
) -> Dict[str, Any]:
    """
    Ejecutar una query descompuesta.

    Args:
        decomposed: Query descompuesta
        query_fn: Función para ejecutar cada sub-query
        synthesize_fn: Función para sintetizar resultados

    Returns:
        Dict con resultados
    """
    results = {}
    sub_results = []

    # Ordenar sub-queries
    sorted_subs = sorted(decomposed.sub_queries, key=lambda x: x.order)

    for sub in sorted_subs:
        # Verificar dependencias
        deps_satisfied = all(d in results for d in sub.depends_on)
        if not deps_satisfied:
            logger.warning(f"Dependencies not satisfied for: {sub.query[:30]}")
            continue

        # Ejecutar sub-query
        logger.info(f"[Decomposer] Ejecutando sub-query {sub.order}: {sub.query[:40]}...")

        # Incluir contexto de dependencias
        context = ""
        if sub.depends_on:
            dep_results = [results[d] for d in sub.depends_on]
            context = "\n".join([f"[Contexto previo]: {r}" for r in dep_results])

        query_with_context = f"{context}\n\n{sub.query}" if context else sub.query
        result = query_fn(query_with_context)

        results[sub.order] = result
        sub_results.append({
            "order": sub.order,
            "query": sub.query,
            "result": result
        })

    # Sintetizar si hay función de síntesis
    final_response = ""
    if synthesize_fn and len(sub_results) > 1:
        final_response = synthesize_fn(
            decomposed.original,
            sub_results,
            decomposed.aggregation_strategy
        )
    elif sub_results:
        # Simple concatenación
        final_response = "\n\n".join([r["result"] for r in sub_results])

    return {
        "original_query": decomposed.original,
        "sub_results": sub_results,
        "final_response": final_response,
        "strategy": decomposed.aggregation_strategy,
        "total_sub_queries": len(sub_results)
    }


# === SINGLETON ===
_decomposer: Optional[QueryDecomposer] = None


def get_decomposer(use_llm: bool = True) -> QueryDecomposer:
    """Obtener instancia singleton"""
    global _decomposer
    if _decomposer is None:
        _decomposer = QueryDecomposer(use_llm=use_llm)
    return _decomposer


# === CLI para pruebas ===
if __name__ == "__main__":
    print("=== Test Query Decomposer ===\n")

    decomposer = QueryDecomposer(use_llm=False)  # Sin LLM para test rápido

    test_queries = [
        "¿Qué es Python?",
        "¿Cuál es la diferencia entre Python y JavaScript?",
        "¿Cómo funciona la fotosíntesis y por qué es importante para el planeta?",
        "Historia de España: ¿Cuáles fueron los eventos más importantes? ¿Quiénes fueron los reyes más influyentes?",
        "Compara React vs Vue vs Angular para desarrollo web",
        "¿Por qué se extinguieron los dinosaurios y qué consecuencias tuvo?",
    ]

    for query in test_queries:
        print(f"📝 Query: {query}")
        result = decomposer.decompose(query)
        print(f"   Tipo: {result.query_type.value}")
        print(f"   Descomponible: {result.is_decomposable}")
        print(f"   Estrategia: {result.aggregation_strategy}")
        print(f"   Sub-queries ({len(result.sub_queries)}):")
        for sq in result.sub_queries:
            deps = f" (depende de: {sq.depends_on})" if sq.depends_on else ""
            print(f"      {sq.order}. {sq.query[:60]}...{deps}")
        print()
