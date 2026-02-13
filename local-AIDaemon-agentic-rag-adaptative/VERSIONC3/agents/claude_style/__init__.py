#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
🧠 CLAUDE STYLE AGENT - Agente Inteligente
========================================
Agente que emula el comportamiento de Claude:
- Pensamiento estructurado (Chain of Thought)
- Planificación antes de actuar
- Ejecución verificada de cada paso
- Autocorrección cuando algo falla
- Reflexión sobre el resultado final

Arquitectura:
┌─────────────────────────────────────────────────┐
│                 ClaudeStyleAgent                │
├─────────────────────────────────────────────────┤
│  ┌─────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Thinker │→ │ Planner  │→ │   Executor   │   │
│  └─────────┘  └──────────┘  └──────┬───────┘   │
│                                     │          │
│  ┌─────────┐  ┌──────────┐  ┌──────▼───────┐   │
│  │Reflector│← │ Corrector│← │   Verifier   │   │
│  └─────────┘  └──────────┘  └──────────────┘   │
└─────────────────────────────────────────────────┘

Uso:
    from agents.claude_style import ClaudeStyleAgent

    agent = ClaudeStyleAgent(llm_interface)
    result = agent.run("Implementa un sistema de caché")
"""

from .agent import ClaudeStyleAgent, AgentConfig, AgentMode, AgentResult, SimpleClaudeAgent
from .thinker import Thinker, Thought
from .planner import Planner, Plan, PlanStep
from .executor import Executor, StepResult
from .verifier import Verifier, VerificationResult
from .corrector import Corrector, CorrectionStrategy
from .reflector import Reflector, Reflection

__all__ = [
    # Agente principal
    'ClaudeStyleAgent',
    'SimpleClaudeAgent',
    'AgentConfig',
    'AgentMode',
    'AgentResult',
    # Thinker
    'Thinker',
    'Thought',
    # Planner
    'Planner',
    'Plan',
    'PlanStep',
    # Executor
    'Executor',
    'StepResult',
    # Verifier
    'Verifier',
    'VerificationResult',
    # Corrector
    'Corrector',
    'CorrectionStrategy',
    # Reflector
    'Reflector',
    'Reflection',
]

__version__ = "1.0.0"
