#!/usr/bin/env python3
# ============================================================
# 🧠 WIKIRAG STRATEGIC AGENT v1.0
# ============================================================
# Agente Meta-Prompt/Estratega que divide tareas complejas
# en subtareas ejecutables. NO ejecuta - PLANIFICA.
# ============================================================

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Setup paths
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.file_queue import FileQueue, FileTask, TaskPriority, TaskType

logger = logging.getLogger(__name__)


@dataclass
class SubTask:
    """Subtarea generada por el estratega"""
    id: str
    title: str
    description: str
    agent: str  # executor, writer, reviewer, researcher, illustrator
    priority: str = "NORMAL"
    dependencies: List[str] = field(default_factory=list)
    expected_output: Optional[str] = None
    estimated_tokens: int = 0
    validation_criteria: List[str] = field(default_factory=list)


@dataclass
class ExecutionPlan:
    """Plan de ejecución generado"""
    id: str
    original_task: str
    strategy: str  # sequential, parallel, hybrid
    subtasks: List[SubTask]
    estimated_total_time: str
    checkpoints: List[str]
    rollback_plan: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StrategicAgent:
    """
    Agente Estratégico - El Cerebro Planificador.

    No ejecuta tareas, las divide y coordina.
    Genera planes que otros agentes ejecutan.
    """

    # Agentes disponibles y sus capacidades
    AGENTS = {
        'researcher': {
            'description': 'Busca información en RAGs y fuentes',
            'capabilities': ['search', 'analyze', 'summarize'],
            'max_context': 4000
        },
        'writer': {
            'description': 'Escribe contenido largo y estructurado',
            'capabilities': ['write', 'expand', 'structure'],
            'max_context': 8000
        },
        'reviewer': {
            'description': 'Revisa y corrige contenido',
            'capabilities': ['review', 'correct', 'validate'],
            'max_context': 4000
        },
        'executor': {
            'description': 'Ejecuta comandos y operaciones',
            'capabilities': ['filesystem', 'shell', 'code'],
            'max_context': 2000
        },
        'illustrator': {
            'description': 'Genera diagramas y visualizaciones',
            'capabilities': ['mermaid', 'ascii-art', 'describe-image'],
            'max_context': 2000
        },
        'translator': {
            'description': 'Traduce entre idiomas',
            'capabilities': ['translate', 'localize'],
            'max_context': 4000
        }
    }

    def __init__(self, file_queue: Optional[FileQueue] = None):
        """
        Inicializar Strategic Agent.

        Args:
            file_queue: Cola de archivos para crear subtareas
        """
        self.fq = file_queue or FileQueue()
        self.plans_dir = Path.home() / "wikirag" / "queue" / "agents" / "strategist"
        self.plans_dir.mkdir(parents=True, exist_ok=True)

    def analyze_complexity(self, task: str) -> Dict[str, Any]:
        """
        Analizar complejidad de una tarea.

        Returns:
            Dict con métricas de complejidad
        """
        words = len(task.split())

        # Detectar indicadores de complejidad
        complexity_indicators = {
            'multi_step': any(w in task.lower() for w in ['y luego', 'después', 'finalmente', 'primero']),
            'large_output': any(w in task.lower() for w in ['libro', 'documento', 'reporte', 'páginas']),
            'research_needed': any(w in task.lower() for w in ['investiga', 'busca', 'analiza', 'compara']),
            'creative': any(w in task.lower() for w in ['escribe', 'crea', 'genera', 'diseña']),
            'technical': any(w in task.lower() for w in ['código', 'script', 'programa', 'función']),
            'review_needed': any(w in task.lower() for w in ['revisa', 'corrige', 'mejora', 'verifica'])
        }

        complexity_score = sum(complexity_indicators.values())

        return {
            'word_count': words,
            'indicators': complexity_indicators,
            'score': complexity_score,
            'needs_planning': complexity_score >= 2 or words > 50,
            'estimated_subtasks': max(1, complexity_score * 2)
        }

    def create_book_plan(
        self,
        topic: str,
        pages: int = 300,
        audience: str = "general",
        style: str = "técnico"
    ) -> ExecutionPlan:
        """
        Crear plan para escribir un libro completo.

        Args:
            topic: Tema del libro
            pages: Número de páginas objetivo
            audience: Audiencia objetivo
            style: Estilo de escritura

        Returns:
            ExecutionPlan con todas las subtareas
        """
        # Calcular estructura
        pages_per_chapter = 10
        chapters = pages // pages_per_chapter

        plan_id = f"book_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        subtasks = []

        # Fase 1: Investigación
        subtasks.append(SubTask(
            id=f"{plan_id}_00_research",
            title="Investigación inicial",
            description=f"Investigar fuentes y material sobre: {topic}",
            agent="researcher",
            priority="HIGH",
            expected_output=f"~/wikirag/output/{plan_id}/research_notes.md",
            estimated_tokens=4000,
            validation_criteria=["Mínimo 10 fuentes", "Resumen de 2000 palabras"]
        ))

        # Fase 2: Esquema
        subtasks.append(SubTask(
            id=f"{plan_id}_01_outline",
            title="Crear esquema del libro",
            description=f"Crear estructura de {chapters} capítulos sobre {topic}",
            agent="writer",
            priority="HIGH",
            dependencies=[f"{plan_id}_00_research"],
            expected_output=f"~/wikirag/output/{plan_id}/outline.md",
            estimated_tokens=2000,
            validation_criteria=["Todos los capítulos tienen título", "Coherencia temática"]
        ))

        # Fase 3: Escribir capítulos
        for i in range(chapters):
            subtasks.append(SubTask(
                id=f"{plan_id}_ch{i+1:02d}_write",
                title=f"Escribir capítulo {i+1}",
                description=f"Escribir ~{pages_per_chapter} páginas del capítulo {i+1}",
                agent="writer",
                priority="NORMAL",
                dependencies=[f"{plan_id}_01_outline"] + ([f"{plan_id}_ch{i:02d}_write"] if i > 0 else []),
                expected_output=f"~/wikirag/output/{plan_id}/chapters/ch{i+1:02d}.md",
                estimated_tokens=8000,
                validation_criteria=[f"Mínimo {pages_per_chapter*250} palabras", "Coherencia con esquema"]
            ))

            # Revisión cada 5 capítulos
            if (i + 1) % 5 == 0:
                subtasks.append(SubTask(
                    id=f"{plan_id}_review_{i+1:02d}",
                    title=f"Revisar capítulos {max(1, i-3)}-{i+1}",
                    description="Revisar coherencia, estilo y errores",
                    agent="reviewer",
                    priority="NORMAL",
                    dependencies=[f"{plan_id}_ch{j:02d}_write" for j in range(max(1, i-3), i+2)],
                    expected_output=f"~/wikirag/output/{plan_id}/reviews/review_{i+1:02d}.md",
                    estimated_tokens=4000
                ))

        # Fase 4: Revisión final
        subtasks.append(SubTask(
            id=f"{plan_id}_final_review",
            title="Revisión final completa",
            description="Revisar todo el libro por coherencia y calidad",
            agent="reviewer",
            priority="HIGH",
            dependencies=[f"{plan_id}_ch{chapters:02d}_write"],
            expected_output=f"~/wikirag/output/{plan_id}/final_review.md",
            estimated_tokens=8000
        ))

        # Fase 5: Compilación
        subtasks.append(SubTask(
            id=f"{plan_id}_compile",
            title="Compilar libro final",
            description="Unir todos los capítulos en documento final",
            agent="executor",
            priority="HIGH",
            dependencies=[f"{plan_id}_final_review"],
            expected_output=f"~/wikirag/output/{plan_id}/BOOK_FINAL.md",
            estimated_tokens=1000
        ))

        return ExecutionPlan(
            id=plan_id,
            original_task=f"Escribir libro de {pages} páginas sobre {topic}",
            strategy="sequential",
            subtasks=subtasks,
            estimated_total_time=f"{chapters * 2} horas",
            checkpoints=[f"Cada 5 capítulos", "Revisión final"],
            metadata={
                'topic': topic,
                'pages': pages,
                'chapters': chapters,
                'audience': audience,
                'style': style
            }
        )

    def create_research_plan(
        self,
        topic: str,
        depth: str = "medium",
        output_format: str = "report"
    ) -> ExecutionPlan:
        """
        Crear plan de investigación.

        Args:
            topic: Tema a investigar
            depth: shallow, medium, deep
            output_format: report, summary, notes
        """
        plan_id = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        subtasks = []

        # Búsqueda inicial
        subtasks.append(SubTask(
            id=f"{plan_id}_01_search",
            title="Búsqueda inicial",
            description=f"Buscar información sobre: {topic}",
            agent="researcher",
            priority="HIGH",
            expected_output=f"~/wikirag/output/{plan_id}/search_results.md",
            estimated_tokens=4000
        ))

        if depth in ("medium", "deep"):
            subtasks.append(SubTask(
                id=f"{plan_id}_02_analyze",
                title="Análisis de fuentes",
                description="Analizar y contrastar información encontrada",
                agent="researcher",
                priority="NORMAL",
                dependencies=[f"{plan_id}_01_search"],
                expected_output=f"~/wikirag/output/{plan_id}/analysis.md",
                estimated_tokens=4000
            ))

        if depth == "deep":
            subtasks.append(SubTask(
                id=f"{plan_id}_03_deep",
                title="Investigación profunda",
                description="Buscar fuentes adicionales y verificar datos",
                agent="researcher",
                priority="NORMAL",
                dependencies=[f"{plan_id}_02_analyze"],
                expected_output=f"~/wikirag/output/{plan_id}/deep_research.md",
                estimated_tokens=6000
            ))

        # Generar output
        last_dep = subtasks[-1].id
        subtasks.append(SubTask(
            id=f"{plan_id}_output",
            title=f"Generar {output_format}",
            description=f"Crear {output_format} final sobre {topic}",
            agent="writer",
            priority="HIGH",
            dependencies=[last_dep],
            expected_output=f"~/wikirag/output/{plan_id}/FINAL.md",
            estimated_tokens=4000
        ))

        return ExecutionPlan(
            id=plan_id,
            original_task=f"Investigar: {topic}",
            strategy="sequential",
            subtasks=subtasks,
            estimated_total_time="1-2 horas",
            checkpoints=["Después de cada fase"],
            metadata={'topic': topic, 'depth': depth, 'format': output_format}
        )

    def create_code_project_plan(
        self,
        description: str,
        language: str = "python",
        include_tests: bool = True
    ) -> ExecutionPlan:
        """
        Crear plan para proyecto de código.
        """
        plan_id = f"code_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        subtasks = []

        # Diseño
        subtasks.append(SubTask(
            id=f"{plan_id}_01_design",
            title="Diseño de arquitectura",
            description=f"Diseñar estructura del proyecto: {description}",
            agent="researcher",
            priority="HIGH",
            expected_output=f"~/wikirag/output/{plan_id}/design.md",
            estimated_tokens=2000
        ))

        # Implementación
        subtasks.append(SubTask(
            id=f"{plan_id}_02_implement",
            title="Implementar código",
            description=f"Escribir código {language} según diseño",
            agent="executor",
            priority="HIGH",
            dependencies=[f"{plan_id}_01_design"],
            expected_output=f"~/wikirag/output/{plan_id}/src/",
            estimated_tokens=6000
        ))

        if include_tests:
            subtasks.append(SubTask(
                id=f"{plan_id}_03_tests",
                title="Escribir tests",
                description="Crear tests unitarios",
                agent="executor",
                priority="NORMAL",
                dependencies=[f"{plan_id}_02_implement"],
                expected_output=f"~/wikirag/output/{plan_id}/tests/",
                estimated_tokens=4000
            ))

        # Documentación
        subtasks.append(SubTask(
            id=f"{plan_id}_04_docs",
            title="Documentar código",
            description="Crear README y documentación",
            agent="writer",
            priority="NORMAL",
            dependencies=[f"{plan_id}_02_implement"],
            expected_output=f"~/wikirag/output/{plan_id}/README.md",
            estimated_tokens=2000
        ))

        # Revisión
        subtasks.append(SubTask(
            id=f"{plan_id}_05_review",
            title="Code review",
            description="Revisar calidad del código",
            agent="reviewer",
            priority="HIGH",
            dependencies=[f"{plan_id}_02_implement"] + ([f"{plan_id}_03_tests"] if include_tests else []),
            expected_output=f"~/wikirag/output/{plan_id}/review.md",
            estimated_tokens=2000
        ))

        return ExecutionPlan(
            id=plan_id,
            original_task=description,
            strategy="hybrid",
            subtasks=subtasks,
            estimated_total_time="2-4 horas",
            checkpoints=["Después de implementación", "Después de tests"],
            metadata={'language': language, 'tests': include_tests}
        )

    def decompose_task(self, task: str) -> ExecutionPlan:
        """
        Descomponer tarea genérica en subtareas.
        Analiza el contenido y crea plan apropiado.
        """
        task_lower = task.lower()

        # Detectar tipo de tarea
        if any(w in task_lower for w in ['libro', 'book', '300 páginas', 'capítulos']):
            # Extraer parámetros
            pages = 300
            for word in task.split():
                if word.isdigit() and int(word) > 50:
                    pages = int(word)
                    break
            return self.create_book_plan(task, pages=pages)

        elif any(w in task_lower for w in ['código', 'script', 'programa', 'implementar']):
            lang = "python"
            if "javascript" in task_lower or "js" in task_lower:
                lang = "javascript"
            elif "bash" in task_lower:
                lang = "bash"
            return self.create_code_project_plan(task, language=lang)

        elif any(w in task_lower for w in ['investiga', 'research', 'analiza', 'busca información']):
            depth = "deep" if "profund" in task_lower else "medium"
            return self.create_research_plan(task, depth=depth)

        else:
            # Plan genérico
            return self._create_generic_plan(task)

    def _create_generic_plan(self, task: str) -> ExecutionPlan:
        """Crear plan genérico para tareas no categorizadas"""
        plan_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        subtasks = [
            SubTask(
                id=f"{plan_id}_01_analyze",
                title="Analizar tarea",
                description=f"Analizar requerimientos: {task}",
                agent="researcher",
                priority="HIGH",
                expected_output=f"~/wikirag/output/{plan_id}/analysis.md",
                estimated_tokens=2000
            ),
            SubTask(
                id=f"{plan_id}_02_execute",
                title="Ejecutar tarea",
                description="Ejecutar según análisis",
                agent="executor",
                priority="NORMAL",
                dependencies=[f"{plan_id}_01_analyze"],
                expected_output=f"~/wikirag/output/{plan_id}/result.md",
                estimated_tokens=4000
            ),
            SubTask(
                id=f"{plan_id}_03_verify",
                title="Verificar resultado",
                description="Verificar que el resultado cumple requerimientos",
                agent="reviewer",
                priority="NORMAL",
                dependencies=[f"{plan_id}_02_execute"],
                expected_output=f"~/wikirag/output/{plan_id}/verification.md",
                estimated_tokens=1000
            )
        ]

        return ExecutionPlan(
            id=plan_id,
            original_task=task,
            strategy="sequential",
            subtasks=subtasks,
            estimated_total_time="30 minutos - 1 hora",
            checkpoints=["Después de análisis", "Después de ejecución"]
        )

    def save_plan(self, plan: ExecutionPlan) -> Path:
        """Guardar plan como archivo .plan"""
        filepath = self.plans_dir / f"{plan.id}.plan"

        content = {
            'id': plan.id,
            'original_task': plan.original_task,
            'strategy': plan.strategy,
            'estimated_time': plan.estimated_total_time,
            'checkpoints': plan.checkpoints,
            'rollback_plan': plan.rollback_plan,
            'metadata': plan.metadata,
            'subtasks': [
                {
                    'id': st.id,
                    'title': st.title,
                    'description': st.description,
                    'agent': st.agent,
                    'priority': st.priority,
                    'dependencies': st.dependencies,
                    'expected_output': st.expected_output,
                    'estimated_tokens': st.estimated_tokens,
                    'validation_criteria': st.validation_criteria
                }
                for st in plan.subtasks
            ],
            'created_at': datetime.now().isoformat()
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)

        logger.info(f"📋 Plan guardado: {filepath}")
        return filepath

    def execute_plan(self, plan: ExecutionPlan) -> List[FileTask]:
        """
        Convertir plan en tareas ejecutables y encolarlas.

        Returns:
            Lista de FileTask creadas
        """
        # Crear directorio de output
        output_dir = Path.home() / "wikirag" / "output" / plan.id
        output_dir.mkdir(parents=True, exist_ok=True)

        tasks = []
        for subtask in plan.subtasks:
            # Crear tarea en la cola
            content = f"""# {subtask.title}

{subtask.description}

## Detalles
- Agente: {subtask.agent}
- Output esperado: {subtask.expected_output}
- Tokens estimados: {subtask.estimated_tokens}

## Criterios de validación
{chr(10).join(f'- {c}' for c in subtask.validation_criteria) if subtask.validation_criteria else '- Completar tarea correctamente'}
"""

            task = self.fq.create_task(
                content=content,
                priority=TaskPriority[subtask.priority],
                agent=subtask.agent,
                dependencies=subtask.dependencies,
                parent_id=plan.id
            )
            task.metadata['expected_output'] = subtask.expected_output
            task.metadata['plan_id'] = plan.id
            tasks.append(task)

        logger.info(f"📋 Plan {plan.id} convertido en {len(tasks)} tareas")
        return tasks


