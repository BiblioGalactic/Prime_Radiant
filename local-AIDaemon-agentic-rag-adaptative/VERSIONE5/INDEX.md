# WikiRAG VERSIONE5: Índice Completo

## Para empezar (2-5 minutos)

1. **[QUICKSTART.md](QUICKSTART.md)** - Instalación y uso en 60 segundos
   - Estructura de directorios
   - Ejemplo de ejecución
   - Troubleshooting rápido

## Para usuarios (10 minutos)

2. **[README.md](README.md)** - Documentación completa para usuarios
   - Requisitos y instalación (3 pasos)
   - Uso interactivo
   - Troubleshooting con tabla
   - Limitaciones intencionales
   - Próximos pasos opcionales

## Para desarrolladores (30 minutos)

3. **[ESTRUCTURA.txt](ESTRUCTURA.txt)** - Arquitectura y diseño interno
   - Responsabilidades de cada módulo
   - Dependencias entre módulos
   - Flujo de inicialización línea por línea
   - Flujo de procesamiento de una pregunta
   - Gestión de errores
   - Patrones de diseño utilizados
   - Extensiones posibles

4. **[RESUMEN.txt](RESUMEN.txt)** - Resumen técnico exhaustivo
   - Objetivo y filosofía
   - Componentes en detalle (78-108 líneas cada uno)
   - Configuración automática
   - Parámetros ajustables
   - Casos de uso y limitaciones
   - Ventajas de E5
   - Benchmarks

## Código fuente (391 líneas totales)

### Core (3 módulos + config)

5. **[config.py](config.py)** (78 líneas)
   - Detección automática de rutas
   - Parámetros de configuración
   - Validación al inicio

6. **[llm.py](llm.py)** (99 líneas)
   - SimpleLLM: interfaz con llama-cli
   - query(prompt) → respuesta
   - stream_query(prompt) → generador

7. **[rag.py](rag.py)** (108 líneas)
   - SimpleRAG: recuperación con FAISS
   - search(query) → contexto
   - search_with_scores(query) → relevancia

8. **[main.py](main.py)** (106 líneas)
   - WikiRAGE5: orquestador principal
   - answer(question) → (respuesta, contexto)
   - interactive_loop() → CLI

### Configuración y dependencias

9. **[requirements.txt](requirements.txt)**
   - faiss-cpu==1.8.0
   - sentence-transformers==3.0.1
   - numpy==1.24.3

### Testing

10. **[test_import.py](test_import.py)** (70 líneas)
    - Verificación de módulos
    - Pruebas de conectividad
    - Detección de problemas

## Mapas visuales

### Dependencias de módulos

```
main.py
  ├─→ config.py    (rutas, parámetros)
  ├─→ llm.py       (SimpleLLM)
  │   └─→ config.py
  └─→ rag.py       (SimpleRAG)
      └─→ config.py
```

### Flujo de una pregunta

```
pregunta → RAG.search() → LLM.query() → respuesta
            ↓                ↓
          contexto      (5 fragmentos)
```

### Inicialización

```
python main.py
  → import config
  → import llm (verifica llama-cli)
  → import rag (carga FAISS + chunks)
  → loop interactivo
```

## Guías por rol

### Soy usuario, quiero usar WikiRAG

→ Lee **QUICKSTART.md** (5 min) + **README.md** (10 min)

### Soy desarrollador, quiero modificar

→ Lee **ESTRUCTURA.txt** (20 min) + revisa código (10 min)

### Soy arquitecto, quiero entender el diseño

→ Lee **RESUMEN.txt** (30 min) + **ESTRUCTURA.txt** (20 min)

### Tengo un error específico

→ Busca en:
1. **README.md** (sección Troubleshooting)
2. **QUICKSTART.md** (sección Troubleshooting)
3. Ejecuta `python test_import.py`

## Filosofía de VERSIONE5

```
┌─────────────────────────────────────────┐
│ Si no es esencial, no está.             │
│ Código legible y directo.               │
│ Funciona con GGUF + FAISS.              │
│ Sin teatro mental.                      │
│ Pregunta → buscar → responder           │
└─────────────────────────────────────────┘
```

## Estadísticas rápidas

| Métrica | Valor |
|---------|-------|
| Líneas de código | 391 |
| Archivos Python | 4 |
| Dependencias externas | 3 |
| Herramientas externas | 1 (llama-cli) |
| Tiempo instalación | ~5 min |
| Tiempo aprendizaje | ~30 min |

## Próximas versiones

### VERSIONE6 (Opcionalmente)
- Caché simple
- Logging a archivo
- API REST (Flask)
- Búsqueda multi-query

### VERSIONE7+ (Extensiones)
- Chat memory
- Evaluadores
- Web UI
- Optimizaciones

**Pero primero: domina E5.**

## Licencia y uso

WikiRAG VERSIONE5 es libre para usar, modificar y distribuir.

Requisito único: Respeta la licencia de:
- llama.cpp (MIT)
- faiss (MIT)
- sentence-transformers (Apache 2.0)

## Feedback

Si encuentras errores o tienes sugerencias:

1. Ejecuta `python test_import.py` para diagnosticar
2. Revisa la sección de errors en ESTRUCTURA.txt
3. Ajusta parámetros en config.py
4. Si todo falla: inicia issue/ticket con output completo

## Índice rápido de búsqueda

**"¿Cómo...?"**
- Instalar → QUICKSTART.md
- Usar → README.md
- Modificar → ESTRUCTURA.txt
- Entender diseño → RESUMEN.txt

**"¿Error de...?"**
- Config → config.py (línea ~73)
- LLM → llm.py (línea ~50)
- RAG → rag.py (línea ~35)
- Main → main.py (línea ~70)

**"¿Quiero...?"**
- Agregar caché → main.py (línea ~45)
- Cambiar prompt → main.py (línea ~57)
- Más fragmentos → config.py (línea ~30)
- Streaming → llm.py (línea ~85)

---

**Última actualización:** 2025-02-13

**Versión:** VERSIONE5 (FINAL)

**Estado:** LISTA PARA PRODUCCIÓN (pequeña escala)

