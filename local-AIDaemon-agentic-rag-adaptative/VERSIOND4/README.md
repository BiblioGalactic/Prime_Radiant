# WikiRAG D4 - Sistema Inteligente de Recuperación Aumentada por Generación

![Version](https://img.shields.io/badge/version-D4-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-green)
![License](https://img.shields.io/badge/license-MIT-brightgreen)

## Descripción

**WikiRAG D4** es una versión completa y **portable** del sistema de Recuperación Aumentada por Generación (RAG). Puede copiarse a cualquier ubicación y funcionar sin cambios de configuración gracias a rutas relativas automáticas.

### Características Principales

- ✅ **Completamente Portable**: Copiar a cualquier carpeta y funciona
- ✅ **Enrutamiento Inteligente**: Clasificación automática de intenciones
- ✅ **RAG Avanzado**: Búsqueda híbrida semántica + palabras clave
- ✅ **Bypass de RAG**: Detecta rutas de filesystem y evita Wikipedia
- ✅ **Toma de Decisiones**: ToolDecider para elegir herramientas correctas
- ✅ **Múltiples Modelos**: Soporta qwen, mistral, deepseek, llama, etc.
- ✅ **Modo Interactivo**: Shell integrada para consultas
- ✅ **Procesamiento por Lotes**: Procesa archivos de múltiples consultas
- ✅ **Arquitectura Modular**: Componentes independientes y reutilizables

## Estructura del Proyecto

```
VERSIOND4/
├── core/                          # Módulos principales
│   ├── __init__.py               # Exporta API pública
│   ├── config.py                 # Config original (fallback)
│   ├── config_portable.py        # ⭐ Config portátil con rutas relativas
│   ├── smart_router.py           # Enrutador inteligente (CON bypass RAG)
│   ├── intent_classifier.py      # Clasificador de intenciones
│   ├── tool_decider.py           # Decisor de herramientas (Capataz)
│   ├── rag_manager.py            # Gestor de RAG
│   ├── hybrid_search.py          # Búsqueda híbrida
│   ├── reranker.py               # Reranking de resultados
│   ├── orchestrator.py           # Orquestador de agentes
│   ├── evaluator.py              # Evaluador de calidad
│   ├── daemon_interface.py       # Interfaz con daemon
│   ├── memory.py                 # Gestor de memoria
│   ├── shared_state.py           # Estado compartido
│   ├── queue_manager.py          # Gestor de cola de mensajes
│   ├── mental_theater.py         # Pensamiento interno
│   ├── streaming.py              # Streaming de respuestas
│   ├── self_rag.py               # Self-RAG mejorado
│   ├── crag.py                   # Corrective RAG
│   ├── query_decomposer.py       # Descomposición de queries
│   ├── query_refiner.py          # Refinamiento de queries
│   ├── prompt_cache.py           # Cacheo de prompts
│   ├── critic.py                 # Crítica de respuestas
│   └── prompts.py                # Plantillas de prompts
├── data/                          # Directorio de datos (generado automáticamente)
│   ├── index/                    # Índices de RAG
│   ├── rags/                     # RAGs específicos
│   ├── logs/                     # Archivos de log
│   ├── queue/                    # Base de datos de cola
│   ├── pipes/                    # Pipes para comunicación
│   ├── personalities/            # Personalidades de agentes
│   └── models/ (opcional)        # Modelos GGUF locales
├── main.py                        # ⭐ Punto de entrada principal
├── requirements.txt              # Dependencias Python
├── README.md                      # Este archivo
└── LICENSE                        # Licencia MIT


## Instalación

### 1. Clonar o Descargar

```bash
# Opción A: Clonar desde repositorio
git clone <repo> wikirag-d4
cd wikirag-d4

# Opción B: Copiar carpeta existente
cp -r /path/to/VERSIOND4 wikirag-d4
cd wikirag-d4
```

### 2. Crear Entorno Virtual

```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Dependencia Especial: llama-cpp-python

Este proyecto requiere `llama-cpp-python` para ejecutar modelos GGUF localmente.

#### En Linux/Mac:

```bash
# Instalación automática (recomendado)
pip install llama-cpp-python --no-cache-dir

# Si la anterior falla, instalar con compilación manual
CMAKE_ARGS="-DLLAMA_CUDA=ON" pip install llama-cpp-python --no-cache-dir
```

#### En Windows:

```bash
# Con CUDA (si tienes GPU NVIDIA)
SET CMAKE_ARGS=-DLLAMA_CUDA=ON
pip install llama-cpp-python --no-cache-dir

# Sin CUDA
pip install llama-cpp-python --no-cache-dir
```

### 5. Inicializar Estructura de Datos

```bash
python main.py --init-data
```

Esto crea los directorios necesarios en `data/`:
- `data/logs/` - Archivos de log
- `data/queue/` - Base de datos SQLite
- `data/rags/` - Índices RAG
- `data/pipes/` - Pipes de IPC
- `data/personalities/` - Personalidades de agentes

## Uso

### Modo Interactivo (Recomendado)

```bash
python main.py
```

Luego escribe tus consultas:

```
📝 > ¿Qué es machine learning?
📤 Respuesta: [respuesta aquí]

📝 > lista los archivos de /tmp
📤 Respuesta: [listado de archivos]

📝 > help
📤 [muestra comandos disponibles]

📝 > exit
👋 ¡Hasta luego!
```

### Consulta Única

```bash
# Consulta simple
python main.py -q "¿Qué es Python?"

# Con contexto adicional
python main.py -q "¿Cómo se usa esto?" -c "contexto específico"
```

### Procesamiento por Lotes

```bash
# Crear archivo queries.txt
echo "¿Qué es AI?" > queries.txt
echo "Lista los archivos" >> queries.txt
echo "¿Cómo funciona RAG?" >> queries.txt

# Procesar
python main.py --batch queries.txt
```

### Ver Estado del Sistema

```bash
python main.py --status
```

Ejemplo de salida:

```
📊 ESTADO DEL SISTEMA
======================================================================
  ✅ initialized: True
  ✅ verbose: False
  📍 config_dir: /path/to/VERSIOND4
  ✅ router_available: True
  ✅ classifier_available: True
======================================================================
```

### Ver Configuración

```bash
python main.py --config
```

## Características Principales

### 1. Bypass Automático de RAG para Paths

El sistema detecta automáticamente cuando mencionas rutas de archivo y **evita buscar en Wikipedia**.

```bash
# Esto detecta la ruta y la busca en filesystem
📝 > lista los archivos de /home/usuario/proyecto

# Esto también funciona
📝 > cat ~/logs/debug.log

# Y esto
📝 > ls -la ./data/
```

**Cómo funciona:**
- Detecta patrones de ruta (`/path`, `~/path`, `./path`, `../path`)
- Reconoce keywords como: "listar", "archivo", "carpeta", "ls", "cat", etc.
- Automáticamente redirige a handler de filesystem en lugar de RAG

### 2. Clasificación Inteligente de Intenciones

El sistema clasifica automáticamente cada consulta en:

- **INFORMATIVE**: Búsqueda en documentos (RAG)
- **ACTION**: Ejecución de herramientas (CLI, filesystem)
- **SYSTEM**: Comandos internos (help, status, exit)
- **HYBRID**: Combina RAG + acción
- **CONVERSATIONAL**: Chat natural

### 3. Toma de Decisiones (ToolDecider)

El "Capataz" decide automáticamente:

- Qué herramienta usar (filesystem, git, API, etc.)
- Si ejecutar directamente o a través de un agente
- Parámetros y configuración

Ejemplo: Para "lista archivos de /tmp", ToolDecider decide:
- Tool: `filesystem_list`
- Params: `{"path": "/tmp"}`
- Execute directly: ✅ (no necesita agente)

### 4. RAG Avanzado

#### Búsqueda Híbrida
- Búsqueda semántica (basada en embeddings)
- Búsqueda por palabras clave (BM25)
- Combinación inteligente de resultados

#### Self-RAG
- Valida si la respuesta es relevante
- Regenera si no es suficientemente buena
- Mantiene métricas de confianza

#### CRAG (Corrective RAG)
- Evaluación de retrieved documents
- Routing a web search si es necesario
- Mejora de precisión

### 5. Memoria y Estado Compartido

- **Memory**: Retiene historial conversacional
- **SharedState**: Estado sincronizado entre agentes
- **PromptCache**: Cachea prompts frecuentes

## Configuración

### Usando config_portable.py

El archivo `core/config_portable.py` es la configuración principal. Detecta automáticamente:

```python
from core import CONFIG, get_portable_path

# Obtener ruta base
print(CONFIG.VERSIOND4_DIR)  # /path/to/VERSIOND4

# Obtener rutas relativas
db_path = get_portable_path("data/queue/queue.db")
log_path = get_portable_path("data/logs/daemon.log")
```

### Variables de Entorno Opcionales

Crear `.env` en el directorio raíz:

```bash
# Rutas personalizadas (opcional)
WIKIRAG_DATA_DIR=/custom/data/path
WIKIRAG_MODELS_DIR=/custom/models/path

# Logging
LOG_LEVEL=INFO
LOG_FILE=./data/logs/wikirag.log

# LLM
LLAMA_THREADS=4
LLAMA_CONTEXT_SIZE=2048
```

## Agregar Modelos Locales

### Opción A: Modelos en `data/models/`

```bash
# Crear estructura
mkdir -p data/models/qwen3
mkdir -p data/models/mistral
mkdir -p data/models/semantic

# Copiar modelos GGUF
cp /path/to/Qwen3-8B-Q4_K_M.gguf data/models/qwen3/
cp /path/to/Mistral-8B-Instruct.gguf data/models/mistral/
```

### Opción B: Modelos en Home

Alternativamente, mantener modelos en `~/modelo/`:

```bash
# El sistema los busca automáticamente en:
# 1. ./data/models/ (local)
# 2. ~/modelo/modelos_grandes/ (home)
```

## Arquitectura

### Flujo de Procesamiento

```
Query Usuario
    ↓
1️⃣ IntentClassifier
   └─ Clasifica intención (INFORMATIVE, ACTION, SYSTEM, etc.)
    ↓
2️⃣ SmartRouter
   ├─ Detecta paths explícitos (BYPASS RAG)
   └─ Enruta al handler correcto
    ↓
3️⃣ Handlers Específicos
   ├─ RAG Handler (consultas informativas)
   ├─ MCP Handler (acciones)
   ├─ System Handler (comandos)
   └─ Hybrid Handler (combo)
    ↓
4️⃣ ToolDecider (si es ACTION)
   ├─ Decide herramienta exacta
   ├─ Genera orden directa
   └─ Ejecuta o delega a agente
    ↓
📤 Respuesta Final
```

### Componentes Principales

| Componente | Responsabilidad |
|------------|-----------------|
| **SmartRouter** | Enrutamiento inteligente de consultas |
| **IntentClassifier** | Clasificación de intenciones |
| **ToolDecider** | Selección y parametrización de herramientas |
| **RAGManager** | Gestión de índices y búsqueda |
| **HybridSearch** | Búsqueda semántica + palabras clave |
| **Orchestrator** | Orquestación de agentes y tareas |
| **Evaluator** | Evaluación de calidad de respuestas |
| **MentalTheater** | Pensamiento interno y razonamiento |
| **PromptCache** | Cacheo inteligente de prompts |

## Ejemplos de Uso

### Ejemplo 1: Búsqueda Informativa

```bash
📝 > ¿Cuál es la capital de Francia?
📤 Respuesta:
   La capital de Francia es París. Es la ciudad más grande
   del país y la capital histórica, cultural y política...
```

**Flujo:**
1. IntentClassifier → INFORMATIVE
2. SmartRouter → RAG Handler
3. RAGManager → Búsqueda en índice
4. Respuesta generada con contexto

### Ejemplo 2: Acción con Filesystem

```bash
📝 > lista los archivos de /home/usuario/proyecto
📤 Respuesta:
   📁 Contenido de `/home/usuario/proyecto`:
   drwxr-xr-x 5 usuario usuario 4096 Feb 13 10:00 src/
   drwxr-xr-x 3 usuario usuario 4096 Feb 13 10:00 tests/
   -rw-r--r-- 1 usuario usuario 1234 Feb 13 10:00 README.md
   ...
```

**Flujo:**
1. SmartRouter → Detecta path `/home/usuario/proyecto`
2. SmartRouter → Detecta keyword "lista"
3. BYPASS RAG activado → Redirige a ACTION
4. ToolDecider → `filesystem_list` tool
5. Ejecución directa
6. Respuesta con contenido real

### Ejemplo 3: Búsqueda + Acción

```bash
📝 > busca información sobre Python y crea un archivo con resultados
📤 Respuesta:
   📚 Información:
   Python es un lenguaje de programación...

   ⚡ Acción ejecutada:
   ✅ Archivo creado en /tmp/python_info.txt
```

**Flujo:**
1. IntentClassifier → HYBRID
2. SmartRouter → Hybrid Handler
3. Primero RAG búsqueda
4. Luego MCP acción (crear archivo)
5. Respuesta combinada

## Extensión y Personalización

### Agregar Nuevo Handler

```python
# En main.py o tu código
from core import get_smart_router

router = get_smart_router()

# Añadir handler personalizado
def my_custom_handler(query: str, context: str) -> str:
    # Tu lógica aquí
    return "Respuesta personalizada"

router.custom_handler = my_custom_handler
```

### Agregar Nuevo Clasificador de Intención

```python
from core import IntentClassifier, Intent

classifier = IntentClassifier()

# Personalizar clasificación
def classify_with_context(query: str):
    result = classifier.classify(query)
    # Tu lógica de refinamiento aquí
    return result
```

### Personalizar Prompts

```python
from core import SYSTEM_PROMPTS, get_prompt

# Ver prompts disponibles
print(SYSTEM_PROMPTS.keys())

# Usar prompt personalizado
prompt = get_prompt("custom_prompt_name")
```

## Solución de Problemas

### Problema: "llama-cpp-python no se instala"

**Solución:**

```bash
# En Linux/Mac
pip install llama-cpp-python --no-cache-dir --force-reinstall

# En Windows (con Visual Studio Build Tools)
set CMAKE_ARGS=-DLLAMA_OPENBLAS=ON
pip install llama-cpp-python --no-cache-dir
```

### Problema: "Módulo no encontrado"

**Solución:**

```bash
# Asegúrate de estar en el directorio correcto
cd /path/to/VERSIOND4

# Reinstalar en modo editable
pip install -e .
```

### Problema: "Las rutas están mal"

**Solución:**

```bash
# Verificar configuración
python main.py --config

# Inicializar directorios
python main.py --init-data

# Verificar estado
python main.py --status
```

### Problema: "RAG no encuentra resultados"

**Solución:**

1. Verificar que el índice existe: `data/index/wikipedia/`
2. Crear índice si no existe: `python -m core.rag_manager --build-index`
3. Usar modo verbose para debuggear: `python main.py --verbose`

## Desarrollo

### Estructura de Pruebas

```bash
# Crear directorio de tests
mkdir -p tests

# Test simple
python -c "from core import SmartRouter; print('✅ Imports OK')"
```

### Debug Mode

```bash
python main.py --verbose
```

Mostrará:
- Detalles de clasificación
- Información de enrutamiento
- Decisiones de ToolDecider
- Resultados de búsqueda

## Rendimiento

### Benchmarks (en máquina típica)

| Operación | Tiempo |
|-----------|--------|
| Clasificación de intención | 50-100ms |
| Búsqueda híbrida | 200-500ms |
| Generación con Mistral 7B | 2-5s |
| Generación con Qwen 8B | 3-8s |
| Ejecución CLI directa | 100-500ms |

### Optimizaciones

- **PromptCache**: Reutiliza prompts frecuentes
- **HybridSearch**: Combina rápida búsqueda de keywords + semántica
- **DirectExecution**: Evita agentes cuando es posible
- **StreamingLLM**: Respuestas en tiempo real

## API Programática

```python
from core import (
    get_smart_router,
    get_intent_classifier,
    get_rag_manager,
    CONFIG
)

# Inicializar componentes
router = get_smart_router(verbose=True)
classifier = get_intent_classifier()
rag = get_rag_manager()

# Procesar consulta
result = router.route("tu consulta")
print(result.response)

# Acceder a clasificación
classification = classifier.classify("otra consulta")
print(f"Intent: {classification.intent}")
print(f"Confidence: {classification.confidence:.0%}")

# Búsqueda directa
documents = rag.search("término de búsqueda", top_k=5)
for doc in documents:
    print(f"- {doc.title}: {doc.content[:100]}...")
```

## Licencia

MIT License - Ver archivo LICENSE

## Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Soporte

Para reportar problemas o hacer sugerencias:

- Crear un issue en GitHub
- Contactar al equipo de desarrollo

## Changelog

### Version D4 (Actual)

- ✨ Versión completamente portable
- ✨ Configuración con rutas relativas automáticas
- ✨ Bypass de RAG para operaciones de filesystem
- ✨ Toma de decisiones mejorada (ToolDecider)
- ✨ Arquitectura modular y limpia
- ✨ Interfaz CLI interactiva
- ✨ Documentación completa

### Versiones Anteriores

- **B2**: Beta con daemon persistente
- **A1**: Versión inicial prototipo

---

**Última actualización**: Febrero 2025

**Versión**: 1.0.0 (D4 Release)

**Estado**: ✅ Producción
