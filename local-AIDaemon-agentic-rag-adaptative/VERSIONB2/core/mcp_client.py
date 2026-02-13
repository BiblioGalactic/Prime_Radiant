#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
🔌 MCP CLIENT - Model Context Protocol
========================================
Cliente MCP para conectar con servidores de herramientas externos.

MCP (Model Context Protocol) es el protocolo estándar de Anthropic
para que modelos de IA usen herramientas externas de forma segura.

Servidores MCP disponibles:
- @modelcontextprotocol/server-brave-search (búsqueda web)
- @modelcontextprotocol/server-filesystem (acceso a archivos)
- @modelcontextprotocol/server-github (GitHub API)
- @modelcontextprotocol/server-slack (Slack API)
- @modelcontextprotocol/server-puppeteer (navegador)

Uso:
    client = MCPClient({
        'web_search': {
            'command': 'npx',
            'args': ['-y', '@modelcontextprotocol/server-brave-search'],
            'env': {'BRAVE_API_KEY': 'xxx'}
        }
    })

    tools = client.list_tools('web_search')
    result = client.call_tool('web_search', 'brave_web_search', {'query': 'Python'})
"""

import os
import sys
import json
import subprocess
import threading
import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCPClient")


@dataclass
class MCPTool:
    """Descripción de una herramienta MCP"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server: str


@dataclass
class MCPServer:
    """Estado de un servidor MCP"""
    name: str
    process: Optional[subprocess.Popen] = None
    tools: List[MCPTool] = field(default_factory=list)
    is_ready: bool = False
    error: Optional[str] = None


