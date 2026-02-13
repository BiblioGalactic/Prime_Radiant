# 🎯 PLAN DE ATAQUE - Funciones de Vanguardia

## Estado Actual del Sistema WikiRAG

### Componentes Existentes
| Componente | Archivo | Estado |
|------------|---------|--------|
| Orquestador | `core/orchestrator.py` | ✅ Funcional |
| RAG Manager | `core/rag_manager.py` | ✅ 4.4M docs Wikipedia |
| Evaluador | `core/evaluator.py` | ⚠️ Básico (heurístico + LLM) |
| Planificador | `agents/planner.py` | ⚠️ Estático, no adaptativo |
| Ejecutor | `agents/executor.py` | ⚠️ Secuencial, sin feedback |
| Model Router | `core/model_router.py` | ✅ Multi-modelo |
| Estado Compartido | `core/shared_state.py` | ✅ SQLite |
| Cola | `core/queue_manager.py` | ✅ Thread-safe |

### Gaps Identificados
1. ❌ Sin RAG adaptativo (siempre k=3 docs)
2. ❌ Sin refinamiento de queries
3. ❌ Sin ciclos de recuperación iterativos
4. ❌ Sin memoria a largo plazo
5. ❌ Sin métricas de confianza sofisticadas
6. ❌ Sin crítico/refinador de respuestas

---

## 📋 MAPEO: Funciones Bash → Implementación Python

### FASE 1: RAG Adaptativo y Refinamiento de Queries

| Función Bash | Implementar en | Prioridad | Complejidad |
|--------------|----------------|-----------|-------------|
| `adaptive_retrieve()` | `rag_manager.py` | 🔴 ALTA | Media |
| `refine_query()` | `core/query_refiner.py` (NUEVO) | 🔴 ALTA | Media |
| `recursive_rag_loop()` | `core/orchestrator.py` | 🔴 ALTA | Alta |
| `hierarchical_chunks()` | `rag_manager.py` | 🟡 MEDIA | Media |

**Cambios necesarios:**
```python
# rag_manager.py - Añadir estrategias de retrieval
class AdaptiveRetriever:
    def retrieve(self, query: str, strategy: str = "balanced") -> List[SearchResult]:
        """
        Strategies:
        - "broad": k=50, threshold bajo → exploración
        - "focused": k=10, threshold alto → precisión
        - "balanced": k=20, threshold medio → default
        """

# query_refiner.py - NUEVO ARCHIVO
class QueryRefiner:
    def refine(self, query: str, context_docs: List[str]) -> str:
        """Usa LLM para reformular query basado en docs recuperados"""

    def expand(self, query: str) -> List[str]:
        """Genera variantes de la query para búsqueda múltiple"""
```

---

### FASE 2: Evaluación y Métricas de Calidad

| Función Bash | Implementar en | Prioridad | Complejidad |
|--------------|----------------|-----------|-------------|
| `quality_ok()` | `core/evaluator.py` | 🔴 ALTA | Baja |
| `compute_confidence()` | `core/evaluator.py` | 🔴 ALTA | Media |
| `critic_refine()` | `core/critic.py` (NUEVO) | 🟡 MEDIA | Media |

**Cambios necesarios:**
```python
# evaluator.py - Mejorar métricas
class ConfidenceCalculator:
    def compute(self, answer: str, query: str, context: str) -> float:
        """
        Métricas combinadas:
        1. Longitud normalizada
        2. Overlap semántico query-answer
        3. Coverage del contexto
        4. Ausencia de incertidumbre
        """

    def quality_ok(self, answer: str, threshold: float = 0.5) -> bool:
        return self.compute(answer, ...) > threshold

# critic.py - NUEVO ARCHIVO
class ResponseCritic:
    def evaluate_and_improve(self, draft: str, context_docs: List[str]) -> str:
        """Critic agent que evalúa y mejora respuestas"""
```

---

### FASE 3: Planificación Adaptativa Dinámica

