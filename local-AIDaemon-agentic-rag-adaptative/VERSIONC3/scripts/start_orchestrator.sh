#!/bin/bash
# ============================================================
# 🎯 START ORCHESTRATOR v2.3 - WikiRAG AUTÓNOMO
# ============================================================
# TODO ES AUTOMÁTICO:
# - Daemon se activa solo cuando se necesita
# - BM25 se carga bajo demanda
# - Cache automático
# ============================================================

set -euo pipefail

# === CLEANUP ===
cleanup() {
    echo ""
    echo -e "${AMARILLO}[$(date '+%H:%M:%S')]${NC} Limpiando recursos..."
    wait 2>/dev/null || true
    deactivate 2>/dev/null || true
    echo -e "${VERDE}✅ Limpieza completada${NC}"
}
trap cleanup EXIT INT TERM

# === COLORES ===
VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
ROJO='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# === CONFIGURACIÓN ===
BASE_DIR="${HOME}/wikirag"
ORCHESTRATOR="${BASE_DIR}/core/orchestrator.py"
VENV="${BASE_DIR}/venv"

# === FUNCIONES ===
log() { echo -e "${CYAN}[$(date '+%H:%M:%S')]${NC} $1"; }
warn() { echo -e "${AMARILLO}[WARN]${NC} $1"; }
error() { echo -e "${ROJO}[ERROR]${NC} $1" >&2; }
success() { echo -e "${VERDE}[OK]${NC} $1"; }

check_model() {
    local MODEL_PATH="${HOME}/modelo/modelos_grandes/mistral3/Ministral-8B-Instruct-2410-Q8_0.gguf"
    local FALLBACK_PATH=$(find "${HOME}/modelo" -name "*.gguf" -type f 2>/dev/null | head -1)

    if [[ -f "$MODEL_PATH" ]]; then
        success "Modelo: Ministral-8B-Q8_0"
        return 0
    elif [[ -n "$FALLBACK_PATH" ]]; then
        warn "Modelo: $(basename "$FALLBACK_PATH")"
        return 0
    else
        error "No se encontró modelo GGUF"
        return 1
    fi
}

check_llama_cli() {
    local LLAMA_CLI="${HOME}/modelo/llama.cpp/build/bin/llama-cli"
    if [[ -x "$LLAMA_CLI" ]]; then
        success "llama-cli OK"
        return 0
    else
        error "llama-cli no encontrado"
        return 1
    fi
}

setup_venv() {
    if [[ ! -d "$VENV" ]]; then
        log "Creando entorno virtual..."
        python3 -m venv "$VENV"
    fi
    source "$VENV/bin/activate"

    local missing=()
    pip show sentence-transformers &>/dev/null || missing+=("sentence-transformers")
    pip show faiss-cpu &>/dev/null || missing+=("faiss-cpu")

    if [[ ${#missing[@]} -gt 0 ]]; then
        warn "Instalando: ${missing[*]}"
        pip install --quiet "${missing[@]}"
    fi
}

run_orchestrator() {
    cd "$BASE_DIR"
    export PYTHONPATH="$BASE_DIR:${PYTHONPATH:-}"
    export LOKY_MAX_CPU_COUNT=1
    export JOBLIB_MULTIPROCESSING=0
    python3 -m core.orchestrator "$@"
}

show_banner() {
    echo -e "${BOLD}${CYAN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║       🧠 WIKIRAG v2.3 - Sistema IA AUTÓNOMO              ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# === MAIN ===
main() {
    show_banner

    log "Verificando sistema..."
    [[ -f "$ORCHESTRATOR" ]] || { error "Orquestador no encontrado"; exit 1; }
    check_llama_cli || exit 1
    check_model || exit 1
    setup_venv

    echo ""
    log "🚀 Iniciando WikiRAG..."
    echo ""

    case "${1:-interactive}" in
        interactive|-i|"")
            run_orchestrator --interactive
            ;;
        query)
            shift
            [[ $# -eq 0 ]] && { error "Uso: $0 query <pregunta>"; exit 1; }
            run_orchestrator "$@"
            ;;
        memory|mem)
            python3 "${BASE_DIR}/scripts/memory_diagnostic.py"
            ;;
        help|-h|--help)
            echo "Uso: $0 [comando]"
            echo ""
            echo "  (vacío)       - Modo interactivo"
            echo "  query <text>  - Consulta única"
            echo "  memory        - Diagnóstico de memoria"
            echo ""
            echo "TODO AUTOMÁTICO - daemon y BM25 se activan solos."
            ;;
        *)
            error "Comando: $1"; echo "Usa: $0 help"; exit 1
            ;;
    esac
}

main "$@"
