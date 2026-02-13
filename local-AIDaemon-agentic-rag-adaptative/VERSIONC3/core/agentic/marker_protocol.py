#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    MARKER PROTOCOL - Protocolo de Marcadores
========================================
Sistema de comunicación simple entre el modelo y el sistema.

El modelo usa marcadores como [[leer /ruta]] que son fáciles de:
1. Generar (incluso modelos pequeños)
2. Detectar (regex simple)
3. Validar (seguridad)

Marcadores soportados:
- [[leer /ruta/archivo]]        → filesystem_read
- [[listar /ruta/directorio]]   → filesystem_list
- [[buscar patron en /ruta]]    → grep_search
- [[encontrar *.py en /ruta]]   → filesystem_search
- [[ejecutar comando]]          → bash_execute (con validación)
- [[git estado]]                → git_status
- [[RESPUESTA: texto]]          → Respuesta final al usuario
========================================
"""

import re
import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger("MarkerProtocol")


@dataclass
class MarkerAction:
    """Acción detectada de un marcador"""
    marker_type: str          # Tipo: read, list, search, execute, response
    tool: Optional[str]       # Herramienta a usar
    params: Dict[str, Any]    # Parámetros
    raw_marker: str           # Marcador original
    is_safe: bool             # Si pasó validación de seguridad
    error: Optional[str]      # Error si no es seguro


# Patrones de marcadores
MARKER_PATTERNS = [
    # [[leer /ruta/archivo]] o [[lee /ruta]] o [[abrir /ruta]]
    (r'\[\[(leer|lee|abrir|abre|ver|muestra)\s+([^\]]+)\]\]', 'read'),

    # [[listar /ruta]] o [[lista /ruta]] o [[ls /ruta]]
    (r'\[\[(listar|lista|ls|dir|mostrar archivos en|archivos de)\s+([^\]]+)\]\]', 'list'),

    # [[buscar patron en /ruta]] o [[grep patron /ruta]]
    (r'\[\[(buscar|grep|encontrar texto)\s+(.+?)\s+en\s+([^\]]+)\]\]', 'grep'),

    # [[encontrar *.py en /ruta]] o [[find *.py /ruta]]
    (r'\[\[(encontrar|find|buscar archivos)\s+([^\s]+)\s+en\s+([^\]]+)\]\]', 'find'),

    # [[ejecutar comando]] o [[exec comando]] o [[run comando]]
    (r'\[\[(ejecutar|ejecuta|exec|run|comando)\s+([^\]]+)\]\]', 'execute'),

    # [[git estado]] o [[git status]]
    (r'\[\[(git\s+(?:estado|status))\]\]', 'git_status'),
    (r'\[\[(git\s+(?:log|historial))\]\]', 'git_log'),
    (r'\[\[(git\s+(?:diff|cambios))\]\]', 'git_diff'),

    # [[RESPUESTA: texto]] o [[respuesta: texto]]
    (r'\[\[(?:RESPUESTA|respuesta|RESULTADO|resultado):\s*([^\]]+)\]\]', 'response'),

    # [[rag consulta]] o [[wikipedia consulta]] o [[buscar en rag consulta]]
    (r'\[\[(rag|wikipedia|wiki|conocimiento)\s+([^\]]+)\]\]', 'rag_search'),
    (r'\[\[(buscar en rag|consultar rag|pregunta a wikipedia)\s+([^\]]+)\]\]', 'rag_search'),
]

# Comandos/patrones peligrosos que NO se ejecutan
DANGEROUS_PATTERNS = [
    r'rm\s+-rf\s+/',
    r'rm\s+-rf\s+~',
    r'rm\s+-rf\s+\*',
    r'mkfs',
    r'dd\s+if=',
    r'>\s*/dev/',
    r'chmod\s+-R\s+777\s+/',
    r'sudo\s+rm',
    r'sudo\s+dd',
    r'sudo\s+su',
    r'sudo\s+-i',
    r'sudo\s+bash',
    r'sudo\s+sh\b',
    r'su\s+-',
    r'su\s+root',
    r':\(\)\{',  # Fork bomb
    r'\|\s*sh',
    r'\|\s*bash',
    r'curl.*\|',
    r'wget.*\|',
]

# Rutas protegidas que NO se pueden modificar
PROTECTED_PATHS = [
    '/System',
    '/usr',
    '/bin',
    '/sbin',
    '/etc',
    '/var',
    '/private',
    '/Library/System',
]


def is_path_safe(path: str) -> Tuple[bool, str]:
    """
    Verificar si una ruta es segura para operar.

    Returns:
        (is_safe, error_message)
    """
    # Expandir ~
    expanded = os.path.expanduser(path)

    # Normalizar
    try:
        normalized = os.path.normpath(expanded)
    except:
        return False, f"Ruta inválida: {path}"

    # Verificar rutas protegidas
    for protected in PROTECTED_PATHS:
        if normalized.startswith(protected):
            return False, f"Ruta protegida: {protected}"

    # Verificar traversal
    if '..' in path:
        # Permitir solo si no escapa del home
        home = os.path.expanduser('~')
        if not normalized.startswith(home):
            return False, "Traversal fuera del home no permitido"

    return True, ""


def is_command_safe(command: str) -> Tuple[bool, str]:
    """
    Verificar si un comando es seguro para ejecutar.

    Returns:
        (is_safe, error_message)
    """
    command_lower = command.lower()

    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command_lower):
            return False, f"Comando peligroso detectado"

    return True, ""


def parse_markers(text: str) -> List[MarkerAction]:
    """
    Detectar y parsear todos los marcadores en un texto.

    Args:
        text: Texto del modelo

    Returns:
        Lista de MarkerAction encontradas
    """
    actions = []

    for pattern, marker_type in MARKER_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            action = _parse_single_marker(match, marker_type)
            if action:
                actions.append(action)

    return actions


def _parse_single_marker(match: re.Match, marker_type: str) -> Optional[MarkerAction]:
    """Parsear un marcador individual"""
    raw_marker = match.group(0)
    groups = match.groups()

    if marker_type == 'read':
        # groups: (verbo, ruta)
        path = groups[1].strip()
        is_safe, error = is_path_safe(path)
        return MarkerAction(
            marker_type='read',
            tool='filesystem_read',
            params={'path': path},
            raw_marker=raw_marker,
            is_safe=is_safe,
            error=error if not is_safe else None
        )

    elif marker_type == 'list':
        path = groups[1].strip()
        is_safe, error = is_path_safe(path)
        return MarkerAction(
            marker_type='list',
            tool='filesystem_list',
            params={'path': path},
            raw_marker=raw_marker,
            is_safe=is_safe,
            error=error if not is_safe else None
        )

    elif marker_type == 'grep':
        # groups: (verbo, patron, ruta)
        pattern = groups[1].strip()
        path = groups[2].strip()
        is_safe, error = is_path_safe(path)
        return MarkerAction(
            marker_type='grep',
            tool='grep_search',
            params={'pattern': pattern, 'path': path},
            raw_marker=raw_marker,
            is_safe=is_safe,
            error=error if not is_safe else None
        )

    elif marker_type == 'find':
        # groups: (verbo, patron, ruta)
        pattern = groups[1].strip()
        path = groups[2].strip()
        is_safe, error = is_path_safe(path)
        return MarkerAction(
            marker_type='find',
            tool='filesystem_search',
            params={'pattern': pattern, 'path': path},
            raw_marker=raw_marker,
            is_safe=is_safe,
            error=error if not is_safe else None
        )

    elif marker_type == 'execute':
        command = groups[1].strip()
        is_safe, error = is_command_safe(command)
        return MarkerAction(
            marker_type='execute',
            tool='bash_execute',
            params={'command': command},
            raw_marker=raw_marker,
            is_safe=is_safe,
            error=error if not is_safe else None
        )

    elif marker_type in ['git_status', 'git_log', 'git_diff']:
        return MarkerAction(
            marker_type=marker_type,
            tool=marker_type,
            params={'path': '.'},
            raw_marker=raw_marker,
            is_safe=True,
            error=None
        )

    elif marker_type == 'rag_search':
        # groups: (tipo, query)
        query = groups[1].strip() if len(groups) > 1 else groups[0].strip()
        rag_type = groups[0].lower() if groups[0].lower() in ['wikipedia', 'wiki'] else 'wikipedia'
        return MarkerAction(
            marker_type='rag_search',
            tool='rag_search',
            params={'query': query, 'rag_name': rag_type if rag_type != 'wiki' else 'wikipedia'},
            raw_marker=raw_marker,
            is_safe=True,
            error=None
        )

    elif marker_type == 'response':
        response_text = groups[0].strip()
        return MarkerAction(
            marker_type='response',
            tool=None,
            params={'text': response_text},
            raw_marker=raw_marker,
            is_safe=True,
            error=None
        )

    return None


def get_first_action(text: str) -> Optional[MarkerAction]:
    """
    Obtener la primera acción válida del texto.

    Args:
        text: Texto del modelo

    Returns:
        Primera MarkerAction segura o None
    """
    actions = parse_markers(text)

    for action in actions:
        if action.is_safe:
            return action
        else:
            logger.warning(f"Acción bloqueada: {action.raw_marker} - {action.error}")

    return None


def marker_to_tool_call(action: MarkerAction) -> Optional[Dict[str, Any]]:
    """
    Convertir MarkerAction a formato de llamada de herramienta.

    Returns:
        Dict con {tool, params} o None si es respuesta
    """
    if not action.is_safe:
        return None

    if action.marker_type == 'response':
        return None  # No es llamada a herramienta

    return {
        'tool': action.tool,
        'params': action.params
    }


# === PROMPT PARA ENSEÑAR MARCADORES ===

# Template base - se completa con PWD en runtime
MARKER_SYSTEM_PROMPT_TEMPLATE = """Eres un EJECUTOR. Tu trabajo es HACER, no explicar.

