#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
🎯 INTENT CLASSIFIER - Clasificador de Intenciones
========================================
Clasifica las consultas del usuario en categorías:
- INFORMATIVA: Usar RAG para buscar información
- ACCION: Ejecutar herramientas (MCP/Claudia/filesystem)
- SISTEMA: Comandos del sistema (help, exit, status)
- CONVERSACIONAL: Chat simple sin herramientas

Este módulo es CRÍTICO para dirigir las consultas al componente correcto.

Uso:
    from core.intent_classifier import IntentClassifier, Intent

    classifier = IntentClassifier()
    result = classifier.classify("lista los archivos de esta carpeta")
    # result.intent == Intent.ACTION
    # result.action_type == "filesystem"
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntentClassifier")


class Intent(Enum):
    """Tipos de intención del usuario"""
    INFORMATIVE = "informative"      # Buscar información (RAG)
    ACTION = "action"                # Ejecutar acción (herramientas)
    SYSTEM = "system"                # Comando del sistema
    CONVERSATIONAL = "conversational"  # Chat simple
    HYBRID = "hybrid"                # Requiere RAG + acción


class ActionType(Enum):
    """Tipos de acción específica"""
    FILESYSTEM = "filesystem"    # Operaciones de archivos
    CODE = "code"                # Análisis/ejecución de código
    SEARCH = "search"            # Búsqueda web
    API = "api"                  # Llamadas a API
    GIT = "git"                  # Operaciones git
    CLAUDIA = "claudia"          # Usar asistente Claudia
    MCP = "mcp"                  # Herramientas MCP genéricas
    NONE = "none"                # Sin acción específica


