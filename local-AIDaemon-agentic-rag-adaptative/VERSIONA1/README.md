# WikiRAG v1.0 - Sistema de IA con Agentes y RAGs

## 🚀 Arquitectura de Vanguardia

Sistema local de IA que combina:
- **RAG Adaptativo**: Estrategias broad/focused/balanced/iterative
- **Multi-Modelo**: 12+ modelos GGUF con selección inteligente
- **Sistema de Triaje**: Modelos grandes como último recurso
- **Memoria a Largo Plazo**: Episódica, semántica, procedural
- **Agentes ReAct**: Razonamiento paso a paso

## 📁 Estructura

```
VERSIONA1/
├── core/                 # Núcleo del sistema
│   ├── orchestrator.py   # Orquestador principal
│   ├── daemon_interface.py # Interface con llama-cli
│   ├── rag_manager.py    # Gestión de RAGs
│   ├── model_router.py   # Selección inteligente de modelos
│   ├── evaluator.py      # Evaluación de respuestas
│   ├── query_refiner.py  # Refinamiento de queries
│   ├── critic.py         # Crítico de respuestas
│   ├── memory.py         # Memoria a largo plazo
│   ├── prompts.py        # Templates CoT/ReAct
│   └── config.py         # Configuración
├── agents/               # Sistema de agentes
│   ├── react_agent.py    # Agente ReAct
│   ├── rag_agent.py      # Agente RAG especializado
│   ├── plan_cache.py     # Cache de planes
│   ├── planner.py        # Planificador
│   └── executor.py       # Ejecutor de planes
└── scripts/              # Scripts de inicio
    └── start_orchestrator.sh
```

## ⚙️ Configuración

### Rutas de Modelos

Editar `core/config.py`:

```python
# Ruta base de modelos
MODELOS_BASE = os.path.expanduser("~/modelo/modelos_grandes")

# llama-cli
LLAMA_CLI = os.path.expanduser("~/modelo/llama.cpp/build/bin/llama-cli")
```

### Sistema de Triaje

Los modelos se clasifican en tiers:

| Tier | Parámetros | Uso | Throttle |
|------|------------|-----|----------|
| TINY | <2B | Evaluación rápida | 0ms |
| SMALL | 2-7B | Default | 0ms |
| MEDIUM | 7-13B | Consultas medias | 0ms |
| LARGE | 13-30B | Consultas complejas | 20ms |
| GIANT | 30B+ | ÚLTIMO RECURSO | 100ms |

**Puntuación de Triaje**:
```
score = complejidad × 10 + fallos_previos × 25
```

- Score < 30: TINY/SMALL
- Score 30-59: MEDIUM permitido
- Score 60-94: LARGE permitido
- Score 95+: GIANT permitido (casi imposible sin múltiples fallos)

## 🚀 Uso

### Modo Interactivo

```bash
cd scripts
./start_orchestrator.sh -i
```

### Comandos

```
salir         - Terminar
status        - Ver estado del sistema
adaptive on   - Activar modo adaptativo
adaptive off  - Desactivar modo adaptativo
```

## 🔧 Dependencias

```bash
pip install sentence-transformers faiss-cpu numpy
```

## 📊 Características

### RAG Adaptativo

- **BROAD**: k=50, exploración amplia
- **FOCUSED**: k=10, precisión alta
- **BALANCED**: k=20, balance
- **ITERATIVE**: Refinamiento recursivo

### Memoria a Largo Plazo

- **Episódica**: Guarda (query, response, rating)
- **Semántica**: Conocimiento extraído
- **Procedural**: Planes exitosos

### Agente ReAct

Ciclo Thought → Action → Observation:
- SEARCH: Buscar en RAG
- LOOKUP: Buscar término
- CALCULATE: Cálculo matemático
- VERIFY: Verificar información
- ANSWER: Respuesta final

## 📝 Versión

- **Versión**: A1 (Alpha 1)
- **Fecha**: Enero 2026
- **Autor**: Sistema WikiRAG

## ⚠️ Notas

- Los modelos GIANT (70B+) requieren puntuación 95+ para activarse
- El throttle en modelos grandes evita sobrecarga de RAM
- La terminal se restaura automáticamente después de cada consulta