DIRECTORIO ACTUAL: {pwd}

FORMATO: Responde SOLO con UN marcador [[...]]

MARCADORES:
[[leer RUTA]]      - Lee archivo
[[listar RUTA]]    - Lista directorio
[[buscar X en RUTA]] - Busca texto
[[ejecutar CMD]]   - Ejecuta comando
[[git estado]]     - Git status
[[rag CONSULTA]]   - Busca en Wikipedia/conocimiento
[[RESPUESTA: X]]   - Respuesta final

CRÍTICO:
- NUNCA uses rutas genéricas como "/ruta/archivo"
- USA la ruta REAL que pide el usuario
- Si no hay ruta, usa el DIRECTORIO ACTUAL: {pwd}
- Si algo falla, NO repitas lo mismo

EJECUTA AHORA:"""

# Versión sin PWD (fallback)
MARKER_SYSTEM_PROMPT = """Eres un EJECUTOR. Tu trabajo es HACER, no explicar.

FORMATO: Responde SOLO con UN marcador [[...]]

MARCADORES:
[[leer RUTA]]      - Lee archivo
[[listar RUTA]]    - Lista directorio
[[buscar X en RUTA]] - Busca texto
[[ejecutar CMD]]   - Ejecuta comando
[[git estado]]     - Git status
[[rag CONSULTA]]   - Busca en Wikipedia/conocimiento
[[RESPUESTA: X]]   - Respuesta final