# ============================================================
# CLI
# ============================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="WikiRAG Strategic Agent")
    parser.add_argument('command', choices=['analyze', 'plan', 'book', 'research', 'code'])
    parser.add_argument('--task', '-t', help="Descripción de la tarea")
    parser.add_argument('--pages', '-p', type=int, default=300)
    parser.add_argument('--execute', '-e', action='store_true', help="Crear tareas en la cola")

    args = parser.parse_args()

    agent = StrategicAgent()

    if args.command == 'analyze':
        if not args.task:
            print("❌ Se requiere --task")
        else:
            analysis = agent.analyze_complexity(args.task)
            print("\n📊 Análisis de Complejidad")
            print("=" * 40)
            print(f"Palabras: {analysis['word_count']}")
            print(f"Score: {analysis['score']}")
            print(f"Necesita planificación: {'Sí' if analysis['needs_planning'] else 'No'}")
            print(f"Subtareas estimadas: {analysis['estimated_subtasks']}")
            print("\nIndicadores:")
            for k, v in analysis['indicators'].items():
                if v:
                    print(f"  ✓ {k}")

    elif args.command == 'plan':
        if not args.task:
            print("❌ Se requiere --task")
        else:
            plan = agent.decompose_task(args.task)
            filepath = agent.save_plan(plan)
            print(f"\n📋 Plan creado: {plan.id}")
            print(f"   Estrategia: {plan.strategy}")
            print(f"   Subtareas: {len(plan.subtasks)}")
            print(f"   Tiempo estimado: {plan.estimated_total_time}")
            print(f"   Archivo: {filepath}")

            if args.execute:
                tasks = agent.execute_plan(plan)
                print(f"\n✅ {len(tasks)} tareas creadas en la cola")

    elif args.command == 'book':
        if not args.task:
            args.task = "Machine Learning para principiantes"

        plan = agent.create_book_plan(args.task, pages=args.pages)
        filepath = agent.save_plan(plan)

        print(f"\n📚 Plan de Libro Creado")
        print("=" * 40)
        print(f"Tema: {args.task}")
        print(f"Páginas: {args.pages}")
        print(f"Capítulos: {plan.metadata['chapters']}")
        print(f"Subtareas: {len(plan.subtasks)}")
        print(f"Tiempo estimado: {plan.estimated_total_time}")

        if args.execute:
            tasks = agent.execute_plan(plan)
            print(f"\n✅ {len(tasks)} tareas encoladas")

    elif args.command == 'research':
        if not args.task:
            args.task = "Últimos avances en LLMs"

        plan = agent.create_research_plan(args.task, depth="deep")
        filepath = agent.save_plan(plan)

        print(f"\n🔍 Plan de Investigación")
        print("=" * 40)
        print(f"Tema: {args.task}")
        print(f"Profundidad: deep")
        print(f"Subtareas: {len(plan.subtasks)}")

        if args.execute:
            tasks = agent.execute_plan(plan)
            print(f"\n✅ {len(tasks)} tareas encoladas")

    elif args.command == 'code':
        if not args.task:
            args.task = "Script de backup automático"

        plan = agent.create_code_project_plan(args.task)
        filepath = agent.save_plan(plan)

        print(f"\n💻 Plan de Código")
        print("=" * 40)
        print(f"Proyecto: {args.task}")
        print(f"Subtareas: {len(plan.subtasks)}")

        if args.execute:
            tasks = agent.execute_plan(plan)
            print(f"\n✅ {len(tasks)} tareas encoladas")
