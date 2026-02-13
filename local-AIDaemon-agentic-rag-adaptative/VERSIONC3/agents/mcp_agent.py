#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
🤖 MCP AGENT - Agente con Herramientas MCP
========================================
Agente ReAct que puede usar herramientas externas via MCP.
Incluye integración con Claudia (asistente de código IA).

v2.3 - Integración Claudia MCP

Flujo ReAct con MCP:
1. Thought: Razonar sobre la query
2. Action: Seleccionar herramienta MCP (o Claudia)
3. Action Input: Parámetros para la herramienta
4. Observation: Resultado de la herramienta
5. ... (repetir hasta ANSWER)

Uso:
    from core.mcp_client import MCPClient
    from agents.mcp_agent import MCPAgent

    client = MCPClient({...})
    agent = MCPAgent(client, llm_interface)

    result = agent.execute("¿Qué noticias hay sobre Python?")
"""

import os
import sys
import json
import logging
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCPAgent")

# === IMPORTAR CLAUDIA ===
try:
    from agents.claudia_agent import ClaudiaAgent, get_claudia_agent
    from agents.tools.mcp_client import MCPClient as ToolClient, MCPToolWrapper
    HAS_CLAUDIA = True
except ImportError:
    HAS_CLAUDIA = False
    logger.warning("⚠️ ClaudiaAgent no disponible para MCPAgent")


class AgentAction(Enum):
    """Tipos de acción del agente"""
    TOOL = "tool"       # Usar una herramienta
    ANSWER = "answer"   # Responder al usuario
    THINK = "think"     # Solo pensar (sin acción)


@dataclass
class AgentStep:
    """Un paso de ejecución del agente"""
    iteration: int
    thought: str
    action: AgentAction
    action_name: Optional[str] = None
    action_input: Optional[Dict] = None
    observation: Optional[str] = None
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class AgentResult:
    """Resultado final del agente"""
    query: str
    response: str
    steps: List[AgentStep] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    total_iterations: int = 0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MCPAgent:
    """
    Agente ReAct que usa herramientas MCP para responder queries.

    El agente sigue el patrón ReAct:
    - Thought: Razonamiento sobre qué hacer
    - Action: Selección de herramienta
    - Observation: Resultado de la herramienta
    - Repeat hasta llegar a una respuesta final

    Características:
    - Detección automática de herramientas disponibles
    - Parsing robusto de respuestas del LLM
    - Manejo de errores y reintentos
    - Límite de iteraciones para evitar loops infinitos
    """

    # Prompt template para el agente
    SYSTEM_PROMPT = """Eres un asistente inteligente con acceso a herramientas externas.

HERRAMIENTAS DISPONIBLES:
{tools_description}

HERRAMIENTAS ESPECIALES - CLAUDIA (Asistente de Código IA):
- claudia: Ejecuta tarea de código con IA local. Ejemplo: {{"action": "claudia", "action_input": {{"task": "analiza main.py"}}}}
- claudia_analyze: Analiza archivo específico. Ejemplo: {{"action": "claudia_analyze", "action_input": {{"file_path": "core/rag.py", "question": "qué hace?"}}}}
- claudia_project: Análisis completo de proyecto. Ejemplo: {{"action": "claudia_project", "action_input": {{"project_path": "~/proyecto"}}}}
- claudia_cmd: Ejecuta comando via Claudia. Ejemplo: {{"action": "claudia_cmd", "action_input": {{"command": "pytest tests/"}}}}

FORMATO DE RESPUESTA:
Para usar una herramienta, responde EXACTAMENTE en este formato JSON:
```json
{{
  "thought": "Tu razonamiento sobre qué hacer",
  "action": "nombre_de_herramienta",
  "action_input": {{"parametro": "valor"}}
}}
```

Para dar la respuesta final al usuario:
```json
{{
  "thought": "Razonamiento final basado en la información obtenida",
  "action": "ANSWER",
  "action_input": {{"response": "Tu respuesta completa al usuario"}}
}}
```

