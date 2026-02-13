#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
🔀 SMART ROUTER - Enrutador Inteligente
========================================
Dirige las consultas al handler correcto basándose en:
- Clasificación de intenciones
- Herramientas disponibles
- Estado del sistema

Flujo:
Query → IntentClassifier → SmartRouter → Handler apropiado
                                           ├─ RAG (informativo)
                                           ├─ MCP/Claudia (acción)
                                           ├─ System (comandos)
                                           └─ Hybrid (combo)

Uso:
    from core.smart_router import SmartRouter

    router = SmartRouter(rag_manager, mcp_tools, claudia)
    result = router.route("lista los archivos")
"""

import os
import sys
import json
import logging
import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum

# Importar clasificador y decisor
from .intent_classifier import (
    IntentClassifier, Intent, ActionType, SystemCommand,
    ClassificationResult, get_intent_classifier
)
from .tool_decider import ToolDecider, DirectOrder, get_tool_decider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SmartRouter")


@dataclass
class RouteResult:
    """Resultado del enrutamiento"""
    query: str
    classification: ClassificationResult
    handler_used: str
    response: str
    success: bool = True
    execution_time: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "query": self.query,
            "intent": self.classification.intent.value,
            "handler": self.handler_used,
            "response": self.response,
            "success": self.success,
            "execution_time": self.execution_time,
            "metadata": self.metadata
        }


class SmartRouter:
    """
    Enrutador inteligente que dirige consultas al handler correcto.

    Handlers disponibles:
    - RAG: Para consultas informativas (Wikipedia, docs, etc.)
    - MCP: Para acciones con herramientas MCP
    - Claudia: Para análisis de código y proyectos
    - System: Para comandos del sistema
    - Hybrid: Para consultas que necesitan RAG + acción
    """

    def __init__(
        self,
        rag_handler: Callable = None,
        mcp_handler: Callable = None,
        claudia_handler: Callable = None,
        system_handler: Callable = None,
        llm_interface: Any = None,
        verbose: bool = True
    ):
        """
        Args:
            rag_handler: Handler para consultas informativas
            mcp_handler: Handler para herramientas MCP
            claudia_handler: Handler para Claudia
            system_handler: Handler para comandos del sistema
            llm_interface: LLM para respuestas conversacionales
            verbose: Mostrar enrutamiento en consola
        """
        self.rag_handler = rag_handler
        self.mcp_handler = mcp_handler
        self.claudia_handler = claudia_handler
        self.system_handler = system_handler or self._default_system_handler
        self.llm = llm_interface
        self.verbose = verbose

        # Clasificador de intenciones
        self.classifier = get_intent_classifier()

        # Decisor de herramientas (EL CAPATAZ)
        self.tool_decider = get_tool_decider()

        # Registry de herramientas para ejecución directa
        self._tool_registry = None
        self._init_tool_registry()

        # Historial de rutas
        self.route_history: List[RouteResult] = []

        # Info del sistema para help
        self._system_info = self._collect_system_info()

    def _init_tool_registry(self):
        """Inicializar registry de herramientas para ejecución directa"""
        try:
            from core.agentic.tool_registry import get_tool_registry
            self._tool_registry = get_tool_registry()
            logger.debug("ToolRegistry inicializado para ejecución directa")
        except ImportError:
            logger.warning("ToolRegistry no disponible, usando fallback")

    def _collect_system_info(self) -> Dict:
        """Recopilar información del sistema"""
        return {
            "rag_available": self.rag_handler is not None,
            "mcp_available": self.mcp_handler is not None,
            "claudia_available": self.claudia_handler is not None,
            "llm_available": self.llm is not None
        }

    def route(self, query: str, context: str = "") -> RouteResult:
        """
        Enrutar una consulta al handler apropiado.

        Args:
            query: Consulta del usuario
            context: Contexto adicional

        Returns:
            RouteResult con la respuesta
        """
        start_time = time.time()

        # Clasificar intención
        classification = self.classifier.classify(query)

        if self.verbose:
            print(f"\n🔀 ENRUTAMIENTO:")
            print(f"   📝 Query: {query[:50]}...")
            print(f"   🎯 Intent: {classification.intent.value} ({classification.confidence:.0%})")

        # Enrutar según intención
        try:
            if classification.intent == Intent.SYSTEM:
                response = self._handle_system(classification)
                handler = "system"

            elif classification.intent == Intent.ACTION:
                response = self._handle_action(classification, context)
                handler = f"action_{classification.action_type.value}"

            elif classification.intent == Intent.INFORMATIVE:
                response = self._handle_informative(classification, context)
                handler = "rag"

            elif classification.intent == Intent.HYBRID:
                response = self._handle_hybrid(classification, context)
                handler = "hybrid"

            else:  # CONVERSATIONAL
                response = self._handle_conversational(classification)
                handler = "conversation"

            success = True

        except Exception as e:
            logger.error(f"Error en handler: {e}")
            response = f"Error procesando la consulta: {str(e)}"
            handler = "error"
            success = False

        execution_time = time.time() - start_time

        if self.verbose:
            print(f"   ⚡ Handler: {handler}")
            print(f"   ⏱️ Tiempo: {execution_time:.2f}s")

        # Crear resultado
        result = RouteResult(
            query=query,
            classification=classification,
            handler_used=handler,
            response=response,
            success=success,
            execution_time=execution_time
        )

        # Guardar en historial
        self.route_history.append(result)

        return result

    def _handle_system(self, classification: ClassificationResult) -> str:
        """Manejar comandos del sistema"""
        cmd = classification.system_command

        if cmd == SystemCommand.HELP:
            return self._generate_help()

        elif cmd == SystemCommand.EXIT:
            return "👋 ¡Hasta luego! Usa Ctrl+C para salir."

        elif cmd == SystemCommand.STATUS:
            return self._generate_status()

        elif cmd == SystemCommand.CLEAR:
            return "\033[2J\033[H"  # Clear screen ANSI

        elif cmd == SystemCommand.HISTORY:
            return self._generate_history()

        elif cmd == SystemCommand.CONFIG:
            return self._generate_config()

        else:
            return "Comando no reconocido. Escribe 'help' para ver comandos disponibles."

    def _handle_action(self, classification: ClassificationResult, context: str) -> str:
        """
        Manejar acciones con herramientas.

        NUEVO FLUJO (Daemon como Capataz):
        1. ToolDecider decide la herramienta EXACTA
        2. Si se puede ejecutar directamente → hacerlo sin agente
        3. Si necesita agente → darle ORDEN DIRECTA, no pregunta
        """
        # === PASO 1: El Capataz decide ===
        order = self.tool_decider.decide(classification)

        if self.verbose:
            print(f"   🎯 Decisión: {order.tool} | Directo: {'✅' if order.can_execute_directly else '❌'}")
            if order.marker:
                print(f"   📝 Marker: {order.marker}")

        # === PASO 2: Ejecutar directamente si es posible ===
        if order.can_execute_directly and self._tool_registry and order.tool:
            result = self._execute_direct(order)
            if result:
                return result

        # === PASO 3: Si no se puede ejecutar directamente, usar handler apropiado ===
        action_type = classification.action_type

        # Claudia
        if action_type == ActionType.CLAUDIA:
            if self.claudia_handler:
                return self.claudia_handler(classification.query, classification.entities)
            else:
                return "⚠️ Claudia no está disponible."

        # Filesystem / MCP genérico - con orden directa
        elif action_type in [ActionType.FILESYSTEM, ActionType.GIT, ActionType.API, ActionType.MCP]:
            if self.mcp_handler:
                # Pasar la orden directa al handler
                return self.mcp_handler(
                    order.agent_prompt,  # ORDEN DIRECTA, no query original
                    action_type.value,
                    {"order": order.to_dict(), **classification.entities},
                    [order.tool] if order.tool else classification.suggested_tools
                )
            else:
                return self._fallback_action_handler(classification, order)

        # Código
        elif action_type == ActionType.CODE:
            if self.claudia_handler:
                return self.claudia_handler(classification.query, classification.entities)
            else:
                return "⚠️ No hay handler disponible para ejecutar código."

        # Búsqueda
        elif action_type == ActionType.SEARCH:
            if order.can_execute_directly and self._tool_registry:
                result = self._execute_direct(order)
                if result:
                    return result
            if self.rag_handler:
                return self.rag_handler(classification.query, context)
            else:
                return "⚠️ No hay handler de búsqueda disponible."

        return "⚠️ Tipo de acción no soportada."

    def _execute_direct(self, order: DirectOrder) -> Optional[str]:
        """
        Ejecutar herramienta directamente SIN AGENTE.
        El Daemon es el capataz, no necesita preguntar.
        """
        if not self._tool_registry or not order.tool:
            return None

        try:
            if self.verbose:
                print(f"   ⚡ Ejecución DIRECTA: {order.tool}")

            result = self._tool_registry.execute(order.tool, order.params)

            if result.success:
                return f"✅ **Resultado:**\n{result.output}"
            else:
                return f"❌ **Error:** {result.error}"

        except Exception as e:
            logger.error(f"Error en ejecución directa: {e}")
            return None

    def _handle_informative(self, classification: ClassificationResult, context: str) -> str:
        """Manejar consultas informativas con RAG"""
        if self.rag_handler:
            return self.rag_handler(classification.query, context)
        elif self.llm:
            # Fallback a LLM directo
            return self._call_llm(classification.query)
        else:
            return "⚠️ No hay sistema de información disponible. Configura RAG o un LLM."

    def _handle_hybrid(self, classification: ClassificationResult, context: str) -> str:
        """Manejar consultas híbridas (RAG + acción)"""
        responses = []

        # Primero obtener información con RAG
        if self.rag_handler:
            rag_response = self.rag_handler(classification.query, context)
            if rag_response and not rag_response.startswith("⚠️"):
                responses.append(f"📚 **Información:**\n{rag_response}")

        # Luego ejecutar acción si es necesario
        action_response = self._handle_action(classification, context)
        if action_response and not action_response.startswith("⚠️"):
            responses.append(f"⚡ **Acción ejecutada:**\n{action_response}")

        if responses:
            return "\n\n".join(responses)
        else:
            return "No pude procesar esta consulta híbrida. Intenta reformularla."

    def _handle_conversational(self, classification: ClassificationResult) -> str:
        """Manejar mensajes conversacionales"""
        query_lower = classification.query.lower()

        # Respuestas predefinidas
        if any(g in query_lower for g in ['hola', 'hello', 'hi', 'hey']):
            return "¡Hola! 👋 ¿En qué puedo ayudarte? Escribe 'help' para ver qué puedo hacer."

        elif any(g in query_lower for g in ['gracias', 'thanks', 'thank you']):
            return "¡De nada! 😊 ¿Algo más en lo que pueda ayudarte?"

        elif any(g in query_lower for g in ['cómo estás', 'como estas', 'how are you']):
            return "¡Estoy bien, gracias! Listo para ayudarte. 🤖"

        elif any(g in query_lower for g in ['ok', 'vale', 'bien', 'entendido']):
            return "👍 Perfecto. ¿Necesitas algo más?"

        else:
            # Fallback a LLM si está disponible
            if self.llm:
                return self._call_llm(classification.query)
            return "¿En qué puedo ayudarte? Escribe 'help' para ver opciones."

    def _fallback_action_handler(
        self,
        classification: ClassificationResult,
        order: DirectOrder = None
    ) -> str:
        """
        Handler de fallback cuando no hay MCP.
        Usa la orden directa del ToolDecider si está disponible.
        """
        import subprocess

        # Si tenemos una orden directa con tool, intentar ejecutar
        if order and order.tool and order.params:
            path = order.params.get("path", ".")

            if order.tool == "filesystem_list":
                try:
                    result = subprocess.run(
                        ["ls", "-la", path],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        return f"📁 Contenido de `{path}`:\n```\n{result.stdout[:2000]}\n```"
                    else:
                        return f"❌ Error: {result.stderr}"
                except Exception as e:
                    return f"❌ Error: {str(e)}"

            elif order.tool == "filesystem_read":
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read(5000)
                    return f"📄 Contenido de `{path}`:\n```\n{content}\n```"
                except Exception as e:
                    return f"❌ Error leyendo archivo: {str(e)}"

            elif order.tool == "git_status":
                try:
                    result = subprocess.run(
                        ["git", "status"],
                        capture_output=True, text=True, timeout=10,
                        cwd=path
                    )
                    return f"📊 Git status:\n```\n{result.stdout}\n```"
                except Exception as e:
                    return f"❌ Error: {str(e)}"

        # Fallback original
        action_type = classification.action_type
        entities = classification.entities

        if action_type == ActionType.FILESYSTEM:
            try:
                if "listar" in classification.query.lower() or "lista" in classification.query.lower():
                    path = entities.get("paths", ["."])[0] if entities.get("paths") else "."
                    result = subprocess.run(
                        ["ls", "-la", path],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        return f"📁 Contenido de `{path}`:\n```\n{result.stdout[:2000]}\n```"
                    else:
                        return f"❌ Error: {result.stderr}"
            except Exception as e:
                return f"❌ Error ejecutando comando: {str(e)}"

        return "⚠️ No hay handler MCP disponible y el fallback no soporta esta acción."

    def _call_llm(self, prompt: str) -> str:
        """Llamar al LLM"""
        if hasattr(self.llm, 'generate_simple'):
            return self.llm.generate_simple(prompt, max_tokens=500)
        elif hasattr(self.llm, 'generate'):
            return self.llm.generate(prompt)
        elif callable(self.llm):
            return self.llm(prompt)
        else:
            return "Error: LLM no configurado correctamente."

    def _generate_help(self) -> str:
        """Generar mensaje de ayuda"""
        help_text = """
