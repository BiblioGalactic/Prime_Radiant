#!/bin/bash
# ==============================================================================
# 🚀 INICIADOR SINGLE AGENT - OpenClaw + llama.cpp
# ==============================================================================
# Autor: Gustavo Silva da Costa (Eto Demerzel)
# GitHub: https://github.com/BiblioGalactic/openclaw-modifier
# Versión: 1.0.0
# Descripción: Inicia un agente único con llama-server local y configura
#              OpenClaw para uso con modelos locales
# ==============================================================================

set -euo pipefail

trap cleanup EXIT

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Directorio base
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODIFIER_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$HOME/.openclaw/logs"
PID_FILE="$HOME/.openclaw/pids/llama-single.pid"

# ============================================
# Variables de configuración
# ============================================

# Cargar configuración
if [ -f "$MODIFIER_DIR/configs/model_config.env" ]; then
    # shellcheck source=/dev/null
    source "$MODIFIER_DIR/configs/model_config.env"
else
    echo -e "${RED}❌ Error: No se encuentra model_config.env${NC}"
    echo "Copia desde: $MODIFIER_DIR/configs/model_config.env.example"
    exit 1
fi

# Valores por defecto si no están definidos
MODEL_PATH="${MODEL_PATH:-}"
MODEL_NAME="${MODEL_NAME:-mistral-7b}"
BASE_PORT="${BASE_PORT:-8080}"
CONTEXT_SIZE="${CONTEXT_SIZE:-4096}"
THREADS="${THREADS:-8}"
LLAMA_BIN="${LLAMA_BIN:-$HOME/modelo/llama.cpp/build/bin/llama-server}"

# ============================================
# Funciones
# ============================================

cleanup() {
    if [ -f "$PID_FILE" ]; then
        echo ""
        echo -e "${YELLOW}🧹 Limpiando procesos...${NC}"
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null || true
            echo -e "${GREEN}✓${NC} Proceso detenido (PID: $PID)"
        fi
        rm -f "$PID_FILE"
    fi
}

validar() {
    echo -e "${CYAN}🔍 Validando configuración...${NC}"
    echo ""

    # Verificar llama-server
    if [ ! -f "$LLAMA_BIN" ]; then
        echo -e "${RED}❌ Error: llama-server no encontrado en: $LLAMA_BIN${NC}"
        exit 1
    fi

    if [ ! -x "$LLAMA_BIN" ]; then
        echo -e "${RED}❌ Error: llama-server no tiene permisos de ejecución${NC}"
        echo "Ejecuta: chmod +x $LLAMA_BIN"
        exit 1
    fi

    echo -e "${GREEN}✓${NC} llama-server: $LLAMA_BIN"

    # Verificar modelo
    if [ -z "$MODEL_PATH" ] || [ ! -f "$MODEL_PATH" ]; then
        echo -e "${RED}❌ Error: Modelo no encontrado: $MODEL_PATH${NC}"
        echo "Edita: $MODIFIER_DIR/configs/model_config.env"
        exit 1
    fi

    local model_size
    model_size=$(du -h "$MODEL_PATH" | cut -f1)
    echo -e "${GREEN}✓${NC} Modelo: $MODEL_PATH ($model_size)"

    # Verificar puerto disponible
    if lsof -Pi :"$BASE_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Error: Puerto $BASE_PORT ya está en uso${NC}"
        echo "Procesos usando el puerto:"
        lsof -Pi :"$BASE_PORT" -sTCP:LISTEN
        exit 1
    fi

    echo -e "${GREEN}✓${NC} Puerto $BASE_PORT disponible"

    # Crear directorios necesarios
    mkdir -p "$LOG_DIR"
    mkdir -p "$(dirname "$PID_FILE")"
    mkdir -p "$HOME/.openclaw/workspace-${MODEL_NAME}"

    echo -e "${GREEN}✓${NC} Directorios creados"
    echo ""
}

iniciar_llama_server() {
    echo -e "${CYAN}🚀 Iniciando llama-server...${NC}"
    echo ""

    local log_file="$LOG_DIR/llama-server-${MODEL_NAME}.log"

    # Comando
    local cmd="$LLAMA_BIN \
        --model \"$MODEL_PATH\" \
        --ctx-size $CONTEXT_SIZE \
        --threads $THREADS \
        --port $BASE_PORT \
        --host 127.0.0.1 \
        --log-format text"

    echo "Puerto: $BASE_PORT"
    echo "Contexto: $CONTEXT_SIZE tokens"
    echo "Threads: $THREADS"
    echo "Log: $log_file"
    echo ""

    # Iniciar en background
    nohup bash -c "$cmd" > "$log_file" 2>&1 &
    local pid=$!

    # Guardar PID
    echo "$pid" > "$PID_FILE"

    echo -e "${BLUE}ℹ${NC}  PID: $pid"

    # Esperar a que arranque
    echo -n "Esperando a que llama-server esté listo"
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s "http://127.0.0.1:$BASE_PORT/health" > /dev/null 2>&1; then
            echo ""
            echo -e "${GREEN}✅ llama-server iniciado correctamente${NC}"
            return 0
        fi

        echo -n "."
        sleep 1
        ((attempt++))
    done

    echo ""
    echo -e "${RED}❌ Error: llama-server no respondió a tiempo${NC}"
    echo "Revisa el log: $log_file"
    exit 1
}

