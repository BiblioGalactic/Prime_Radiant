#!/bin/bash
# ==============================================================================
# 🚀 INICIADOR MULTI-AGENT - OpenClaw + llama.cpp
# ==============================================================================
# Autor: Gustavo Silva da Costa (Eto Demerzel)
# GitHub: https://github.com/BiblioGalactic/openclaw-modifier
# Versión: 1.0.0
# Descripción: Inicia tres agentes simultáneos (Daneel, Dors, Giskard) con
#              personalidades únicas y routing por canal
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
PID_DIR="$HOME/.openclaw/pids"

# Arrays para gestión de procesos
declare -a PIDS=()
declare -a AGENTS=("daneel" "dors" "giskard")
declare -a PORTS=(8080 8081 8082)

# ============================================
# Cargar configuración
# ============================================

if [ -f "$MODIFIER_DIR/configs/model_config.env" ]; then
    # shellcheck source=/dev/null
    source "$MODIFIER_DIR/configs/model_config.env"
else
    echo -e "${RED}❌ Error: No se encuentra model_config.env${NC}"
    exit 1
fi

MODEL_PATH="${MODEL_PATH:-}"
LLAMA_BIN="${LLAMA_BIN:-$HOME/modelo/llama.cpp/build/bin/llama-server}"
CONTEXT_SIZE="${CONTEXT_SIZE:-4096}"
THREADS="${THREADS:-8}"

# ============================================
# Funciones
# ============================================

cleanup() {
    echo ""
    echo -e "${YELLOW}🧹 Limpiando procesos...${NC}"

    # Matar procesos por PID guardados
    for i in "${!AGENTS[@]}"; do
        local agent="${AGENTS[$i]}"
        local pid_file="$PID_DIR/llama-${agent}.pid"

        if [ -f "$pid_file" ]; then
            local pid
            pid=$(cat "$pid_file")
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
                echo -e "${GREEN}✓${NC} ${agent} detenido (PID: $pid)"
            fi
            rm -f "$pid_file"
        fi
    done

    echo -e "${GREEN}✓${NC} Limpieza completa"
}

validar() {
    echo -e "${CYAN}🔍 Validando configuración...${NC}"
    echo ""

    # Verificar llama-server
    if [ ! -f "$LLAMA_BIN" ] || [ ! -x "$LLAMA_BIN" ]; then
        echo -e "${RED}❌ Error: llama-server no encontrado o sin permisos${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} llama-server: $LLAMA_BIN"

    # Verificar modelo
    if [ -z "$MODEL_PATH" ] || [ ! -f "$MODEL_PATH" ]; then
        echo -e "${RED}❌ Error: Modelo no encontrado: $MODEL_PATH${NC}"
        exit 1
    fi
    local model_size
    model_size=$(du -h "$MODEL_PATH" | cut -f1)
    echo -e "${GREEN}✓${NC} Modelo: $MODEL_PATH ($model_size)"

    # Verificar puertos disponibles
    for port in "${PORTS[@]}"; do
        if lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${RED}❌ Error: Puerto $port ya está en uso${NC}"
            lsof -Pi :"$port" -sTCP:LISTEN
            exit 1
        fi
    done
    echo -e "${GREEN}✓${NC} Todos los puertos disponibles (8080-8082)"

    # Crear directorios
    mkdir -p "$LOG_DIR" "$PID_DIR"
    for agent in "${AGENTS[@]}"; do
        mkdir -p "$HOME/.openclaw/workspace-${agent}"
    done
    echo -e "${GREEN}✓${NC} Directorios creados"
    echo ""
}

iniciar_agente() {
    local agent=$1
    local port=$2
    local log_file="$LOG_DIR/llama-server-${agent}.log"
    local pid_file="$PID_DIR/llama-${agent}.pid"

    echo -e "${BLUE}▶${NC}  Iniciando ${agent} en puerto ${port}..."

    # Comando
    local cmd="$LLAMA_BIN \
        --model \"$MODEL_PATH\" \
        --ctx-size $CONTEXT_SIZE \
        --threads $THREADS \
        --port $port \
        --host 127.0.0.1 \
        --log-format text"

    # Iniciar en background
    nohup bash -c "$cmd" > "$log_file" 2>&1 &
    local pid=$!

    # Guardar PID
    echo "$pid" > "$pid_file"
    PIDS+=("$pid")

    echo -e "   PID: $pid | Log: $log_file"

    # Esperar a que arranque
    local max_attempts=30
    local attempt=0
    echo -n "   Esperando"

    while [ $attempt -lt $max_attempts ]; do
        if curl -s "http://127.0.0.1:$port/health" > /dev/null 2>&1; then
            echo ""
            echo -e "${GREEN}   ✓${NC} ${agent} listo"
            return 0
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done

    echo ""
    echo -e "${RED}   ✗${NC} ${agent} no respondió a tiempo"
    return 1
}