CRÍTICO:
- NUNCA uses rutas genéricas como "/ruta/archivo"
- USA la ruta REAL que pide el usuario
- Si piden "lista archivos", usa [[listar .]] o la ruta específica
- Si algo falla, NO repitas lo mismo

EJECUTA AHORA:"""


def get_marker_prompt(pwd: str = None) -> str:
    """
    Obtener prompt de marcadores con PWD dinámico.

    Args:
        pwd: Directorio de trabajo actual

    Returns:
        Prompt configurado
    """
    if pwd:
        return MARKER_SYSTEM_PROMPT_TEMPLATE.format(pwd=pwd)
    return MARKER_SYSTEM_PROMPT


# === TEST ===
if __name__ == "__main__":
    print("=== TEST MARKER PROTOCOL ===\n")

    test_texts = [
        "Voy a leer el archivo [[leer ~/documento.txt]]",
        "Primero [[listar ~/proyecto]] para ver qué hay",
        "[[buscar TODO en ~/codigo]]",
        "[[encontrar *.py en ~/proyecto]]",
        "[[ejecutar ls -la]]",
        "[[ejecutar rm -rf /]]",  # PELIGROSO - debe bloquearse
        "[[git estado]]",
        "[[RESPUESTA: El archivo contiene información sobre el proyecto]]",
        "Texto sin marcadores",
    ]

    for text in test_texts:
        print(f"Input: {text[:60]}...")
        action = get_first_action(text)
        if action:
            status = "✅ SAFE" if action.is_safe else f"❌ BLOCKED: {action.error}"
            print(f"  → {action.marker_type}: {action.tool} | {status}")
            if action.params:
                print(f"     Params: {action.params}")
        else:
            print(f"  → (sin marcadores)")
        print()