test_llama_server() {
    echo ""
    echo -e "${CYAN}🧪 Probando llama-server...${NC}"
    echo ""

    # Test health
    if curl -s "http://127.0.0.1:$BASE_PORT/health" | grep -q "ok"; then
        echo -e "${GREEN}✓${NC} Health check: OK"
    else
        echo -e "${RED}✗${NC} Health check: FAILED"
        return 1
    fi

    # Test models endpoint
    if curl -s "http://127.0.0.1:$BASE_PORT/v1/models" | grep -q "model"; then
        echo -e "${GREEN}✓${NC} Models endpoint: OK"
    else
        echo -e "${RED}✗${NC} Models endpoint: FAILED"
        return 1
    fi

    # Test chat completion (simple)
    local response
    response=$(curl -s "http://127.0.0.1:$BASE_PORT/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "local-model",
            "messages": [{"role": "user", "content": "Say hello"}],
            "max_tokens": 10
        }')

    if echo "$response" | grep -q "choices"; then
        echo -e "${GREEN}✓${NC} Chat completion: OK"
    else
        echo -e "${RED}✗${NC} Chat completion: FAILED"
        echo "Response: $response"
        return 1
    fi

    echo ""
    echo -e "${GREEN}✅ Todos los tests pasaron${NC}"
}

configurar_openclaw() {
    echo ""
    echo -e "${CYAN}⚙️  Configurando OpenClaw...${NC}"
    echo ""

    # Copiar configuración
    local config_src="$MODIFIER_DIR/configs/single_agent.json"
    local config_dst="$HOME/.openclaw/openclaw.json"

    if [ ! -f "$config_src" ]; then
        echo -e "${RED}❌ Error: Configuración no encontrada: $config_src${NC}"
        exit 1
    fi

    # Reemplazar variables en la configuración
    cat "$config_src" | \
        sed "s|{{MODEL_NAME}}|$MODEL_NAME|g" | \
        sed "s|{{BASE_PORT}}|$BASE_PORT|g" \
        > "$config_dst"

    echo -e "${GREEN}✓${NC} Configuración copiada a: $config_dst"

    # Copiar workspace si existe
    local workspace_src="$MODIFIER_DIR/workspaces/default"
    local workspace_dst="$HOME/.openclaw/workspace-${MODEL_NAME}"

    if [ -d "$workspace_src" ]; then
        cp -r "$workspace_src"/* "$workspace_dst/" 2>/dev/null || true
        echo -e "${GREEN}✓${NC} Workspace copiado a: $workspace_dst"
    fi

    echo ""
}

mostrar_info() {
    echo ""
    echo "=================================================="
    echo -e "${GREEN}✅ SINGLE AGENT INICIADO CORRECTAMENTE${NC}"
    echo "=================================================="
    echo ""
    echo "📊 Información del servicio:"
    echo "----------------------------"
    echo "Modelo: $MODEL_NAME"
    echo "Puerto: $BASE_PORT"
    echo "PID: $(cat "$PID_FILE")"
    echo ""
    echo "🔗 Endpoints:"
    echo "----------------------------"
    echo "Health: http://127.0.0.1:$BASE_PORT/health"
    echo "Models: http://127.0.0.1:$BASE_PORT/v1/models"
    echo "Chat: http://127.0.0.1:$BASE_PORT/v1/chat/completions"
    echo ""
    echo "📝 Logs:"
    echo "----------------------------"
    echo "tail -f $LOG_DIR/llama-server-${MODEL_NAME}.log"
    echo ""
    echo "🛑 Para detener:"
    echo "----------------------------"
    echo "./scripts/stop_all.sh"
    echo ""
    echo "▶️  Siguiente paso:"
    echo "----------------------------"
    echo "Inicia OpenClaw:"
    echo "  openclaw start"
    echo ""
    echo "O visita el dashboard:"
    echo "  http://localhost:3000"
    echo ""
    echo "=================================================="
}

# ============================================
# Ejecución principal
# ============================================

echo "=================================================="
echo "🚀 SINGLE AGENT - OpenClaw + llama.cpp"
echo "=================================================="
echo ""

validar
iniciar_llama_server
test_llama_server
configurar_openclaw
mostrar_info

echo -e "${BLUE}ℹ${NC}  Presiona Ctrl+C para detener el servidor"
echo ""

# Mantener el script corriendo
trap cleanup EXIT

# Esperar señal
wait