REGLAS:
1. SIEMPRE responde en formato JSON válido
2. Usa las herramientas cuando necesites información externa
3. Para tareas de CÓDIGO usa las herramientas de Claudia (claudia, claudia_analyze, etc.)
4. Si no necesitas herramientas, responde directamente con ANSWER
5. Razona paso a paso antes de actuar
6. Si una herramienta falla, intenta otra estrategia

OBSERVACIONES PREVIAS:
{observations}

QUERY DEL USUARIO: {query}

Tu respuesta (JSON):"""

    def __init__(
        self,
        mcp_client: Any,
        llm_interface: Any,
        max_iterations: int = 5,
        verbose: bool = True,
        enable_claudia: bool = True
    ):
        """
        Inicializar agente MCP.

        Args:
            mcp_client: Cliente MCP con servidores configurados
            llm_interface: Interfaz al modelo de lenguaje
            max_iterations: Máximo de iteraciones ReAct
            verbose: Si mostrar pasos en consola
            enable_claudia: Habilitar herramientas Claudia
        """
        self.mcp = mcp_client
        self.llm = llm_interface
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.enable_claudia = enable_claudia and HAS_CLAUDIA

        # Cache de herramientas disponibles
        self._tools_cache = None

        # Verificar Claudia
        self._claudia_available = False
        if self.enable_claudia:
            try:
                agent = get_claudia_agent()
                self._claudia_available = agent.is_available
                if self._claudia_available:
                    logger.info("🤖 MCPAgent: Claudia disponible ✅")
            except Exception:
                pass

        logger.info(f"🤖 MCPAgent inicializado (max_iter={max_iterations}, claudia={self._claudia_available})")

    @property
    def available_tools(self) -> List[Dict]:
        """Obtener herramientas disponibles de todos los servidores MCP + Claudia"""
        if self._tools_cache is None:
            self._tools_cache = []

            # Herramientas MCP estándar
            for tool in self.mcp.list_tools():
                self._tools_cache.append({
                    'server': tool.server,
                    'name': tool.name,
                    'description': tool.description,
                    'schema': tool.input_schema
                })

            # Herramientas Claudia
            if self._claudia_available:
                claudia_tools = [
                    {
                        'server': 'claudia',
                        'name': 'claudia',
                        'description': 'Ejecuta tarea de código con asistente IA local',
                        'schema': {'properties': {'task': {'type': 'string'}, 'agentic': {'type': 'boolean'}}, 'required': ['task']}
                    },
                    {
                        'server': 'claudia',
                        'name': 'claudia_analyze',
                        'description': 'Analiza archivo de código con explicación detallada',
                        'schema': {'properties': {'file_path': {'type': 'string'}, 'question': {'type': 'string'}}, 'required': ['file_path']}
                    },
                    {
                        'server': 'claudia',
                        'name': 'claudia_project',
                        'description': 'Análisis completo de proyecto con modo agéntico',
                        'schema': {'properties': {'project_path': {'type': 'string'}}}
                    },
                    {
                        'server': 'claudia',
                        'name': 'claudia_cmd',
                        'description': 'Ejecuta comando del sistema via Claudia',
                        'schema': {'properties': {'command': {'type': 'string'}, 'working_dir': {'type': 'string'}}, 'required': ['command']}
                    },
                ]
                self._tools_cache.extend(claudia_tools)

        return self._tools_cache

    def refresh_tools(self):
        """Refrescar cache de herramientas"""
        self._tools_cache = None
        _ = self.available_tools

    def execute(self, query: str) -> AgentResult:
        """
        Ejecutar query con acceso a herramientas MCP.

        Args:
            query: Consulta del usuario

        Returns:
            AgentResult con respuesta y pasos
        """
        start_time = time.time()
        steps = []
        observations = []
        tools_used = []

        if self.verbose:
            print(f"\n🔍 Query: {query}")
            print("=" * 50)

        for iteration in range(self.max_iterations):
            if self.verbose:
                print(f"\n📍 Iteración {iteration + 1}/{self.max_iterations}")

            # Generar prompt con contexto
            prompt = self._build_prompt(query, observations)

            # Llamar al LLM
            try:
                llm_response = self._call_llm(prompt)
            except Exception as e:
                logger.error(f"❌ Error en LLM: {e}")
                step = AgentStep(
                    iteration=iteration + 1,
                    thought="Error llamando al LLM",
                    action=AgentAction.THINK,
                    error=str(e)
                )
                steps.append(step)
                continue

            # Parsear respuesta
            parsed = self._parse_response(llm_response)

            if parsed is None:
                # Respuesta no parseable, intentar extraer respuesta directa
                if self.verbose:
                    print(f"⚠️ Respuesta no parseable, usando como respuesta directa")

                return AgentResult(
                    query=query,
                    response=llm_response,
                    steps=steps,
                    tools_used=tools_used,
                    total_iterations=iteration + 1,
                    success=True,
                    metadata={"time_ms": (time.time() - start_time) * 1000}
                )

            thought = parsed.get('thought', '')
            action = parsed.get('action', '')
            action_input = parsed.get('action_input', {})

            if self.verbose:
                print(f"💭 Thought: {thought[:100]}...")
                print(f"🔧 Action: {action}")

            # Crear step
            step = AgentStep(
                iteration=iteration + 1,
                thought=thought,
                action=AgentAction.ANSWER if action == "ANSWER" else AgentAction.TOOL,
                action_name=action,
                action_input=action_input
            )

            # Si es ANSWER, terminar
            if action.upper() == "ANSWER":
                response = action_input.get('response', str(action_input))
                step.observation = "Respuesta final generada"
                steps.append(step)

                if self.verbose:
                    print(f"\n✅ Respuesta final:")
                    print(f"   {response[:200]}...")

                return AgentResult(
                    query=query,
                    response=response,
                    steps=steps,
                    tools_used=list(set(tools_used)),
                    total_iterations=iteration + 1,
                    success=True,
                    metadata={"time_ms": (time.time() - start_time) * 1000}
                )

            # Ejecutar herramienta
            observation = self._execute_tool(action, action_input)
            step.observation = observation
            steps.append(step)

            if "Error:" not in observation:
                tools_used.append(action)

            observations.append(f"[{action}] {observation}")

            if self.verbose:
                print(f"👁️ Observation: {observation[:150]}...")

        # Máximo de iteraciones alcanzado
        logger.warning("⚠️ Máximo de iteraciones alcanzado")

        # Generar respuesta de fallback
        fallback_response = self._generate_fallback_response(query, observations)

        return AgentResult(
            query=query,
            response=fallback_response,
            steps=steps,
            tools_used=list(set(tools_used)),
            total_iterations=self.max_iterations,
            success=False,
            error="Máximo de iteraciones alcanzado",
            metadata={"time_ms": (time.time() - start_time) * 1000}
        )

    def _build_prompt(self, query: str, observations: List[str]) -> str:
        """Construir prompt para el LLM"""
        # Formatear herramientas
        tools_desc = self._format_tools_description()

        # Formatear observaciones
        obs_text = "\n".join(observations) if observations else "(Ninguna aún)"

        return self.SYSTEM_PROMPT.format(
            tools_description=tools_desc,
            observations=obs_text,
            query=query
        )

    def _format_tools_description(self) -> str:
        """Formatear descripción de herramientas para el prompt"""
        if not self.available_tools:
            return "(No hay herramientas disponibles)"

        lines = []
        for tool in self.available_tools:
            lines.append(f"- {tool['name']}: {tool['description']}")

            # Mostrar parámetros requeridos
            schema = tool.get('schema', {})
            if 'properties' in schema:
                params = list(schema['properties'].keys())
                required = schema.get('required', [])
                param_str = ", ".join([
                    f"{p}{'*' if p in required else ''}"
                    for p in params[:5]  # Máximo 5 params
                ])
                lines.append(f"  Parámetros: {param_str}")

        return "\n".join(lines)

    def _call_llm(self, prompt: str) -> str:
        """Llamar al LLM para generar respuesta"""
        if hasattr(self.llm, 'generate_simple'):
            return self.llm.generate_simple(prompt, max_tokens=800)
        elif hasattr(self.llm, 'generate'):
            return self.llm.generate(prompt)
        elif callable(self.llm):
            return self.llm(prompt)
        else:
            raise ValueError("Interfaz LLM no reconocida")

    def _parse_response(self, response: str) -> Optional[Dict]:
        """
        Parsear respuesta del LLM a JSON.

        Intenta varios métodos de parsing para ser robusto.
        """
        response = response.strip()

        # Método 1: JSON directo
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Método 2: Extraer JSON de código markdown
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Método 3: Buscar cualquier objeto JSON en el texto
        json_pattern = r'\{[^{}]*"thought"[^{}]*"action"[^{}]*\}'
        json_match = re.search(json_pattern, response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Método 4: Parsing heurístico
        parsed = self._heuristic_parse(response)
        if parsed:
            return parsed

        return None

    def _heuristic_parse(self, response: str) -> Optional[Dict]:
        """Parsing heurístico cuando JSON falla"""
        result = {}

        # Buscar thought
        thought_match = re.search(r'"thought"\s*:\s*"([^"]*)"', response)
        if thought_match:
            result['thought'] = thought_match.group(1)

        # Buscar action
        action_match = re.search(r'"action"\s*:\s*"([^"]*)"', response)
        if action_match:
            result['action'] = action_match.group(1)

        # Si tiene thought y action, intentar extraer action_input
        if 'thought' in result and 'action' in result:
            # Buscar action_input como objeto
            input_match = re.search(r'"action_input"\s*:\s*(\{[^}]*\})', response)
            if input_match:
                try:
                    result['action_input'] = json.loads(input_match.group(1))
                except json.JSONDecodeError:
                    result['action_input'] = {}
            else:
                result['action_input'] = {}

            return result

        return None

    def _execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """Ejecutar herramienta MCP o Claudia"""

        # === HERRAMIENTAS CLAUDIA ===
        if tool_name.startswith('claudia'):
            return self._execute_claudia_tool(tool_name, arguments)

        # === HERRAMIENTAS MCP ESTÁNDAR ===
        # Buscar herramienta
        tool_info = None
        for tool in self.available_tools:
            if tool['name'] == tool_name:
                tool_info = tool
                break

        if not tool_info:
            # Verificar si es herramienta Claudia no reconocida
            claudia_tools = ['claudia', 'claudia_analyze', 'claudia_project', 'claudia_cmd']
            if tool_name in claudia_tools:
                return self._execute_claudia_tool(tool_name, arguments)

            return f"Error: Herramienta '{tool_name}' no existe. Disponibles: {[t['name'] for t in self.available_tools]}"

        try:
            result = self.mcp.call_tool(
                tool_info['server'],
                tool_info['name'],
                arguments
            )

            # Formatear resultado
            if isinstance(result, dict):
                # Extraer contenido si existe
                if 'content' in result:
                    content = result['content']
                    if isinstance(content, list):
                        texts = [c.get('text', str(c)) for c in content if isinstance(c, dict)]
                        return "\n".join(texts)[:2000]
                    return str(content)[:2000]
                return json.dumps(result, indent=2, ensure_ascii=False)[:2000]
            else:
                return str(result)[:2000]

        except Exception as e:
            return f"Error ejecutando {tool_name}: {str(e)}"

    def _execute_claudia_tool(self, tool_name: str, arguments: Dict) -> str:
        """
        Ejecutar herramienta de Claudia.

        Args:
            tool_name: Nombre de la herramienta (claudia, claudia_analyze, etc.)
            arguments: Argumentos de la herramienta

        Returns:
            Resultado como string
        """
        if not HAS_CLAUDIA:
            return "Error: Claudia no está disponible en este sistema"

        try:
            agent = get_claudia_agent()

            if not agent.is_available:
                return "Error: Claudia no está instalada o no se encontró en el sistema"

            # === claudia: Tarea general ===
            if tool_name == 'claudia':
                task = arguments.get('task', '')
                if not task:
                    return "Error: Parámetro 'task' es requerido"
                agentic = arguments.get('agentic', False)
                result = agent.execute(task, agentic=agentic)

            # === claudia_analyze: Analizar archivo ===
            elif tool_name == 'claudia_analyze':
                file_path = arguments.get('file_path', '')
                if not file_path:
                    return "Error: Parámetro 'file_path' es requerido"
                question = arguments.get('question', None)
                result = agent.analyze_file(file_path, question)

            # === claudia_project: Análisis de proyecto ===
            elif tool_name == 'claudia_project':
                project_path = arguments.get('project_path', None)
                result = agent.analyze_project(project_path)

            # === claudia_cmd: Ejecutar comando ===
            elif tool_name == 'claudia_cmd':
                command = arguments.get('command', '')
                if not command:
                    return "Error: Parámetro 'command' es requerido"
                working_dir = arguments.get('working_dir', None)
                result = agent.run_command(command, working_dir)

            else:
                return f"Error: Herramienta Claudia '{tool_name}' no reconocida"

            # Formatear resultado
            if result.success:
                return f"[Claudia:{result.mode}] {result.response[:1500]}"
            else:
                return f"Error Claudia: {result.error}"

        except Exception as e:
            return f"Error ejecutando Claudia ({tool_name}): {str(e)}"

    def _generate_fallback_response(self, query: str, observations: List[str]) -> str:
        """Generar respuesta de fallback con información recopilada"""
        if observations:
            obs_summary = "\n".join(observations[-3:])  # Últimas 3
            return f"Basándome en la información recopilada:\n\n{obs_summary}\n\nNo pude completar la tarea en el número máximo de pasos."
        else:
            return "No pude obtener información suficiente para responder. Por favor, intenta reformular tu pregunta."


class MCPAgentWithMemory(MCPAgent):
    """
    Agente MCP con memoria de conversación.

    Mantiene historial de queries y respuestas anteriores
    para contexto en conversaciones multi-turno.
    """

    def __init__(self, *args, memory_size: int = 5, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory: List[Dict] = []
        self.memory_size = memory_size

    def execute(self, query: str) -> AgentResult:
        """Ejecutar con memoria de contexto"""
        result = super().execute(query)

        # Guardar en memoria
        self.memory.append({
            'query': query,
            'response': result.response,
            'success': result.success
        })

        # Mantener tamaño de memoria
        if len(self.memory) > self.memory_size:
            self.memory = self.memory[-self.memory_size:]

        return result

    def _build_prompt(self, query: str, observations: List[str]) -> str:
        """Construir prompt con memoria de conversación"""
        base_prompt = super()._build_prompt(query, observations)

        if self.memory:
            memory_text = "\n\nCONTEXTO DE CONVERSACIÓN ANTERIOR:\n"
            for m in self.memory[-3:]:
                memory_text += f"- Usuario: {m['query'][:100]}...\n"
                memory_text += f"  Respuesta: {m['response'][:100]}...\n"

            # Insertar antes de la query
            base_prompt = base_prompt.replace(
                f"QUERY DEL USUARIO: {query}",
                f"{memory_text}\nQUERY DEL USUARIO: {query}"
            )

        return base_prompt

    def clear_memory(self):
        """Limpiar memoria de conversación"""
        self.memory = []


# === TEST ===
if __name__ == "__main__":
    print("🤖 Test de MCP Agent con Claudia")
    print("=" * 50)

    # Mock MCP Client
    class MockMCPClient:
        def list_tools(self):
            from dataclasses import dataclass

            @dataclass
            class MockTool:
                server: str
                name: str
                description: str
                input_schema: dict

            return [
                MockTool(
                    server='mock',
                    name='web_search',
                    description='Buscar en la web',
                    input_schema={'properties': {'query': {'type': 'string'}}, 'required': ['query']}
                ),
                MockTool(
                    server='mock',
                    name='calculator',
                    description='Realizar cálculos matemáticos',
                    input_schema={'properties': {'expression': {'type': 'string'}}}
                )
            ]

        def call_tool(self, server, tool_name, arguments):
            if tool_name == 'web_search':
                return {'content': [{'text': f"Resultados de búsqueda para: {arguments.get('query', '')}"}]}
            elif tool_name == 'calculator':
                expr = arguments.get('expression', '0')
                try:
                    result = eval(expr)
                    return {'content': [{'text': f"Resultado: {result}"}]}
                except Exception:
                    return {'content': [{'text': "Error en cálculo"}]}
            return {'content': [{'text': 'OK'}]}

    # Mock LLM
    class MockLLM:
        def __init__(self):
            self.call_count = 0

        def generate_simple(self, prompt, max_tokens=500):
            self.call_count += 1
            # Simular respuestas del agente
            if self.call_count == 1:
                return json.dumps({
                    "thought": "Necesito buscar información sobre Python",
                    "action": "web_search",
                    "action_input": {"query": "Python programming language"}
                })
            else:
                return json.dumps({
                    "thought": "Ya tengo información suficiente para responder",
                    "action": "ANSWER",
                    "action_input": {"response": "Python es un lenguaje de programación versátil y popular."}
                })

    # Crear agente
    mcp_client = MockMCPClient()
    llm = MockLLM()
    agent = MCPAgent(mcp_client, llm, max_iterations=3, verbose=True, enable_claudia=True)

    # Mostrar herramientas disponibles
    print("\n🔧 Herramientas disponibles:")
    for tool in agent.available_tools:
        print(f"   [{tool['server']}] {tool['name']}: {tool['description'][:50]}...")

    # Test básico
    print("\n--- Test 1: Búsqueda web ---")
    result = agent.execute("¿Qué es Python?")

    print(f"\n📊 Resultado:")
    print(f"   Respuesta: {result.response}")
    print(f"   Éxito: {result.success}")
    print(f"   Iteraciones: {result.total_iterations}")
    print(f"   Herramientas usadas: {result.tools_used}")

    # Test Claudia (si está disponible)
    if agent._claudia_available:
        print("\n--- Test 2: Claudia ---")
        llm.call_count = 0  # Reset

        class ClaudiaTestLLM:
            def __init__(self):
                self.call_count = 0

            def generate_simple(self, prompt, max_tokens=500):
                self.call_count += 1
                if self.call_count == 1:
                    return json.dumps({
                        "thought": "Voy a usar Claudia para analizar el código",
                        "action": "claudia",
                        "action_input": {"task": "explica qué es Python"}
                    })
                else:
                    return json.dumps({
                        "thought": "Ya tengo la explicación de Claudia",
                        "action": "ANSWER",
                        "action_input": {"response": "Según Claudia, Python es un lenguaje de programación."}
                    })

        agent2 = MCPAgent(mcp_client, ClaudiaTestLLM(), max_iterations=3, verbose=True, enable_claudia=True)
        result2 = agent2.execute("Usa Claudia para explicar Python")

        print(f"\n📊 Resultado Claudia:")
        print(f"   Respuesta: {result2.response[:200]}...")
        print(f"   Herramientas: {result2.tools_used}")
    else:
        print("\n⚠️ Claudia no disponible para test")
