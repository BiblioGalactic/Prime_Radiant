#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    QUERY REFINER - Refinamiento de Consultas
========================================
Sistema de IA con Agentes y RAGs

Refina y expande consultas para mejorar la recuperación RAG:
- Reformulación basada en contexto
- Expansión con sinónimos y términos relacionados
- Descomposición de consultas complejas
"""

import os
import sys
import re
import subprocess
import json
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("QueryRefiner")


@dataclass
class RefinedQuery:
    """Resultado de refinamiento de query"""
    original: str
    refined: str
    expansions: List[str]  # Queries expandidas/alternativas
    keywords: List[str]     # Palabras clave extraídas
    strategy_used: str      # Estrategia aplicada
    confidence: float       # Confianza en el refinamiento


class QueryRefiner:
    """
    Refinador de consultas para mejorar recuperación RAG.

    Estrategias:
    1. Reformulación: Reescribe la query para mayor claridad
    2. Expansión: Genera variantes con sinónimos
    3. Descomposición: Divide queries complejas en sub-queries
    4. Contextual: Refina basándose en documentos recuperados
    """

    # Prompt para refinamiento con LLM
    REFINE_PROMPT = """Eres un experto en reformular consultas de búsqueda.

Tu tarea es mejorar la siguiente consulta para obtener mejores resultados de búsqueda.

CONSULTA ORIGINAL: {query}

CONTEXTO DISPONIBLE (documentos recuperados):
{context}

Genera una versión mejorada de la consulta que:
1. Sea más específica y clara
2. Use términos que probablemente aparezcan en los documentos
3. Mantenga la intención original

Responde SOLO con JSON:
{{
  "refined_query": "la consulta mejorada",
  "keywords": ["palabra1", "palabra2", "palabra3"],
  "reasoning": "breve explicación"
}}"""

    EXPAND_PROMPT = """Genera 3 variantes de la siguiente consulta de búsqueda.
Cada variante debe buscar la misma información pero con diferentes palabras.

CONSULTA: {query}

