#!/bin/bash
# ============================================================
# 🧠 START DAEMON - Inicia el Daemon IA
# ============================================================
# Mantiene Ministral-8B cargado en memoria, lee del pipe
# y escribe respuestas al log.
# ============================================================

set -euo pipefail

# === COLORES ===
VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
ROJO='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# === CONFIGURACIÓN ===
BASE_DIR="${HOME}/wikirag"
PIPE="${BASE_DIR}/pipes/entrada.pipe"
LOG_PATH="${BASE_DIR}/logs/daemon.log"
VISUAL_OUT="${BASE_DIR}/logs/visual.txt"

# Modelo principal
MODEL="${HOME}/modelo/modelos_grandes/mistral3/Ministral-8B-Instruct-2410-Q8_0.gguf"
LLAMA_CLI="${HOME}/modelo/llama.cpp/build/bin/llama-cli"

# Prompt del sistema
SYSTEM_PROMPT="Eres un asistente IA experto. Respondes de forma precisa y útil.
Cuando respondas, evalúa tu respuesta:
- Si es completa y correcta, termina con OK
- Si falta información, termina con PARCIAL
- Si no puedes responder, termina con FALLA"

# === FUNCIONES ===
log() {
    echo -e "${CYAN}[$(date '+%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${ROJO}[ERROR]${NC} $1" >&2
}

validar_archivos() {
    log "Validando archivos..."

    if [[ ! -x "$LLAMA_CLI" ]]; then
        error "llama-cli no encontrado o no ejecutable: $LLAMA_CLI"
        exit 1
    fi

    if [[ ! -f "$MODEL" ]]; then
        error "Modelo no encontrado: $MODEL"
        exit 1
    fi

    log "✅ Archivos validados"
}

crear_directorios() {
    mkdir -p "$(dirname "$PIPE")"
    mkdir -p "$(dirname "$LOG_PATH")"
}

crear_pipe() {
    if [[ ! -p "$PIPE" ]]; then
        log "Creando pipe: $PIPE"
        mkfifo "$PIPE"
    fi
}

limpiar() {
    log "Limpiando..."
    # No eliminar el pipe, solo limpiar procesos
    pkill -f "llama-cli.*Ministral" 2>/dev/null || true
}

trap limpiar EXIT

# === MAIN ===
main() {
    echo -e "${VERDE}"
    echo "============================================================"
    echo "   🧠 DAEMON IA - Ministral-8B"
    echo "   Lee de: $PIPE"
    echo "   Escribe a: $LOG_PATH"
    echo "============================================================"
    echo -e "${NC}"

    validar_archivos
    crear_directorios
    crear_pipe

    # Limpiar log anterior
    > "$LOG_PATH"

    log "🚀 Iniciando daemon IA..."
    log "📝 Escribe en otro terminal: echo 'tu pregunta' > $PIPE"

    # Ejecutar daemon
    "$LLAMA_CLI" \
        -m "$MODEL" \
        --ctx-size 30096 \
        --threads 4 \
        --predict 500 \
        --interactive \
        --interactive-first \
        --color \
        -p "$SYSTEM_PROMPT" \
        < "$PIPE" 2>&1 | tee -a "$LOG_PATH" | tee "$VISUAL_OUT"
}

main "$@"
