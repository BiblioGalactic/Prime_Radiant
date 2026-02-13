#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
🎯 TOOL DECIDER - El Capataz que Decide
========================================
Este módulo es el "dictador" que decide EXACTAMENTE qué herramienta
usar ANTES de que el agente empiece a divagar.

El flujo es:
1. IntentClassifier detecta intención + extrae entidades
2. ToolDecider decide la herramienta EXACTA y parámetros
3. El agente recibe una ORDEN DIRECTA, no una pregunta

Esto evita que modelos pequeños (8B) se pierdan "pensando".
========================================
"""

import os
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

from .intent_classifier import (
    ClassificationResult, Intent, ActionType
)

logger = logging.getLogger("ToolDecider")


@dataclass
class DirectOrder:
    """
    Orden directa para el agente.
    El agente NO piensa, solo EJECUTA.
    """
    # Herramienta a usar
    tool: str  # filesystem_read, filesystem_list, rag_search, etc.
    marker: str  # [[leer ~/path]], [[listar .]], etc.

    # Parámetros ya resueltos
    params: Dict[str, Any]

    # Mensaje pre-construido para el agente
    agent_prompt: str

    # Metadata
    action_type: ActionType
    confidence: float
    can_execute_directly: bool = True  # Si True, no necesita agente
    fallback_to_agent: bool = False  # Si True, dejar que agente decida

    def to_dict(self) -> Dict:
        return {
            "tool": self.tool,
            "marker": self.marker,
            "params": self.params,
            "agent_prompt": self.agent_prompt[:200],
            "action_type": self.action_type.value,
            "confidence": self.confidence,
            "can_execute_directly": self.can_execute_directly
        }


class ToolDecider:
    """
    El Capataz: Decide la herramienta exacta basándose en la clasificación.

    Reglas:
    1. Si hay path explícito → usar ese path
    2. Si no hay path → usar PWD
    3. Si la acción es clara → ejecutar directamente (sin agente)
    4. Si hay ambigüedad → dar orden específica al agente
    """

    # Mapeo de acciones a herramientas por defecto
    DEFAULT_TOOLS = {
        ActionType.FILESYSTEM: {
            "listar": ("filesystem_list", "[[listar {path}]]"),
            "leer": ("filesystem_read", "[[leer {path}]]"),
            "buscar": ("grep_search", "[[buscar {pattern} en {path}]]"),
            "crear": ("filesystem_write", "[[escribir {path}]]"),
            "eliminar": None,  # Peligroso, no auto-ejecutar
        },
        ActionType.GIT: {
            "status": ("git_status", "[[git estado]]"),
            "log": ("git_log", "[[git log]]"),
            "diff": ("git_diff", "[[git diff]]"),
        },
    }

    # Patrones para detectar sub-acción
    ACTION_SUBPATTERNS = {
        "listar": [r"lista", r"listar", r"muestra.*archivos", r"qué hay", r"ls\b", r"dir\b"],
        "leer": [r"lee", r"leer", r"muestra.*contenido", r"abre", r"cat\b", r"ver archivo"],
        "buscar": [r"busca", r"encuentra", r"grep", r"dónde", r"localiza"],
        "crear": [r"crea", r"escribe", r"guarda", r"nuevo archivo"],
        "eliminar": [r"elimina", r"borra", r"delete", r"rm\b"],
        "status": [r"status", r"estado"],
        "log": [r"log", r"historial", r"commits"],
        "diff": [r"diff", r"cambios", r"diferencias"],
    }

    def __init__(self, default_pwd: str = None):
        """
        Args:
            default_pwd: Directorio de trabajo por defecto
        """
        self.pwd = default_pwd or os.getcwd()
        self._compile_patterns()

    def _compile_patterns(self):
        """Compilar patrones de sub-acciones"""
        self._compiled = {}
        for action, patterns in self.ACTION_SUBPATTERNS.items():
            self._compiled[action] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def decide(self, classification: ClassificationResult) -> DirectOrder:
        """
        Decidir la herramienta exacta para una clasificación.

        Args:
            classification: Resultado del IntentClassifier

        Returns:
            DirectOrder con la herramienta y parámetros decididos
        """
        query = classification.query.lower()
        entities = classification.entities
        action_type = classification.action_type

        # Extraer path de las entidades o usar PWD
        paths = entities.get("paths", [])
        path = paths[0] if paths else self.pwd

        # Expandir ~ si es necesario
        if path.startswith("~"):
            path = os.path.expanduser(path)

        # Determinar sub-acción
        sub_action = self._detect_sub_action(query, action_type)

        # Decidir herramienta según tipo de acción
        if action_type == ActionType.FILESYSTEM:
            return self._decide_filesystem(query, path, sub_action, entities, classification)

        elif action_type == ActionType.GIT:
            return self._decide_git(query, path, sub_action, classification)

        elif action_type == ActionType.CLAUDIA:
            return self._decide_claudia(query, path, entities, classification)

        elif action_type == ActionType.SEARCH:
            return self._decide_search(query, entities, classification)

        else:
            # Fallback: dejar que el agente decida pero con contexto
            return self._create_agent_fallback(classification, path)

    def _detect_sub_action(self, query: str, action_type: ActionType) -> str:
        """Detectar la sub-acción específica"""
        for action, patterns in self._compiled.items():
            for pattern in patterns:
                if pattern.search(query):
                    return action
        return "unknown"

    def _decide_filesystem(
        self,
        query: str,
        path: str,
        sub_action: str,
        entities: Dict,
        classification: ClassificationResult
    ) -> DirectOrder:
        """Decidir herramienta de filesystem"""

        if sub_action == "listar":
            return DirectOrder(
                tool="filesystem_list",
                marker=f"[[listar {path}]]",
                params={"path": path},
                agent_prompt=f"EJECUTA: [[listar {path}]]",
                action_type=ActionType.FILESYSTEM,
                confidence=0.95,
                can_execute_directly=True
            )

        elif sub_action == "leer":
            # Si no hay archivo específico, no podemos ejecutar directamente
            if not entities.get("paths"):
                return DirectOrder(
                    tool="filesystem_read",
                    marker="[[leer ???]]",
                    params={"path": path},
                    agent_prompt=f"El usuario quiere leer un archivo pero no especificó cuál. "
                                f"Primero usa [[listar {self.pwd}]] para ver qué hay, "
                                f"luego pregunta cuál archivo leer.",
                    action_type=ActionType.FILESYSTEM,
                    confidence=0.6,
                    can_execute_directly=False,
                    fallback_to_agent=True
                )
            return DirectOrder(
                tool="filesystem_read",
                marker=f"[[leer {path}]]",
                params={"path": path},
                agent_prompt=f"EJECUTA: [[leer {path}]]",
                action_type=ActionType.FILESYSTEM,
                confidence=0.95,
                can_execute_directly=True
            )

        elif sub_action == "buscar":
            # Extraer patrón de búsqueda
            pattern = self._extract_search_pattern(query)
            if pattern:
                return DirectOrder(
                    tool="grep_search",
                    marker=f"[[buscar {pattern} en {path}]]",
                    params={"pattern": pattern, "path": path},
                    agent_prompt=f"EJECUTA: [[buscar {pattern} en {path}]]",
                    action_type=ActionType.FILESYSTEM,
                    confidence=0.9,
                    can_execute_directly=True
                )
            else:
                return self._create_agent_fallback(classification, path)

        elif sub_action == "eliminar":
            # NUNCA auto-ejecutar eliminación
            return DirectOrder(
                tool="",
                marker="",
                params={},
                agent_prompt="⚠️ Operación de eliminación detectada. "
                            "Por seguridad, no se ejecuta automáticamente. "
                            "Pide confirmación al usuario.",
                action_type=ActionType.FILESYSTEM,
                confidence=1.0,
                can_execute_directly=False
            )

        else:
            return self._create_agent_fallback(classification, path)

    def _decide_git(
        self,
        query: str,
        path: str,
        sub_action: str,
        classification: ClassificationResult
    ) -> DirectOrder:
        """Decidir herramienta de git"""

        if sub_action in ["status", "unknown"]:
            return DirectOrder(
                tool="git_status",
                marker="[[git estado]]",
                params={"path": path},
                agent_prompt="EJECUTA: [[git estado]]",
                action_type=ActionType.GIT,
                confidence=0.95,
                can_execute_directly=True
            )

        elif sub_action == "log":
            return DirectOrder(
                tool="git_log",
                marker="[[git log]]",
                params={"path": path},
                agent_prompt="EJECUTA: [[git log]]",
                action_type=ActionType.GIT,
                confidence=0.95,
                can_execute_directly=True
            )

        elif sub_action == "diff":
            return DirectOrder(
                tool="git_diff",
                marker="[[git diff]]",
                params={"path": path},
                agent_prompt="EJECUTA: [[git diff]]",
                action_type=ActionType.GIT,
                confidence=0.95,
                can_execute_directly=True
            )

        return self._create_agent_fallback(classification, path)

    def _decide_claudia(
        self,
        query: str,
        path: str,
        entities: Dict,
        classification: ClassificationResult
    ) -> DirectOrder:
        """Decidir acción de Claudia"""
        # Claudia siempre necesita al agente, pero con contexto claro
        return DirectOrder(
            tool="claudia",
            marker="",
            params={"path": path, "query": query},
            agent_prompt=f"Usa Claudia para: {query}\nPath de contexto: {path}",
            action_type=ActionType.CLAUDIA,
            confidence=0.8,
            can_execute_directly=False,
            fallback_to_agent=True
        )

    def _decide_search(
        self,
        query: str,
        entities: Dict,
        classification: ClassificationResult
    ) -> DirectOrder:
        """Decidir búsqueda (RAG o web)"""
        # Extraer tema de búsqueda
        topic = self._extract_search_topic(query)

        return DirectOrder(
            tool="rag_search",
            marker=f"[[rag {topic}]]",
            params={"query": topic, "rag_name": "wikipedia"},
            agent_prompt=f"EJECUTA: [[rag {topic}]]",
            action_type=ActionType.SEARCH,
            confidence=0.85,
            can_execute_directly=True
        )

    def _create_agent_fallback(
        self,
        classification: ClassificationResult,
        path: str
    ) -> DirectOrder:
        """Crear orden de fallback cuando no podemos decidir"""
        return DirectOrder(
            tool="",
            marker="",
            params={"path": path},
            agent_prompt=f"""CONTEXTO:
