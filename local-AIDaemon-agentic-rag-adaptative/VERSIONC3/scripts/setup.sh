#!/bin/bash
# ============================================================
# 🔧 SETUP - Configuración inicial del sistema
# ============================================================
# Crea directorios, instala dependencias y valida configuración.
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
VENV="${BASE_DIR}/venv"

# === FUNCIONES ===
log() {
    echo -e "${CYAN}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${VERDE}✅${NC} $1"
}

warning() {
    echo -e "${AMARILLO}⚠️${NC} $1"
}

error() {
    echo -e "${ROJO}❌${NC} $1" >&2
}

crear_directorios() {
    log "Creando estructura de directorios..."

    mkdir -p "${BASE_DIR}/rags/exitos"
    mkdir -p "${BASE_DIR}/rags/fallos"
    mkdir -p "${BASE_DIR}/rags/agentes"
    mkdir -p "${BASE_DIR}/logs"
    mkdir -p "${BASE_DIR}/pipes"
    mkdir -p "${BASE_DIR}/queue"

    success "Directorios creados"
}

crear_pipe() {
    local pipe="${BASE_DIR}/pipes/entrada.pipe"

    if [[ ! -p "$pipe" ]]; then
        log "Creando pipe nombrado..."
        mkfifo "$pipe"
        success "Pipe creado: $pipe"
    else
        success "Pipe ya existe: $pipe"
    fi
}

setup_venv() {
    if [[ ! -d "$VENV" ]]; then
        log "Creando entorno virtual Python..."
        python3 -m venv "$VENV"
    fi

    log "Activando entorno virtual..."
    source "$VENV/bin/activate"

    log "Instalando dependencias Python..."
    pip install --quiet --upgrade pip
    pip install --quiet \
        sentence-transformers \
        faiss-cpu \
        numpy \
        torch

    success "Dependencias instaladas"
    deactivate
}

validar_llama() {
    local llama_cli="${HOME}/modelo/llama.cpp/build/bin/llama-cli"

    log "Validando llama-cli..."

    if [[ -x "$llama_cli" ]]; then
        success "llama-cli encontrado: $llama_cli"
    else
        warning "llama-cli no encontrado en: $llama_cli"
        echo "   Asegúrate de compilar llama.cpp:"
        echo "   cd ~/modelo/llama.cpp && make"
    fi
}

validar_modelos() {
    log "Validando modelos..."

    local models=(
        "${HOME}/modelo/modelos_grandes/mistral3/Ministral-8B-Instruct-2410-Q8_0.gguf"
        "${HOME}/modelo/modelos_grandes/M6/mistral-7b-instruct-v0.1.Q6_K.gguf"
    )

    for model in "${models[@]}"; do
        if [[ -f "$model" ]]; then
            success "Modelo encontrado: $(basename "$model")"
        else
            warning "Modelo no encontrado: $model"
        fi
    done
}

validar_rag_index() {
    local index="${BASE_DIR}/index"

    log "Validando índice RAG de Wikipedia..."

    if [[ -d "$index" ]] && [[ -f "$index/faiss_index.index" ]]; then
        local size=$(du -sh "$index" 2>/dev/null | cut -f1)
        success "Índice RAG encontrado: $size"
    else
        warning "Índice RAG no encontrado en: $index"
        echo "   El sistema funcionará pero sin contexto de Wikipedia"
    fi
}

hacer_ejecutables() {
    log "Haciendo scripts ejecutables..."

    chmod +x "${BASE_DIR}/scripts/"*.sh 2>/dev/null || true
    success "Scripts configurados"
}

mostrar_resumen() {
    echo ""
    echo -e "${VERDE}============================================================${NC}"
    echo -e "${VERDE}   🎉 SETUP COMPLETADO${NC}"
    echo -e "${VERDE}============================================================${NC}"
    echo ""
    echo "Estructura creada en: $BASE_DIR"
    echo ""
    echo "Para usar el sistema:"
    echo ""
    echo "  1. Terminal 1 (daemon):"
    echo "     cd $BASE_DIR/scripts"
    echo "     ./start_daemon.sh"
    echo ""
    echo "  2. Terminal 2 (orquestador):"
    echo "     cd $BASE_DIR/scripts"
    echo "     ./start_orchestrator.sh"
    echo ""
    echo "  O consulta única:"
    echo "     ./query.sh \"¿Qué es Python?\""
    echo ""
}

# === MAIN ===
main() {
    echo -e "${CYAN}"
    echo "============================================================"
    echo "   🔧 SETUP - Sistema de IA con Agentes y RAGs"
    echo "============================================================"
    echo -e "${NC}"

    crear_directorios
    crear_pipe
    setup_venv
    validar_llama
    validar_modelos
    validar_rag_index
    hacer_ejecutables
    mostrar_resumen
}

main "$@"
