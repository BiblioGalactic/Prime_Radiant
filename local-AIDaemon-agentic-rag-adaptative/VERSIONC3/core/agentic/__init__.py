#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    AGENTIC - Sistema Agentico Real
========================================
WikiRAG v2.3.1

Implementa un loop agentico real con:
- Tool Registry con JSON Schema
- Prompts detallados por herramienta
- Loop Think→Act→Observe→Repeat
========================================
"""

from .tool_registry import (
    ToolRegistry,
    Tool,
    ToolParameter,
    ToolResult,
    get_tool_registry
)

from .agent_prompts import (
    AgentPrompts,
    SYSTEM_PROMPT,
    TOOL_PROMPTS,
    get_agent_prompts
)

from .agent_runtime import (
    AgentRuntime,
    AgentState,
    AgentStep,
    AgentResult,
    get_agent_runtime
)

__all__ = [
    # Tool Registry
    'ToolRegistry',
    'Tool',
    'ToolParameter',
    'ToolResult',
    'get_tool_registry',

    # Prompts
    'AgentPrompts',
    'SYSTEM_PROMPT',
    'TOOL_PROMPTS',
    'get_agent_prompts',

    # Runtime
    'AgentRuntime',
    'AgentState',
    'AgentStep',
    'AgentResult',
    'get_agent_runtime',
]