- Directorio actual: {path}
- Query del usuario: {classification.query}
- Tipo detectado: {classification.action_type.value}

INSTRUCCIÓN: Usa UN marcador [[...]] para ejecutar la acción apropiada.
NO expliques, NO pienses. Solo [[ejecuta]].""",
            action_type=classification.action_type,
            confidence=0.5,
            can_execute_directly=False,
            fallback_to_agent=True
        )

    def _extract_search_pattern(self, query: str) -> Optional[str]:
        """Extraer patrón de búsqueda de la query"""
        # Buscar texto entre comillas
        quoted = re.search(r'["\']([^"\']+)["\']', query)
        if quoted:
            return quoted.group(1)

        # Buscar después de "busca", "encuentra", etc.
        match = re.search(r'(?:busca|encuentra|grep)\s+(\S+)', query, re.IGNORECASE)
        if match:
            return match.group(1)

        return None

    def _extract_search_topic(self, query: str) -> str:
        """Extraer tema de búsqueda para RAG"""
        # Remover palabras clave de búsqueda
        topic = re.sub(r'^(busca|encuentra|qué es|que es|explica)\s+', '', query, flags=re.IGNORECASE)
        return topic.strip()[:100]


# ============================================================
# 🎭 INTEGRACIÓN CON TEATRO MENTAL
# ============================================================

class SmartToolDecider(ToolDecider):
    """
    ToolDecider con Teatro Mental integrado.

    Para operaciones críticas, primero delibera con el Teatro Mental
    antes de decidir la herramienta. Esto previene acciones destructivas
    accidentales y mejora la toma de decisiones para modelos 8B.
    """

    # Operaciones que SIEMPRE requieren deliberación
    CRITICAL_OPERATIONS = [
        "eliminar", "borrar", "delete", "rm ",
        "modificar", "cambiar", "reemplazar", "overwrite",
        "sudo", "root", "chmod", "chown",
        "producción", "deploy", "push"
    ]

    def __init__(
        self,
        default_pwd: str = None,
        llm_interface=None,
        memory_interface=None,
        auto_deliberate_critical: bool = True
    ):
        super().__init__(default_pwd)
        self.llm = llm_interface
        self.memory = memory_interface
        self.auto_deliberate = auto_deliberate_critical
        self._theater = None

    @property
    def theater(self):
        """Lazy init del Teatro Mental"""
        if self._theater is None:
            from core.agentic.mental_theater import MentalTheater
            self._theater = MentalTheater(
                llm_interface=self.llm,
                memory_interface=self.memory,
                verbose=True
            )
        return self._theater

    def decide_with_deliberation(
        self,
        classification,
        force_deliberation: bool = False
    ) -> DirectOrder:
        """
        Decidir herramienta CON deliberación del Teatro Mental.

        Args:
            classification: Resultado del IntentClassifier
            force_deliberation: Forzar deliberación aunque no sea crítico

        Returns:
            DirectOrder enriquecida con deliberación
        """
        query = classification.query.lower()

        # Determinar si necesita deliberación
        needs_deliberation = force_deliberation or (
            self.auto_deliberate and self._is_critical(query)
        )

        deliberation = None
        if needs_deliberation:
            logger.info("🎭 Activando Teatro Mental para deliberación...")

            context = {
                "query": classification.query,
                "action_type": classification.action_type.value,
                "entities": classification.entities,
                "pwd": self.pwd
            }

            deliberation = self.theater.deliberate(query, context)

            # Si el teatro bloquea, retornar orden de bloqueo
            if not deliberation.should_proceed:
                return DirectOrder(
                    tool="BLOCKED",
                    marker="",
                    params={},
                    agent_prompt=f"⛔ BLOQUEADO por Teatro Mental:\n{deliberation.reasoning}",
                    action_type=classification.action_type,
                    confidence=1.0,
                    can_execute_directly=False
                )

            # Si hay sugerencias del teatro, enriquecer el contexto
            if deliberation.consensus:
                logger.info(f"🎭 Consenso: {deliberation.consensus[:100]}...")

        # Decidir herramienta normal
        order = self.decide(classification)

        # Enriquecer orden con deliberación si existe
        if deliberation:
            # Añadir advertencias al prompt del agente
            warnings = [op.concerns for op in deliberation.opinions if op.concerns]
            flat_warnings = [w for sublist in warnings for w in sublist]

            if flat_warnings:
                order.agent_prompt = (
                    f"⚠️ ADVERTENCIAS: {'; '.join(flat_warnings[:3])}\n\n"
                    f"{order.agent_prompt}"
                )

            # Añadir metadata de deliberación
            order.params["_deliberation"] = {
                "risk": deliberation.risk_assessment,
                "consensus": deliberation.consensus,
                "duration_ms": deliberation.duration_ms
            }

        return order

    def _is_critical(self, query: str) -> bool:
        """Determinar si la query es crítica y requiere deliberación"""
        query_lower = query.lower()
        return any(op in query_lower for op in self.CRITICAL_OPERATIONS)

    def quick_safety_check(self, query: str) -> bool:
        """
        Verificación rápida de seguridad.
        Solo usa Luz y Sombra del teatro.

        Returns:
            True si es seguro proceder
        """
        return self.theater.quick_check(query)


# === SINGLETON ===
_decider_instance: Optional[ToolDecider] = None
_smart_decider_instance: Optional[SmartToolDecider] = None


def get_tool_decider(pwd: str = None) -> ToolDecider:
    """Obtener instancia del ToolDecider básico"""
    global _decider_instance
    if _decider_instance is None:
        _decider_instance = ToolDecider(pwd)
    return _decider_instance


def get_smart_tool_decider(
    pwd: str = None,
    llm_interface=None,
    memory_interface=None
) -> SmartToolDecider:
    """Obtener instancia del SmartToolDecider con Teatro Mental"""
    global _smart_decider_instance
    if _smart_decider_instance is None:
        _smart_decider_instance = SmartToolDecider(
            default_pwd=pwd,
            llm_interface=llm_interface,
            memory_interface=memory_interface
        )
    return _smart_decider_instance


# === TEST ===
if __name__ == "__main__":
    from .intent_classifier import IntentClassifier

    print("🎯 Test de Tool Decider")
    print("=" * 60)

    classifier = IntentClassifier()
    decider = ToolDecider(default_pwd="/Users/test/wikirag")

    test_queries = [
        "lista los archivos",
        "lista los archivos de ~/proyecto",
        "lee el archivo config.py",
        "busca 'error' en los logs",
        "git status",
        "usa claudia para analizar el código",
        "qué es Python?",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"📝 Query: {query}")

        # Clasificar
        classification = classifier.classify(query)
        print(f"🎯 Intent: {classification.intent.value} / {classification.action_type.value}")
        print(f"📦 Entities: {classification.entities}")

        # Decidir
        order = decider.decide(classification)
        print(f"\n🔧 DECISIÓN:")
        print(f"   Tool: {order.tool}")
        print(f"   Marker: {order.marker}")
        print(f"   Directo: {'✅' if order.can_execute_directly else '❌'}")
        print(f"   Prompt: {order.agent_prompt[:100]}...")
