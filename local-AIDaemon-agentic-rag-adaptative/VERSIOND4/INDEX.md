# 📑 Índice de Archivos - WikiRAG D4

## Estructura Completa

### Raíz (11 archivos)

#### Ejecutables
- **main.py** - Punto de entrada principal del sistema
- **test_wikirag.py** - Suite de tests para verificar instalación

#### Configuración
- **setup.py** - Setup para instalación como paquete pip
- **requirements.txt** - Dependencias Python
- **__init__.py** - Inicializador del paquete

#### Documentación
- **README.md** - Documentación completa (16KB)
- **QUICKSTART.md** - Guía de inicio rápido
- **MANIFEST.md** - Checklist de contenido incluido
- **REFERENCE.md** - Referencia rápida de comandos
- **INDEX.md** - Este archivo

#### Control de Versiones
- **.gitignore** - Configuración de Git
- **LICENSE** - Licencia MIT

### core/ - Módulos Principales (24 archivos Python)

#### Configuración (3 archivos)
- **__init__.py** - Inicializador del core, exporta API pública
- **config.py** - Configuración original (fallback)
- **config_portable.py** - **NUEVO** Configuración portátil con rutas relativas automáticas

#### Enrutamiento (3 archivos)
- **smart_router.py** - Enrutador inteligente CON bypass de RAG para paths
- **intent_classifier.py** - Clasificador automático de intenciones
- **tool_decider.py** - Decisor de herramientas (El "Capataz")

#### RAG y Búsqueda (5 archivos)
- **rag_manager.py** - Gestor central de RAG
- **hybrid_search.py** - Búsqueda híbrida (semántica + palabras clave)
- **reranker.py** - Reranking inteligente de resultados
- **self_rag.py** - Self-RAG mejorado con validación automática
- **crag.py** - Corrective RAG (corrección automática de retrievals)

#### Orquestación (3 archivos)
- **orchestrator.py** - Orquestador de agentes y tareas
- **evaluator.py** - Evaluador de calidad de respuestas
- **daemon_interface.py** - Interfaz para comunicación con daemon

#### Estado y Memoria (4 archivos)
- **memory.py** - Gestor de memoria conversacional
- **shared_state.py** - Estado compartido entre agentes
- **queue_manager.py** - Gestor de cola de mensajes
- **prompt_cache.py** - Cacheo inteligente de prompts frecuentes

#### Procesamiento de Queries (3 archivos)
- **query_decomposer.py** - Descomposición de queries complejas
- **query_refiner.py** - Refinamiento iterativo de queries
- **critic.py** - Crítica y validación de respuestas

#### LLM y Generación (2 archivos)
- **streaming.py** - Streaming de respuestas en tiempo real
- **mental_theater.py** - Pensamiento interno y razonamiento

#### Utilidades (1 archivo)
- **prompts.py** - Plantillas de prompts del sistema

### data/ - Estructura de Datos (autogenerada)

Generada automáticamente al ejecutar `python main.py --init-data`

