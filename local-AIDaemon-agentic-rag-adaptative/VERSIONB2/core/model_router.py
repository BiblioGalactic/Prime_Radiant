#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    MODEL ROUTER - Selector Inteligente de Modelos
========================================
Selecciona el modelo óptimo según la tarea, idioma y complejidad.
"""

import os
import sys
import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import logging

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ModelRouter")


class TaskType(Enum):
    """Tipos de tareas para selección de modelo"""
    GENERAL = "general"           # Consultas generales
    CODE = "code"                 # Código, programación
    PLANNING = "planning"         # Planificación de agentes
    EVALUATION = "evaluation"     # Evaluación rápida
    COMPLEX = "complex"           # Razonamiento complejo
    AGENT = "agent"               # Ejecución de agentes
    MEDICAL = "medical"           # Consultas médicas
    LEGAL = "legal"               # Consultas legales/éticas
    CREATIVE = "creative"         # Escritura creativa
    DEBATE = "debate"             # Análisis filosófico


class Language(Enum):
    """Idiomas detectados"""
    SPANISH = "es"
    ENGLISH = "en"
    GERMAN = "de"
    JAPANESE = "ja"
    CHINESE = "zh"
    MULTILINGUAL = "multi"


class ModelTier(Enum):
    """Niveles de modelos por consumo de recursos"""
    TINY = "tiny"        # < 2B params - Instantáneo
    SMALL = "small"      # 2-7B params - Rápido
    MEDIUM = "medium"    # 7-13B params - Normal
    LARGE = "large"      # 13-30B params - Lento
    GIANT = "giant"      # 30B+ params - Muy lento, último recurso


@dataclass
class ModelSpec:
    """Especificación de un modelo"""
    name: str
    path: str
    tasks: List[TaskType]
    languages: List[Language]
    ctx_size: int = 4096
    n_predict: int = 1000
    temperature: float = 0.7
    threads: int = 6
    repeat_penalty: float = 1.1
    priority: int = 5  # 1=más prioritario
    description: str = ""
    tier: ModelTier = ModelTier.SMALL  # Nivel de recursos
    min_complexity_score: int = 0  # Puntuación mínima para usar este modelo
    throttle_delay: float = 0.0  # Delay entre tokens (para no quemar RAM)


@dataclass
class ModelSelection:
    """Resultado de selección de modelo"""
    model: ModelSpec
    reason: str
    confidence: float


class ModelRouter:
    """
    Router inteligente que selecciona el modelo óptimo.

    Criterios:
    1. Tipo de tarea (código, general, médico, etc.)
    2. Idioma detectado
    3. Complejidad estimada
    4. Disponibilidad del modelo
    """

    # === SISTEMA DE TRIAJE ===
    # Los modelos GIANT requieren puntuación casi imposible (95+)
    # La puntuación se calcula: complejidad * 10 + fallos_previos * 20
    # Una consulta normal: 2*10 = 20 puntos
    # Consulta compleja: 5*10 = 50 puntos
    # Consulta + 2 fallos: 5*10 + 2*20 = 90 puntos
    # Consulta + 3 fallos: 5*10 + 3*20 = 110 puntos (ahora sí usa GIANT)
    TRIAJE_THRESHOLD_GIANT = 95  # Mínimo para usar modelos gigantes
    TRIAJE_THRESHOLD_LARGE = 60  # Mínimo para usar modelos grandes

    # === CATÁLOGO DE MODELOS ===
    MODELS: Dict[str, ModelSpec] = {
        # === TIER TINY - Instantáneos ===
        "phi2": ModelSpec(
            name="phi2",
            path=os.path.expanduser("~/modelo/modelos_grandes/phi/phi-2.Q5_K_M.gguf"),
            tasks=[TaskType.EVALUATION],
            languages=[Language.ENGLISH],
            ctx_size=2048,
            n_predict=100,
            temperature=0.1,
            threads=4,
            priority=1,
            description="Ultra rápido para evaluación",
            tier=ModelTier.TINY,
            min_complexity_score=0
        ),

        "tinyllama": ModelSpec(
            name="tinyllama",
            path=os.path.expanduser("~/modelo/modelos_grandes/tiny/tinyllama-1.1b-chat-v1.0.Q5_K_M.gguf"),
            tasks=[TaskType.EVALUATION],
            languages=[Language.ENGLISH],
            ctx_size=2048,
            n_predict=100,
            temperature=0.1,
            threads=2,
            priority=1,
            description="Ultra ligero, pruebas rápidas",
            tier=ModelTier.TINY,
            min_complexity_score=0
        ),

        # === TIER SMALL - Rápidos (default) ===
        "mistral": ModelSpec(
            name="mistral",
            path=os.path.expanduser("~/modelo/modelos_grandes/M6/mistral-7b-instruct-v0.1.Q6_K.gguf"),
            tasks=[TaskType.GENERAL, TaskType.PLANNING],
            languages=[Language.ENGLISH, Language.SPANISH],
            ctx_size=4096,
            n_predict=1000,
            temperature=0.7,
            priority=2,
            description="Rápido, default para consultas simples",
            tier=ModelTier.SMALL,
            min_complexity_score=0
        ),

        "deepseek_coder": ModelSpec(
            name="deepseek_coder",
            path=os.path.expanduser("~/modelo/modelos_grandes/deep/deepseek-coder-6.7b-instruct.Q8_0.gguf"),
            tasks=[TaskType.CODE, TaskType.PLANNING, TaskType.AGENT],
            languages=[Language.ENGLISH],
            ctx_size=4096,
            n_predict=1500,
            temperature=0.3,
            priority=2,
            description="Código y razonamiento estructurado",
            tier=ModelTier.SMALL,
            min_complexity_score=0
        ),

        # === TIER MEDIUM - Normales ===
        "qwen3": ModelSpec(
            name="qwen3",
            path=os.path.expanduser("~/modelo/modelos_grandes/qwen3/Qwen3-8B-Q4_K_M.gguf"),
            tasks=[TaskType.GENERAL, TaskType.COMPLEX, TaskType.PLANNING],
            languages=[Language.MULTILINGUAL, Language.CHINESE, Language.ENGLISH, Language.SPANISH],
            ctx_size=4096,
            n_predict=1000,
            temperature=0.7,
            priority=3,
            description="Multilingüe, instrucciones complejas",
            tier=ModelTier.MEDIUM,
            min_complexity_score=20  # Consultas medias+
        ),

            temperature=0.5,
            priority=3,
            description="Decisiones, gestión, agentes",
            tier=ModelTier.MEDIUM,
            min_complexity_score=20
        ),

        "meditron": ModelSpec(
            name="meditron",
            path=os.path.expanduser("~/modelo/modelos_grandes/meditron/meditron-7b.Q5_0.gguf"),
            tasks=[TaskType.MEDICAL],
            languages=[Language.ENGLISH],
            ctx_size=4096,
            n_predict=1000,
            temperature=0.3,
            priority=2,
            description="Consultas médicas",
            tier=ModelTier.SMALL,
            min_complexity_score=0
        ),

        # === TIER LARGE - Lentos, para consultas complejas ===
        "nous_hermes": ModelSpec(
            name="nous_hermes",
            path=os.path.expanduser("~/modelo/modelos_grandes/etica/nous-hermes-llama2-13b.Q4_K_M.gguf"),
            tasks=[TaskType.LEGAL],
            languages=[Language.ENGLISH],
            ctx_size=4096,
            n_predict=1000,
            temperature=0.3,
            priority=5,
            description="Precisión jurídica y ética",
            tier=ModelTier.LARGE,
            min_complexity_score=40,
            throttle_delay=0.02  # 20ms entre tokens
        ),

        "mythomax": ModelSpec(
            name="mythomax",
            path=os.path.expanduser("~/modelo/modelos_grandes/creatividad/mythomax-l2-13b.Q4_K_M.gguf"),
            tasks=[TaskType.CREATIVE],
            languages=[Language.ENGLISH],
            ctx_size=4096,
            n_predict=1500,
            temperature=0.9,
            priority=5,
            description="Narrativa, creatividad",
            tier=ModelTier.LARGE,
            min_complexity_score=40,
            throttle_delay=0.02
        ),

        "socrates": ModelSpec(
            name="socrates",
            path=os.path.expanduser("~/modelo/modelos_grandes/debate/digital-socrates-13b.Q4_K_M.gguf"),
            tasks=[TaskType.DEBATE],
            languages=[Language.ENGLISH],
            ctx_size=4096,
            n_predict=1000,
            temperature=0.7,
            priority=5,
            description="Razonamiento crítico, diálogo socrático",
            tier=ModelTier.LARGE,
            min_complexity_score=40,
            throttle_delay=0.02
        ),

        "wizardcoder": ModelSpec(
            name="wizardcoder",
            path=os.path.expanduser("~/modelo/modelos_grandes/wizard/WizardCoder-Python-13B-V1.0.Q5_K_M.gguf"),
            tasks=[TaskType.CODE],
            languages=[Language.ENGLISH],
            ctx_size=4096,
            n_predict=1500,
            temperature=0.2,
            priority=4,
            description="Python experto (fallback si deepseek falla)",
            tier=ModelTier.LARGE,
            min_complexity_score=40,
            throttle_delay=0.02
        ),

        # === TIER GIANT - ÚLTIMO RECURSO ABSOLUTO ===
        # Requiere puntuación 95+ (casi imposible sin múltiples fallos)
        "llama70b": ModelSpec(
            name="llama70b",
            path=os.path.expanduser("~/modelo/modelos_grandes/llama31-70b/Meta-Llama-3.1-70B-Instruct-Q4_K_M.gguf"),
            tasks=[TaskType.COMPLEX],  # SOLO para COMPLEX
            languages=[Language.MULTILINGUAL, Language.ENGLISH, Language.SPANISH],
            ctx_size=4096,  # Muy reducido
            n_predict=500,   # Muy reducido
            temperature=0.7,
            threads=2,       # Mínimo threads
            priority=99,     # Casi imposible de seleccionar
            description="⚠️ ÚLTIMO RECURSO - Solo si 3+ modelos fallan",
            tier=ModelTier.GIANT,
            min_complexity_score=95,  # Puntuación casi imposible
            throttle_delay=0.1  # 100ms entre tokens - muy lento deliberadamente
        ),
    }

    # Patrones para detectar tipo de tarea
    TASK_PATTERNS = {
        TaskType.CODE: [
            r'\b(código|code|programa|function|def |class |import |python|javascript|bash|script)\b',
            r'\b(error|bug|debug|compilar|ejecutar|run)\b',
            r'\b(api|endpoint|request|response|json|xml)\b',
        ],
        TaskType.MEDICAL: [
            r'\b(médic|medical|salud|health|síntoma|symptom|diagnóstico|diagnosis)\b',
            r'\b(enfermedad|disease|tratamiento|treatment|medicamento|drug)\b',
            r'\b(doctor|hospital|clínic|patient|paciente)\b',
        ],
        TaskType.LEGAL: [
            r'\b(legal|ley|law|jurídic|derecho|right|contrato|contract)\b',
            r'\b(demanda|lawsuit|tribunal|court|abogad|lawyer)\b',
            r'\b(ético|ethical|moral|norm|regulación)\b',
        ],
        TaskType.CREATIVE: [
            r'\b(escrib|write|historia|story|cuento|tale|poema|poem)\b',
            r'\b(creativ|imagin|inventar|invent|ficción|fiction)\b',
            r'\b(personaje|character|narrativa|narrative)\b',
        ],
        TaskType.DEBATE: [
            r'\b(filosof|philosophy|ética|ethics|moral|argument)\b',
            r'\b(debate|discus|opinión|opinion|perspectiva)\b',
            r'\b(por qué|why|razón|reason|causa|cause)\b',
        ],
        TaskType.COMPLEX: [
            r'\b(explica detalladamente|explain in detail|analiza|analyze)\b',
            r'\b(compara|compare|diferencia|difference|ventaja|advantage)\b',
            r'\b(paso a paso|step by step|profundidad|depth)\b',
        ],
    }

    # Patrones para detectar idioma
    LANGUAGE_PATTERNS = {
        Language.SPANISH: [r'\b(qué|cómo|cuál|dónde|por qué|historia|ciudad|país)\b'],
        Language.GERMAN: [r'\b(was|wie|warum|Geschichte|Stadt|Land|ist|sind)\b'],
        Language.JAPANESE: [r'[\u3040-\u309f\u30a0-\u30ff]'],  # Hiragana/Katakana
        Language.CHINESE: [r'[\u4e00-\u9fff]'],  # Caracteres chinos
    }

    def __init__(self):
        """Inicializar router"""
        self.available_models = self._check_available_models()
        logger.info(f"ModelRouter: {len(self.available_models)} modelos disponibles")

    def _check_available_models(self) -> Dict[str, ModelSpec]:
        """Verificar qué modelos están disponibles en disco"""
        available = {}
        for name, spec in self.MODELS.items():
            if os.path.exists(spec.path):
                available[name] = spec
                logger.debug(f"  ✓ {name}")
            else:
                logger.debug(f"  ✗ {name} (no encontrado)")
        return available

    def detect_task_type(self, query: str) -> TaskType:
        """Detectar tipo de tarea desde la consulta"""
        query_lower = query.lower()

        for task_type, patterns in self.TASK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    return task_type

        return TaskType.GENERAL

    def detect_language(self, query: str) -> Language:
        """Detectar idioma de la consulta"""
        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return lang

        return Language.ENGLISH  # Default

    def estimate_complexity(self, query: str, context: str = "") -> int:
        """
        Estimar complejidad (1-5) con múltiples factores.

        Factores considerados:
        1. Longitud de la consulta
        2. Número de entidades detectadas
        3. Presencia de operadores lógicos
        4. Palabras que indican análisis profundo
        5. Estructura de la pregunta
        """
        complexity = 2  # Base

        query_lower = query.lower()

        # 1. Longitud de consulta
        if len(query) > 150:
            complexity += 0.5
        if len(query) > 300:
            complexity += 0.5
        if len(query) > 500:
            complexity += 0.5

        # 2. Contexto largo
        if len(context) > 1000:
            complexity += 0.5
        if len(context) > 3000:
            complexity += 0.5

        # 3. Palabras de análisis profundo
        deep_analysis_words = [
            'detalladamente', 'analiza', 'compara', 'explica', 'profundidad',
            'detail', 'analyze', 'compare', 'explain', 'depth', 'comprehensive',
            'exhaustivo', 'completo', 'todas las', 'each', 'every', 'diferencias',
            'similarities', 'pros y contras', 'advantages', 'disadvantages'
        ]
        deep_matches = sum(1 for w in deep_analysis_words if w in query_lower)
        complexity += min(deep_matches * 0.3, 1.0)

        # 4. Operadores lógicos y complejidad estructural
        logical_patterns = [
            r'\b(y también|and also|además|furthermore)\b',
            r'\b(pero|but|however|sin embargo)\b',
            r'\b(si|if|cuando|when|mientras)\b',
            r'\b(o|or|either|neither)\b',
            r'\b(primero|segundo|tercero|first|second|third)\b',
        ]
        for pattern in logical_patterns:
            if re.search(pattern, query_lower):
                complexity += 0.2

        # 5. Número de preguntas (múltiples ?)
        question_count = query.count('?')
        if question_count > 1:
            complexity += min(question_count * 0.3, 1.0)

        # 6. Detectar entidades (aproximación: palabras capitalizadas no al inicio)
        words = query.split()
        entities = [w for i, w in enumerate(words)
                   if i > 0 and w[0].isupper() and len(w) > 2]
        if len(entities) > 2:
            complexity += 0.5
        if len(entities) > 5:
            complexity += 0.5

        # 7. Consultas que requieren razonamiento multi-paso
        multistep_patterns = [
            r'\b(paso a paso|step by step)\b',
            r'\b(cómo|how).*(y luego|and then|después)\b',
            r'\b(por qué|why).*(causa|cause|razón|reason)\b',
        ]
        for pattern in multistep_patterns:
            if re.search(pattern, query_lower):
                complexity += 0.5
                break

        return min(int(round(complexity)), 5)

    def get_complexity_breakdown(self, query: str, context: str = "") -> Dict[str, Any]:
        """
        Obtener desglose detallado de la complejidad.

        Returns:
            Dict con factores individuales y score total
        """
        query_lower = query.lower()
        breakdown = {
            "length_factor": 0,
            "context_factor": 0,
            "analysis_words": 0,
            "logical_operators": 0,
            "question_count": 0,
            "entities": 0,
            "multistep": 0,
            "total": 0
        }

        # Longitud
        if len(query) > 150: breakdown["length_factor"] += 0.5
        if len(query) > 300: breakdown["length_factor"] += 0.5
        if len(query) > 500: breakdown["length_factor"] += 0.5

        # Contexto
        if len(context) > 1000: breakdown["context_factor"] += 0.5
        if len(context) > 3000: breakdown["context_factor"] += 0.5

        # Palabras de análisis
        deep_words = ['detalladamente', 'analiza', 'compara', 'explica', 'depth',
                     'comprehensive', 'exhaustivo', 'diferencias']
        breakdown["analysis_words"] = min(sum(1 for w in deep_words if w in query_lower) * 0.3, 1.0)

        # Preguntas múltiples
        breakdown["question_count"] = min(query.count('?') * 0.3, 1.0)

        # Entidades
        words = query.split()
        entities = [w for i, w in enumerate(words) if i > 0 and w[0].isupper() and len(w) > 2]
        if len(entities) > 2: breakdown["entities"] += 0.5
        if len(entities) > 5: breakdown["entities"] += 0.5

        # Total
        breakdown["total"] = min(int(round(2 + sum(v for k, v in breakdown.items() if k != "total"))), 5)

        return breakdown

    def calculate_triaje_score(
        self,
        complexity: int,
        previous_failures: int = 0,
        is_retry: bool = False
    ) -> int:
        """
        Calcular puntuación de triaje para determinar qué tier de modelo usar.

        Fórmula: complejidad * 10 + fallos_previos * 25 + (retry_bonus)

        Ejemplos:
        - Consulta simple (2): 2*10 = 20 → TINY/SMALL
        - Consulta media (3): 3*10 = 30 → SMALL
        - Consulta compleja (5): 5*10 = 50 → MEDIUM
        - Consulta compleja + 1 fallo: 5*10 + 25 = 75 → LARGE
        - Consulta compleja + 2 fallos: 5*10 + 50 = 100 → GIANT (¡por fin!)

        Args:
            complexity: Complejidad estimada (1-5)
            previous_failures: Número de fallos previos con modelos más pequeños
            is_retry: Si es un reintento

        Returns:
            Puntuación de triaje (0-100+)
        """
        base_score = complexity * 10
        failure_bonus = previous_failures * 25
        retry_bonus = 10 if is_retry else 0

        total = base_score + failure_bonus + retry_bonus

        logger.info(f"📊 Triaje: complexity={complexity} × 10 + failures={previous_failures} × 25 = {total}")
        return total

    def get_allowed_tiers(self, triaje_score: int) -> List[ModelTier]:
        """Obtener tiers permitidos según puntuación de triaje"""
        allowed = [ModelTier.TINY, ModelTier.SMALL]

        if triaje_score >= 30:
            allowed.append(ModelTier.MEDIUM)
        if triaje_score >= self.TRIAJE_THRESHOLD_LARGE:
            allowed.append(ModelTier.LARGE)
        if triaje_score >= self.TRIAJE_THRESHOLD_GIANT:
            allowed.append(ModelTier.GIANT)

        return allowed

    def select_model(
        self,
        query: str,
        task_type: TaskType = None,
        context: str = "",
        prefer_fast: bool = False,
        previous_failures: int = 0,
        is_retry: bool = False
    ) -> ModelSelection:
        """
        Seleccionar el modelo óptimo para una consulta con sistema de triaje.

        Args:
            query: Consulta del usuario
            task_type: Tipo de tarea (auto-detectado si None)
            context: Contexto adicional
            prefer_fast: Si preferir velocidad sobre calidad
            previous_failures: Número de fallos previos (para escalar a modelos grandes)
            is_retry: Si es un reintento

        Returns:
            ModelSelection con modelo seleccionado y razón
        """
        # Auto-detectar si no se especifica
        if task_type is None:
            task_type = self.detect_task_type(query)

        language = self.detect_language(query)
        complexity = self.estimate_complexity(query, context)

        # === SISTEMA DE TRIAJE ===
        triaje_score = self.calculate_triaje_score(complexity, previous_failures, is_retry)
        allowed_tiers = self.get_allowed_tiers(triaje_score)

        logger.info(f"🎯 Selección: task={task_type.value}, lang={language.value}, complexity={complexity}")
        logger.info(f"🎯 Triaje: score={triaje_score}, tiers_permitidos={[t.value for t in allowed_tiers]}")

        # Filtrar modelos por tarea Y tier permitido
        candidates = []
        for name, spec in self.available_models.items():
            # Verificar tier permitido
            if spec.tier not in allowed_tiers:
                continue

            # Verificar puntuación mínima del modelo
            if triaje_score < spec.min_complexity_score:
                continue

            if task_type in spec.tasks:
                # Verificar idioma
                if language in spec.languages or Language.MULTILINGUAL in spec.languages:
                    candidates.append(spec)

        # Si no hay candidatos específicos para la tarea, buscar GENERAL
        if not candidates:
            for spec in self.available_models.values():
                if spec.tier not in allowed_tiers:
                    continue
                if triaje_score < spec.min_complexity_score:
                    continue
                if TaskType.GENERAL in spec.tasks:
                    candidates.append(spec)

        # Fallback: cualquier modelo en tiers permitidos
        if not candidates:
            for spec in self.available_models.values():
                if spec.tier in allowed_tiers:
                    candidates.append(spec)

        # Último fallback: mistral siempre disponible
        if not candidates:
            if "mistral" in self.available_models:
                candidates = [self.available_models["mistral"]]
            else:
                candidates = list(self.available_models.values())[:1]

        if not candidates:
            raise ValueError("No hay modelos disponibles")

        # Ordenar por prioridad
        if prefer_fast:
            # Preferir modelos rápidos (baja prioridad = más rápido)
            candidates.sort(key=lambda m: m.priority)
        else:
            # Para tareas complejas, preferir modelos potentes
            if complexity >= 4:
                candidates.sort(key=lambda m: -m.ctx_size)  # Mayor contexto
            else:
                candidates.sort(key=lambda m: m.priority)

        selected = candidates[0]

        reason = f"Tarea: {task_type.value}, Idioma: {language.value}, Complejidad: {complexity}/5"
        confidence = 0.8 if task_type != TaskType.GENERAL else 0.6

        logger.info(f"✓ Seleccionado: {selected.name} - {selected.description}")

        return ModelSelection(
            model=selected,
            reason=reason,
            confidence=confidence
        )

    def get_model_for_task(self, task_type: TaskType) -> Optional[ModelSpec]:
        """Obtener modelo directo por tipo de tarea"""
        for spec in self.available_models.values():
            if task_type in spec.tasks:
                return spec
        return None

    def get_fast_evaluator(self) -> ModelSpec:
        """Obtener el modelo más rápido para evaluación"""
        # Intentar phi2 o tinyllama
        for name in ["phi2", "tinyllama"]:
            if name in self.available_models:
                return self.available_models[name]
        # Fallback a mistral
        return self.available_models.get("mistral", list(self.available_models.values())[0])

    def list_available(self) -> List[str]:
        """Listar modelos disponibles"""
        return list(self.available_models.keys())


# === Instancia global ===
_router: Optional[ModelRouter] = None


def get_router() -> ModelRouter:
    """Obtener router singleton"""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router


# === CLI para pruebas ===
if __name__ == "__main__":
    router = ModelRouter()

    print("=== Modelos Disponibles ===")
    for name in router.list_available():
        spec = router.available_models[name]
        print(f"  {name}: {spec.description}")

    print("\n=== Test de Selección ===")
    test_queries = [
        "¿Cuál es la historia de Barcelona?",
        "Write a Python function to sort a list",
        "¿Qué síntomas tiene la gripe?",
        "Analiza los aspectos éticos de la IA",
        "Escribe un cuento de fantasía",
        "¿Por qué existe el universo?",
    ]

    for query in test_queries:
        selection = router.select_model(query)
        print(f"\n📝 '{query[:40]}...'")
        print(f"   → {selection.model.name}: {selection.reason}")
