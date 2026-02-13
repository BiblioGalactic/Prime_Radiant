#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    MCP CLIENT - Cliente MCP para Agentes
========================================
Cliente JSON-RPC para comunicarse con el servidor MCP.
Las 11 herramientas del servidor MCP + 4 herramientas Claudia.

v2.3 - Integración Claudia como herramientas MCP
"""

import os
import json
import subprocess
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCPClient")

# === IMPORTAR CLAUDIA ===
try:
    from agents.claudia_agent import ClaudiaAgent, ClaudiaResult, get_claudia_agent
    HAS_CLAUDIA = True
except ImportError:
    HAS_CLAUDIA = False
    logger.warning("⚠️ ClaudiaAgent no disponible")


@dataclass
class MCPTool:
    """Definición de herramienta MCP"""
    name: str
    description: str
    params: List[str]


class MCPClient:
    """
    Cliente para servidor MCP (Model Context Protocol).
    Comunicación via JSON-RPC stdin/stdout.
    """

    # Herramientas disponibles en el servidor MCP (11 core + 4 Claudia)
    AVAILABLE_TOOLS = [
        # === HERRAMIENTAS CORE (11) ===
        MCPTool("leer_archivo", "Lee contenido de un archivo (máx 64KB)", ["ruta"]),
        MCPTool("consultar_memoria", "Consulta recursos del sistema (RAM, CPU, disco)", []),
        MCPTool("ejecutar_comando", "Ejecuta un comando bash (bloqueados: rm, dd, sudo)", ["comando", "timeout"]),
        MCPTool("listar_directorio", "Lista contenido de un directorio", ["ruta", "mostrar_ocultos"]),
        MCPTool("buscar_archivos", "Busca archivos por patrón (glob) recursivamente", ["directorio", "patron", "max_resultados"]),
        MCPTool("consultar_api", "Hace petición HTTP a una API", ["url", "metodo", "headers", "body", "timeout"]),
        MCPTool("escribir_archivo", "Escribe contenido en un archivo (máx 10MB)", ["ruta", "contenido", "modo"]),
        MCPTool("descargar_archivo", "Descarga archivo desde URL (máx 10MB)", ["url", "ruta_destino"]),
        MCPTool("comprimir_descomprimir", "Comprime/descomprime archivos", ["operacion", "origen", "destino", "formato"]),
        MCPTool("git_operation", "Operaciones git (status, log, diff, branch, remote)", ["operacion", "repo_path", "args"]),
        MCPTool("buscar_en_contenido", "Busca texto dentro de archivos (grep)", ["directorio", "patron", "extension", "max_resultados"]),
        # === HERRAMIENTAS CLAUDIA (4) ===
        MCPTool("claudia_execute", "Ejecuta tarea de código con asistente IA local (Claudia)", ["task", "agentic"]),
        MCPTool("claudia_analyze_file", "Analiza archivo de código con Claudia", ["file_path", "question"]),
        MCPTool("claudia_analyze_project", "Análisis completo de proyecto con modo agéntico", ["project_path"]),
        MCPTool("claudia_run_command", "Ejecuta comando del sistema via Claudia", ["command", "working_dir"]),
    ]

    def __init__(self, mcp_server_path: str = None, timeout: int = 30):
        """
        Inicializar cliente MCP.

        Args:
            mcp_server_path: Ruta al script del servidor MCP
            timeout: Timeout para operaciones
        """
        self.mcp_server_path = mcp_server_path or self._find_mcp_server()
        self.timeout = timeout
        self._request_id = 0

    def _find_mcp_server(self) -> str:
        """Buscar el servidor MCP"""
        possible_paths = [
            os.path.expanduser("~/.mcp_local/mcp_server.py"),
            os.path.expanduser("~/proyecto/mcp_tool.py"),
            os.path.expanduser("~/wikirag/mcp_server.py"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return ""

    def _make_request(self, method: str, params: Dict = None) -> Dict[str, Any]:
        """
        Hacer request JSON-RPC al servidor MCP.

        Args:
            method: Método a llamar
            params: Parámetros del método

        Returns:
            Respuesta del servidor
        """
        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params or {}
        }

        if not self.mcp_server_path or not os.path.exists(self.mcp_server_path):
            return {"error": {"code": -1, "message": "Servidor MCP no encontrado"}}

        try:
            proc = subprocess.Popen(
                ["python3", self.mcp_server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = proc.communicate(
                json.dumps(request),
                timeout=self.timeout
            )

            # Parsear respuesta
            for line in stdout.strip().split('\n'):
                if line.startswith('{'):
                    return json.loads(line)

            return {"error": {"code": -2, "message": f"Sin respuesta válida: {stderr}"}}

        except subprocess.TimeoutExpired:
            proc.kill()
            return {"error": {"code": -3, "message": "Timeout"}}
        except Exception as e:
            return {"error": {"code": -4, "message": str(e)}}

    def list_tools(self) -> List[MCPTool]:
        """Listar herramientas disponibles"""
        response = self._make_request("tools/list")
        if "error" in response:
            return self.AVAILABLE_TOOLS  # Fallback a lista estática

        result = response.get("result", [])
        return [MCPTool(**t) if isinstance(t, dict) else t for t in result]

    def call(self, tool_name: str, **params) -> Dict[str, Any]:
        """
        Llamar a una herramienta MCP.

        Args:
            tool_name: Nombre de la herramienta
            **params: Parámetros de la herramienta

        Returns:
            Resultado de la herramienta
        """
        response = self._make_request(tool_name, params)

        if "error" in response:
            logger.error(f"Error MCP [{tool_name}]: {response['error']}")
            return {"error": response["error"]["message"]}

        return response.get("result", {})

    # === Métodos de conveniencia para cada herramienta ===

    def leer_archivo(self, ruta: str) -> str:
        """Leer contenido de un archivo"""
        result = self.call("leer_archivo", ruta=ruta)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("contenido", "")

    def consultar_memoria(self) -> Dict[str, Any]:
        """Consultar recursos del sistema"""
        return self.call("consultar_memoria")

    def ejecutar_comando(self, comando: str, timeout: int = 10) -> Dict[str, Any]:
        """Ejecutar comando bash"""
        return self.call("ejecutar_comando", comando=comando, timeout=timeout)

    def listar_directorio(self, ruta: str = "~", mostrar_ocultos: bool = False) -> Dict[str, Any]:
        """Listar directorio"""
        return self.call("listar_directorio", ruta=ruta, mostrar_ocultos=mostrar_ocultos)

    def buscar_archivos(
        self,
        directorio: str = "~",
        patron: str = "*",
        max_resultados: int = 50
    ) -> Dict[str, Any]:
        """Buscar archivos por patrón"""
        return self.call(
            "buscar_archivos",
            directorio=directorio,
            patron=patron,
            max_resultados=max_resultados
        )

    def consultar_api(
        self,
        url: str,
        metodo: str = "GET",
        headers: Dict = None,
        body: Any = None,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """Consultar API HTTP"""
        return self.call(
            "consultar_api",
            url=url,
            metodo=metodo,
            headers=headers,
            body=body,
            timeout=timeout
        )

    def escribir_archivo(
        self,
        ruta: str,
        contenido: str,
        modo: str = "w"
    ) -> Dict[str, Any]:
        """Escribir archivo"""
        return self.call(
            "escribir_archivo",
            ruta=ruta,
            contenido=contenido,
            modo=modo
        )

    def descargar_archivo(self, url: str, ruta_destino: str) -> Dict[str, Any]:
        """Descargar archivo desde URL"""
        return self.call(
            "descargar_archivo",
            url=url,
            ruta_destino=ruta_destino
        )

    def comprimir(
        self,
        origen: str,
        destino: str = None,
        formato: str = "zip"
    ) -> Dict[str, Any]:
        """Comprimir archivos"""
        return self.call(
            "comprimir_descomprimir",
            operacion="comprimir",
            origen=origen,
            destino=destino,
            formato=formato
        )

    def descomprimir(
        self,
        origen: str,
        destino: str = None,
        formato: str = "zip"
    ) -> Dict[str, Any]:
        """Descomprimir archivos"""
        return self.call(
            "comprimir_descomprimir",
            operacion="descomprimir",
            origen=origen,
            destino=destino,
            formato=formato
        )

    def git_status(self, repo_path: str = ".") -> str:
        """Git status"""
        result = self.call("git_operation", operacion="status", repo_path=repo_path)
        return result.get("stdout", str(result))

    def git_log(self, repo_path: str = ".") -> str:
        """Git log"""
        result = self.call("git_operation", operacion="log", repo_path=repo_path)
        return result.get("stdout", str(result))

    def git_diff(self, repo_path: str = ".") -> str:
        """Git diff"""
        result = self.call("git_operation", operacion="diff", repo_path=repo_path)
        return result.get("stdout", str(result))

    def grep(
        self,
        directorio: str = ".",
        patron: str = "",
        extension: str = None,
        max_resultados: int = 50
    ) -> Dict[str, Any]:
        """Buscar texto en archivos"""
        return self.call(
            "buscar_en_contenido",
            directorio=directorio,
            patron=patron,
            extension=extension,
            max_resultados=max_resultados
        )

    # === MÉTODOS CLAUDIA (4 herramientas) ===

    def claudia_execute(self, task: str, agentic: bool = False) -> Dict[str, Any]:
        """
        Ejecutar tarea con Claudia (asistente de código IA).

        Args:
            task: Tarea a ejecutar (ej: "analiza main.py")
            agentic: Usar modo agéntico (planificar → ejecutar → sintetizar)

        Returns:
            Dict con success, response, mode, error
        """
        if not HAS_CLAUDIA:
            return {"error": "Claudia no disponible", "success": False}

        try:
            agent = get_claudia_agent()
            if not agent.is_available:
                return {"error": "Claudia no encontrada en el sistema", "success": False}

            result = agent.execute(task, agentic=agentic)
            return {
                "success": result.success,
                "response": result.response,
                "mode": result.mode,
                "error": result.error
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def claudia_analyze_file(self, file_path: str, question: str = None) -> Dict[str, Any]:
        """
        Analizar archivo de código con Claudia.

        Args:
            file_path: Ruta al archivo
            question: Pregunta específica sobre el archivo

        Returns:
            Dict con análisis
        """
        if not HAS_CLAUDIA:
            return {"error": "Claudia no disponible", "success": False}

        try:
            agent = get_claudia_agent()
            if not agent.is_available:
                return {"error": "Claudia no encontrada", "success": False}

            result = agent.analyze_file(file_path, question)
            return {
                "success": result.success,
                "response": result.response,
                "mode": result.mode,
                "error": result.error
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def claudia_analyze_project(self, project_path: str = None) -> Dict[str, Any]:
        """
        Análisis completo de proyecto con modo agéntico.

        Args:
            project_path: Ruta al proyecto (default: directorio actual)

        Returns:
            Dict con análisis completo
        """
        if not HAS_CLAUDIA:
            return {"error": "Claudia no disponible", "success": False}

        try:
            agent = get_claudia_agent()
            if not agent.is_available:
                return {"error": "Claudia no encontrada", "success": False}

            result = agent.analyze_project(project_path)
            return {
                "success": result.success,
                "response": result.response,
                "mode": result.mode,
                "error": result.error
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def claudia_run_command(self, command: str, working_dir: str = None) -> Dict[str, Any]:
        """
        Ejecutar comando del sistema via Claudia.

        Args:
            command: Comando a ejecutar
            working_dir: Directorio de trabajo

        Returns:
            Dict con resultado
        """
        if not HAS_CLAUDIA:
            return {"error": "Claudia no disponible", "success": False}

        try:
            agent = get_claudia_agent()
            if not agent.is_available:
                return {"error": "Claudia no encontrada", "success": False}

            result = agent.run_command(command, working_dir)
            return {
                "success": result.success,
                "response": result.response,
                "mode": result.mode,
                "error": result.error
            }
        except Exception as e:
            return {"error": str(e), "success": False}


class MCPToolWrapper:
    """
    Wrapper que convierte herramientas MCP en Tool objects para agentes.
    Incluye 11 herramientas core + 4 herramientas Claudia.
    """

    def __init__(self, client: MCPClient = None):
        self.client = client or MCPClient()

    def get_tools(self) -> List['Tool']:
        """Obtener herramientas como objetos Tool para agentes"""
        from agents.base_agent import Tool

        tools = []

        # === HERRAMIENTAS CORE ===

        # leer_archivo
        tools.append(Tool(
            name="leer_archivo",
            description="Lee contenido de un archivo",
            parameters=["ruta"],
            handler=lambda ruta: self.client.leer_archivo(ruta)
        ))

        # consultar_memoria
        tools.append(Tool(
            name="memoria",
            description="Consulta recursos del sistema",
            parameters=[],
            handler=lambda: json.dumps(self.client.consultar_memoria())
        ))

        # ejecutar_comando
        tools.append(Tool(
            name="bash",
            description="Ejecuta comando bash",
            parameters=["comando"],
            handler=lambda cmd: json.dumps(self.client.ejecutar_comando(cmd))
        ))

        # buscar_archivos
        tools.append(Tool(
            name="buscar",
            description="Busca archivos por patrón",
            parameters=["patron"],
            handler=lambda patron: json.dumps(self.client.buscar_archivos(patron=patron))
        ))

        # consultar_api
        tools.append(Tool(
            name="api",
            description="Consulta API HTTP",
            parameters=["url"],
            handler=lambda url: json.dumps(self.client.consultar_api(url))
        ))

        # grep
        tools.append(Tool(
            name="grep",
            description="Busca texto en archivos",
            parameters=["patron"],
            handler=lambda patron: json.dumps(self.client.grep(patron=patron))
        ))

        # === HERRAMIENTAS CLAUDIA (4) ===

        # claudia_execute - Tarea general
        tools.append(Tool(
            name="claudia",
            description="Ejecuta tarea de código con asistente IA local (Claudia). Útil para análisis de código, debugging, refactoring.",
            parameters=["task"],
            handler=lambda task: json.dumps(self.client.claudia_execute(task))
        ))

        # claudia_analyze_file - Analizar archivo
        tools.append(Tool(
            name="claudia_analyze",
            description="Analiza archivo de código con Claudia. Proporciona explicación detallada del código.",
            parameters=["file_path", "question"],
            handler=lambda file_path, question=None: json.dumps(
                self.client.claudia_analyze_file(file_path, question)
            )
        ))

        # claudia_analyze_project - Análisis completo
        tools.append(Tool(
            name="claudia_project",
            description="Análisis completo de proyecto con modo agéntico. Examina arquitectura, dependencias, código.",
            parameters=["project_path"],
            handler=lambda project_path=None: json.dumps(
                self.client.claudia_analyze_project(project_path)
            )
        ))

        # claudia_run_command - Ejecutar comando
        tools.append(Tool(
            name="claudia_cmd",
            description="Ejecuta comando del sistema via Claudia con contexto de IA.",
            parameters=["command", "working_dir"],
            handler=lambda command, working_dir=None: json.dumps(
                self.client.claudia_run_command(command, working_dir)
            )
        ))

        return tools

    def get_claudia_tools(self) -> List['Tool']:
        """Obtener solo herramientas Claudia"""
        from agents.base_agent import Tool

        if not HAS_CLAUDIA:
            return []

        return [
            Tool(
                name="claudia",
                description="Ejecuta tarea de código con asistente IA local",
                parameters=["task"],
                handler=lambda task: json.dumps(self.client.claudia_execute(task))
            ),
            Tool(
                name="claudia_analyze",
                description="Analiza archivo de código",
                parameters=["file_path", "question"],
                handler=lambda file_path, question=None: json.dumps(
                    self.client.claudia_analyze_file(file_path, question)
                )
            ),
            Tool(
                name="claudia_project",
                description="Análisis completo de proyecto (modo agéntico)",
                parameters=["project_path"],
                handler=lambda project_path=None: json.dumps(
                    self.client.claudia_analyze_project(project_path)
                )
            ),
            Tool(
                name="claudia_cmd",
                description="Ejecuta comando via Claudia",
                parameters=["command", "working_dir"],
                handler=lambda command, working_dir=None: json.dumps(
                    self.client.claudia_run_command(command, working_dir)
                )
            ),
        ]

    def is_claudia_available(self) -> bool:
        """Verificar si Claudia está disponible"""
        if not HAS_CLAUDIA:
            return False
        try:
            agent = get_claudia_agent()
            return agent.is_available
        except:
            return False


# === CLI para pruebas ===
if __name__ == "__main__":
    import sys

    client = MCPClient()

    if len(sys.argv) < 2:
        print("Uso: mcp_client.py [tools|memoria|ls|cat|grep] [args]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "tools":
        print("🔧 Herramientas MCP disponibles:")
        for tool in client.list_tools():
            print(f"  - {tool.name}: {tool.description}")

    elif cmd == "memoria":
        result = client.consultar_memoria()
        print("💻 Estado del sistema:")
        for k, v in result.items():
            print(f"  {k}: {v}")

    elif cmd == "ls":
        ruta = sys.argv[2] if len(sys.argv) > 2 else "~"
        result = client.listar_directorio(ruta)
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"📁 Contenido de {result.get('ruta', ruta)}:")
            for item in result.get("items", [])[:20]:
                tipo = "📁" if item["tipo"] == "directorio" else "📄"
                print(f"  {tipo} {item['nombre']}")

    elif cmd == "cat":
        if len(sys.argv) < 3:
            print("Uso: mcp_client.py cat <archivo>")
            sys.exit(1)
        contenido = client.leer_archivo(sys.argv[2])
        print(contenido[:2000])

    elif cmd == "grep":
        if len(sys.argv) < 3:
            print("Uso: mcp_client.py grep <patron>")
            sys.exit(1)
        result = client.grep(patron=sys.argv[2])
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"🔍 Resultados ({result.get('total_encontrado', 0)}):")
            for r in result.get("resultados", [])[:10]:
                print(f"  {r['archivo']}:{r['linea']}")
                print(f"    {r['contenido'][:80]}")

    else:
        print(f"Comando desconocido: {cmd}")
