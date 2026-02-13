#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tools - Herramientas MCP para Agentes
"""

import os
import sys

# Setup paths
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agents.tools.mcp_client import MCPClient, MCPTool
from agents.tools.web_search import WebSearchTool
from agents.tools.file_ops import FileOpsTool
from agents.tools.python_exec import PythonExecTool
from agents.tools.system_ops import SystemOpsTool

__all__ = [
    'MCPClient', 'MCPTool',
    'WebSearchTool',
    'FileOpsTool',
    'PythonExecTool',
    'SystemOpsTool'
]