╔══════════════════════════════════════════════════════════════╗
║                    📚 AYUDA - WikiRAG v2.3                   ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  🔍 CONSULTAS INFORMATIVAS (usa RAG)                        ║
║    • "¿Qué es Python?"                                      ║
║    • "Explícame machine learning"                           ║
║    • "Historia de la inteligencia artificial"               ║
║                                                              ║
║  ⚡ ACCIONES (usa herramientas)                              ║
║    • "Lista los archivos de esta carpeta"                   ║
║    • "Busca archivos .py en el proyecto"                    ║
║    • "Usa Claudia para analizar el código"                  ║
║    • "git status"                                           ║
║                                                              ║
║  🛠️ COMANDOS DEL SISTEMA                                    ║
║    • help     - Muestra esta ayuda                          ║
║    • status   - Estado del sistema                          ║
║    • history  - Historial de consultas                      ║
║    • exit     - Salir                                       ║
║                                                              ║
║  📊 ESTADO ACTUAL                                           ║
"""
        # Añadir estado de componentes
        components = []
        if self._system_info["rag_available"]:
            components.append("║    ✅ RAG disponible")
        else:
            components.append("║    ❌ RAG no configurado")

        if self._system_info["mcp_available"]:
            components.append("║    ✅ MCP Tools disponibles")
        else:
            components.append("║    ❌ MCP Tools no configurados")

        if self._system_info["claudia_available"]:
            components.append("║    ✅ Claudia disponible")
        else:
            components.append("║    ⚠️ Claudia no disponible")

        help_text += "\n".join(f"{c:<62}║" for c in components)
        help_text += """
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
        return help_text

    def _generate_status(self) -> str:
        """Generar estado del sistema"""
        status_lines = [
            "📊 **ESTADO DEL SISTEMA**",
            "",
            "**Componentes:**"
        ]

        for name, available in self._system_info.items():
            icon = "✅" if available else "❌"
            status_lines.append(f"  {icon} {name.replace('_', ' ').title()}")

        status_lines.append("")
        status_lines.append(f"**Historial:** {len(self.route_history)} consultas")

        if self.route_history:
            # Últimas 3
            status_lines.append("\n**Últimas consultas:**")
            for r in self.route_history[-3:]:
                icon = "✅" if r.success else "❌"
                status_lines.append(f"  {icon} [{r.handler_used}] {r.query[:40]}...")

        return "\n".join(status_lines)

    def _generate_history(self) -> str:
        """Generar historial"""
        if not self.route_history:
            return "📜 Historial vacío"

        lines = ["📜 **HISTORIAL DE CONSULTAS**", ""]

        for i, r in enumerate(self.route_history[-10:], 1):
            icon = "✅" if r.success else "❌"
            lines.append(f"{i}. {icon} [{r.classification.intent.value}] {r.query[:50]}...")

        return "\n".join(lines)

    def _generate_config(self) -> str:
        """Generar configuración"""
        return f"""
⚙️ **CONFIGURACIÓN**

**Handlers configurados:**
  • RAG: {'✅ Sí' if self.rag_handler else '❌ No'}
  • MCP: {'✅ Sí' if self.mcp_handler else '❌ No'}
  • Claudia: {'✅ Sí' if self.claudia_handler else '❌ No'}
  • LLM: {'✅ Sí' if self.llm else '❌ No'}

**Modo:** Verbose = {self.verbose}
"""

    def _default_system_handler(self, classification: ClassificationResult) -> str:
        """Handler por defecto para comandos del sistema"""
        return self._handle_system(classification)


# === SINGLETON ===
_router_instance: Optional[SmartRouter] = None


def get_smart_router(**kwargs) -> SmartRouter:
    """Obtener instancia singleton del router"""
    global _router_instance
    if _router_instance is None:
        _router_instance = SmartRouter(**kwargs)
    return _router_instance


# === TEST ===
if __name__ == "__main__":
    print("🔀 Test de Smart Router")
    print("=" * 60)

    # Crear router sin handlers para probar enrutamiento
    router = SmartRouter(verbose=True)

    test_queries = [
        "help",
        "lista los archivos",
        "qué es Python?",
        "usa claudia para analizar el proyecto",
        "hola!",
        "git status",
        "status",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        result = router.route(query)
        print(f"   📤 Respuesta: {result.response[:100]}...")
