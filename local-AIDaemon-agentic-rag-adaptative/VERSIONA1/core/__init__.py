#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core - Núcleo del Sistema de IA con Agentes y RAGs
"""

import os
import sys

# Setup paths
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config import Config, config
from core.queue_manager import QueueManager, QueueMessage, Priority
from core.daemon_interface import DaemonInterface, DaemonCLI
from core.rag_manager import RAGManager
from core.evaluator import ResponseEvaluator, HeuristicEvaluator, Verdict, create_evaluator
from core.shared_state import SharedState, get_shared_state

__all__ = [
    'Config', 'config',
    'QueueManager', 'QueueMessage', 'Priority',
    'DaemonInterface', 'DaemonCLI',
    'RAGManager',
    'ResponseEvaluator', 'HeuristicEvaluator', 'Verdict', 'create_evaluator',
    'SharedState', 'get_shared_state'
]
__version__ = '2.0.0'
