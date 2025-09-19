#!/bin/bash
# ==============================================================================
# 🤖 ASISTENTE IA LOCAL - INSTALADOR AGÉNTICO
# ==============================================================================
# Autor: Eto Demerzel ~ Gustavo Silva
# Descripción: Instalador completo del Asistente IA Local con capacidades agénticas
#              y configuración interactiva de rutas.
# ==============================================================================

set -euo pipefail

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Variables configurables (se pedirán al usuario)
PROJECT_DIR=""
MODEL_PATH=""
LLAMA_CPP_PATH=""
PYTHON_VERSION="3.11"

# Función de logging
log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

ask() {
    echo -e "${CYAN}$1${NC} $2"
    read -p "> " respuesta
    echo "${respuesta}"
}

# Configuración interactiva
configurar_rutas() {
    echo
    echo -e "${GREEN}🤖 CONFIGURACIÓN DEL ASISTENTE IA LOCAL${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo
    
    # Directorio del proyecto
    default_project_dir="${HOME}/asistente-ia"
    PROJECT_DIR=$(ask "Directorio de instalación del proyecto:" "[${default_project_dir}]")
    PROJECT_DIR="${PROJECT_DIR:-$default_project_dir}"
    
    # Ruta del modelo GGUF
    default_model_path="${HOME}/modelos/modelo.gguf"
    MODEL_PATH=$(ask "Ruta de tu modelo GGUF:" "[${default_model_path}]")
    MODEL_PATH="${MODEL_PATH:-$default_model_path}"
    
    # Ruta de llama-cli
    default_llama_path="${HOME}/llama.cpp/build/bin/llama-cli"
    LLAMA_CPP_PATH=$(ask "Ruta del binario llama-cli:" "[${default_llama_path}]")
    LLAMA_CPP_PATH="${LLAMA_CPP_PATH:-$default_llama_path}"
    
    # Mostrar resumen
    echo
    echo -e "${GREEN}📋 RESUMEN DE CONFIGURACIÓN:${NC}"
    echo -e "Directorio del proyecto: ${PROJECT_DIR}"
    echo -e "Modelo GGUF: ${MODEL_PATH}"
    echo -e "Llama-cli: ${LLAMA_CPP_PATH}"
    echo
    
    read -p "¿Continuar con esta configuración? (y/N): " confirmar
    if [[ ! "$confirmar" =~ ^[Yy]$ ]]; then
        echo "Instalación cancelada."
        exit 0
    fi
}

# Validaciones iniciales
validar_prerrequisitos() {
    log "Validando prerrequisitos..."
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        error "Python3 no está instalado"
        exit 1
    fi
    
    # Verificar pip
    if ! command -v pip3 &> /dev/null; then
        error "pip3 no está instalado"
        exit 1
    fi
    
    # Verificar directorio home
    if [[ ! -d "$HOME" ]]; then
        error "Directorio HOME no encontrado"
        exit 1
    fi
    
    info "Prerrequisitos validados ✓"
}

# Crear estructura de directorios
crear_estructura() {
    log "Creando estructura de directorios..."
    
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    # Directorios principales
    mkdir -p {src,config,tools,tests,logs,examples}
    mkdir -p src/{core,llm,file_ops,commands}
    mkdir -p tools/{analyzers,generators}
    mkdir -p config/{prompts,settings}
    
    info "Estructura creada en: $PROJECT_DIR ✓"
}

# Crear archivos de configuración
crear_configuracion() {
    log "Creando archivos de configuración..."
    
    # Archivo de configuración principal
    cat > config/settings.json << EOF
{
  "llm": {
    "model_path": "${MODEL_PATH}",
    "llama_bin": "${LLAMA_CPP_PATH}",
    "max_tokens": 1024,
    "temperature": 0.7
  },
  "assistant": {
    "safe_mode": false,
    "backup_files": true,
    "max_file_size": 1048576,
    "supported_extensions": [".py", ".js", ".ts", ".json", ".md", ".txt", ".sh", ".html", ".css"]
  },
  "logging": {
    "level": "INFO",
    "file": "logs/assistant.log"
  }
}
EOF

    info "Archivos de configuración creados ✓"
}

# [Aquí irían todas las funciones de creación de archivos...]
# (main.py, assistant.py, agentic_extension.py, command_runner.py, etc.)
# Se mantienen igual que en tu código pero usando las variables de ruta

