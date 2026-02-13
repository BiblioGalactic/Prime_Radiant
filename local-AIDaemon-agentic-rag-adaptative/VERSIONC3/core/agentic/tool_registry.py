#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    TOOL REGISTRY - Registro de Herramientas
========================================
Define herramientas con JSON Schema para function calling.
Compatible con Mistral, Qwen, Llama, y otros modelos.
========================================
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger("ToolRegistry")


@dataclass
class ToolParameter:
    """Parámetro de una herramienta"""
    name: str
    type: str  # string, integer, boolean, array, object
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None


@dataclass
class ToolResult:
    """Resultado de ejecutar una herramienta"""
    success: bool
    output: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Tool:
    """
    Definición de una herramienta.

    Compatible con el formato de function calling de OpenAI/Anthropic/Mistral.
    """
    name: str
    description: str
    parameters: List[ToolParameter]
    handler: Callable[..., ToolResult]
    category: str = "general"
    requires_confirmation: bool = False
    dangerous: bool = False

    def to_json_schema(self) -> Dict[str, Any]:
        """Convertir a JSON Schema para function calling"""
        properties = {}
        required = []

        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default

            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    def to_prompt_description(self) -> str:
        """Generar descripción para incluir en prompt"""
        params_desc = []
        for p in self.parameters:
            req = "(required)" if p.required else "(optional)"
            params_desc.append(f"    - {p.name} ({p.type}) {req}: {p.description}")

        params_str = "\n".join(params_desc) if params_desc else "    (sin parámetros)"

        return f"""### {self.name}
**Descripción**: {self.description}
**Categoría**: {self.category}
**Parámetros**:
{params_str}
"""


