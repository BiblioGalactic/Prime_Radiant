#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    AGENT PROMPTS - Prompts Detallados
========================================
Prompts cuidadosamente diseñados para el sistema agentico.
Basados en las mejores prácticas de Claude, GPT-4, y ReAct.
========================================
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

# ============================================================================
# SYSTEM PROMPT PRINCIPAL
# ============================================================================

SYSTEM_PROMPT = """Eres un agente que ejecuta herramientas. Responde SOLO con JSON.

HERRAMIENTAS:
- filesystem_read: Leer archivo. Params: {"path": "/ruta/archivo"}
- filesystem_list: Listar directorio. Params: {"path": "/ruta/dir"}
- filesystem_search: Buscar archivos. Params: {"path": "/ruta", "pattern": "*.txt"}
- bash_execute: Ejecutar comando. Params: {"command": "ls -la"}
- git_status: Estado git. Params: {"path": "."}
- grep_search: Buscar texto. Params: {"pattern": "texto", "path": "."}

FORMATO DE RESPUESTA (OBLIGATORIO):

{"tool": "nombre_herramienta", "params": {"param": "valor"}}

EJEMPLOS:

Usuario: lee /home/user/archivo.txt
{"tool": "filesystem_read", "params": {"path": "/home/user/archivo.txt"}}

Usuario: lista los archivos de ~/proyecto
{"tool": "filesystem_list", "params": {"path": "~/proyecto"}}

Usuario: busca README en ~/docs
{"tool": "filesystem_search", "params": {"path": "~/docs", "pattern": "README*"}}

Usuario: ejecuta git status
{"tool": "git_status", "params": {"path": "."}}

REGLAS:
1. Responde SOLO con JSON, nada más
2. Una herramienta por respuesta
3. Usa rutas completas
4. Si ya tienes el resultado, responde: {"done": true, "result": "tu respuesta aquí"}

{tools_description}
"""

# ============================================================================
# PROMPTS ESPECÍFICOS POR HERRAMIENTA
# ============================================================================

TOOL_PROMPTS: Dict[str, str] = {
    "filesystem_list": """
### filesystem_list
**Propósito**: Listar contenido de directorios
**Cuándo usar**:
- Usuario pregunta "qué archivos hay en..."
- Necesitas explorar estructura de carpetas
- Verificar si un directorio existe

**Parámetros**:
- `path` (string, requerido): Ruta del directorio. Soporta ~
- `show_hidden` (boolean, opcional): Incluir archivos ocultos. Default: true

**Tips**:
- Siempre expande ~ a la ruta completa en tu mente
- Si falla, verifica que el path existe
- Paths comunes: ~/proyecto, ~/wikirag, ~/Documents

**Ejemplo**:
```json
{
  "tool": "filesystem_list",
  "params": {"path": "~/proyecto", "show_hidden": false}
}
```
""",

    "filesystem_read": """
### filesystem_read
**Propósito**: Leer contenido de archivos de texto
**Cuándo usar**:
- Usuario pide "lee el archivo..."
- Necesitas analizar código o configuración
- Verificar contenido antes de modificar

**Parámetros**:
- `path` (string, requerido): Ruta del archivo
- `max_lines` (integer, opcional): Límite de líneas. Default: 500

**Tips**:
- Primero verifica que el archivo existe con filesystem_list si no estás seguro
- Para archivos grandes, usa max_lines para evitar sobrecarga
- No funciona con archivos binarios (imágenes, PDFs)

**Ejemplo**:
```json
{
  "tool": "filesystem_read",
  "params": {"path": "~/proyecto/main.py", "max_lines": 100}
}
```
""",

    "filesystem_write": """
### filesystem_write
**Propósito**: Escribir contenido a archivos
**Cuándo usar**:
- Usuario pide crear o modificar un archivo
- Guardar resultados de procesamiento
- Crear configuraciones

**ADVERTENCIA**: Esta herramienta SOBRESCRIBE archivos existentes.

**Parámetros**:
- `path` (string, requerido): Ruta del archivo destino
- `content` (string, requerido): Contenido completo a escribir

**Tips**:
- Siempre lee el archivo primero si existe y quieres preservar contenido
- Crea directorios automáticamente si no existen
- Usa encoding UTF-8

**Ejemplo**:
```json
{
  "tool": "filesystem_write",
  "params": {
    "path": "~/proyecto/nuevo.txt",
    "content": "Contenido del archivo\\nLínea 2"
  }
}
```
""",

    "bash_execute": """
### bash_execute
**Propósito**: Ejecutar comandos de terminal
**Cuándo usar**:
- Comandos git (commit, push, pull)
- Instalación de paquetes (pip, npm)
- Operaciones que no tienen herramienta dedicada

**NO USAR para**:
- Listar archivos (usa filesystem_list)
- Leer archivos (usa filesystem_read)
- Buscar texto (usa grep_search)

**Parámetros**:
- `command` (string, requerido): Comando a ejecutar
- `timeout` (integer, opcional): Segundos antes de timeout. Default: 30
- `cwd` (string, opcional): Directorio de trabajo

**PRECAUCIÓN**:
- NUNCA ejecutes rm -rf sin confirmación
- NUNCA ejecutes sudo sin permiso explícito
- NUNCA ejecutes comandos que modifiquen sistema

**Ejemplo**:
```json
{
  "tool": "bash_execute",
  "params": {
    "command": "pip list | grep numpy",
    "timeout": 15
  }
}
```
""",

    "grep_search": """
### grep_search
**Propósito**: Buscar texto dentro de archivos
**Cuándo usar**:
- Encontrar definiciones de funciones/clases
- Buscar imports o dependencias
- Localizar TODO, FIXME, errores

**Parámetros**:
- `pattern` (string, requerido): Patrón regex a buscar
- `path` (string, opcional): Dónde buscar. Default: "."
- `file_pattern` (string, opcional): Filtrar por tipo (ej: "*.py")
- `context_lines` (integer, opcional): Líneas de contexto. Default: 2

**Tips**:
- Usa regex simples: "def function_name" mejor que regex complejos
- Para Python: "def nombre|class Nombre"
- Para JavaScript: "function nombre|const nombre"

**Ejemplo**:
```json
{
  "tool": "grep_search",
  "params": {
    "pattern": "class.*Agent",
    "path": "~/wikirag/agents",
    "file_pattern": "*.py",
    "context_lines": 3
  }
}
```
""",

    "python_execute": """
### python_execute
**Propósito**: Ejecutar código Python
**Cuándo usar**:
- Cálculos matemáticos
- Procesamiento de datos simple
- Validar sintaxis

**NO USAR para**:
- Código que necesita librerías no disponibles
- Operaciones de archivos (usa filesystem_*)
- Comandos del sistema (usa bash_execute)

**Parámetros**:
- `code` (string, requerido): Código Python a ejecutar

**Funciones disponibles**: print, len, range, str, int, float, list, dict, set, sum, min, max, abs, round, sorted, enumerate, zip, map, filter

**Ejemplo**:
```json
{
  "tool": "python_execute",
  "params": {
    "code": "result = sum(range(1, 101))\\nprint(f'La suma de 1 a 100 es: {result}')"
  }
}
```
"""
}

