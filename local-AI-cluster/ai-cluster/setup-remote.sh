#!/bin/bash
# ===================================================================
# 🛠️ SETUP REMOTE - Helper para Preparar Máquinas Remotas
# ===================================================================
# Script auxiliar para instalar llama.cpp y copiar modelos
# a máquinas remotas de forma automática
# ===================================================================

set -euo pipefail

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $*"; }
success() { echo -e "${GREEN}[✓]${NC} $*"; }
warning() { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*"; }

# ===================================================================
# FUNCIONES
# ===================================================================

mostrar_ayuda() {
    cat << 'EOF'
🛠️  SETUP REMOTE - Helper para Preparar Máquinas Remotas

USO:
  ./setup-remote.sh <usuario@ip> <ruta_modelo_local>

EJEMPLO:
  ./setup-remote.sh gustavo@192.168.1.82 ~/modelo/mistral.gguf

LO QUE HACE:
  1. Verifica conexión SSH
  2. Instala dependencias (si es necesario)
  3. Clona y compila llama.cpp
  4. Copia el modelo GGUF
  5. Verifica que todo funcione

REQUISITOS:
  - SSH sin contraseña configurado (ssh-copy-id)
  - Conexión a internet en la máquina remota

EOF
}

verificar_ssh() {
    local target=$1
    
    log "Verificando conexión SSH con $target..."
    
    if ssh -o BatchMode=yes -o ConnectTimeout=5 "$target" "echo ok" &>/dev/null; then
        success "Conexión SSH OK"
        return 0
    else
        error "No se puede conectar por SSH"
        warning "Ejecuta primero: ssh-copy-id $target"
        return 1
    fi
}

detectar_os() {
    local target=$1
    
    log "Detectando sistema operativo..."
    
    local os=$(ssh "$target" "uname -s" 2>/dev/null)
    
    case "$os" in
        Darwin)
            success "Detectado: macOS"
            echo "macos"
            ;;
        Linux)
            success "Detectado: Linux"
            echo "linux"
            ;;
        *)
            warning "Sistema desconocido: $os"
            echo "unknown"
            ;;
    esac
}

instalar_dependencias() {
    local target=$1
    local os=$2
    
    log "Verificando dependencias..."
    
    case "$os" in
        macos)
            # Verifica Xcode Command Line Tools
            if ! ssh "$target" "xcode-select -p" &>/dev/null; then
                log "Instalando Xcode Command Line Tools..."
                ssh "$target" "xcode-select --install" || true
                success "Dependencias instaladas"
            else
                success "Dependencias ya instaladas"
            fi
            ;;
        linux)
            # Verifica build-essential
            if ! ssh "$target" "which gcc" &>/dev/null; then
                log "Instalando build-essential..."
                ssh "$target" "sudo apt-get update && sudo apt-get install -y build-essential git" || {
                    warning "No se pudieron instalar dependencias automáticamente"
                    warning "Instala manualmente: sudo apt-get install build-essential git"
                }
            else
                success "Dependencias ya instaladas"
            fi
            ;;
    esac
}

instalar_llama_cpp() {
    local target=$1
    
    log "Instalando llama.cpp..."
    
    # Verifica si ya existe
    if ssh "$target" "test -d ~/modelo/llama.cpp"; then
        warning "llama.cpp ya existe"
        read -p "¿Reinstalar? (s/n): " respuesta
        [[ "$respuesta" != "s" ]] && return 0
        ssh "$target" "rm -rf ~/modelo/llama.cpp"
    fi
    
    # Clona y compila
    ssh "$target" << 'ENDSSH'
        mkdir -p ~/modelo
        cd ~/modelo
        git clone https://github.com/ggerganov/llama.cpp
        cd llama.cpp
        make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
ENDSSH
    
    if ssh "$target" "test -f ~/modelo/llama.cpp/build/bin/llama-cli"; then
        success "llama.cpp instalado correctamente"
        return 0
    else
        error "Falló la instalación de llama.cpp"
        return 1
    fi
}

copiar_modelo() {
    local target=$1
    local modelo_local=$2
    
    if [[ ! -f "$modelo_local" ]]; then
        error "Modelo no encontrado: $modelo_local"
        return 1
    fi
    
    local modelo_nombre=$(basename "$modelo_local")
    local tamano=$(du -h "$modelo_local" | cut -f1)
    
    log "Copiando modelo ($tamano)..."
    warning "Esto puede tardar varios minutos..."
    
    # Copia con progress
    if command -v rsync &>/dev/null; then
        rsync -avh --progress "$modelo_local" "${target}:~/modelo/"
    else
        scp "$modelo_local" "${target}:~/modelo/"
    fi
    
    if ssh "$target" "test -f ~/modelo/$modelo_nombre"; then
        success "Modelo copiado: ~/modelo/$modelo_nombre"
        return 0
    else
        error "Falló la copia del modelo"
        return 1
    fi
}

verificar_instalacion() {
    local target=$1
    
    log "Verificando instalación..."
    
    local modelo=$(ssh "$target" "ls ~/modelo/*.gguf 2>/dev/null | head -n1")
    
    if [[ -z "$modelo" ]]; then
        error "No se encontró modelo GGUF"
        return 1
    fi
    
    log "Probando llama-cli con modelo..."
    
    ssh "$target" << ENDSSH
        ~/modelo/llama.cpp/build/bin/llama-cli \
            -m $modelo \
            -p "Di hola" \
            -n 5 \
            --no-display-prompt
ENDSSH
    
    if [[ $? -eq 0 ]]; then
        success "¡Todo funciona correctamente!"
        echo ""
        success "Configuración completada:"
        echo "  llama-cli: ~/modelo/llama.cpp/build/bin/llama-cli"
        echo "  Modelo: $modelo"
        return 0
    else
        error "La prueba falló"
        return 1
    fi
}

# ===================================================================
# MAIN
# ===================================================================

main() {
    if [[ $# -lt 2 ]]; then
        mostrar_ayuda
        exit 1
    fi
    
    local target=$1
    local modelo_local=$2
    
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════╗
║     🛠️  SETUP REMOTE - Preparar Máquina Remota           ║
╚═══════════════════════════════════════════════════════════╝
EOF
    echo ""
    
    log "Target: $target"
    log "Modelo: $modelo_local"
    echo ""
    
    # Pipeline de instalación
    verificar_ssh "$target" || exit 1
    
    local os=$(detectar_os "$target")
    [[ "$os" == "unknown" ]] && { warning "Continuando con OS desconocido..."; }
    
    instalar_dependencias "$target" "$os"
    instalar_llama_cpp "$target" || exit 1
    copiar_modelo "$target" "$modelo_local" || exit 1
    verificar_instalacion "$target" || exit 1
    
    echo ""
    success "🎉 Máquina remota lista para usar con AI Cluster"
    echo ""
    log "Ahora puedes ejecutar:"
    echo "  ./ai-cluster.sh setup"
}

main "$@"