class ToolRegistry:
    """
    Registro central de herramientas disponibles.

    Uso:
        registry = ToolRegistry()
        registry.register_defaults()  # Registrar herramientas built-in

        # Ejecutar herramienta
        result = registry.execute("filesystem_list", {"path": "~/proyecto"})
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(self, tool: Tool):
        """Registrar una herramienta"""
        self._tools[tool.name] = tool

        # Agregar a categoría
        if tool.category not in self._categories:
            self._categories[tool.category] = []
        self._categories[tool.category].append(tool.name)

        logger.debug(f"Herramienta registrada: {tool.name}")

    def get(self, name: str) -> Optional[Tool]:
        """Obtener herramienta por nombre"""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """Listar nombres de herramientas"""
        return list(self._tools.keys())

    def list_by_category(self, category: str) -> List[str]:
        """Listar herramientas por categoría"""
        return self._categories.get(category, [])

    def get_categories(self) -> List[str]:
        """Obtener lista de categorías"""
        return list(self._categories.keys())

    def execute(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Ejecutar una herramienta.

        Args:
            name: Nombre de la herramienta
            params: Parámetros

        Returns:
            ToolResult con el resultado
        """
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(
                success=False,
                output="",
                error=f"Herramienta no encontrada: {name}"
            )

        try:
            # Validar parámetros requeridos
            for param in tool.parameters:
                if param.required and param.name not in params:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"Parámetro requerido faltante: {param.name}"
                    )

            # Ejecutar handler
            result = tool.handler(**params)
            return result

        except Exception as e:
            logger.error(f"Error ejecutando {name}: {e}")
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )

    def to_json_schema_list(self) -> List[Dict[str, Any]]:
        """Exportar todas las herramientas como JSON Schema"""
        return [tool.to_json_schema() for tool in self._tools.values()]

    def to_prompt_text(self) -> str:
        """Generar texto de herramientas para incluir en prompt"""
        sections = []

        for category in sorted(self._categories.keys()):
            tool_names = self._categories[category]
            tools_text = []

            for name in tool_names:
                tool = self._tools[name]
                tools_text.append(tool.to_prompt_description())

            sections.append(f"## {category.upper()}\n\n" + "\n".join(tools_text))

        return "\n\n".join(sections)

    def register_defaults(self):
        """Registrar herramientas built-in"""
        # === FILESYSTEM ===
        self.register(Tool(
            name="filesystem_list",
            description="Lista archivos y directorios en una ruta. Muestra permisos, tamaño y fechas.",
            category="filesystem",
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Ruta del directorio a listar. Soporta ~ para home.",
                    required=True
                ),
                ToolParameter(
                    name="show_hidden",
                    type="boolean",
                    description="Mostrar archivos ocultos (empiezan con .)",
                    required=False,
                    default=True
                )
            ],
            handler=self._handle_filesystem_list
        ))

        self.register(Tool(
            name="filesystem_read",
            description="Lee el contenido de un archivo de texto. Ideal para código, configs, logs.",
            category="filesystem",
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Ruta del archivo a leer",
                    required=True
                ),
                ToolParameter(
                    name="max_lines",
                    type="integer",
                    description="Número máximo de líneas a leer (0 = todas)",
                    required=False,
                    default=500
                )
            ],
            handler=self._handle_filesystem_read
        ))

        self.register(Tool(
            name="filesystem_write",
            description="Escribe contenido a un archivo. CUIDADO: Sobrescribe si existe.",
            category="filesystem",
            dangerous=True,
            requires_confirmation=True,
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Ruta del archivo a escribir",
                    required=True
                ),
                ToolParameter(
                    name="content",
                    type="string",
                    description="Contenido a escribir",
                    required=True
                )
            ],
            handler=self._handle_filesystem_write
        ))

        self.register(Tool(
            name="filesystem_search",
            description="Busca archivos por nombre o patrón en un directorio.",
            category="filesystem",
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Directorio donde buscar",
                    required=True
                ),
                ToolParameter(
                    name="pattern",
                    type="string",
                    description="Patrón de búsqueda (ej: *.py, config*, etc.)",
                    required=True
                ),
                ToolParameter(
                    name="max_depth",
                    type="integer",
                    description="Profundidad máxima de búsqueda",
                    required=False,
                    default=3
                )
            ],
            handler=self._handle_filesystem_search
        ))

        # === BASH ===
        self.register(Tool(
            name="bash_execute",
            description="Ejecuta un comando bash. Útil para git, npm, pip, etc. NO usar para operaciones de archivos simples.",
            category="bash",
            dangerous=True,
            parameters=[
                ToolParameter(
                    name="command",
                    type="string",
                    description="Comando a ejecutar",
                    required=True
                ),
                ToolParameter(
                    name="timeout",
                    type="integer",
                    description="Timeout en segundos",
                    required=False,
                    default=30
                ),
                ToolParameter(
                    name="cwd",
                    type="string",
                    description="Directorio de trabajo",
                    required=False
                )
            ],
            handler=self._handle_bash_execute
        ))

        # === GIT ===
        self.register(Tool(
            name="git_status",
            description="Muestra el estado del repositorio git (archivos modificados, staged, etc.)",
            category="git",
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Ruta del repositorio",
                    required=False,
                    default="."
                )
            ],
            handler=self._handle_git_status
        ))

        self.register(Tool(
            name="git_log",
            description="Muestra historial de commits recientes",
            category="git",
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Ruta del repositorio",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="count",
                    type="integer",
                    description="Número de commits a mostrar",
                    required=False,
                    default=10
                )
            ],
            handler=self._handle_git_log
        ))

        self.register(Tool(
            name="git_diff",
            description="Muestra diferencias en archivos modificados",
            category="git",
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Ruta del repositorio",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="staged",
                    type="boolean",
                    description="Mostrar solo cambios staged",
                    required=False,
                    default=False
                )
            ],
            handler=self._handle_git_diff
        ))

        # === SEARCH ===
        self.register(Tool(
            name="grep_search",
            description="Busca texto dentro de archivos usando patrones regex",
            category="search",
            parameters=[
                ToolParameter(
                    name="pattern",
                    type="string",
                    description="Patrón de búsqueda (regex)",
                    required=True
                ),
                ToolParameter(
                    name="path",
                    type="string",
                    description="Directorio o archivo donde buscar",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="file_pattern",
                    type="string",
                    description="Patrón de archivos (ej: *.py)",
                    required=False
                ),
                ToolParameter(
                    name="context_lines",
                    type="integer",
                    description="Líneas de contexto alrededor del match",
                    required=False,
                    default=2
                )
            ],
            handler=self._handle_grep_search
        ))

        # === PYTHON ===
        self.register(Tool(
            name="python_execute",
            description="Ejecuta código Python y devuelve el resultado. Útil para cálculos, procesamiento de datos.",
            category="python",
            parameters=[
                ToolParameter(
                    name="code",
                    type="string",
                    description="Código Python a ejecutar",
                    required=True
                )
            ],
            handler=self._handle_python_execute
        ))

        # === RAG SEARCH ===
        self.register(Tool(
            name="rag_search",
            description="Busca información en las bases de conocimiento RAG (Wikipedia, éxitos, fallos, agentes).",
            category="rag",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Consulta de búsqueda semántica",
                    required=True
                ),
                ToolParameter(
                    name="rag_name",
                    type="string",
                    description="Nombre del RAG: wikipedia, exitos, fallos, agentes (default: wikipedia)",
                    required=False,
                    default="wikipedia",
                    enum=["wikipedia", "exitos", "fallos", "agentes", "all"]
                ),
                ToolParameter(
                    name="top_k",
                    type="integer",
                    description="Número de resultados a devolver",
                    required=False,
                    default=5
                )
            ],
            handler=self._handle_rag_search
        ))

        logger.info(f"✅ {len(self._tools)} herramientas registradas")

    # === HANDLERS ===

    def _handle_filesystem_list(self, path: str, show_hidden: bool = True) -> ToolResult:
        """Handler para filesystem_list"""
        try:
            path = os.path.expanduser(path)

            if not os.path.exists(path):
                return ToolResult(False, "", f"Ruta no existe: {path}")

            if not os.path.isdir(path):
                return ToolResult(False, "", f"No es un directorio: {path}")

            cmd = ["ls", "-la" if show_hidden else "-l", path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return ToolResult(True, result.stdout, metadata={"path": path})
            else:
                return ToolResult(False, "", result.stderr)

        except Exception as e:
            return ToolResult(False, "", str(e))

    def _handle_filesystem_read(self, path: str, max_lines: int = 500) -> ToolResult:
        """Handler para filesystem_read"""
        try:
            path = os.path.expanduser(path)

            if not os.path.exists(path):
                return ToolResult(False, "", f"Archivo no existe: {path}")

            if not os.path.isfile(path):
                return ToolResult(False, "", f"No es un archivo: {path}")

            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                if max_lines > 0:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            lines.append(f"\n... (truncado a {max_lines} líneas)")
                            break
                        lines.append(line)
                    content = ''.join(lines)
                else:
                    content = f.read()

            return ToolResult(
                True,
                content,
                metadata={"path": path, "lines": len(content.splitlines())}
            )

        except Exception as e:
            return ToolResult(False, "", str(e))

    def _handle_filesystem_write(self, path: str, content: str) -> ToolResult:
        """Handler para filesystem_write"""
        try:
            path = os.path.expanduser(path)

            # Crear directorio si no existe
            parent = os.path.dirname(path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            return ToolResult(
                True,
                f"Archivo escrito: {path} ({len(content)} bytes)",
                metadata={"path": path, "size": len(content)}
            )

        except Exception as e:
            return ToolResult(False, "", str(e))

    def _handle_filesystem_search(self, path: str, pattern: str, max_depth: int = 3) -> ToolResult:
        """Handler para filesystem_search"""
        try:
            path = os.path.expanduser(path)

            cmd = ["find", path, "-maxdepth", str(max_depth), "-name", pattern]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

            if result.returncode == 0:
                files = [f for f in result.stdout.strip().split('\n') if f]
                return ToolResult(
                    True,
                    result.stdout,
                    metadata={"count": len(files), "pattern": pattern}
                )
            else:
                return ToolResult(False, "", result.stderr)

        except Exception as e:
            return ToolResult(False, "", str(e))

    # FIX: Lista de comandos/patrones peligrosos a bloquear
    DANGEROUS_PATTERNS = [
        "rm -rf /",
        "rm -rf ~",
        "rm -rf *",
        "mkfs",
        ":(){:|:&};:",  # Fork bomb
        "dd if=",
        "> /dev/sda",
        "chmod -R 777 /",
        "wget * | sh",
        "curl * | sh",
        "sudo rm",
        "sudo dd",
    ]

    def _is_command_safe(self, command: str) -> tuple:
        """
        Verificar si un comando es seguro de ejecutar.

        Returns:
            (is_safe, reason)
        """
        command_lower = command.lower().strip()

        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in command_lower:
                return False, f"Comando peligroso detectado: {pattern}"

        # Verificar caracteres de inyección
        if "$((" in command or "$()" in command:
            # Permitir sustitución normal pero alertar
            logger.debug(f"Comando con sustitución: {command[:50]}")

        return True, ""

    def _handle_bash_execute(self, command: str, timeout: int = 30, cwd: str = None) -> ToolResult:
        """Handler para bash_execute (con validación de seguridad)"""
        try:
            # FIX: Validar comando antes de ejecutar
            is_safe, reason = self._is_command_safe(command)
            if not is_safe:
                logger.warning(f"Comando bloqueado: {reason}")
                return ToolResult(
                    False,
                    "",
                    f"Comando bloqueado por seguridad: {reason}"
                )

            if cwd:
                cwd = os.path.expanduser(cwd)
                # FIX: Verificar que el directorio existe
                if not os.path.isdir(cwd):
                    return ToolResult(False, "", f"Directorio no existe: {cwd}")

            # FIX: Limitar timeout máximo
            timeout = min(timeout, 120)  # Máximo 2 minutos

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )

            output = result.stdout
            if result.stderr:
                output += f"\n[STDERR]:\n{result.stderr}"

            # FIX: Truncar output muy largo
            max_output = 50000
            if len(output) > max_output:
                output = output[:max_output] + f"\n... (truncado, {len(output)} chars total)"

            return ToolResult(
                result.returncode == 0,
                output,
                error=result.stderr if result.returncode != 0 else None,
                metadata={"returncode": result.returncode, "command": command[:100]}
            )

        except subprocess.TimeoutExpired:
            return ToolResult(False, "", f"Timeout después de {timeout}s")
        except PermissionError:
            return ToolResult(False, "", "Permiso denegado")
        except FileNotFoundError as e:
            return ToolResult(False, "", f"Comando o archivo no encontrado: {e}")
        except Exception as e:
            logger.error(f"Error en bash_execute: {e}")
            return ToolResult(False, "", str(e))

    def _handle_git_status(self, path: str = ".") -> ToolResult:
        """Handler para git_status"""
        return self._handle_bash_execute(f"cd {path} && git status", timeout=10)

    def _handle_git_log(self, path: str = ".", count: int = 10) -> ToolResult:
        """Handler para git_log"""
        return self._handle_bash_execute(
            f"cd {path} && git log --oneline -n {count}",
            timeout=10
        )

    def _handle_git_diff(self, path: str = ".", staged: bool = False) -> ToolResult:
        """Handler para git_diff"""
        staged_flag = "--staged" if staged else ""
        return self._handle_bash_execute(
            f"cd {path} && git diff {staged_flag} --stat",
            timeout=10
        )

    def _handle_grep_search(
        self,
        pattern: str,
        path: str = ".",
        file_pattern: str = None,
        context_lines: int = 2
    ) -> ToolResult:
        """Handler para grep_search"""
        try:
            path = os.path.expanduser(path)

            cmd = ["grep", "-r", "-n", f"-C{context_lines}"]

            if file_pattern:
                cmd.extend(["--include", file_pattern])

            cmd.extend([pattern, path])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            # grep retorna 1 si no hay matches (no es error)
            if result.returncode in [0, 1]:
                matches = len([l for l in result.stdout.splitlines() if l and not l.startswith('--')])
                return ToolResult(
                    True,
                    result.stdout if result.stdout else "No se encontraron coincidencias",
                    metadata={"matches": matches, "pattern": pattern}
                )
            else:
                return ToolResult(False, "", result.stderr)

        except Exception as e:
            return ToolResult(False, "", str(e))

    def _handle_python_execute(self, code: str) -> ToolResult:
        """Handler para python_execute (con sandbox de seguridad)"""
        try:
            # FIX: Validar código antes de ejecutar
            dangerous_imports = ['os', 'subprocess', 'sys', 'shutil', 'socket', 'requests', 'urllib']
            for imp in dangerous_imports:
                if f'import {imp}' in code or f'from {imp}' in code:
                    return ToolResult(
                        False, "",
                        f"Import bloqueado por seguridad: {imp}"
                    )

            # FIX: Limitar tamaño del código
            if len(code) > 10000:
                return ToolResult(False, "", "Código demasiado largo (max 10000 chars)")

            # Crear un contexto seguro
            import io
            import sys
            from contextlib import redirect_stdout, redirect_stderr

            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()

            # Variables globales limitadas
            safe_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "set": set,
                    "tuple": tuple,
                    "sum": sum,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "round": round,
                    "sorted": sorted,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                    "True": True,
                    "False": False,
                    "None": None,
                    "bool": bool,
                    "type": type,
                    "isinstance": isinstance,
                    "hasattr": hasattr,
                    "getattr": getattr,
                    "repr": repr,
                    "all": all,
                    "any": any,
                }
            }

            # FIX: Timeout para ejecución de código
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("Ejecución de código excedió el tiempo límite")

            # Solo en Unix
            if hasattr(signal, 'SIGALRM'):
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(10)  # 10 segundos máximo

            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    exec(code, safe_globals)
            finally:
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)

            stdout_val = stdout_capture.getvalue()
            stderr_val = stderr_capture.getvalue()

            output = stdout_val
            if stderr_val:
                output += f"\n[STDERR]: {stderr_val}"

            # FIX: Truncar output largo
            if len(output) > 10000:
                output = output[:10000] + "\n... (output truncado)"

            return ToolResult(True, output or "(sin output)", metadata={"code_length": len(code)})

        except TimeoutError as e:
            return ToolResult(False, "", str(e))
        except SyntaxError as e:
            return ToolResult(False, "", f"Error de sintaxis: {e}")
        except Exception as e:
            return ToolResult(False, "", f"Error ejecutando Python: {str(e)}")

    def _handle_rag_search(self, query: str, rag_name: str = "wikipedia", top_k: int = 5) -> ToolResult:
        """Handler para rag_search - Búsqueda en RAGs"""
        try:
            # Importar RAG manager dinámicamente
            try:
                from core.rag_manager import UnifiedRAGManager
            except ImportError:
                return ToolResult(
                    False, "",
                    "RAG Manager no disponible. Instalar: pip install sentence-transformers faiss-cpu"
                )

            # Obtener instancia del manager
            rag_manager = UnifiedRAGManager()

            # Buscar en el RAG especificado
            if rag_name == "all":
                # Buscar en todos los RAGs
                all_results = []
                for name in ["wikipedia", "exitos", "fallos", "agentes"]:
                    try:
                        results = rag_manager.search(name, query, top_k=top_k)
                        for r in results:
                            r['source_rag'] = name
                            all_results.append(r)
                    except Exception as e:
                        logger.debug(f"RAG {name} no disponible: {e}")

                if not all_results:
                    return ToolResult(True, "No se encontraron resultados en ningún RAG", metadata={"count": 0})

                # Ordenar por score y limitar
                all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
                results = all_results[:top_k]
            else:
                results = rag_manager.search(rag_name, query, top_k=top_k)

            if not results:
                return ToolResult(True, f"No se encontraron resultados en RAG '{rag_name}'", metadata={"count": 0})

            # Formatear resultados
            output_lines = [f"📚 Resultados de RAG '{rag_name}' para: \"{query}\"\n"]
            for i, result in enumerate(results, 1):
                title = result.get('title', 'Sin título')
                content = result.get('content', result.get('text', ''))[:500]
                score = result.get('score', 0)
                source = result.get('source_rag', rag_name)

                output_lines.append(f"--- Resultado {i} (score: {score:.3f}) [{source}] ---")
                output_lines.append(f"📄 {title}")
                output_lines.append(f"{content}...")
                output_lines.append("")

            return ToolResult(
                True,
                "\n".join(output_lines),
                metadata={"count": len(results), "rag": rag_name, "query": query}
            )

        except Exception as e:
            logger.error(f"Error en RAG search: {e}")
            return ToolResult(False, "", f"Error buscando en RAG: {str(e)}")


# === SINGLETON (thread-safe) ===
import threading
_registry_instance: Optional[ToolRegistry] = None
_registry_lock = threading.Lock()  # FIX: Proteger singleton


def get_tool_registry(auto_register: bool = True) -> ToolRegistry:
    """Obtener instancia singleton del registry (thread-safe)"""
    global _registry_instance

    with _registry_lock:
        if _registry_instance is None:
            _registry_instance = ToolRegistry()
            if auto_register:
                _registry_instance.register_defaults()

        return _registry_instance


if __name__ == "__main__":
    # Test
    registry = get_tool_registry()

    print("=== Herramientas Registradas ===\n")
    for cat in registry.get_categories():
        print(f"📁 {cat.upper()}")
        for tool_name in registry.list_by_category(cat):
            tool = registry.get(tool_name)
            print(f"   • {tool_name}: {tool.description[:50]}...")
        print()

    print("\n=== Test: filesystem_list ===")
    result = registry.execute("filesystem_list", {"path": "~"})
    print(f"Success: {result.success}")
    print(f"Output (primeras 5 líneas):")
    for line in result.output.splitlines()[:5]:
        print(f"  {line}")
