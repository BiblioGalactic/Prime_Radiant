#!/bin/bash
# ============================================================
# 🚀 WIKIRAG ECOSYSTEM LAUNCHER v1.0
# ============================================================
# Inicia todos los componentes del sistema WikiRAG:
# 1. Queue Watcher (monitorea inbox)
# 2. Queue Daemon (procesa tareas)
# 3. MCP Servers (opcional)
# 4. Resource Monitor (opcional)
# ============================================================
set -euo pipefail

# === CONFIGURACIÓN ===
WIKIRAG_HOME="${HOME}/wikirag"
LOG_DIR="${WIKIRAG_HOME}/logs"
PIDS_DIR="${WIKIRAG_HOME}/.pids"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# === FUNCIONES ===

log() {
    echo -e "[$(date '+%H:%M:%S')] $1"
}

ensure_dirs() {
    mkdir -p "$LOG_DIR" "$PIDS_DIR"
    mkdir -p "${WIKIRAG_HOME}/queue"/{inbox,processing,archive,logs}
}

check_running() {
    local name=$1
    local pid_file="${PIDS_DIR}/${name}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0  # Corriendo
        fi
    fi
    return 1  # No corriendo
}

start_queue_daemon() {
    log "${BLUE}🤖 Iniciando Queue Daemon...${NC}"

    if check_running "queue_daemon"; then
        log "${YELLOW}   Ya está corriendo${NC}"
        return
    fi

    cd "$WIKIRAG_HOME"
    nohup python3 -m core.queue_daemon --daemon \
        > "${LOG_DIR}/queue_daemon.log" 2>&1 &

    echo $! > "${PIDS_DIR}/queue_daemon.pid"
    log "${GREEN}   ✅ PID: $!${NC}"
}

start_queue_watcher() {
    log "${BLUE}👁️ Iniciando Queue Watcher...${NC}"

    if check_running "queue_watcher"; then
        log "${YELLOW}   Ya está corriendo${NC}"
        return
    fi

    cd "$WIKIRAG_HOME"
    nohup bash scripts/queue_watcher.sh \
        > "${LOG_DIR}/queue_watcher.log" 2>&1 &

    echo $! > "${PIDS_DIR}/queue_watcher.pid"
    log "${GREEN}   ✅ PID: $!${NC}"
}

start_orchestrator_daemon() {
    log "${BLUE}🧠 Iniciando Orchestrator Daemon...${NC}"

    if check_running "orchestrator"; then
        log "${YELLOW}   Ya está corriendo${NC}"
        return
    fi

    cd "$WIKIRAG_HOME"
    nohup python3 -m core.orchestrator --worker \
        > "${LOG_DIR}/orchestrator.log" 2>&1 &

    echo $! > "${PIDS_DIR}/orchestrator.pid"
    log "${GREEN}   ✅ PID: $!${NC}"
}

start_all() {
    log "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
    log "${CYAN}║         🚀 WIKIRAG ECOSYSTEM - INICIANDO              ║${NC}"
    log "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""

    ensure_dirs

    start_queue_daemon
    sleep 1

    # El watcher es opcional si ya tienes el daemon
    # start_queue_watcher

    start_orchestrator_daemon
    sleep 1

    echo ""
    log "${GREEN}✅ Ecosistema WikiRAG iniciado${NC}"
    echo ""
    show_status
    echo ""
    log "${YELLOW}📝 Para crear tareas:${NC}"
    log "   echo 'Tu tarea aquí' > ~/wikirag/queue/inbox/mi_tarea.task"
    echo ""
    log "${YELLOW}📊 Para ver logs:${NC}"
    log "   tail -f ~/wikirag/logs/queue_daemon.log"
}

stop_all() {
    log "${CYAN}🛑 Deteniendo ecosistema WikiRAG...${NC}"
    echo ""

    for pid_file in "${PIDS_DIR}"/*.pid; do
        if [ -f "$pid_file" ]; then
            local name=$(basename "$pid_file" .pid)
            local pid=$(cat "$pid_file")

            if kill -0 "$pid" 2>/dev/null; then
                log "   Deteniendo ${name} (PID: $pid)..."
                kill "$pid" 2>/dev/null || true
            fi
            rm -f "$pid_file"
        fi
    done

    log "${GREEN}✅ Ecosistema detenido${NC}"
}

show_status() {
    log "${CYAN}📊 ESTADO DEL ECOSISTEMA${NC}"
    echo ""

    for service in queue_daemon queue_watcher orchestrator; do
        local pid_file="${PIDS_DIR}/${service}.pid"
        local status="${RED}⚫ DETENIDO${NC}"

        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            if kill -0 "$pid" 2>/dev/null; then
                status="${GREEN}🟢 ACTIVO (PID: $pid)${NC}"
            fi
        fi

        printf "   %-20s %b\n" "$service:" "$status"
    done

    echo ""

    # Estado de la cola
    if [ -d "${WIKIRAG_HOME}/queue/inbox" ]; then
        local inbox_count=$(find "${WIKIRAG_HOME}/queue/inbox" -maxdepth 1 -type f \( -name "*.task" -o -name "*.plan" -o -name "*.msg" \) 2>/dev/null | wc -l | tr -d ' ')
        local processing_count=$(find "${WIKIRAG_HOME}/queue/processing" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' ')

        log "${BLUE}📬 Cola de tareas:${NC}"
        echo "   Inbox:      $inbox_count tareas"
        echo "   Processing: $processing_count tareas"
    fi
}

show_logs() {
    local service=${1:-"queue_daemon"}
    local log_file="${LOG_DIR}/${service}.log"

    if [ -f "$log_file" ]; then
        tail -f "$log_file"
    else
        log "${RED}Log no encontrado: $log_file${NC}"
    fi
}

# === MAIN ===

case "${1:-start}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        sleep 2
        start_all
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "${2:-queue_daemon}"
        ;;
    help|--help|-h)
        echo "WikiRAG Ecosystem Launcher"
        echo ""
        echo "Uso: $0 [comando]"
        echo ""
        echo "Comandos:"
        echo "  start    Iniciar todos los servicios (default)"
        echo "  stop     Detener todos los servicios"
        echo "  restart  Reiniciar todos los servicios"
        echo "  status   Mostrar estado de los servicios"
        echo "  logs     Ver logs (ej: $0 logs queue_daemon)"
        echo "  help     Mostrar esta ayuda"
        ;;
    *)
        echo "Comando desconocido: $1"
        echo "Usa '$0 help' para ver opciones"
        exit 1
        ;;
esac
