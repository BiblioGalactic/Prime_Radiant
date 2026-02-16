#!/bin/bash
# ==============================================================================
# 🔍 VERIFICADOR DE REQUISITOS - OpenClaw Local Model Modifier
# ==============================================================================
# Autor: Gustavo Silva da Costa (Eto Demerzel)
# GitHub: https://github.com/BiblioGalactic/openclaw-modifier
# Versión: 1.0.0
# Descripción: Valida requisitos del sistema para ejecutar OpenClaw con
#              modelos locales mediante llama.cpp
# ==============================================================================

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=================================================="
echo "🔍 Verificando requisitos para OpenClaw + llama.cpp"
echo "=================================================="
echo ""

ERRORS=0
WARNINGS=0

# ============================================
# Funciones de utilidad
# ============================================

check_command() {
    local cmd=$1
    local name=$2
    local required=$3

    if command -v "$cmd" &> /dev/null; then
        local version
        version=$($cmd --version 2>&1 | head -n 1 || echo "unknown")
        echo -e "${GREEN}✓${NC} $name: ${BLUE}$version${NC}"
        return 0
    else
        if [ "$required" = "yes" ]; then
            echo -e "${RED}✗${NC} $name: NO ENCONTRADO (REQUERIDO)"
            ((ERRORS++))
        else
            echo -e "${YELLOW}⚠${NC} $name: NO ENCONTRADO (OPCIONAL)"
            ((WARNINGS++))
        fi
        return 1
    fi
}

check_node_version() {
    if command -v node &> /dev/null; then
        local version
        version=$(node --version | sed 's/v//')
        local major
        major=$(echo "$version" | cut -d. -f1)

        if [ "$major" -ge 18 ]; then
            echo -e "${GREEN}✓${NC} Node.js: ${BLUE}v$version${NC} (>= 18.0.0)"
        else
            echo -e "${RED}✗${NC} Node.js: ${YELLOW}v$version${NC} (se requiere >= 18.0.0)"
            ((ERRORS++))
        fi
    else
        echo -e "${RED}✗${NC} Node.js: NO ENCONTRADO"
        ((ERRORS++))
    fi
}

check_ram() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        local ram_gb
        ram_gb=$(sysctl hw.memsize | awk '{print int($2/1024/1024/1024)}')
        if [ "$ram_gb" -ge 8 ]; then
            echo -e "${GREEN}✓${NC} RAM: ${BLUE}${ram_gb}GB${NC}"
        else
            echo -e "${YELLOW}⚠${NC} RAM: ${YELLOW}${ram_gb}GB${NC} (recomendado 8GB+)"
            ((WARNINGS++))
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        local ram_gb
        ram_gb=$(free -g | awk '/^Mem:/{print $2}')
        if [ "$ram_gb" -ge 8 ]; then
            echo -e "${GREEN}✓${NC} RAM: ${BLUE}${ram_gb}GB${NC}"
        else
            echo -e "${YELLOW}⚠${NC} RAM: ${YELLOW}${ram_gb}GB${NC} (recomendado 8GB+)"
            ((WARNINGS++))
        fi
    fi
}

check_disk_space() {
    local free_space
    if [[ "$OSTYPE" == "darwin"* ]]; then
        free_space=$(df -g . | awk 'NR==2 {print $4}')
    else
        free_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    fi

    if [ "$free_space" -ge 10 ]; then
        echo -e "${GREEN}✓${NC} Espacio en disco: ${BLUE}${free_space}GB libres${NC}"
    else
        echo -e "${YELLOW}⚠${NC} Espacio en disco: ${YELLOW}${free_space}GB libres${NC} (recomendado 10GB+)"
        ((WARNINGS++))
    fi
}

check_openclaw() {
    if command -v openclaw &> /dev/null; then
        local version
        version=$(openclaw --version 2>&1 | head -n 1 || echo "unknown")
        echo -e "${GREEN}✓${NC} OpenClaw CLI: ${BLUE}$version${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} OpenClaw CLI: NO ENCONTRADO"
        echo "   Instalar desde: https://github.com/openclaws/openclaw"
        ((WARNINGS++))
        return 1
    fi
}

# ============================================
# Verificaciones
# ============================================

echo "📦 Comandos básicos:"
echo "-------------------"
check_command "bash" "Bash" "yes"
check_command "curl" "curl" "yes"
check_command "jq" "jq" "no"

echo ""
echo "🖥️  Sistema:"
echo "-------------------"
check_ram
check_disk_space
echo -e "${BLUE}ℹ${NC}  OS: $OSTYPE"

echo ""
echo "🔧 Herramientas de desarrollo:"
echo "-------------------"
check_node_version
check_command "npm" "npm" "yes"
check_command "git" "git" "no"

