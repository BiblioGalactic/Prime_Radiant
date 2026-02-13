# WikiRAG E5: Quick Start Guide

## 60 Segundos

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Descargar llama-cli (5 min)
wget https://github.com/ggerganov/llama.cpp/releases/download/.../llama-cli-linux-x86_64
chmod +x llama-cli
export PATH=$PATH:$(pwd)

# 3. Preparar directorio
mkdir -p ../models ../data/faiss_index
cp tu_modelo.gguf ../models/
cp tu_index.faiss ../data/faiss_index/
cp tu_chunks.pkl ../data/faiss_index/

# 4. Ejecutar
python main.py
```

## Estructura de directorios esperada

```
wikirag/                      (BASE_PATH)
├── releases/
│   └── VERSIONE5/            (Tu código está aquí)
├── models/
│   └── model.gguf            (Tu modelo GGUF)
└── data/
    └── faiss_index/
        ├── index.faiss       (Índice FAISS)
        └── chunks.pkl        (Metadatos)
```

## Ejemplo de uso

```bash
$ python main.py

=== WikiRAG VERSIONE5 ===

Cargando componentes...
✓ LLM listo
✓ RAG listo

Sistema listo. Escribe 'exit' para salir.

> Pregunta: ¿Qué es machine learning?

[Buscando contexto...]
[Generando respuesta...]

[RESPUESTA]
Machine learning es una rama de la inteligencia artificial que permite
a las computadoras aprender de los datos sin ser programadas explícitamente...

¿Ver contexto? (s/n): n

> Pregunta: exit
Hasta luego!
```

## Archivos principales

| Archivo | Líneas | Propósito |
|---------|--------|----------|
| `config.py` | 78 | Detecta rutas automáticamente |
| `llm.py` | 99 | Interfaz con llama-cli |
| `rag.py` | 108 | RAG con FAISS |
| `main.py` | 106 | Loop interactivo |
| `requirements.txt` | 3 | Dependencias pip |

Total: 391 líneas de código.

## Verificación

```bash
python test_import.py
```

Output:
```
=== Verificación de Módulos WikiRAG E5 ===

[1/4] Importando config...
  ✓ config.py cargado
    - Base path: /sessions/friendly-zealous-heisenberg/mnt/wikirag
    ...

[4/4] Importando main...
  ✓ main.py cargado

=== Verificación Completada ===

✓ Todos los módulos importan correctamente

Próximo paso: python main.py
```

## Troubleshooting

| Error | Solución |
|-------|----------|
| `llama-cli not found` | Descargar de https://github.com/ggerganov/llama.cpp/releases y agregar a PATH |
| `Índice FAISS no encontrado` | Copiar `index.faiss` a `data/faiss_index/` |
| `No se encontró modelo GGUF` | Copiar tu `.gguf` a `models/` |
| `Timeout (timeout)` | Aumentar timeout en `llm.py` (línea ~95) o usar modelo más rápido |
| `OutOfMemory` | Usar modelo más pequeño (ej: 7B en vez de 13B) |

## Parámetros ajustables

En `config.py`:

```python
CONTEXT_WINDOW = 5          # Fragmentos recuperados (↑ = más contexto)
MAX_TOKENS = 512            # Tokens generados (↑ = respuesta más larga)
TEMPERATURE = 0.7           # Creatividad (0.1 = exacto, 1.0 = creativo)
```

Ajusta según necesidad.

## Límites intencionales

VERSIONE5 NO tiene:
- Chat memory (cada pregunta es independiente)
- Caché (la misma pregunta se procesa cada vez)
- Evaluadores (no mide calidad)
- Web UI (solo CLI)
- API REST (aún)

Esto es por diseño. Si necesitas estas features, agréalas en VERSIONE6.

## Próximo paso

Lee `RESUMEN.txt` para entender la arquitectura completa.

O directamente:

```bash
# Ejecuta e interactúa
python main.py

# Pregunta algo
> ¿Cuál es el significado de la vida?
```

Fin. Sin teatro mental.