- **logs/** - Archivos de log
- **queue/** - Base de datos SQLite para cola de mensajes
- **index/** - Índices de búsqueda RAG
- **rags/** - RAGs específicos por tema
- **pipes/** - Pipes IPC para comunicación inter-proceso
- **personalities/** - Personalidades de agentes

### agents/ - Estructura Base

Directorio para agentes (estructura presente, no editado)

### scripts/ - Utilidades

Directorio para scripts de utilidad (estructura presente)


## Mapeo de Características a Archivos

### Portabilidad
- ✅ **config_portable.py** - Rutas relativas automáticas
- ✅ **main.py** - Interfaz portable

### Inteligencia
- ✅ **intent_classifier.py** - Clasificación de intenciones
- ✅ **smart_router.py** - Enrutamiento inteligente
- ✅ **tool_decider.py** - Selección de herramientas

### RAG Avanzado
- ✅ **hybrid_search.py** - Búsqueda múltiple
- ✅ **self_rag.py** - Validación automática
- ✅ **crag.py** - Corrección automática
- ✅ **reranker.py** - Reranking

### Bypass de RAG
- ✅ **smart_router.py** - Detecta rutas explícitas
- ✅ **intent_classifier.py** - Clasifica como ACTION/FILESYSTEM

### Interfaz
- ✅ **main.py** - CLI completa
- ✅ **__init__.py (raíz)** - API programática

### Testing
- ✅ **test_wikirag.py** - Suite de tests


## Líneas de Código por Archivo

```
core/config_portable.py     ~300 líneas (NUEVO)
core/smart_router.py        ~700 líneas (CON bypass RAG)
core/orchestrator.py        ~2000 líneas
core/rag_manager.py         ~1200 líneas
core/intent_classifier.py   ~600 líneas
core/tool_decider.py        ~500 líneas
core/memory.py              ~400 líneas
core/hybrid_search.py       ~500 líneas
core/evaluator.py           ~600 líneas
core/daemon_interface.py    ~700 líneas
core/mental_theater.py      ~600 líneas
core/query_decomposer.py    ~500 líneas
core/streaming.py           ~350 líneas
core/critic.py              ~400 líneas
core/query_refiner.py       ~400 líneas
core/prompt_cache.py        ~350 líneas
core/shared_state.py        ~300 líneas
core/queue_manager.py       ~350 líneas
core/reranker.py            ~400 líneas
core/self_rag.py            ~500 líneas
core/crag.py                ~700 líneas
core/memory.py              ~400 líneas
core/prompts.py             ~350 líneas
core/__init__.py            ~300 líneas (NUEVO)

main.py                     ~350 líneas (NUEVO)
test_wikirag.py            ~250 líneas (NUEVO)
__init__.py                ~100 líneas (NUEVO)
config.py                  ~300 líneas (copiado)

TOTAL: ~15,000+ líneas de código
```


## Documentación Total

```
README.md                   ~16 KB (documentación completa)
QUICKSTART.md              ~3 KB (inicio rápido)
MANIFEST.md                ~8 KB (checklist)
REFERENCE.md               ~2 KB (referencia rápida)
INDEX.md                   ~3 KB (este archivo)

TOTAL: ~32 KB de documentación
```


## Archivos por Propósito

### NUEVOS (Creados para D4)
- config_portable.py - Configuración con rutas relativas
- main.py - Punto de entrada
- core/__init__.py - API pública
- __init__.py - Inicializador raíz
- test_wikirag.py - Tests
- README.md - Documentación
- QUICKSTART.md - Inicio rápido
- MANIFEST.md - Checklist
- REFERENCE.md - Referencia rápida
- setup.py - Setup
- requirements.txt - Dependencias
- .gitignore - Git config
- LICENSE - MIT
- INDEX.md - Este

### COPIADOS (Del core original)
- 22 archivos Python del core/
- Todos los módulos principales

### NO INCLUIDOS (Experimentales)
- agentic/ - experimental
- sandbox/ - experimental
- security/ - experimental
- self_learning.py - experimental
- claude_style/ - experimental


## Guía de Lectura

1. **Primero**: `QUICKSTART.md` - 5 minutos
2. **Luego**: `README.md` - Documentación completa
3. **Referencia**: `REFERENCE.md` - Comandos rápidos
4. **Verificación**: `MANIFEST.md` - Checklist
5. **Código**: Ver `core/` para implementación


## Cómo Encontrar Funcionalidades

### Quiero... → Ver archivo

- Usar el sistema → `main.py`
- Cambiar configuración → `core/config_portable.py`
- Entender intenciones → `core/intent_classifier.py`
- Agregar bypass → `core/smart_router.py`
- Cambiar búsqueda → `core/rag_manager.py` o `core/hybrid_search.py`
- Personalizar → `core/prompts.py`
- Depurar → `test_wikirag.py`
- Extender → `core/__init__.py` y `__init__.py`


---

**Total de Archivos**: 35+
**Tamaño**: ~600 KB
**Complejidad**: Modular y extensible
**Mantenibilidad**: Alta

✅ VERSIOND4 está completamente documentado e indexado.