class SystemCommand(Enum):
    """Comandos del sistema"""
    HELP = "help"
    EXIT = "exit"
    STATUS = "status"
    CLEAR = "clear"
    CONFIG = "config"
    HISTORY = "history"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Resultado de la clasificación"""
    query: str
    intent: Intent
    confidence: float  # 0.0 a 1.0

    # Detalles según tipo
    action_type: ActionType = ActionType.NONE
    system_command: SystemCommand = SystemCommand.UNKNOWN

    # Entidades extraídas
    entities: Dict[str, Any] = field(default_factory=dict)

    # Sugerencias de enrutamiento
    suggested_handler: str = ""
    suggested_tools: List[str] = field(default_factory=list)

    # Metadata
    reasoning: str = ""

    def to_dict(self) -> Dict:
        return {
            "query": self.query,
            "intent": self.intent.value,
            "confidence": self.confidence,
            "action_type": self.action_type.value,
            "system_command": self.system_command.value,
            "entities": self.entities,
            "suggested_handler": self.suggested_handler,
            "suggested_tools": self.suggested_tools,
            "reasoning": self.reasoning
        }

    @property
    def is_action(self) -> bool:
        return self.intent in [Intent.ACTION, Intent.HYBRID]

    @property
    def needs_rag(self) -> bool:
        return self.intent in [Intent.INFORMATIVE, Intent.HYBRID]

    @property
    def is_system(self) -> bool:
        return self.intent == Intent.SYSTEM


class IntentClassifier:
    """
    Clasificador de intenciones basado en reglas y patrones.

    Flujo:
    1. Detectar comandos del sistema
    2. Detectar intención de acción
    3. Detectar intención informativa
    4. Default: conversacional

    El clasificador es rápido y no requiere LLM.
    """

    # === PATRONES DE COMANDOS DEL SISTEMA ===
    SYSTEM_PATTERNS = {
        SystemCommand.HELP: [
            r'^help$', r'^ayuda$', r'^\?$', r'^--help$',
            r'^qué puedo hacer', r'^que puedo hacer',
            r'^cómo funciona', r'^como funciona',
            r'^comandos disponibles', r'^muestra ayuda'
        ],
        SystemCommand.EXIT: [
            r'^exit$', r'^salir$', r'^quit$', r'^bye$',
            r'^adiós$', r'^adios$', r'^terminar$', r'^cerrar$'
        ],
        SystemCommand.STATUS: [
            r'^status$', r'^estado$', r'^info$',
            r'^estado del sistema', r'^system status'
        ],
        SystemCommand.CLEAR: [
            r'^clear$', r'^limpiar$', r'^cls$', r'^borrar pantalla'
        ],
        SystemCommand.CONFIG: [
            r'^config', r'^configuración', r'^settings',
            r'^ajustes', r'^opciones'
        ],
        SystemCommand.HISTORY: [
            r'^history$', r'^historial$', r'^últimas consultas'
        ]
    }

    # === PATRONES DE ACCIONES ===
    ACTION_PATTERNS = {
        ActionType.FILESYSTEM: [
            # Listar
            r'lista(?:r)?(?:\s+(?:los\s+)?archivos)', r'ls\s', r'dir\s',
            r'muestra(?:me)?\s+(?:los\s+)?archivos', r'qué hay en',
            r'contenido de(?:l)?\s+(?:la\s+)?carpeta',
            r'archivos en', r'directorio', r'folder',
            # Leer
            r'lee(?:r)?(?:\s+el)?\s+archivo', r'abre(?:\s+el)?\s+archivo',
            r'muestra(?:me)?(?:\s+el)?\s+contenido',
            r'cat\s', r'mostrar archivo',
            # Buscar
            r'busca(?:r)?(?:\s+el)?\s+archivo', r'encuentra(?:\s+el)?\s+archivo',
            r'dónde está', r'donde esta', r'localiza',
            # Crear/Modificar
            r'crea(?:r)?(?:\s+un)?\s+archivo', r'escribe(?:\s+en)?',
            r'guarda(?:r)?', r'nuevo archivo', r'touch\s',
            # Eliminar
            r'elimina(?:r)?', r'borra(?:r)?', r'remove', r'delete',
        ],
        ActionType.CODE: [
            r'ejecuta(?:r)?(?:\s+el)?\s+(?:código|script|programa)',
            r'run\s', r'python\s', r'node\s', r'npm\s',
            r'compila(?:r)?', r'build', r'test(?:s)?',
            r'depura(?:r)?', r'debug', r'analiza(?:r)?(?:\s+el)?\s+código',
            r'refactoriza', r'optimiza(?:r)?(?:\s+el)?\s+código',
            r'revisa(?:r)?(?:\s+el)?\s+código', r'code review',
        ],
        ActionType.CLAUDIA: [
            r'\bclaudia\b', r'asistente de código', r'asistente ia',
            r'usa(?:r)?\s+claudia', r'pregunta(?:le)?\s+a\s+claudia',
            r'que claudia', r'con claudia', r'mediante claudia',
            r'análisis(?:\s+de)?\s+proyecto', r'analiza(?:r)?(?:\s+el)?\s+proyecto',
        ],
        ActionType.GIT: [
            r'\bgit\s', r'commit', r'push', r'pull', r'merge',
            r'branch', r'checkout', r'clone', r'diff',
            r'historial de commits', r'cambios en el repo',
        ],
        ActionType.API: [
            r'consulta(?:r)?(?:\s+la)?\s+api', r'llama(?:r)?(?:\s+a)?\s+api',
            r'fetch', r'request', r'http', r'endpoint',
            r'curl\s', r'wget\s',
        ],
        ActionType.SEARCH: [
            r'busca(?:r)?(?:\s+en)?\s+(?:la\s+)?web', r'google',
            r'investiga(?:r)?(?:\s+en)?\s+internet', r'search online',
        ],
    }

    # === PATRONES INFORMATIVOS ===
    INFORMATIVE_PATTERNS = [
        r'^qué es\b', r'^que es\b', r'^what is\b',
        r'^quién (?:es|fue)\b', r'^quien (?:es|fue)\b', r'^who is\b',
        r'^cuándo\b', r'^cuando\b', r'^when\b',
        r'^dónde\b', r'^donde\b', r'^where\b',
        r'^por qué\b', r'^por que\b', r'^why\b',
        r'^cómo funciona\b', r'^como funciona\b', r'^how does\b',
        r'^explica(?:me)?\b', r'^explain\b',
        r'^define\b', r'^definición de\b', r'^definition\b',
        r'^cuál es\b', r'^cual es\b', r'^which is\b',
        r'^cuánto\b', r'^cuanto\b', r'^how much\b',
        r'^historia de\b', r'^history of\b',
        r'^información sobre\b', r'^información de\b',
        r'^dime (?:algo )?sobre\b', r'^tell me about\b',
        r'^háblame de\b', r'^hablame de\b',
        r'^resumen de\b', r'^summary of\b',
    ]

    # === PATRONES CONVERSACIONALES ===
    CONVERSATIONAL_PATTERNS = [
        r'^hola\b', r'^hello\b', r'^hi\b', r'^hey\b',
        r'^buenos días', r'^buenas tardes', r'^buenas noches',
        r'^gracias\b', r'^thanks\b', r'^thank you\b',
        r'^ok\b', r'^vale\b', r'^bien\b', r'^entendido\b',
        r'^sí\b', r'^si\b', r'^no\b', r'^yes\b',
        r'^de acuerdo\b', r'^claro\b', r'^perfecto\b',
        r'^cómo estás', r'^como estas', r'^how are you',
    ]

    def __init__(self, use_llm: bool = False, llm_interface: Any = None):
        """
        Args:
            use_llm: Usar LLM para clasificación avanzada
            llm_interface: Interfaz al LLM (opcional)
        """
        self.use_llm = use_llm and llm_interface is not None
        self.llm = llm_interface

        # Compilar patrones
        self._compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict:
        """Compilar expresiones regulares"""
        compiled = {
            "system": {},
            "action": {},
            "informative": [],
            "conversational": []
        }

        # Sistema
        for cmd, patterns in self.SYSTEM_PATTERNS.items():
            compiled["system"][cmd] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

        # Acciones
        for action, patterns in self.ACTION_PATTERNS.items():
            compiled["action"][action] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

        # Informativo
        compiled["informative"] = [
            re.compile(p, re.IGNORECASE) for p in self.INFORMATIVE_PATTERNS
        ]

        # Conversacional
        compiled["conversational"] = [
            re.compile(p, re.IGNORECASE) for p in self.CONVERSATIONAL_PATTERNS
        ]

        return compiled

    def classify(self, query: str) -> ClassificationResult:
        """
        Clasificar una consulta.

        Args:
            query: La consulta del usuario

        Returns:
            ClassificationResult con la clasificación
        """
        query = query.strip()

        if not query:
            return ClassificationResult(
                query=query,
                intent=Intent.CONVERSATIONAL,
                confidence=1.0,
                reasoning="Consulta vacía"
            )

        # 1. Detectar comandos del sistema (prioridad máxima)
        system_result = self._check_system_command(query)
        if system_result:
            return system_result

        # 2. Detectar intención de acción
        action_result = self._check_action_intent(query)
        if action_result and action_result.confidence >= 0.7:
            return action_result

        # 3. Detectar intención informativa
        info_result = self._check_informative_intent(query)
        if info_result and info_result.confidence >= 0.6:
            # Si también hay acción detectada, es híbrido
            if action_result and action_result.confidence >= 0.5:
                return ClassificationResult(
                    query=query,
                    intent=Intent.HYBRID,
                    confidence=(info_result.confidence + action_result.confidence) / 2,
                    action_type=action_result.action_type,
                    entities={**info_result.entities, **action_result.entities},
                    suggested_handler="hybrid_handler",
                    suggested_tools=action_result.suggested_tools,
                    reasoning="Requiere RAG + ejecución de herramientas"
                )
            return info_result

        # 4. Detectar conversacional
        conv_result = self._check_conversational(query)
        if conv_result:
            return conv_result

        # 5. Si hay acción con baja confianza, usarla
        if action_result:
            return action_result

        # 6. Default: asumir informativo
        return ClassificationResult(
            query=query,
            intent=Intent.INFORMATIVE,
            confidence=0.5,
            suggested_handler="rag_handler",
            reasoning="Default a búsqueda RAG"
        )

    def _check_system_command(self, query: str) -> Optional[ClassificationResult]:
        """Verificar si es comando del sistema"""
        for cmd, patterns in self._compiled_patterns["system"].items():
            for pattern in patterns:
                if pattern.search(query):
                    return ClassificationResult(
                        query=query,
                        intent=Intent.SYSTEM,
                        confidence=1.0,
                        system_command=cmd,
                        suggested_handler="system_handler",
                        reasoning=f"Comando del sistema: {cmd.value}"
                    )
        return None

    def _check_action_intent(self, query: str) -> Optional[ClassificationResult]:
        """Verificar si es intención de acción"""
        best_match = None
        best_confidence = 0

        for action_type, patterns in self._compiled_patterns["action"].items():
            for pattern in patterns:
                match = pattern.search(query)
                if match:
                    # Calcular confianza basada en posición del match
                    position_factor = 1 - (match.start() / max(len(query), 1))
                    confidence = 0.7 + (position_factor * 0.3)

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = action_type

        if best_match:
            entities = self._extract_entities(query, best_match)
            suggested_tools = self._get_suggested_tools(best_match)

            return ClassificationResult(
                query=query,
                intent=Intent.ACTION,
                confidence=best_confidence,
                action_type=best_match,
                entities=entities,
                suggested_handler=f"{best_match.value}_handler",
                suggested_tools=suggested_tools,
                reasoning=f"Acción detectada: {best_match.value}"
            )

        return None

    def _check_informative_intent(self, query: str) -> Optional[ClassificationResult]:
        """Verificar si es intención informativa"""
        for pattern in self._compiled_patterns["informative"]:
            match = pattern.search(query)
            if match:
                # Calcular confianza
                position_factor = 1 - (match.start() / max(len(query), 1))
                confidence = 0.6 + (position_factor * 0.3)

                # Extraer tema
                topic = query[match.end():].strip()[:100]

                return ClassificationResult(
                    query=query,
                    intent=Intent.INFORMATIVE,
                    confidence=confidence,
                    entities={"topic": topic} if topic else {},
                    suggested_handler="rag_handler",
                    reasoning="Pregunta informativa detectada"
                )

        return None

    def _check_conversational(self, query: str) -> Optional[ClassificationResult]:
        """Verificar si es conversacional"""
        for pattern in self._compiled_patterns["conversational"]:
            if pattern.search(query):
                return ClassificationResult(
                    query=query,
                    intent=Intent.CONVERSATIONAL,
                    confidence=0.9,
                    suggested_handler="conversation_handler",
                    reasoning="Mensaje conversacional"
                )
        return None

    def _extract_entities(self, query: str, action_type: ActionType) -> Dict[str, Any]:
        """Extraer entidades relevantes de la consulta"""
        entities = {}

        # Extraer rutas de archivos
        path_pattern = r'[\'"]?([/~][\w/.\-_]+)[\'"]?|[\'"]?([\w.\-_]+\.\w+)[\'"]?'
        paths = re.findall(path_pattern, query)
        if paths:
            entities["paths"] = [p[0] or p[1] for p in paths if p[0] or p[1]]

        # Extraer extensiones de archivo
        ext_pattern = r'\.(py|js|ts|json|yaml|yml|md|txt|sh|bash|html|css|sql)(?:\s|$)'
        extensions = re.findall(ext_pattern, query, re.IGNORECASE)
        if extensions:
            entities["extensions"] = list(set(extensions))

        # Extraer comandos entre comillas
        command_pattern = r'[\'"`]([^\'"`]+)[\'"`]'
        commands = re.findall(command_pattern, query)
        if commands:
            entities["quoted"] = commands

        # Extraer URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, query)
        if urls:
            entities["urls"] = urls

        return entities

    def _get_suggested_tools(self, action_type: ActionType) -> List[str]:
        """Obtener herramientas sugeridas para un tipo de acción"""
        tool_map = {
            ActionType.FILESYSTEM: ["leer_archivo", "listar_directorio", "buscar_archivos", "escribir_archivo"],
            ActionType.CODE: ["claudia", "claudia_analyze", "ejecutar_comando"],
            ActionType.CLAUDIA: ["claudia", "claudia_analyze", "claudia_project"],
            ActionType.GIT: ["git_operation"],
            ActionType.API: ["consultar_api"],
            ActionType.SEARCH: ["buscar_en_contenido", "buscar_archivos"],
            ActionType.MCP: ["ejecutar_comando"],
        }
        return tool_map.get(action_type, [])

    def get_handler_for_intent(self, result: ClassificationResult) -> str:
        """Obtener el handler recomendado para un resultado"""
        if result.intent == Intent.SYSTEM:
            return "system_handler"
        elif result.intent == Intent.ACTION:
            if result.action_type == ActionType.CLAUDIA:
                return "claudia_handler"
            elif result.action_type == ActionType.FILESYSTEM:
                return "filesystem_handler"
            else:
                return "mcp_handler"
        elif result.intent == Intent.INFORMATIVE:
            return "rag_handler"
        elif result.intent == Intent.HYBRID:
            return "hybrid_handler"
        else:
            return "default_handler"


# === SINGLETON ===
_classifier_instance: Optional[IntentClassifier] = None


def get_intent_classifier(use_llm: bool = False, llm: Any = None) -> IntentClassifier:
    """Obtener instancia singleton del clasificador"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = IntentClassifier(use_llm, llm)
    return _classifier_instance