test_agente() {
    local agent=$1
    local port=$2

    echo -n "   Testing ${agent}..."

    # Health check
    if ! curl -s "http://127.0.0.1:$port/health" | grep -q "ok"; then
        echo -e " ${RED}✗ FAILED${NC}"
        return 1
    fi

    # Models endpoint
    if ! curl -s "http://127.0.0.1:$port/v1/models" | grep -q "model"; then
        echo -e " ${RED}✗ FAILED${NC}"
        return 1
    fi

    echo -e " ${GREEN}✓ OK${NC}"
    return 0
}

copiar_workspaces() {
    echo ""
    echo -e "${CYAN}📁 Copiando workspaces...${NC}"

    for agent in "${AGENTS[@]}"; do
        local src="$MODIFIER_DIR/workspaces/${agent}"
        local dst="$HOME/.openclaw/workspace-${agent}"

        if [ -d "$src" ]; then
            cp -r "$src"/* "$dst/" 2>/dev/null || true
            echo -e "${GREEN}✓${NC} Workspace de ${agent} copiado"
        else
            echo -e "${YELLOW}⚠${NC} Workspace de ${agent} no encontrado, usando default"
        fi
    done
    echo ""
}

configurar_openclaw() {
    echo -e "${CYAN}⚙️  Configurando OpenClaw...${NC}"

    local config_src="$MODIFIER_DIR/configs/multi_agent.json"
    local config_dst="$HOME/.openclaw/openclaw.json"

    if [ ! -f "$config_src" ]; then
        echo -e "${RED}❌ Error: Configuración no encontrada${NC}"
        exit 1
    fi

    cp "$config_src" "$config_dst"
    echo -e "${GREEN}✓${NC} Configuración copiada a: $config_dst"
    echo ""
}

mostrar_info() {
    echo ""
    echo "=================================================="
    echo -e "${GREEN}✅ MULTI-AGENT INICIADO CORRECTAMENTE${NC}"
    echo "=================================================="
    echo ""
    echo "🤖 Agentes activos:"
    echo "----------------------------"
    for i in "${!AGENTS[@]}"; do
        local agent="${AGENTS[$i]}"
        local port="${PORTS[$i]}"
        local pid="${PIDS[$i]}"
        echo "  ${agent}: localhost:${port} (PID: ${pid})"
    done
    echo ""
    echo "🔗 Endpoints:"
    echo "----------------------------"
    for i in "${!AGENTS[@]}"; do
        echo "  ${AGENTS[$i]}: http://127.0.0.1:${PORTS[$i]}/v1/chat/completions"
    done
    echo ""
    echo "📝 Logs:"
    echo "----------------------------"
    echo "  tail -f $LOG_DIR/llama-server-*.log"
    echo ""
    echo "🎭 Routing configurado:"
    echo "----------------------------"
    echo "  WhatsApp → Daneel (estratega)"
    echo "  Telegram → Dors (protectora)"
    echo "  Discord → Giskard (filósofo)"
    echo ""
    echo "🛑 Para detener:"
    echo "----------------------------"
    echo "  ./scripts/stop_all.sh"
    echo ""
    echo "▶️  Siguiente paso:"
    echo "----------------------------"
    echo "  Inicia OpenClaw:"
    echo "    openclaw start"
    echo ""
    echo "  O visita el dashboard:"
    echo "    http://localhost:3000"
    echo ""
    echo "=================================================="
}

# ============================================
# Ejecución principal
# ============================================

echo "=================================================="
echo "🚀 MULTI-AGENT - OpenClaw + llama.cpp"
echo "=================================================="
echo ""

validar

echo -e "${CYAN}🚀 Iniciando agentes...${NC}"
echo ""

# Iniciar cada agente
for i in "${!AGENTS[@]}"; do
    if ! iniciar_agente "${AGENTS[$i]}" "${PORTS[$i]}"; then
        echo -e "${RED}❌ Error al iniciar ${AGENTS[$i]}${NC}"
        cleanup
        exit 1
    fi
    echo ""
done

echo -e "${CYAN}🧪 Probando agentes...${NC}"
for i in "${!AGENTS[@]}"; do
    test_agente "${AGENTS[$i]}" "${PORTS[$i]}"
done

copiar_workspaces
configurar_openclaw
mostrar_info

echo -e "${BLUE}ℹ${NC}  Presiona Ctrl+C para detener todos los servidores"
echo ""

# Mantener el script corriendo
wait
