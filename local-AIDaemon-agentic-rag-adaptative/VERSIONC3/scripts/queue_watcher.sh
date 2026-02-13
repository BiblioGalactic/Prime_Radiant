#!/bin/bash
# ============================================================
# 🤖 WIKIRAG QUEUE WATCHER v1.0
# ============================================================
# Monitorea la carpeta inbox y despierta al daemon cuando
# hay nuevas tareas. Usa fswatch para eventos de filesystem.
# ============================================================
set -euo pipefail
trap cleanup EXIT

# === CONFIGURACIÓN ===
WIKIRAG_HOME="${HOME}/wikirag"
WATCH_DIR="${WIKIRAG_HOME}/queue/inbox"
LOG_DIR="${WIKIRAG_HOME}/queue/logs"
PID_FILE="${WIKIRAG_HOME}/queue/.watcher.pid"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# === FUNCIONES ===

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

cleanup() {
    log "${YELLOW}🛑 Deteniendo watcher...${NC}"
    rm -f "$PID_FILE"
    rm -rf "${WATCH_DIR}"/*.tmp 2>/dev/null || true
}

check_dependencies() {
    # Verificar fswatch
    if ! command -v fswatch &> /dev/null; then
        log "${RED}❌ fswatch no instalado${NC}"
        log "   Instala con: brew install fswatch"
        exit 1
    fi

    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        log "${RED}❌ Python3 no encontrado${NC}"
        exit 1
    fi
}

ensure_directories() {
    mkdir -p "$WATCH_DIR" "$LOG_DIR"
}

process_queue() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local log_file="${LOG_DIR}/queue_${timestamp}.log"

    log "${BLUE}📩 Nueva actividad detectada...${NC}"

    # Procesar todas las tareas pendientes
    cd "$WIKIRAG_HOME"
    python3 -m core.queue_daemon --process-all 2>&1 | tee -a "$log_file"

    log "${GREEN}✅ Procesamiento completado${NC}"
}

show_status() {
    log "${BLUE}📊 Estado de la cola:${NC}"
    cd "$WIKIRAG_HOME"
    python3 -m core.queue_daemon --status
}

# === MAIN ===

main() {
    check_dependencies
    ensure_directories

    # Guardar PID
    echo $$ > "$PID_FILE"

    log "${GREEN}🚀 Queue Watcher iniciado${NC}"
    log "   📂 Monitoreando: ${WATCH_DIR}"
    log "   📝 Logs en: ${LOG_DIR}"
    log "   🔧 PID: $$"
    echo ""

    # Mostrar estado inicial
    show_status
    echo ""

    log "${YELLOW}⏳ Esperando tareas... (Ctrl+C para salir)${NC}"
    echo ""

    # Monitorear con fswatch
    # -o: Modo batch (agrupa eventos)
    # -r: Recursivo
    # -e ".*": Excluir archivos ocultos
    # --event Created: Solo eventos de creación
    fswatch -o -r -e ".*" --event Created --event Updated "$WATCH_DIR" | while read -r num_events; do
        # Pequeño delay para que terminen de escribirse los archivos
        sleep 1

        # Contar archivos pendientes
        count=$(find "$WATCH_DIR" -maxdepth 1 -type f \( -name "*.task" -o -name "*.plan" -o -name "*.msg" \) 2>/dev/null | wc -l | tr -d ' ')

        if [ "$count" -gt 0 ]; then
            log "${GREEN}📥 $count tarea(s) detectada(s)${NC}"
            process_queue
        fi
    done
}

# === ARGUMENT PARSING ===

case "${1:-}" in
    --help|-h)
        echo "WikiRAG Queue Watcher"
        echo ""
        echo "Uso: $0 [opciones]"
        echo ""
        echo "Opciones:"
        echo "  --help, -h     Mostrar esta ayuda"
        echo "  --status, -s   Mostrar estado de la cola"
        echo "  --stop         Detener watcher en ejecución"
        echo ""
        echo "Sin argumentos: iniciar monitoreo"
        ;;
    --status|-s)
        show_status
        ;;
    --stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                log "Deteniendo watcher (PID: $PID)..."
                kill "$PID"
                log "✅ Watcher detenido"
            else
                log "Watcher no está corriendo"
                rm -f "$PID_FILE"
            fi
        else
            log "No hay watcher en ejecución"
        fi
        ;;
    *)
        main
        ;;
esac