# === TEST ===
if __name__ == "__main__":
    print("🎯 Test de Intent Classifier")
    print("=" * 60)

    classifier = IntentClassifier()

    test_queries = [
        # Sistema
        ("help", Intent.SYSTEM),
        ("salir", Intent.SYSTEM),
        ("status", Intent.SYSTEM),

        # Acciones - Filesystem
        ("lista los archivos de esta carpeta", Intent.ACTION),
        ("muéstrame el contenido del archivo config.json", Intent.ACTION),
        ("busca archivos .py en el proyecto", Intent.ACTION),

        # Acciones - Claudia
        ("usa claudia para analizar el código", Intent.ACTION),
        ("que claudia revise el proyecto", Intent.ACTION),

        # Acciones - Git
        ("git status", Intent.ACTION),
        ("muéstrame los últimos commits", Intent.ACTION),

        # Informativas
        ("qué es Python?", Intent.INFORMATIVE),
        ("explícame cómo funciona el garbage collector", Intent.INFORMATIVE),
        ("información sobre machine learning", Intent.INFORMATIVE),

        # Conversacionales
        ("hola", Intent.CONVERSATIONAL),
        ("gracias", Intent.CONVERSATIONAL),
    ]

    passed = 0
    for query, expected in test_queries:
        result = classifier.classify(query)
        match = "✅" if result.intent == expected else "❌"
        print(f"{match} '{query[:40]:<40}' → {result.intent.value:<15} ({result.confidence:.0%})")

        if result.intent == expected:
            passed += 1

        # Mostrar detalles extra para acciones
        if result.intent == Intent.ACTION:
            print(f"      Tipo: {result.action_type.value}, Tools: {result.suggested_tools[:3]}")

    print(f"\n📊 Resultado: {passed}/{len(test_queries)} tests pasados")
