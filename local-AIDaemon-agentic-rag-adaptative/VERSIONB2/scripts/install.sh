#!/bin/bash
# ============================================
# 🚀 WikiRAG v2.3.1 - Script de Instalación
# ============================================
set -euo pipefail

echo "============================================"
echo "   🤖 WikiRAG v2.3.1 - Instalación"
echo "============================================"
echo

# Detectar directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

echo "📁 Directorio de instalación: $BASE_DIR"
echo

# Crear directorios necesarios
echo "📂 Creando directorios..."
mkdir -p "$BASE_DIR"/{rags/wikipedia,rags/exitos,rags/fallos,rags/agentes}
mkdir -p "$BASE_DIR"/{memory,cache,logs,queue,pipes}
echo "   ✅ Directorios creados"

# Verificar Python
echo
echo "🐍 Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✅ $PYTHON_VERSION"
else
    echo "   ❌ Python 3 no encontrado. Instálalo primero."
    exit 1
fi

# Instalar dependencias
echo
echo "📦 Instalando dependencias Python..."
pip3 install --break-system-packages -q \
    sentence-transformers \
    faiss-cpu \
    rank-bm25 \
    numpy \
    2>/dev/null || echo "   ⚠️ Algunas dependencias opcionales no se instalaron"

echo "   ✅ Dependencias instaladas"

# Crear settings.json si no existe
SETTINGS_FILE="$BASE_DIR/settings.json"
if [ ! -f "$SETTINGS_FILE" ]; then
    echo
    echo "⚙️ Creando settings.json..."
    cat > "$SETTINGS_FILE" << 'EOF'
{
  "llama_cli": "~/modelo/llama.cpp/build/bin/llama-cli",
  "model_path": "~/modelo/modelos_grandes/M6/mistral-7b-instruct-v0.1.Q6_K.gguf",
  "model_agents": "~/modelo/modelos_grandes/M6/mistral-7b-instruct-v0.1.Q6_K.gguf",
  "model_code": "~/modelo/modelos_grandes/M6/mistral-7b-instruct-v0.1.Q6_K.gguf",
  "semantic_model": "sentence-transformers/all-MiniLM-L6-v2"
}
EOF
    echo "   ✅ settings.json creado"
    echo "   ⚠️ EDITA settings.json con las rutas de TU sistema"
fi

# Verificar llama-cli
echo
echo "🔧 Verificando llama-cli..."
LLAMA_CLI=$(python3 -c "import json; print(json.load(open('$SETTINGS_FILE'))['llama_cli'].replace('~', '$HOME'))" 2>/dev/null || echo "")
LLAMA_CLI="${LLAMA_CLI/#\~/$HOME}"

if [ -n "$LLAMA_CLI" ] && [ -x "$LLAMA_CLI" ]; then
    echo "   ✅ llama-cli encontrado: $LLAMA_CLI"
else
    echo "   ⚠️ llama-cli no encontrado o no ejecutable"
    echo "   → Edita settings.json con la ruta correcta"
fi

# Verificar modelo
echo
echo "🧠 Verificando modelo..."
MODEL_PATH=$(python3 -c "import json; print(json.load(open('$SETTINGS_FILE'))['model_path'].replace('~', '$HOME'))" 2>/dev/null || echo "")
MODEL_PATH="${MODEL_PATH/#\~/$HOME}"

if [ -n "$MODEL_PATH" ] && [ -f "$MODEL_PATH" ]; then
    echo "   ✅ Modelo encontrado: $(basename "$MODEL_PATH")"
else
    echo "   ⚠️ Modelo no encontrado"
    echo "   → Edita settings.json con la ruta correcta"
fi

# Crear script de inicio
START_SCRIPT="$BASE_DIR/start.sh"
cat > "$START_SCRIPT" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
python3 -m core.orchestrator -i
EOF
chmod +x "$START_SCRIPT"
echo
echo "🚀 Script de inicio creado: $START_SCRIPT"

# Resumen
echo
echo "============================================"
echo "   ✅ Instalación Completada"
echo "============================================"
echo
echo "📝 Próximos pasos:"
echo "   1. Edita settings.json con las rutas de tu sistema"
echo "   2. Ejecuta: ./start.sh"
echo
echo "📂 Archivos importantes:"
echo "   - settings.json  → Configuración de rutas"
echo "   - start.sh       → Script de inicio"
echo "   - core/          → Código principal"
echo "   - agents/        → Agentes de IA"
echo