# ============================================================================
# PROMPTS DE ERROR Y RECUPERACIÓN
# ============================================================================

ERROR_RECOVERY_PROMPT = """
La acción anterior falló con el siguiente error:
{error}

Analiza el error y decide cómo proceder:

1. **Si es un error de parámetros**: Corrige los parámetros y reintenta
2. **Si el recurso no existe**: Informa al usuario o busca alternativas
3. **Si es un timeout**: Considera una operación más simple
4. **Si es un error de permisos**: Informa al usuario

Responde en el formato XML estándar con tu análisis y siguiente acción.
"""

CLARIFICATION_PROMPT = """
No tengo suficiente información para completar esta tarea.

**Lo que entendí**: {understanding}
**Lo que necesito saber**: {questions}

Por favor proporciona más detalles.
"""

# ============================================================================
# CLASE PARA GESTIONAR PROMPTS
# ============================================================================

@dataclass
class AgentPrompts:
    """Gestiona los prompts del agente"""

    system_prompt: str = SYSTEM_PROMPT
    tool_prompts: Dict[str, str] = None
    error_recovery: str = ERROR_RECOVERY_PROMPT
    clarification: str = CLARIFICATION_PROMPT

    def __post_init__(self):
        if self.tool_prompts is None:
            self.tool_prompts = TOOL_PROMPTS

    def get_system_prompt(self, tools_description: str) -> str:
        """Obtener system prompt con herramientas inyectadas"""
        # Usar replace en vez de format para evitar conflictos con {} en JSON
        return self.system_prompt.replace("{tools_description}", tools_description)

    def get_tool_prompt(self, tool_name: str) -> str:
        """Obtener prompt específico de herramienta"""
        return self.tool_prompts.get(tool_name, f"Herramienta: {tool_name}")

    def get_error_prompt(self, error: str) -> str:
        """Obtener prompt de recuperación de error"""
        return self.error_recovery.format(error=error)

    def get_clarification_prompt(self, understanding: str, questions: List[str]) -> str:
        """Obtener prompt de clarificación"""
        return self.clarification.format(
            understanding=understanding,
            questions="\n".join(f"- {q}" for q in questions)
        )


# Singleton
_prompts_instance: Optional[AgentPrompts] = None


def get_agent_prompts() -> AgentPrompts:
    """Obtener instancia de prompts"""
    global _prompts_instance
    if _prompts_instance is None:
        _prompts_instance = AgentPrompts()
    return _prompts_instance


if __name__ == "__main__":
    prompts = get_agent_prompts()
    print("=== SYSTEM PROMPT (primeras 50 líneas) ===\n")
    for line in prompts.system_prompt.splitlines()[:50]:
        print(line)
    print("\n...")
    print(f"\n=== Total: {len(prompts.system_prompt)} caracteres ===")
