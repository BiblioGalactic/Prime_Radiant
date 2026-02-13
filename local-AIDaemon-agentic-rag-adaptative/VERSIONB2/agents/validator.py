#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    VALIDATOR - Validador de Planes
========================================
Valida que los planes sean ejecutables y coherentes.
"""

import os
import sys
import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

# === Setup paths para imports absolutos ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agents.planner import Plan, PlanStep, StepType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Validator")


@dataclass
class ValidationResult:
    """Resultado de validación"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


class PlanValidator:
    """
    Validador de planes de ejecución.
    Verifica coherencia, disponibilidad de recursos y posibles conflictos.
    """

    # Herramientas conocidas
    KNOWN_TOOLS = {
        "leer_archivo", "escribir_archivo", "buscar_archivos",
        "consultar_memoria", "ejecutar_comando", "listar_directorio",
        "consultar_api", "descargar_archivo", "comprimir_descomprimir",
        "git_operation", "buscar_en_contenido",
        "web_search", "python_exec", "grep"
    }

    # Agentes conocidos
    KNOWN_AGENTS = {
        "generic", "search", "code", "validation"
    }

    # Máximos permitidos
    MAX_STEPS = 10
    MAX_DEPENDENCIES = 5
    MAX_TOOLS_PER_STEP = 5

    def __init__(self):
        """Inicializar validador"""
        pass

    def validate(self, plan: Plan) -> ValidationResult:
        """
        Validar un plan completo.

        Args:
            plan: Plan a validar

        Returns:
            ValidationResult con errores, warnings y sugerencias
        """
        errors = []
        warnings = []
        suggestions = []

        # Validaciones básicas
        basic_errors = self._validate_basic(plan)
        errors.extend(basic_errors)

        # Validar cada paso
        for step in plan.steps:
            step_errors, step_warnings = self._validate_step(step, plan)
            errors.extend(step_errors)
            warnings.extend(step_warnings)

        # Validar dependencias
        dep_errors = self._validate_dependencies(plan)
        errors.extend(dep_errors)

        # Validar coherencia
        coherence_warnings = self._validate_coherence(plan)
        warnings.extend(coherence_warnings)

        # Generar sugerencias
        suggestions = self._generate_suggestions(plan, errors, warnings)

        is_valid = len(errors) == 0

        result = ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )

        if is_valid:
            logger.info(f"Plan {plan.id} validado correctamente")
        else:
            logger.warning(f"Plan {plan.id} tiene {len(errors)} errores")

        return result

    def _validate_basic(self, plan: Plan) -> List[str]:
        """Validaciones básicas del plan"""
        errors = []

        if not plan.id:
            errors.append("Plan sin ID")

        if not plan.steps:
            errors.append("Plan sin pasos")

        if len(plan.steps) > self.MAX_STEPS:
            errors.append(f"Plan excede máximo de {self.MAX_STEPS} pasos ({len(plan.steps)})")

        if not plan.original_query:
            errors.append("Plan sin consulta original")

        return errors

    def _validate_step(self, step: PlanStep, plan: Plan) -> Tuple[List[str], List[str]]:
        """Validar un paso individual"""
        errors = []
        warnings = []

        # Validar ID único
        ids = [s.id for s in plan.steps]
        if ids.count(step.id) > 1:
            errors.append(f"Paso {step.id}: ID duplicado")

        # Validar tipo de paso
        if not isinstance(step.type, StepType):
            errors.append(f"Paso {step.id}: Tipo inválido")

        # Validar agente
        if step.agent_type not in self.KNOWN_AGENTS:
            warnings.append(f"Paso {step.id}: Agente desconocido '{step.agent_type}'")

        # Validar herramientas
        for tool in step.tools_required:
            if tool not in self.KNOWN_TOOLS:
                warnings.append(f"Paso {step.id}: Herramienta desconocida '{tool}'")

        if len(step.tools_required) > self.MAX_TOOLS_PER_STEP:
            warnings.append(f"Paso {step.id}: Muchas herramientas ({len(step.tools_required)})")

        # Validar descripción
        if not step.description:
            errors.append(f"Paso {step.id}: Sin descripción")
        elif len(step.description) < 10:
            warnings.append(f"Paso {step.id}: Descripción muy corta")

        # Validar dependencias
        if len(step.dependencies) > self.MAX_DEPENDENCIES:
            warnings.append(f"Paso {step.id}: Muchas dependencias ({len(step.dependencies)})")

        return errors, warnings

    def _validate_dependencies(self, plan: Plan) -> List[str]:
        """Validar dependencias entre pasos"""
        errors = []
        step_ids = {s.id for s in plan.steps}

        for step in plan.steps:
            for dep_id in step.dependencies:
                # Verificar que la dependencia existe
                if dep_id not in step_ids:
                    errors.append(f"Paso {step.id}: Dependencia {dep_id} no existe")

                # Verificar que no depende de sí mismo
                if dep_id == step.id:
                    errors.append(f"Paso {step.id}: Depende de sí mismo")

                # Verificar que no hay dependencias hacia adelante
                if dep_id > step.id:
                    errors.append(f"Paso {step.id}: Depende de paso futuro {dep_id}")

        # Verificar ciclos
        if self._has_cycles(plan):
            errors.append("Plan tiene dependencias cíclicas")

        return errors

    def _has_cycles(self, plan: Plan) -> bool:
        """Detectar ciclos en dependencias"""
        # Usar DFS para detectar ciclos
        visited = set()
        rec_stack = set()

        def dfs(step_id):
            visited.add(step_id)
            rec_stack.add(step_id)

            step = next((s for s in plan.steps if s.id == step_id), None)
            if step:
                for dep_id in step.dependencies:
                    if dep_id not in visited:
                        if dfs(dep_id):
                            return True
                    elif dep_id in rec_stack:
                        return True

            rec_stack.remove(step_id)
            return False

        for step in plan.steps:
            if step.id not in visited:
                if dfs(step.id):
                    return True

        return False

    def _validate_coherence(self, plan: Plan) -> List[str]:
        """Validar coherencia del plan"""
        warnings = []

        # Verificar que hay al menos un paso de síntesis si hay múltiples pasos
        if len(plan.steps) > 2:
            has_synthesize = any(s.type == StepType.SYNTHESIZE for s in plan.steps)
            if not has_synthesize:
                warnings.append("Plan largo sin paso de síntesis final")

        # Verificar que búsquedas van antes de análisis
        search_steps = [s for s in plan.steps if s.type == StepType.SEARCH]
        analyze_steps = [s for s in plan.steps if s.type == StepType.ANALYZE]

        for search in search_steps:
            for analyze in analyze_steps:
                if search.id > analyze.id and search.id not in analyze.dependencies:
                    warnings.append(f"Búsqueda (paso {search.id}) después de análisis (paso {analyze.id})")

        # Verificar coherencia agente-tipo
        coherence_map = {
            StepType.SEARCH: ["search", "generic"],
            StepType.CODE: ["code", "generic"],
            StepType.VALIDATE: ["validation", "generic"],
        }

        for step in plan.steps:
            if step.type in coherence_map:
                valid_agents = coherence_map[step.type]
                if step.agent_type not in valid_agents:
                    warnings.append(
                        f"Paso {step.id}: Tipo '{step.type.value}' con agente '{step.agent_type}' "
                        f"(recomendado: {valid_agents})"
                    )

        return warnings

    def _generate_suggestions(
        self,
        plan: Plan,
        errors: List[str],
        warnings: List[str]
    ) -> List[str]:
        """Generar sugerencias de mejora"""
        suggestions = []

        # Sugerencia si hay muchos pasos
        if len(plan.steps) > 5:
            suggestions.append(
                "Considerar simplificar el plan agrupando pasos relacionados"
            )

        # Sugerencia si no hay validación
        has_validation = any(s.type == StepType.VALIDATE for s in plan.steps)
        if not has_validation and len(plan.steps) > 1:
            suggestions.append(
                "Añadir un paso de validación para verificar resultados"
            )

        # Sugerencia si hay warnings de herramientas desconocidas
        unknown_tools = [w for w in warnings if "Herramienta desconocida" in w]
        if unknown_tools:
            suggestions.append(
                "Verificar que las herramientas desconocidas están disponibles "
                "o usar alternativas conocidas"
            )

        return suggestions

    def fix_plan(self, plan: Plan) -> Plan:
        """
        Intentar corregir errores comunes en un plan.

        Args:
            plan: Plan a corregir

        Returns:
            Plan corregido
        """
        # Corregir IDs duplicados
        seen_ids = set()
        new_id = 1
        for step in plan.steps:
            while new_id in seen_ids:
                new_id += 1
            step.id = new_id
            seen_ids.add(new_id)
            new_id += 1

        # Corregir dependencias inválidas
        valid_ids = {s.id for s in plan.steps}
        for step in plan.steps:
            step.dependencies = [
                d for d in step.dependencies
                if d in valid_ids and d != step.id and d < step.id
            ]

        # Añadir paso de síntesis si falta
        has_synthesize = any(s.type == StepType.SYNTHESIZE for s in plan.steps)
        if not has_synthesize and len(plan.steps) > 1:
            plan.steps.append(PlanStep(
                id=len(plan.steps) + 1,
                type=StepType.SYNTHESIZE,
                description="Sintetizar resultados de los pasos anteriores",
                agent_type="generic",
                dependencies=[s.id for s in plan.steps]
            ))

        logger.info(f"Plan {plan.id} corregido")
        return plan


# === CLI para pruebas ===
if __name__ == "__main__":
    from agents.planner import AgentPlanner

    # Crear plan de ejemplo
    planner = AgentPlanner()
    plan = planner.create_plan(
        "¿Cómo funciona Python?",
        "Necesito buscar más información sobre Python."
    )

    # Validar
    validator = PlanValidator()
    result = validator.validate(plan)

    print(f"📋 Validación del plan: {plan.id}")
    print(f"   Válido: {'✅' if result.is_valid else '❌'}")

    if result.errors:
        print(f"\n❌ Errores ({len(result.errors)}):")
        for e in result.errors:
            print(f"   - {e}")

    if result.warnings:
        print(f"\n⚠️ Warnings ({len(result.warnings)}):")
        for w in result.warnings:
            print(f"   - {w}")

    if result.suggestions:
        print(f"\n💡 Sugerencias ({len(result.suggestions)}):")
        for s in result.suggestions:
            print(f"   - {s}")
