#!/bin/bash
# ==============================================================================
# 🛑 DETENER TODOS LOS SERVICIOS - OpenClaw Local Model Modifier
# ==============================================================================
# Autor: Gustavo Silva da Costa (Eto Demerzel)
# GitHub: https://github.com/BiblioGalactic/openclaw-modifier
# Versión: 1.0.0
# Descripción: Detiene todos los llama-servers y procesos de OpenClaw de forma
#              limpia y segura
# ==============================================================================

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PID_DIR="$HOME/.openclaw/pids"

echo "=================================================="
echo "🛑 Deteniendo OpenClaw + llama-servers"
echo "=================================================="
echo ""

STOPPED=0
NOT_RUNNING=0

# Detener llama-servers por archivos PID
if [ -d "$PID_DIR" ]; then
    for pid_file in "$PID_DIR"/llama-*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            agent=$(basename "$pid_file" .pid | sed 's/llama-//')

            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null
                echo -e "${GREEN}✓${NC} Detenido: $agent (PID: $pid)"
                ((STOPPED++))
            else
                echo -e "${YELLOW}⚠${NC} No corriendo: $agent"
                ((NOT_RUNNING++))
            fi

            rm -f "$pid_file"
        fi
    done
fi

# Buscar procesos huérfanos de llama-server
echo ""
echo -e "${BLUE}🔍 Buscando procesos huérfanos...${NC}"

ORPHANS=$(pgrep -f "llama-server" || true)
if [ -n "$ORPHANS" ]; then
    echo "$ORPHANS" | while read -r pid; do
        kill "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null
        echo -e "${GREEN}✓${NC} Proceso huérfano detenido (PID: $pid)"
        ((STOPPED++))
    done
else
    echo -e "${GREEN}✓${NC} No se encontraron procesos huérfanos"
fi

# Detener OpenClaw si está corriendo
echo ""
echo -e "${BLUE}🔍 Verificando OpenClaw gateway...${NC}"

if pgrep -f "openclaw" > /dev/null; then
    pkill -f "openclaw" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} OpenClaw gateway detenido"
    ((STOPPED++))
else
    echo -e "${GREEN}✓${NC} OpenClaw gateway no estaba corriendo"
fi

# Resumen
echo ""
echo "=================================================="
echo "📊 RESUMEN"
echo "=================================================="
echo ""
echo "Procesos detenidos: $STOPPED"
echo "No corriendo: $NOT_RUNNING"
echo ""

if [ $STOPPED -gt 0 ]; then
    echo -e "${GREEN}✅ Todos los servicios detenidos${NC}"
else
    echo -e "${BLUE}ℹ${NC}  No había servicios corriendo"
fi

echo ""
