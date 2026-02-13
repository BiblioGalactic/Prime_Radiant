# 🤖 WikiRAG v2.3.1 - Versión Portable

**Sistema de IA Autónomo Local** - Versión pública portable que puedes instalar en cualquier sistema.

## 🚀 Instalación Rápida

```bash
# 1. Clona o copia esta carpeta a tu sistema
cp -r VERSIONB2 ~/wikirag

# 2. Ejecuta el instalador
cd ~/wikirag
chmod +x scripts/install.sh
./scripts/install.sh

# 3. Edita la configuración
nano settings.json  # o tu editor favorito

# 4. Inicia WikiRAG
./start.sh
```

## ⚙️ Configuración

Edita `settings.json` con las rutas de tu sistema:

```json
{
  "llama_cli": "/ruta/a/llama-cli",
  "model_path": "/ruta/a/modelo.gguf",
  "model_agents": "/ruta/a/modelo.gguf",
  "semantic_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

### Variables de Entorno (alternativa)

```bash
export WIKIRAG_LLAMA_CLI=/ruta/a/llama-cli
export WIKIRAG_MODEL_PATH=/ruta/a/modelo.gguf
```

## 📋 Requisitos

- Python 3.8+
- llama.cpp compilado con llama-cli
- Modelo GGUF (recomendado: Mistral 7B, Qwen 8B, o similar)
- 8GB+ RAM (16GB recomendado)

### Dependencias Python

```bash
pip install sentence-transformers faiss-cpu rank-bm25 numpy
```

## 🌟 Características

| Característica | Descripción |
|----------------|-------------|
| **Intent Classifier** | Clasifica queries automáticamente |
| **Smart Router** | Enruta a RAG, Claudia, Filesystem o Git |
| **Claude-style Agent** | Piensa, planifica, ejecuta, verifica, corrige |
| **Daemon Persistente** | Modelo cargado en memoria |
| **Hybrid Search** | FAISS + BM25 |
| **Prompt Cache** | Caché L1 + L2 |

## 💻 Uso

### Modo Interactivo

```bash
./start.sh
```

### Ejemplos de Consultas

```
❓ ¿Qué es Python?                      → RAG (informativo)
❓ lista archivos de ~/proyecto          → Filesystem (acción)
❓ git status                            → Git (acción)
❓ usa claudia para analizar main.py     → Claudia (análisis)
❓ help                                  → Sistema
```

## 📁 Estructura

```
wikirag/
├── core/                  # Código principal
│   ├── orchestrator.py    # Orquestador
│   ├── intent_classifier.py
│   ├── daemon_persistent.py
│   └── config.py          # Config portable
├── agents/                # Agentes de IA
│   ├── claude_style/      # Agente estilo Claude
│   └── ...
├── scripts/               # Scripts
│   └── install.sh
├── rags/                  # Índices RAG
├── memory/                # Base de datos
├── cache/                 # Cache
├── logs/                  # Logs
├── settings.json          # Tu configuración
├── start.sh               # Script de inicio
└── README.md
```

## 🔧 Solución de Problemas

### "llama-cli no encontrado"

1. Compila llama.cpp: https://github.com/ggerganov/llama.cpp
2. Actualiza settings.json con la ruta correcta

### "Modelo no encontrado"

1. Descarga un modelo GGUF (ej: Mistral 7B Q6_K)
2. Actualiza settings.json con la ruta

### "Error de memoria"

- Usa un modelo más pequeño (Q4 en vez de Q8)
- Reduce ctx_size en config.py

## 📝 Changelog

### v2.3.1 (2025-01-31)
- Intent Classifier y Smart Router
- Claude-style Agent
- Daemon auto-start mejorado
- Versión portable

## 📄 Licencia

MIT

---

**WikiRAG v2.3.1** - *Tu asistente de IA local*
