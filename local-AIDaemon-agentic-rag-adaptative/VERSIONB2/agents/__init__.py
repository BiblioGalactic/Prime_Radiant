#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agents - Sistema de Agentes IA
"""

from .base_agent import BaseAgent, AgentResult
from .planner import AgentPlanner, Plan, PlanStep
from .validator import PlanValidator
from .executor import AgentExecutor

# === MCP Agent (opcional) ===
MCPAgent = None
MCPAgentWithMemory = None
HAS_MCP_AGENT = False

try:
    from .mcp_agent import MCPAgent, MCPAgentWithMemory, AgentStep
    HAS_MCP_AGENT = True
except (ImportError, Exception):
    pass

# === Claudia Agent (asistente de código) ===
ClaudiaAgent = None
HAS_CLAUDIA = False

try:
    from .claudia_agent import ClaudiaAgent, ClaudiaResult, get_claudia_agent
    HAS_CLAUDIA = True
except (ImportError, Exception):
    pass

__all__ = [
    'BaseAgent', 'AgentResult',
    'AgentPlanner', 'Plan', 'PlanStep',
    'PlanValidator',
    'AgentExecutor',
    # MCP
    'MCPAgent', 'MCPAgentWithMemory', 'HAS_MCP_AGENT',
    # Claudia
    'ClaudiaAgent', 'HAS_CLAUDIA', 'get_claudia_agent'
]
