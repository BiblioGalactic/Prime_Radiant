#!/bin/bash
# ============================================================
# 📝 QUERY - Enviar consulta al sistema
# ============================================================
# Script simple para enviar consultas desde terminal.
# ============================================================

set -euo pipefail

# === CONFIGURACIÓN ===
BASE_DIR="${HOME}/wikirag"
PIPE="${BASE_DIR}/pipes/entrada.pipe"
LOG_PATH="${BASE_DIR}/logs/daemon.log"
ORCHESTRATOR="${BASE_DIR}/core/orchestrator.py"
VENV="${BASE_DIR}/venv"

# === COLORES ===
VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
ROJO='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# === FUNCIONES ===
send_to_pipe() {
    local query="$1"

    if [[ ! -p "$PIPE" ]]; then
        echo -e "${ROJO}❌ Pipe no existe. ¿Está el daemon corriendo?${NC}"
        echo "   Inicia el daemon con: ./start_daemon.sh"
        exit 1
    fi

    echo -e "${CYAN}📤 Enviando al daemon...${NC}"
    echo "$query" > "$PIPE"

    # Esperar respuesta
    echo -e "${CYAN}⏳ Esperando respuesta...${NC}"
    sleep 2

    # Mostrar últimas líneas del log
    echo -e "${VERDE}📥 Respuesta:${NC}"
    tail -n 20 "$LOG_PATH" 2>/dev/null || echo "Sin respuesta aún"
}

send_to_orchestrator() {
    local query="$1"

    if [[ ! -f "$ORCHESTRATOR" ]]; then
        echo -e "${ROJO}❌ Orquestador no encontrado${NC}"
        exit 1
    fi

    # Activar venv si existe
    if [[ -d "$VENV" ]]; then
        source "$VENV/bin/activate"
    fi

    echo -e "${CYAN}🎯 Enviando al orquestador...${NC}"
    python3 "$ORCHESTRATOR" "$query"

    deactivate 2>/dev/null || true
}

# === MAIN ===
main() {
    if [[ $# -eq 0 ]]; then
        echo "============================================================"
        echo "   📝 QUERY - Enviar consulta al sistema"
        echo "============================================================"
        echo ""
        echo "Uso: $0 [--pipe|--orch] <tu pregunta>"
        echo ""
        echo "Modos:"
        echo "  --pipe  - Enviar directamente al pipe del daemon"
        echo "  --orch  - Enviar al orquestador (default)"
        echo ""
        echo "Ejemplos:"
        echo "  $0 \"¿Qué es Python?\""
        echo "  $0 --pipe \"Hola, ¿cómo estás?\""
        echo ""
        exit 0
    fi

    local mode="orch"
    local query=""

    # Parsear argumentos
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --pipe)
                mode="pipe"
                shift
                ;;
            --orch)
                mode="orch"
                shift
                ;;
            *)
                query="$*"
                break
                ;;
        esac
    done

    if [[ -z "$query" ]]; then
        echo -e "${ROJO}❌ No se proporcionó consulta${NC}"
        exit 1
    fi

    echo -e "${AMARILLO}❓ Consulta: $query${NC}"
    echo ""

    case "$mode" in
        pipe)
            send_to_pipe "$query"
            ;;
        orch)
            send_to_orchestrator "$query"
            ;;
    esac
}

main "$@"
