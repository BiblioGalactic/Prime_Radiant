#!/bin/bash
# ============================================================
#   🚀 WIKIRAG VERSIONA1 - Script de Inicio
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}"
echo "============================================================"
echo "   🤖 WIKIRAG VERSIONA1 - Sistema de IA con Agentes y RAGs"
echo "============================================================"
echo -e "${NC}"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 no encontrado${NC}"
    exit 1
fi

# Verificar dependencias
echo "📦 Verificando dependencias..."
python3 -c "import sentence_transformers" 2>/dev/null || {
    echo -e "${YELLOW}⚠️ Instalando sentence-transformers...${NC}"
    pip3 install sentence-transformers --quiet
}

python3 -c "import faiss" 2>/dev/null || {
    echo -e "${YELLOW}⚠️ Instalando faiss-cpu...${NC}"
    pip3 install faiss-cpu --quiet
}

# Verificar configuración
echo "🔧 Verificando configuración..."
python3 config_portable.py

# Variables de entorno para evitar problemas de memoria
export LOKY_MAX_CPU_COUNT=1
export JOBLIB_MULTIPROCESSING=0
export TOKENIZERS_PARALLELISM=false

# Añadir al PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Modo de ejecución
MODE="${1:--i}"

case "$MODE" in
    -i|--interactive)
        echo ""
        echo -e "${GREEN}🚀 Iniciando modo interactivo...${NC}"
        echo ""
        python3 -m core.orchestrator --interactive
        ;;
    -w|--worker)
        echo ""
        echo -e "${GREEN}🚀 Iniciando worker de cola...${NC}"
        python3 -m core.orchestrator --worker
        ;;
    -q|--query)
        shift
        QUERY="$*"
        echo ""
        echo -e "${GREEN}📝 Consulta: $QUERY${NC}"
        python3 -m core.orchestrator "$QUERY"
        ;;
    -h|--help)
        echo "Uso: ./run.sh [opción]"
        echo ""
        echo "Opciones:"
        echo "  -i, --interactive  Modo interactivo (default)"
        echo "  -w, --worker       Iniciar worker de cola"
        echo "  -q, --query        Ejecutar consulta directa"
        echo "  -h, --help         Mostrar ayuda"
        echo ""
        echo "Ejemplos:"
        echo "  ./run.sh -i"
        echo "  ./run.sh -q \"¿Qué es Python?\""
        ;;
    *)
        echo -e "${YELLOW}Modo no reconocido: $MODE${NC}"
        echo "Usa ./run.sh -h para ver opciones"
        ;;
esac

# Restaurar terminal al salir
reset 2>/dev/null || true