class MCPClient:
    """
    Cliente para comunicarse con servidores MCP via stdio (JSON-RPC 2.0).

    El protocolo MCP usa JSON-RPC 2.0 sobre stdin/stdout:
    - Cliente → Servidor: request JSON en stdin
    - Servidor → Cliente: response JSON en stdout

    Métodos principales:
    - initialize: Iniciar handshake con servidor
    - tools/list: Listar herramientas disponibles
    - tools/call: Ejecutar una herramienta
    """

    # Timeout para operaciones MCP
    DEFAULT_TIMEOUT = 30

    def __init__(self, server_configs: Dict[str, Dict] = None, auto_start: bool = True):
        """
        Inicializar cliente MCP.

        Args:
            server_configs: Configuración de servidores
                {
                    'nombre_servidor': {
                        'command': 'npx',
                        'args': ['-y', '@modelcontextprotocol/server-xxx'],
                        'env': {'API_KEY': 'xxx'}  # opcional
                    }
                }
            auto_start: Si iniciar servidores automáticamente
        """
        self.servers: Dict[str, MCPServer] = {}
        self._request_id = 0
        self._lock = threading.Lock()

        if server_configs and auto_start:
            self.start_servers(server_configs)

    def _next_id(self) -> int:
        """Generar ID único para request"""
        with self._lock:
            self._request_id += 1
            return self._request_id

    def start_servers(self, configs: Dict[str, Dict]):
        """
        Iniciar múltiples servidores MCP.

        Args:
            configs: Diccionario de configuraciones
        """
        for name, config in configs.items():
            try:
                self.start_server(name, config)
            except Exception as e:
                logger.error(f"❌ Error iniciando servidor '{name}': {e}")

    def start_server(self, name: str, config: Dict) -> bool:
        """
        Iniciar un servidor MCP individual.

        Args:
            name: Nombre identificador del servidor
            config: Configuración del servidor

        Returns:
            True si se inició correctamente
        """
        if name in self.servers and self.servers[name].is_ready:
            logger.warning(f"⚠️ Servidor '{name}' ya está corriendo")
            return True

        command = config.get('command', 'npx')
        args = config.get('args', [])
        env_extra = config.get('env', {})

        # Preparar entorno
        env = os.environ.copy()
        env.update(env_extra)

        # Comando completo
        cmd = [command] + args

        logger.info(f"🚀 Iniciando servidor MCP '{name}': {' '.join(cmd[:3])}...")

        try:
            # Iniciar proceso
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                bufsize=0  # Sin buffer para comunicación inmediata
            )

            server = MCPServer(name=name, process=process)
            self.servers[name] = server

            # Esperar un momento para que inicie
            time.sleep(0.5)

            # Verificar que está vivo
            if process.poll() is not None:
                stderr = process.stderr.read().decode() if process.stderr else ""
                server.error = f"Proceso terminó prematuramente: {stderr[:200]}"
                logger.error(f"❌ {server.error}")
                return False

            # Inicializar protocolo MCP
            if self._initialize_server(name):
                server.is_ready = True
                # Descubrir herramientas
                server.tools = self._discover_tools(name)
                logger.info(f"✅ Servidor '{name}' listo con {len(server.tools)} herramientas")
                return True
            else:
                server.error = "Falló inicialización MCP"
                return False

        except FileNotFoundError as e:
            error_msg = f"Comando no encontrado: {command}. ¿Está instalado npx/node?"
            logger.error(f"❌ {error_msg}")
            self.servers[name] = MCPServer(name=name, error=error_msg)
            return False
        except Exception as e:
            logger.error(f"❌ Error iniciando servidor '{name}': {e}")
            self.servers[name] = MCPServer(name=name, error=str(e))
            return False

    def _initialize_server(self, server_name: str) -> bool:
        """
        Realizar handshake de inicialización con servidor MCP.

        Según el protocolo MCP, el cliente debe enviar 'initialize'
        y el servidor responde con sus capacidades.
        """
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True}
                },
                "clientInfo": {
                    "name": "WikiRAG-MCP-Client",
                    "version": "1.0.0"
                }
            },
            "id": self._next_id()
        }

        response = self._send_request(server_name, request)

        if response and 'result' in response:
            logger.debug(f"MCP initialize OK: {response['result'].get('serverInfo', {})}")

            # Enviar 'initialized' notification
            notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            self._send_notification(server_name, notification)

            return True

        return False

    def _discover_tools(self, server_name: str) -> List[MCPTool]:
        """
        Descubrir herramientas disponibles en un servidor.
        """
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": self._next_id()
        }

        response = self._send_request(server_name, request)

        tools = []
        if response and 'result' in response:
            for tool_data in response['result'].get('tools', []):
                tools.append(MCPTool(
                    name=tool_data.get('name', ''),
                    description=tool_data.get('description', ''),
                    input_schema=tool_data.get('inputSchema', {}),
                    server=server_name
                ))

        return tools

    def _send_request(self, server_name: str, request: Dict, timeout: float = None) -> Optional[Dict]:
        """
        Enviar request JSON-RPC y esperar respuesta.

        Args:
            server_name: Nombre del servidor
            request: Request JSON-RPC
            timeout: Timeout en segundos

        Returns:
            Response JSON-RPC o None si error
        """
        timeout = timeout or self.DEFAULT_TIMEOUT

        if server_name not in self.servers:
            logger.error(f"❌ Servidor '{server_name}' no existe")
            return None

        server = self.servers[server_name]
        if not server.process or server.process.poll() is not None:
            logger.error(f"❌ Servidor '{server_name}' no está corriendo")
            return None

        try:
            # Serializar y enviar
            request_bytes = (json.dumps(request) + '\n').encode('utf-8')
            server.process.stdin.write(request_bytes)
            server.process.stdin.flush()

            # Leer respuesta con timeout
            import select
            ready, _, _ = select.select([server.process.stdout], [], [], timeout)

            if not ready:
                logger.warning(f"⚠️ Timeout esperando respuesta de '{server_name}'")
                return None

            response_line = server.process.stdout.readline()
            if not response_line:
                logger.warning(f"⚠️ Respuesta vacía de '{server_name}'")
                return None

            response = json.loads(response_line.decode('utf-8'))

            if 'error' in response:
                logger.error(f"❌ Error MCP: {response['error']}")

            return response

        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando respuesta JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error en comunicación MCP: {e}")
            return None

    def _send_notification(self, server_name: str, notification: Dict):
        """Enviar notificación (sin esperar respuesta)"""
        if server_name not in self.servers:
            return

        server = self.servers[server_name]
        if not server.process or server.process.poll() is not None:
            return

        try:
            notification_bytes = (json.dumps(notification) + '\n').encode('utf-8')
            server.process.stdin.write(notification_bytes)
            server.process.stdin.flush()
        except Exception as e:
            logger.warning(f"⚠️ Error enviando notificación: {e}")

    def list_tools(self, server_name: str = None) -> List[MCPTool]:
        """
        Listar herramientas disponibles.

        Args:
            server_name: Nombre del servidor (None = todos)

        Returns:
            Lista de MCPTool
        """
        if server_name:
            if server_name in self.servers:
                return self.servers[server_name].tools
            return []

        # Todos los servidores
        all_tools = []
        for server in self.servers.values():
            all_tools.extend(server.tools)
        return all_tools

    def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: float = None
    ) -> Dict[str, Any]:
        """
        Ejecutar una herramienta MCP.

        Args:
            server_name: Nombre del servidor
            tool_name: Nombre de la herramienta
            arguments: Argumentos para la herramienta
            timeout: Timeout en segundos

        Returns:
            Resultado de la herramienta
        """
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": self._next_id()
        }

        logger.info(f"🔧 Llamando {server_name}/{tool_name}...")

        response = self._send_request(server_name, request, timeout=timeout)

        if response and 'result' in response:
            return response['result']
        elif response and 'error' in response:
            raise MCPError(
                code=response['error'].get('code', -1),
                message=response['error'].get('message', 'Unknown error')
            )
        else:
            raise MCPError(code=-1, message="No response from server")

    def get_server_status(self) -> Dict[str, Dict]:
        """Obtener estado de todos los servidores"""
        status = {}
        for name, server in self.servers.items():
            status[name] = {
                'is_ready': server.is_ready,
                'tools_count': len(server.tools),
                'error': server.error,
                'pid': server.process.pid if server.process else None,
                'alive': server.process.poll() is None if server.process else False
            }
        return status

    def stop_server(self, server_name: str):
        """Detener un servidor MCP"""
        if server_name not in self.servers:
            return

        server = self.servers[server_name]
        if server.process:
            try:
                server.process.terminate()
                server.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.process.kill()
            except Exception:
                pass

        server.is_ready = False
        logger.info(f"🛑 Servidor '{server_name}' detenido")

    def stop_all(self):
        """Detener todos los servidores"""
        for name in list(self.servers.keys()):
            self.stop_server(name)

    def __del__(self):
        """Cleanup al destruir objeto"""
        try:
            self.stop_all()
        except Exception:
            pass


