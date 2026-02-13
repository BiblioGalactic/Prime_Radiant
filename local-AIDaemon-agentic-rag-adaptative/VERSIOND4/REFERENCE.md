# WikiRAG D4 - Referencia Rápida

## Inicio Rápido

```bash
# Dentro de VERSIOND4/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Comandos CLI

| Comando | Descripción |
|---------|-------------|
| `python main.py` | Modo interactivo |
| `python main.py -q "consulta"` | Consulta única |
| `python main.py --batch archivo.txt` | Procesar lotes |
| `python main.py --status` | Ver estado |
| `python main.py --config` | Ver configuración |
| `python main.py --init-data` | Inicializar directorios |
| `python main.py --verbose` | Modo verbose |
| `python test_wikirag.py` | Ejecutar tests |

## Ejemplos de Uso

### Búsqueda Informativa
```bash
python main.py -q "¿Qué es machine learning?"
```

### Operación de Filesystem (BYPASS RAG automático)
```bash
python main.py -q "lista los archivos de /home"
python main.py -q "cat ~/logs/debug.log"
python main.py -q "ls -la ./data/"
```

### Procesamiento de Archivo
```bash
echo "¿Qué es Python?" > queries.txt
echo "¿Cómo funciona RAG?" >> queries.txt
python main.py --batch queries.txt
```

## Módulos Principales del Core

### Enrutamiento
- `smart_router.py` - Enrutador inteligente
- `intent_classifier.py` - Clasificador de intenciones
- `tool_decider.py` - Decisor de herramientas

### RAG
- `rag_manager.py` - Gestor de RAG
- `hybrid_search.py` - Búsqueda híbrida
- `self_rag.py` - Self-RAG
- `crag.py` - Corrective RAG

### Orquestación
- `orchestrator.py` - Orquestador
- `evaluator.py` - Evaluador
- `daemon_interface.py` - Interfaz daemon

### Utilidades
- `memory.py` - Memoria
- `prompt_cache.py` - Cache de prompts
- `mental_theater.py` - Pensamiento interno

## Configuración

El sistema usa `config_portable.py` que detecta automáticamente:
- Ubicación de VERSIOND4
- Rutas de datos (relativas)
- Rutas de logs y bases de datos
- Rutas de índices

### Personalización

En Python:
```python
from core import CONFIG, get_smart_router

cfg = CONFIG
router = get_smart_router()

# Usar
result = router.route("tu consulta")
print(result.response)
```

## Estructura de Directorios

```
VERSIOND4/
├── core/              # 24 módulos Python
├── data/              # Datos (autogenerado)
│   ├── logs/
│   ├── queue/
│   ├── rags/
│   └── index/
├── main.py
├── requirements.txt
└── README.md
```

## Características de Intenciones

| Intención | Descripción | Ejemplo |
|-----------|-------------|---------|
| INFORMATIVE | Búsqueda en documentos | "¿Qué es Python?" |
| ACTION | Ejecutar herramientas | "lista los archivos" |
| SYSTEM | Comandos internos | "help", "status" |
| HYBRID | RAG + acción | "busca y guarda" |
| CONVERSATIONAL | Chat natural | "Hola!" |

## Bypass de RAG

Detecta automáticamente y evita RAG cuando:
- Mencionas rutas: `/path`, `~/path`, `./path`
- Usas keywords: listar, archivo, carpeta, ls, cat, etc.
- Ejecutas comandos: `ls -la`, `cat archivo`, etc.

## Modelos Soportados

- Qwen 3 (8B)
- Mistral (7B-8B)
- DeepSeek Coder
- Llama (variantes)
- Phi-2

Ubicar en `data/models/` o `~/modelo/`

## Solución Rápida de Problemas

| Problema | Solución |
|----------|----------|
| "Módulo no encontrado" | `pip install -r requirements.txt` |
| "llama-cpp-python" falla | `pip install --no-cache-dir --force-reinstall` |
| "Las rutas están mal" | `python main.py --init-data` |
| "RAG no encuentra resultados" | Verificar `data/index/` existe |

## API Programática

```python
from VERSIOND4 import WikiRAGD4

# Inicializar
wikirag = WikiRAGD4(verbose=True)

# Procesar consulta
response = wikirag.query("tu consulta")
print(response)

# Clasificar
classification = wikirag.classify("otra consulta")
print(f"Intent: {classification.intent}")
```

## Instalación Como Paquete

```bash
pip install -e .
```

Luego importar:
```python
from VERSIOND4 import WikiRAGD4
```

## Variables de Entorno (Opcional)

```bash
export LOG_LEVEL=DEBUG
export WIKIRAG_VERBOSE=true
```

## Archivos Importantes

- `README.md` - Documentación completa
- `QUICKSTART.md` - Inicio rápido
- `MANIFEST.md` - Checklist de contenido
- `requirements.txt` - Dependencias
- `main.py` - Punto de entrada
- `test_wikirag.py` - Tests

## Contacto y Soporte

- Ver `README.md` para documentación completa
- Ejecutar `python main.py --help` para opciones
- Ejecutar `python test_wikirag.py` para verificar

---

**Versión**: 1.0.0 (D4)
**Estado**: Producción
**Portable**: 100%

¡Listo para usar!
