#!/bin/bash
# ============================================
# 🚀 WikiRAG v2.3.1 - Inicio Rápido
# ============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verificar settings.json
if [ ! -f "settings.json" ]; then
    echo "⚠️ settings.json no encontrado"
    echo "   Copia settings.json.example a settings.json y edítalo"
    exit 1
fi

# Iniciar
python3 -m core.orchestrator -i
