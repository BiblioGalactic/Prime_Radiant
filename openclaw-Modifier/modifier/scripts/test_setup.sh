#!/bin/bash
# ==============================================================================
# 🧪 TEST AUTOMATIZADO - Verificación Completa
# ==============================================================================
# Autor: Gustavo Silva da Costa (Eto Demerzel)
# GitHub: https://github.com/BiblioGalactic/openclaw-modifier
# Versión: 1.0.0
# Descripción: Suite de 39 tests automatizados para validar configuración,
#              requisitos, workspaces y funcionamiento del sistema
# ==============================================================================

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Contadores
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# ============================================
# Funciones de utilidad
# ============================================

test_start() {
    echo -n "  $1... "
    ((TESTS_TOTAL++))
}

test_pass() {
    echo -e "${GREEN}✓ PASS${NC}"
    ((TESTS_PASSED++))
}

test_fail() {
    echo -e "${RED}✗ FAIL${NC}"
    if [ -n "${1:-}" ]; then
        echo "    Error: $1"
    fi
    ((TESTS_FAILED++))
}

# ============================================
# Tests de requisitos
# ============================================

test_requisitos() {
    echo ""
    echo -e "${CYAN}📦 Testing requisitos básicos${NC}"

    # bash
    test_start "bash disponible"
    if command -v bash &> /dev/null; then
        test_pass
    else
        test_fail "bash no encontrado"
    fi

    # curl
    test_start "curl disponible"
    if command -v curl &> /dev/null; then
        test_pass
    else
        test_fail "curl no encontrado"
    fi

    # node
    test_start "node >= 18"
    if command -v node &> /dev/null; then
        version=$(node --version | sed 's/v//' | cut -d. -f1)
        if [ "$version" -ge 18 ]; then
            test_pass
        else
            test_fail "node version $version < 18"
        fi
    else
        test_fail "node no encontrado"
    fi
}

# ============================================
# Tests de configuración
# ============================================

test_configuracion() {
    echo ""
    echo -e "${CYAN}⚙️  Testing configuración${NC}"

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    MODIFIER_DIR="$(dirname "$SCRIPT_DIR")"

    # model_config.env existe
    test_start "model_config.env existe"
    if [ -f "$MODIFIER_DIR/configs/model_config.env" ]; then
        test_pass
    else
        test_fail "Archivo no encontrado"
        return
    fi

    # shellcheck source=/dev/null
    source "$MODIFIER_DIR/configs/model_config.env"

    # MODEL_PATH configurado
    test_start "MODEL_PATH configurado"
    if [ -n "${MODEL_PATH:-}" ]; then
        test_pass
    else
        test_fail "MODEL_PATH vacío"
    fi

    # Modelo existe
    test_start "Archivo de modelo existe"
    if [ -f "${MODEL_PATH:-}" ]; then
        test_pass
    else
        test_fail "Modelo no encontrado en: ${MODEL_PATH:-}"
    fi

    # llama-server existe
    test_start "llama-server existe"
    if [ -f "${LLAMA_BIN:-}" ]; then
        test_pass
    else
        test_fail "llama-server no encontrado en: ${LLAMA_BIN:-}"
    fi

    # llama-server ejecutable
    test_start "llama-server ejecutable"
    if [ -x "${LLAMA_BIN:-}" ]; then
        test_pass
    else
        test_fail "Sin permisos de ejecución"
    fi

    # Configuraciones JSON existen
    test_start "single_agent.json existe"
    if [ -f "$MODIFIER_DIR/configs/single_agent.json" ]; then
        test_pass
    else
        test_fail
    fi

    test_start "multi_agent.json existe"
    if [ -f "$MODIFIER_DIR/configs/multi_agent.json" ]; then
        test_pass
    else
        test_fail
    fi
}

# ============================================
# Tests de workspaces
# ============================================

test_workspaces() {
    echo ""
    echo -e "${CYAN}📁 Testing workspaces${NC}"

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    MODIFIER_DIR="$(dirname "$SCRIPT_DIR")"

    for agent in default daneel dors giskard; do
        test_start "Workspace $agent existe"
        if [ -d "$MODIFIER_DIR/workspaces/$agent" ]; then
            test_pass
        else
            test_fail
        fi

        if [ "$agent" != "default" ]; then
            test_start "SOUL.md de $agent existe"
            if [ -f "$MODIFIER_DIR/workspaces/$agent/SOUL.md" ]; then
                test_pass
            else
                test_fail
            fi
        fi
    done
}

# ============================================
# Tests de puertos
# ============================================

test_puertos() {
    echo ""
    echo -e "${CYAN}🔌 Testing disponibilidad de puertos${NC}"

    for port in 8080 8081 8082 3000; do
        test_start "Puerto $port disponible"
        if lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
            test_fail "Puerto en uso"
        else
            test_pass
        fi
    done
}

# ============================================
# Tests de scripts
# ============================================

test_scripts() {
    echo ""
    echo -e "${CYAN}📜 Testing scripts${NC}"

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    for script in check_requirements.sh start_single_agent.sh start_multi_agent.sh stop_all.sh; do
        test_start "Script $script existe"
        if [ -f "$SCRIPT_DIR/$script" ]; then
            test_pass
        else
            test_fail
        fi

        test_start "Script $script ejecutable"
        if [ -x "$SCRIPT_DIR/$script" ]; then
            test_pass
        else
            test_fail
        fi
    done
}

# ============================================
# Test de llama-server (si ya está corriendo)
# ============================================

test_llama_server_running() {
    echo ""
    echo -e "${CYAN}🚀 Testing llama-server (si está corriendo)${NC}"

    # Solo test si el servidor está activo
    for port in 8080 8081 8082; do
        if curl -s "http://127.0.0.1:$port/health" > /dev/null 2>&1; then
            test_start "llama-server en :$port health check"
            if curl -s "http://127.0.0.1:$port/health" | grep -q "ok"; then
                test_pass
            else
                test_fail
            fi

            test_start "llama-server en :$port models endpoint"
            if curl -s "http://127.0.0.1:$port/v1/models" | grep -q "model"; then
                test_pass
            else
                test_fail
            fi
        fi
    done
}

# ============================================
# Resumen final
# ============================================

mostrar_resumen() {
    echo ""
    echo "=================================================="
    echo "📊 RESUMEN DE TESTS"
    echo "=================================================="
    echo ""
    echo "Total:   $TESTS_TOTAL"
    echo -e "Pasados: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Fallados: ${RED}$TESTS_FAILED${NC}"
    echo ""

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ TODOS LOS TESTS PASARON${NC}"
        echo ""
        echo "El sistema está listo para usarse."
        echo ""
        echo "Siguiente paso:"
        echo "  ./scripts/start_single_agent.sh    # Para un solo agente"
        echo "  ./scripts/start_multi_agent.sh     # Para multi-agente"
        echo ""
        return 0
    else
        echo -e "${RED}❌ HAY TESTS QUE FALLARON${NC}"
        echo ""
        echo "Revisa los errores arriba antes de continuar."
        echo ""
        return 1
    fi
}

# ============================================
# Ejecución principal
# ============================================

echo "=================================================="
echo "🧪 TEST AUTOMATIZADO - OpenClaw Local Modifier"
echo "=================================================="

test_requisitos
test_configuracion
test_workspaces
test_puertos
test_scripts
test_llama_server_running
mostrar_resumen