class MCPError(Exception):
    """Error de protocolo MCP"""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"MCP Error {code}: {message}")


# === CONFIGURACIONES PREDEFINIDAS ===

def get_default_configs() -> Dict[str, Dict]:
    """
    Configuraciones predefinidas para servidores MCP comunes.

    Requiere:
    - Node.js instalado
    - npx disponible
    - API keys configuradas en variables de entorno
    """
    return {
        'brave_search': {
            'command': 'npx',
            'args': ['-y', '@modelcontextprotocol/server-brave-search'],
            'env': {'BRAVE_API_KEY': os.getenv('BRAVE_API_KEY', '')}
        },
        'filesystem': {
            'command': 'npx',
            'args': [
                '-y',
                '@modelcontextprotocol/server-filesystem',
                str(Path.home())  # Acceso al home del usuario
            ],
            'env': {}
        },
        'github': {
            'command': 'npx',
            'args': ['-y', '@modelcontextprotocol/server-github'],
            'env': {'GITHUB_PERSONAL_ACCESS_TOKEN': os.getenv('GITHUB_TOKEN', '')}
        }
    }


def create_mcp_client_with_defaults(
    servers: List[str] = None,
    custom_configs: Dict[str, Dict] = None
) -> MCPClient:
    """
    Crear cliente MCP con configuraciones predefinidas.

    Args:
        servers: Lista de servidores a iniciar ['brave_search', 'filesystem']
        custom_configs: Configuraciones personalizadas adicionales

    Returns:
        MCPClient configurado
    """
    default_configs = get_default_configs()

    # Filtrar solo los servidores solicitados
    if servers:
        configs = {k: v for k, v in default_configs.items() if k in servers}
    else:
        configs = {}

    # Agregar configuraciones personalizadas
    if custom_configs:
        configs.update(custom_configs)

    return MCPClient(configs, auto_start=True)


# === TEST ===
if __name__ == "__main__":
    print("🔌 Test de MCP Client")
    print("=" * 50)

    # Verificar si npx está disponible
    try:
        result = subprocess.run(['npx', '--version'], capture_output=True, text=True)
        print(f"✅ npx version: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ npx no encontrado. Instalar Node.js primero.")
        print("   brew install node")
        sys.exit(1)

    # Test con filesystem server (no requiere API key)
    print("\n📂 Probando servidor filesystem...")

    client = MCPClient({
        'filesystem': {
            'command': 'npx',
            'args': ['-y', '@modelcontextprotocol/server-filesystem', '/tmp'],
            'env': {}
        }
    })

    status = client.get_server_status()
    print(f"\n📊 Estado de servidores:")
    for name, info in status.items():
        ready = "✅" if info['is_ready'] else "❌"
        print(f"   {ready} {name}: {info['tools_count']} herramientas")
        if info['error']:
            print(f"      Error: {info['error']}")

    # Listar herramientas
    tools = client.list_tools()
    if tools:
        print(f"\n🔧 Herramientas disponibles:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description[:60]}...")

    # Cleanup
    client.stop_all()
    print("\n✅ Test completado")