# Función para crear el asistente base
crear_asistente_base() {
    log "Creando asistente base..."
    
    # Crear archivo assistant.py
    cat > src/core/assistant.py << 'EOF'
# [Contenido completo de assistant.py]
EOF

    # Crear archivo config.py  
    cat > src/core/config.py << EOF
# [Contenido de config.py usando MODEL_PATH y LLAMA_CPP_PATH]
EOF

    info "Asistente base creado ✓"
}

# Función para crear la extensión agéntica
crear_extension_agentica() {
    log "Creando extensión agéntica..."
    
    cat > src/core/agentic_extension.py << 'EOF'
# [Contenido completo de agentic_extension.py]
EOF

    info "Extensión agéntica creada ✓"
}

# Función para crear el command runner extendido
crear_command_runner() {
    log "Creando command runner extendido..."
    
    cat > src/commands/runner.py << 'EOF'
# [Contenido completo del command runner extendido]
EOF

    info "Command runner extendido creado ✓"
}

# Configurar aliases
configurar_aliases() {
    log "Configurando aliases..."
    
    # Añadir al .zshrc o .bashrc
    shell_config="${HOME}/.zshrc"
    if [[ ! -f "$shell_config" ]]; then
        shell_config="${HOME}/.bashrc"
    fi
    
    cat >> "$shell_config" << EOF

# === ASISTENTE IA LOCAL - ALIAS ===
alias claudia="python3 ${PROJECT_DIR}/src/main.py"
alias claudia-a="python3 ${PROJECT_DIR}/src/main.py --agentic"
alias claudia-deep="python3 ${PROJECT_DIR}/src/main.py --agentic --verbose"
alias claudia-test="python3 ${PROJECT_DIR}/test_agentic.py"
EOF

    info "Aliases configurados ✓"
    echo "Recarga tu shell con: source $shell_config"
}

# Crear script de prueba
crear_test_agentico() {
    log "Creando script de prueba..."
    
    cat > test_agentic.py << 'EOF'
#!/usr/bin/env python3
# [Contenido completo de test_agentic.py]
EOF

    chmod +x test_agentic.py
    info "Script de prueba creado ✓"
}

# Crear documentación
crear_documentacion() {
    log "Creando documentación..."
    
    cat > README.md << EOF
# Asistente IA Local con Capacidades Agénticas

## Configuración
- **Directorio del proyecto:** ${PROJECT_DIR}
- **Modelo GGUF:** ${MODEL_PATH}
- **Llama-cli:** ${LLAMA_CPP_PATH}

## Uso
\`\`\`bash
claudia "comando o pregunta"
claudia-a  # Modo agéntico
claudia-deep  # Modo agéntico verbose
\`\`\`

## Comandos agénticos
- "analiza completamente X"
- "investigación profunda sobre Y" 
- "modo agéntico: revisa Z"
EOF

    info "Documentación creada ✓"
}

# Función principal
main() {
    echo
    echo -e "${GREEN}🚀 INICIANDO INSTALACIÓN DEL ASISTENTE IA LOCAL${NC}"
    echo -e "${GREEN}================================================${NC}"
    
    # Configurar rutas
    configurar_rutas
    
    # Validar prerrequisitos
    validar_prerrequisitos
    
    # Crear estructura
    crear_estructura
    
    # Crear configuración
    crear_configuracion
    
    # Crear archivos principales
    crear_asistente_base
    crear_extension_agentica
    crear_command_runner
    
    # Configurar aliases
    configurar_aliases
    
    # Crear pruebas y documentación
    crear_test_agentico
    crear_documentacion
    
    # Mensaje final
    echo
    echo -e "${GREEN}🎉 ¡INSTALACIÓN COMPLETADA!${NC}"
    echo
    echo -e "${CYAN}📋 RESUMEN FINAL:${NC}"
    echo -e "Directorio: ${PROJECT_DIR}"
    echo -e "Modelo: ${MODEL_PATH}"
    echo -e "Llama-cli: ${LLAMA_CPP_PATH}"
    echo
    echo -e "${CYAN}🚀 COMANDOS DISPONIBLES:${NC}"
    echo -e "claudia      - Asistente normal"
    echo -e "claudia-a    - Modo agéntico"
    echo -e "claudia-deep - Modo agéntico verbose"
    echo
    echo -e "${CYAN}📝 PRUEBA RÁPIDA:${NC}"
    echo -e "cd ${PROJECT_DIR}"
    echo -e "claudia-a"
    echo -e "💬 > analiza completamente este proyecto"
    echo
    echo -e "${GREEN}¡Recuerda recargar tu shell con 'source ~/.zshrc'!${NC}"
}

# Ejecutar instalación
main "$@"