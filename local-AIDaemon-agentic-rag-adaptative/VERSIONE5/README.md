# WikiRAG VERSIONE5

Sistema RAG mínimo, práctico y funcional. Sin teatro mental.

**Filosofía:** Si no es esencial, no está.

## Requisitos

- Python 3.10+
- llama-cli instalado y en PATH
- Un modelo GGUF
- Índice FAISS pre-generado

## Instalación (3 pasos)

### 1. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

### 2. Instalar llama-cli

Descargar desde: https://github.com/ggerganov/llama.cpp/releases

O en Linux/Mac:
```bash
curl -L https://github.com/ggerganov/llama.cpp/releases/download/b2664/llama-cli-linux-x86_64 -o ~/bin/llama-cli
chmod +x ~/bin/llama-cli
```

### 3. Preparar estructura de directorios

```
wikirag/
├── releases/
│   └── VERSIONE5/          (este directorio)
├── models/
│   └── model.gguf          (coloca aquí tu modelo)
└── data/
    └── faiss_index/
        ├── index.faiss     (índice generado)
        └── chunks.pkl      (fragmentos de texto)
```

## Uso

```bash
python main.py
```

Luego escribe preguntas naturales:

```
> Pregunta: ¿Cuál es la capital de Francia?

[Buscando contexto...]
[Generando respuesta...]

[RESPUESTA]
La capital de Francia es París. Es la ciudad más grande...

¿Ver contexto? (s/n): n

> Pregunta: exit
Hasta luego!
```

## Arquitectura

### `config.py` (~50 líneas)
- Detecta automáticamente rutas
- Carga configuración de modelo GGUF
- Sin dependencias externas

### `llm.py` (~100 líneas)
- Interfaz simple con llama-cli
- Solo subprocess, sin daemons
- Métodos: `query(prompt)`, `stream_query(prompt)`

### `rag.py` (~150 líneas)
- RAG básico con FAISS
- Carga índice existente
- Métodos: `search(query)`, `search_with_scores(query)`

### `main.py` (~100 líneas)
- Loop interactivo simple
- Flujo: pregunta → RAG → LLM → respuesta
- Sin evaluadores complejos

## Generación de índice

Si no tienes índice FAISS, usarás `build_index.py` (no incluido aquí, usa tu propio script):

```bash
python scripts/build_index.py --input documents.txt --output data/faiss_index/
```

El índice debe generar:
- `data/faiss_index/index.faiss` (índice FAISS)
- `data/faiss_index/chunks.pkl` (fragmentos de texto)

## Troubleshooting

| Problema | Solución |
|----------|----------|
| `llama-cli not found` | Instala llama-cli y agrega a PATH |
| `Índice FAISS no encontrado` | Genera el índice con build_index.py |
| `Timeout (timeout)` | Aumenta el timeout o usa modelo más rápido |
| `Out of memory` | Usa un modelo más pequeño (.gguf) |

## Limitaciones intencionales

- Sin chat memory (cada pregunta es independiente)
- Sin evaluadores de respuesta
- Sin gestión de sesiones
- Sin APIs REST
- Sin MCP o smart routers

Todo eso es "teatro mental". VERSIONE5 es solo:

```
pregunta → buscar → responder
```

## Próximos pasos

Para extender VERSIONE5:

1. Agregar **caché de respuestas** (dict simple)
2. Implementar **búsqueda múltiple** (AND/OR queries)
3. Usar modelo más rápido (**TinyLlama**)
4. Agregar **logging simple** (print + archivo)
5. Crear **API REST mínima** (Flask 50 líneas)

Nada más es necesario.