Responde SOLO con JSON:
{{
  "variants": [
    "variante 1",
    "variante 2",
    "variante 3"
  ]
}}"""

    # Sinónimos comunes para expansión sin LLM
    SYNONYM_MAP = {
        # Español
        "qué es": ["definición de", "concepto de", "significado de"],
        "cómo": ["de qué manera", "proceso para", "pasos para"],
        "por qué": ["razón de", "causa de", "motivo de"],
        "cuándo": ["fecha de", "momento de", "época de"],
        "quién": ["persona que", "autor de", "creador de"],
        "dónde": ["lugar de", "ubicación de", "sitio de"],
        "historia": ["origen", "evolución", "desarrollo"],
        "mejor": ["óptimo", "más efectivo", "recomendado"],
        "problema": ["error", "falla", "issue", "bug"],
        # English
        "what is": ["definition of", "meaning of", "concept of"],
        "how to": ["steps to", "process for", "way to"],
        "why": ["reason for", "cause of", "explanation for"],
        "best": ["optimal", "recommended", "top"],
        "problem": ["issue", "error", "bug", "failure"],
    }

    def __init__(self, use_llm: bool = True):
        """
        Inicializar refinador.

        Args:
            use_llm: Si usar LLM para refinamiento avanzado
        """
        self.use_llm = use_llm
        self.llama_cli = config.LLAMA_CLI
        self.model = config.MODEL_FAST  # Modelo rápido para refinamiento

    def refine(
        self,
        query: str,
        context_docs: List[str] = None,
        strategy: str = "auto"
    ) -> RefinedQuery:
        """
        Refinar una consulta.

        Args:
            query: Consulta original
            context_docs: Documentos de contexto (opcional)
            strategy: "auto", "expand", "decompose", "contextual"

        Returns:
            RefinedQuery con la consulta mejorada
        """
        # Seleccionar estrategia automáticamente si es "auto"
        if strategy == "auto":
            strategy = self._select_strategy(query, context_docs)

        logger.info(f"[QueryRefiner] Estrategia: {strategy}")

        if strategy == "expand":
            return self._expand_query(query)
        elif strategy == "decompose":
            return self._decompose_query(query)
        elif strategy == "contextual" and context_docs:
            return self._contextual_refine(query, context_docs)
        else:
            # Default: expansión simple
            return self._expand_query(query)

    def _select_strategy(self, query: str, context_docs: List[str] = None) -> str:
        """Seleccionar estrategia óptima"""
        query_lower = query.lower()

        # Query muy larga o con múltiples preguntas → descomponer
        if len(query) > 200 or query.count('?') > 1:
            return "decompose"

        # Hay contexto disponible → refinamiento contextual
        if context_docs and len(context_docs) > 0:
            return "contextual"

        # Default → expansión
        return "expand"

    def expand(self, query: str) -> List[str]:
        """
        Generar variantes expandidas de la query.

        Args:
            query: Consulta original

        Returns:
            Lista de queries alternativas
        """
        result = self._expand_query(query)
        return [result.refined] + result.expansions

    def _expand_query(self, query: str) -> RefinedQuery:
        """Expandir query con sinónimos y variantes"""
        expansions = []
        keywords = self._extract_keywords(query)

        # 1. Expansión con sinónimos locales
        query_lower = query.lower()
        for phrase, synonyms in self.SYNONYM_MAP.items():
            if phrase in query_lower:
                for syn in synonyms[:2]:  # Max 2 variantes por frase
                    expanded = query_lower.replace(phrase, syn)
                    if expanded not in expansions:
                        expansions.append(expanded)

        # 2. Expansión con keywords
        if keywords:
            keyword_query = " ".join(keywords)
            if keyword_query != query.lower() and keyword_query not in expansions:
                expansions.append(keyword_query)

        # 3. Si hay LLM disponible, generar más variantes
        if self.use_llm and len(expansions) < 3:
            try:
                llm_expansions = self._llm_expand(query)
                for exp in llm_expansions:
                    if exp not in expansions:
                        expansions.append(exp)
            except Exception as e:
                logger.warning(f"[QueryRefiner] LLM expansion failed: {e}")

        # Refined = primera expansión o original si no hay
        refined = expansions[0] if expansions else query

        return RefinedQuery(
            original=query,
            refined=refined,
            expansions=expansions[:5],  # Max 5 expansiones
            keywords=keywords,
            strategy_used="expand",
            confidence=0.7 if expansions else 0.5
        )

    def _decompose_query(self, query: str) -> RefinedQuery:
        """Descomponer query compleja en sub-queries"""
        sub_queries = []

        # 1. Dividir por conectores
        connectors = [' y ', ' e ', ' and ', ' además ', ' también ',
                     ' pero ', ' pero también ', ' o ', ' or ']

        parts = [query]
        for conn in connectors:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(conn))
            parts = new_parts

        # Limpiar y filtrar partes muy cortas
        sub_queries = [p.strip() for p in parts if len(p.strip()) > 10]

        # 2. Si hay múltiples preguntas (?)
        if query.count('?') > 1:
            questions = [q.strip() + '?' for q in query.split('?') if q.strip()]
            sub_queries.extend(questions)

        # Eliminar duplicados manteniendo orden
        seen = set()
        unique_subs = []
        for sq in sub_queries:
            if sq.lower() not in seen:
                seen.add(sq.lower())
                unique_subs.append(sq)

        keywords = self._extract_keywords(query)

        return RefinedQuery(
            original=query,
            refined=unique_subs[0] if unique_subs else query,
            expansions=unique_subs[1:] if len(unique_subs) > 1 else [],
            keywords=keywords,
            strategy_used="decompose",
            confidence=0.8 if len(unique_subs) > 1 else 0.5
        )

    def _contextual_refine(self, query: str, context_docs: List[str]) -> RefinedQuery:
        """Refinar query basándose en documentos recuperados"""
        # Extraer términos frecuentes del contexto
        context_text = " ".join(context_docs[:3])  # Top 3 docs
        context_words = re.findall(r'\b\w{4,}\b', context_text.lower())

        # Contar frecuencias
        word_freq = {}
        for w in context_words:
            word_freq[w] = word_freq.get(w, 0) + 1

        # Top palabras del contexto que no están en la query
        query_words = set(query.lower().split())
        context_terms = [
            w for w, _ in sorted(word_freq.items(), key=lambda x: -x[1])
            if w not in query_words and len(w) > 4
        ][:5]

        # Construir query refinada
        if context_terms:
            refined = f"{query} {' '.join(context_terms[:3])}"
        else:
            refined = query

        # Si hay LLM, hacer refinamiento más sofisticado
        if self.use_llm:
            try:
                llm_result = self._llm_refine(query, context_text[:1000])
                if llm_result:
                    refined = llm_result.get("refined_query", refined)
                    context_terms = llm_result.get("keywords", context_terms)
            except Exception as e:
                logger.warning(f"[QueryRefiner] LLM refine failed: {e}")

        return RefinedQuery(
            original=query,
            refined=refined,
            expansions=[],  # Contextual no genera expansiones
            keywords=context_terms,
            strategy_used="contextual",
            confidence=0.75
        )

    def _extract_keywords(self, query: str) -> List[str]:
        """Extraer palabras clave de una query"""
        # Stopwords
        stopwords = {
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
            'de', 'del', 'al', 'a', 'en', 'por', 'para', 'con', 'sin',
            'que', 'qué', 'como', 'cómo', 'es', 'son', 'fue', 'ser',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'of', 'to', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
            'and', 'or', 'but', 'if', 'then', 'so', 'than', 'this', 'that'
        }

        # Extraer palabras
        words = re.findall(r'\b\w{3,}\b', query.lower())
        keywords = [w for w in words if w not in stopwords]

        return keywords[:10]  # Max 10 keywords

    def _llm_expand(self, query: str) -> List[str]:
        """Generar expansiones con LLM"""
        prompt = self.EXPAND_PROMPT.format(query=query)
        result = self._call_llm(prompt)

        try:
            data = json.loads(result)
            return data.get("variants", [])
        except:
            return []

    def _llm_refine(self, query: str, context: str) -> Optional[Dict]:
        """Refinar con LLM usando contexto"""
        prompt = self.REFINE_PROMPT.format(query=query, context=context[:1000])
        result = self._call_llm(prompt)

        try:
            # Buscar JSON en la respuesta
            json_match = re.search(r'\{[^{}]*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return None

    def _call_llm(self, prompt: str) -> str:
        """Llamar al LLM"""
        cmd = [
            self.llama_cli,
            "-m", self.model.path,
            "-c", str(2048),
            "-t", str(4),
            "-n", str(200),
            "--temp", "0.3",
            "-p", prompt,
            "--no-display-prompt"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30,
                stdin=subprocess.DEVNULL
            )

            # Decodificar
            output = result.stdout
            try:
                return output.decode('utf-8')
            except:
                return output.decode('latin-1', errors='replace')

        except subprocess.TimeoutExpired:
            logger.warning("[QueryRefiner] LLM timeout")
            return ""
        except Exception as e:
            logger.error(f"[QueryRefiner] LLM error: {e}")
            return ""


# === Factory ===
_refiner: Optional[QueryRefiner] = None


def get_refiner(use_llm: bool = True) -> QueryRefiner:
    """Obtener instancia singleton del refiner"""
    global _refiner
    if _refiner is None:
        _refiner = QueryRefiner(use_llm=use_llm)
    return _refiner


# === CLI para pruebas ===
if __name__ == "__main__":
    print("=== Test Query Refiner ===\n")

    refiner = QueryRefiner(use_llm=False)  # Sin LLM para test rápido

    test_queries = [
        "¿Qué es Python?",
        "Cómo instalar Docker en Ubuntu y configurar contenedores",
        "Historia de España y sus reyes más importantes",
        "Best practices for React performance optimization",
        "¿Por qué el cielo es azul? ¿Y por qué el mar también?",
    ]

    for query in test_queries:
        print(f"📝 Original: {query}")
        result = refiner.refine(query)
        print(f"   ✨ Refined: {result.refined}")
        print(f"   🔑 Keywords: {result.keywords}")
        print(f"   📊 Strategy: {result.strategy_used}")
        if result.expansions:
            print(f"   📋 Expansions: {result.expansions[:2]}")
        print()