| Función Bash | Implementar en | Prioridad | Complejidad |
|--------------|----------------|-----------|-------------|
| `generate_plan()` | `agents/planner.py` | 🟢 EXISTE | Mejorar |
| `cot_prompt()` | `core/prompts.py` (NUEVO) | 🟡 MEDIA | Baja |
| `react_step()` | `agents/react_agent.py` (NUEVO) | 🟡 MEDIA | Alta |
| `pipeline_planner_rag()` | `core/orchestrator.py` | 🔴 ALTA | Alta |

**Cambios necesarios:**
```python
# agents/planner.py - Mejorar planificación
class AdaptivePlanner:
    def generate_plan(self, query: str, tools: List[str], complexity: float) -> Plan:
        """
        Plan dinámico basado en:
        1. Complejidad estimada de la query
        2. Tools disponibles
        3. Historial de planes similares (memoria)
        """

    def adjust_plan(self, plan: Plan, feedback: str) -> Plan:
        """Ajusta plan en runtime basado en feedback de ejecución"""

# agents/react_agent.py - NUEVO ARCHIVO
class ReActAgent:
    """
    Thought → Action → Observation loop
    Similar a ReAct paper
    """
    def step(self, question: str, state: Dict) -> Tuple[str, str]:
        """Returns (thought, action)"""
```

---

### FASE 4: Orquestación Multi-turno Adaptativa

| Función Bash | Implementar en | Prioridad | Complejidad |
|--------------|----------------|-----------|-------------|
| `multi_turn_adaptive()` | `core/orchestrator.py` | 🔴 ALTA | Alta |
| `rag_agent()` | `agents/rag_agent.py` (NUEVO) | 🟡 MEDIA | Media |
| `run_agents()` | `agents/executor.py` | 🟢 EXISTE | Mejorar |

**Cambios necesarios:**
```python
# orchestrator.py - Nuevo flujo principal
class AdaptiveOrchestrator:
    def process_query_adaptive(self, query: str) -> QueryResult:
        """
        Flujo:
        1. Retrieve (broad)
        2. Generate answer
        3. If needs_refinement:
           - Refine query
           - Retrieve (focused)
           - Regenerate
        4. Critic review
        5. Final answer
        """

    def decide_strategy(self, query: str, context: str) -> str:
        """Decide: broad, focused, iterative, agent-based"""
```

---

### FASE 5: Model Router Mejorado

| Función Bash | Implementar en | Prioridad | Complejidad |
|--------------|----------------|-----------|-------------|
| `choose_model_router()` | `core/model_router.py` | 🟢 EXISTE | Mejorar |

**Ya implementado**, pero mejorar:
```python
# model_router.py - Añadir complejidad estimada
class ModelRouter:
    def estimate_complexity(self, query: str, context: str) -> float:
        """
        Mejorar con:
        1. Embeddings de query
        2. Número de entidades detectadas
        3. Presencia de operadores lógicos
        4. Longitud y estructura
        """
```

---

### FASE 6: Memoria a Largo Plazo

| Componente | Archivo | Prioridad | Complejidad |
|------------|---------|-----------|-------------|
| Memoria Episódica | `core/memory.py` (NUEVO) | 🟡 MEDIA | Alta |
| Memoria Semántica | `core/memory.py` (NUEVO) | 🟡 MEDIA | Alta |
| Cache de Planes | `agents/plan_cache.py` (NUEVO) | 🟡 MEDIA | Media |

**Nuevos archivos:**
```python
# core/memory.py - NUEVO ARCHIVO
class LongTermMemory:
    """
    Tipos de memoria:
    1. Episódica: (query, response, rating) - conversaciones pasadas
    2. Semántica: (concept, facts) - conocimiento extraído
    3. Procedural: (task_type, best_plan) - planes exitosos
    """

    def remember(self, query: str, response: str, success: bool):
        """Almacena en SQLite con embeddings"""

    def recall(self, query: str, k: int = 5) -> List[Memory]:
        """Recupera memorias relevantes por similitud"""

    def consolidate(self):
        """Proceso nocturno: agrupa memorias similares"""
```

---

## 📊 ORDEN DE IMPLEMENTACIÓN PROPUESTO