echo ""
echo "🤖 llama.cpp:"
echo "-------------------"
LLAMA_PATHS=(
    "$HOME/modelo/llama.cpp/build/bin/llama-cli"
    "$HOME/llama.cpp/build/bin/llama-cli"
    "/usr/local/bin/llama-cli"
    "$(which llama-cli 2>/dev/null || echo '')"
)

LLAMA_FOUND=""
for path in "${LLAMA_PATHS[@]}"; do
    if [ -n "$path" ] && [ -f "$path" ]; then
        LLAMA_FOUND="$path"
        break
    fi
done

if [ -n "$LLAMA_FOUND" ]; then
    echo -e "${GREEN}✓${NC} llama-cli: ${BLUE}$LLAMA_FOUND${NC}"

    # Verificar que tenga permisos de ejecución
    if [ -x "$LLAMA_FOUND" ]; then
        echo -e "${GREEN}✓${NC} Permisos de ejecución: OK"
    else
        echo -e "${RED}✗${NC} Permisos de ejecución: FALTA"
        echo "   Ejecuta: chmod +x $LLAMA_FOUND"
        ((ERRORS++))
    fi

    # Verificar llama-server
    LLAMA_SERVER="${LLAMA_FOUND/llama-cli/llama-server}"
    if [ -f "$LLAMA_SERVER" ]; then
        echo -e "${GREEN}✓${NC} llama-server: ${BLUE}$LLAMA_SERVER${NC}"
    else
        echo -e "${RED}✗${NC} llama-server: NO ENCONTRADO"
        echo "   Esperado en: $LLAMA_SERVER"
        ((ERRORS++))
    fi
else
    echo -e "${RED}✗${NC} llama-cli: NO ENCONTRADO"
    echo "   Buscar en:"
    for path in "${LLAMA_PATHS[@]}"; do
        [ -n "$path" ] && echo "   - $path"
    done
    echo ""
    echo "   Instalar desde: https://github.com/ggerganov/llama.cpp"
    ((ERRORS++))
fi

echo ""
echo "🌐 OpenClaw:"
echo "-------------------"
check_openclaw

# Verificar directorio .openclaw
if [ -d "$HOME/.openclaw" ]; then
    echo -e "${GREEN}✓${NC} Directorio ~/.openclaw: EXISTE"

    # Verificar permisos
    if [ -w "$HOME/.openclaw" ]; then
        echo -e "${GREEN}✓${NC} Permisos de escritura: OK"
    else
        echo -e "${RED}✗${NC} Permisos de escritura: FALTA"
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}⚠${NC} Directorio ~/.openclaw: NO EXISTE (se creará al iniciar)"
fi

echo ""
echo "📝 Archivos de configuración:"
echo "-------------------"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODIFIER_DIR="$(dirname "$SCRIPT_DIR")"

# Verificar model_config.env
if [ -f "$MODIFIER_DIR/configs/model_config.env" ]; then
    echo -e "${GREEN}✓${NC} model_config.env: EXISTE"

    # Verificar que tenga MODEL_PATH configurado
    if grep -q "^MODEL_PATH=" "$MODIFIER_DIR/configs/model_config.env"; then
        MODEL_PATH=$(grep "^MODEL_PATH=" "$MODIFIER_DIR/configs/model_config.env" | cut -d= -f2- | tr -d '"' | tr -d "'")
        if [ -f "$MODEL_PATH" ]; then
            MODEL_SIZE=$(du -h "$MODEL_PATH" | cut -f1)
            echo -e "${GREEN}✓${NC} Modelo configurado: ${BLUE}$MODEL_PATH${NC} (${MODEL_SIZE})"
        else
            echo -e "${YELLOW}⚠${NC} Modelo configurado: ${YELLOW}$MODEL_PATH${NC} (NO EXISTE)"
            echo "   Edita: $MODIFIER_DIR/configs/model_config.env"
            ((WARNINGS++))
        fi
    else
        echo -e "${YELLOW}⚠${NC} MODEL_PATH no configurado en model_config.env"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}⚠${NC} model_config.env: NO EXISTE"
    echo "   Copia desde: $MODIFIER_DIR/configs/model_config.env.example"
    ((WARNINGS++))
fi

# ============================================
# Resumen final
# ============================================

echo ""
echo "=================================================="
echo "📊 RESUMEN"
echo "=================================================="
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ TODO LISTO${NC} - Puedes continuar con el setup"
    echo ""
    echo "Siguiente paso:"
    echo "  ./scripts/start_single_agent.sh    # Para un solo agente"
    echo "  ./scripts/start_multi_agent.sh     # Para multi-agente"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  HAY $WARNINGS ADVERTENCIA(S)${NC} - Puedes continuar, pero revisa los warnings"
    echo ""
    exit 0
else
    echo -e "${RED}❌ HAY $ERRORS ERROR(ES)${NC} - Corrige los errores antes de continuar"
    echo ""

    if [ $ERRORS -gt 0 ]; then
        echo "Errores críticos que debes solucionar:"
        echo ""
    fi

    exit 1
fi
