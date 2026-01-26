#!/bin/bash
# ============================================================
# 🎯 START ORCHESTRATOR - Inicia el Orquestador
# ============================================================
# Modo interactivo o worker de cola.
# ============================================================
# ==================================================================================
# Compare responses across multiple LLaMA models with cross-evaluation and response
# combination. Supports automatic setup and model configuration.
# 
# Author: Gustavo Silva da Costa
# License: MIT
# Version: 1.0.0
# ==================================================================================

set -euo pipefail

# === CLEANUP ===
cleanup() {
    # Esperar a que Python termine limpiamente
    wait 2>/dev/null || true
    deactivate 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# === COLORES ===
VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
ROJO='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# === CONFIGURACIÓN ===
BASE_DIR="${HOME}/wikirag"
ORCHESTRATOR="${BASE_DIR}/core/orchestrator.py"
VENV="${BASE_DIR}/venv"

# === FUNCIONES ===
log() {
    echo -e "${CYAN}[$(date '+%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${ROJO}[ERROR]${NC} $1" >&2
}

setup_venv() {
    if [[ ! -d "$VENV" ]]; then
        log "Creando entorno virtual..."
        python3 -m venv "$VENV"
    fi

    log "Activando entorno virtual..."
    source "$VENV/bin/activate"

    # Instalar dependencias si es necesario
    if ! pip show sentence-transformers &>/dev/null; then
        log "Instalando dependencias..."
        pip install --quiet sentence-transformers faiss-cpu
    fi
}

run_orchestrator() {
    # Ejecutar desde directorio base con PYTHONPATH
    cd "$BASE_DIR"
    export PYTHONPATH="$BASE_DIR:${PYTHONPATH:-}"

    # Evitar leak de semáforos de loky/joblib
    export LOKY_MAX_CPU_COUNT=1
    export JOBLIB_MULTIPROCESSING=0

    python3 -m core.orchestrator "$@"
}

# === MAIN ===
main() {
    echo -e "${VERDE}"
    echo "============================================================"
    echo "   🎯 ORQUESTADOR - Sistema de IA con Agentes y RAGs"
    echo "============================================================"
    echo -e "${NC}"

    if [[ ! -f "$ORCHESTRATOR" ]]; then
        error "Orquestador no encontrado: $ORCHESTRATOR"
        exit 1
    fi

    setup_venv

    case "${1:-interactive}" in
        interactive|-i)
            log "Iniciando modo interactivo..."
            run_orchestrator --interactive
            ;;
        worker|-w)
            log "Iniciando worker de cola..."
            run_orchestrator --worker
            ;;
        query)
            shift
            if [[ $# -eq 0 ]]; then
                error "Uso: $0 query <tu pregunta>"
                exit 1
            fi
            run_orchestrator "$@"
            ;;
        *)
            echo "Uso: $0 [interactive|worker|query <pregunta>]"
            echo ""
            echo "Modos:"
            echo "  interactive  - Modo interactivo (default)"
            echo "  worker       - Worker de cola en background"
            echo "  query <text> - Consulta única"
            ;;
    esac

}

main "$@"