### Sprint 1: Fundamentos (1-2 días)
1. ✅ `adaptive_retrieve()` en rag_manager.py
2. ✅ `quality_ok()` y `compute_confidence()` en evaluator.py
3. ✅ Mejorar `choose_model_router()` con complejidad

### Sprint 2: Refinamiento (2-3 días)
4. 🆕 `QueryRefiner` - query_refiner.py
5. 🆕 `ResponseCritic` - critic.py
6. ✅ `recursive_rag_loop()` en orchestrator.py

### Sprint 3: Adaptativo (3-4 días)
7. ✅ `multi_turn_adaptive()` en orchestrator.py
8. 🆕 `ReActAgent` - react_agent.py
9. ✅ `AdaptivePlanner` en planner.py

### Sprint 4: Memoria (2-3 días)
10. 🆕 `LongTermMemory` - memory.py
11. 🆕 `PlanCache` - plan_cache.py
12. Integración con orchestrator

---

## 🔧 FUNCIONES BASH → PYTHON: TRADUCCIÓN DIRECTA

```python
# === TRADUCCIONES 1:1 ===

# generate_plan() → Ya existe en AgentPlanner.create_plan()
# recursive_rag_loop() → NUEVO en Orchestrator.recursive_rag()
# refine_query() → NUEVO en QueryRefiner.refine()
# critic_refine() → NUEVO en ResponseCritic.evaluate_and_improve()
# adaptive_retrieve() → NUEVO en RAGManager.adaptive_search()
# run_agents() → Ya existe en AgentExecutor.execute_plan()
# hierarchical_chunks() → NUEVO en RAGManager.hierarchical_search()
# choose_model_router() → Ya existe en ModelRouter.select_model()
# cot_prompt() → NUEVO en PromptBuilder.chain_of_thought()
# quality_ok() → NUEVO en ConfidenceCalculator.quality_ok()
# compute_confidence() → NUEVO en ConfidenceCalculator.compute()
# react_step() → NUEVO en ReActAgent.step()
# multi_turn_adaptive() → NUEVO en Orchestrator.adaptive_loop()
# rag_agent() → NUEVO en RAGAgent (combina retrieve + critic)
# pipeline_planner_rag() → NUEVO en Orchestrator.pipeline_with_planning()
```

---

## 📁 NUEVOS ARCHIVOS A CREAR

```
wikirag/
├── core/
│   ├── query_refiner.py      # 🆕 Refinamiento de queries
│   ├── critic.py             # 🆕 Crítico de respuestas
│   ├── memory.py             # 🆕 Memoria a largo plazo
│   └── prompts.py            # 🆕 Templates de prompts (CoT, ReAct)
├── agents/
│   ├── react_agent.py        # 🆕 Agente ReAct
│   ├── rag_agent.py          # 🆕 Agente RAG especializado
│   └── plan_cache.py         # 🆕 Cache de planes exitosos
```

---

## 🎯 MÉTRICAS DE ÉXITO

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Respuestas OK primer intento | ~40% | >70% |
| Tiempo promedio respuesta | 30-60s | <20s |
| Uso de agentes innecesario | Alto | Bajo |
| Calidad percibida | Media | Alta |
| Memoria entre sesiones | ❌ | ✅ |
| Adaptación a complejidad | ❌ | ✅ |

---

## ⚠️ RIESGOS Y MITIGACIONES

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Demasiadas llamadas LLM | Lentitud | Caché agresivo, heurísticas primero |
| Loops infinitos de refinamiento | Sistema colgado | max_iterations estricto |
| Memoria crece sin límite | Disco lleno | TTL + cleanup periódico |
| Complejidad de debug | Desarrollo lento | Logging exhaustivo |

---

## 🚀 PRÓXIMOS PASOS

1. **Revisar este plan** - ¿Falta algo? ¿Prioridades correctas?
2. **Decidir Sprint 1** - ¿Empezamos con adaptive_retrieve?
3. **Crear tests** - Antes de implementar
4. **Implementar incrementalmente** - Una función a la vez

---

*Plan creado: $(date)*
*Sistema: WikiRAG v2.0 - Arquitectura de Vanguardia*
