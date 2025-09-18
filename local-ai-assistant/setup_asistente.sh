#!/bin/bash
# ==============================================================================
# 🤖 SETUP ASISTENTE IA LOCAL
# ==============================================================================
# Autor: Eto Demerzel ~ Gustavo Silva
# Descripción: Script de instalación automatizada para Asistente IA Local
#              que utiliza modelos de llama.cpp. Configura estructura completa
#              del proyecto, validaciones y archivos de configuración.
# ==============================================================================
set -euo pipefail

# Variables configurables
PROJECT_DIR=""
MODEL_PATH=""
LLAMA_CPP_PATH=""
PYTHON_VERSION="3.11"

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

# Función para solicitar entrada con valor por defecto
ask() {
    local prompt default answer
    prompt=$1
    default=$2
    
    read -p "$prompt [$default]: " answer
    echo "${answer:-$default}"
}

# Solicitar configuración al usuario
get_configuration() {
    log "Configuración inicial del asistente IA"
    echo "Por favor, proporciona las siguientes rutas:"
    
    PROJECT_DIR=$(ask "Directorio del proyecto" "$(pwd)/asistente-ia")
    MODEL_PATH=$(ask "Ruta del modelo GGUF" "$HOME/modelo/modelo.gguf")
    LLAMA_CPP_PATH=$(ask "Ruta de llama.cpp" "$HOME/llama.cpp/build/bin/llama-cli")
    
    # Mostrar configuración
    echo -e "\n${GREEN}Configuración seleccionada:${NC}"
    echo "Directorio del proyecto: $PROJECT_DIR"
    echo "Modelo: $MODEL_PATH"
    echo "Llama.cpp: $LLAMA_CPP_PATH"
    echo ""
    
    read -p "¿Continuar con esta configuración? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
}

# Validaciones
validar() {
    log "Validando prerrequisitos..."
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python3 no está instalado"
        exit 1
    fi
    
    # Verificar pip
    if ! command -v pip3 &> /dev/null; then
        echo "Error: pip3 no está instalado"
        exit 1
    fi
    
    # Verificar llama.cpp
    if [[ ! -f "$LLAMA_CPP_PATH" ]]; then
        warn "ADVERTENCIA: llama-cli no encontrado en la ruta especificada: $LLAMA_CPP_PATH"
        warn "El asistente necesitará llama.cpp para funcionar correctamente"
    fi
    
    # Verificar modelo
    if [[ ! -f "$MODEL_PATH" ]]; then
        warn "ADVERTENCIA: Modelo no encontrado en la ruta especificada: $MODEL_PATH"
        warn "Necesitarás descargar un modelo GGUF para usar el asistente"
    fi
    
    info "Validaciones completadas ✓"
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
    
    info "Estructura creada en: $PROJECT_DIR"
}

# Crear archivos principales (el contenido se mantiene igual pero con las variables)
crear_archivos() {
    log "Creando archivos principales..."
    
    # main.py (modificado para usar config por defecto)
    cat > src/main.py << EOF
#!/usr/bin/env python3
"""
Asistente IA Local - Punto de entrada principal
Inspirado en Claude Code pero usando modelos locales
"""

import sys
import os
import argparse
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent))

from core.assistant import LocalAssistant
from core.config import Config

def main():
    parser = argparse.ArgumentParser(description='Asistente IA Local')
    parser.add_argument('--config', '-c', default='config/settings.json', help='Archivo de configuración')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo verbose')
    parser.add_argument('command', nargs='*', help='Comando a ejecutar')
    
    args = parser.parse_args()
    
    # Inicializar configuración
    config = Config(args.config)
    
    # Crear asistente
    assistant = LocalAssistant(config, verbose=args.verbose)
    
    if args.command:
        # Modo comando único
        result = assistant.execute(' '.join(args.command))
        print(result)
    else:
        # Modo interactivo
        assistant.interactive_mode()

if __name__ == "__main__":
    main()
EOF

    # config.py (modificado para usar rutas relativas)
    cat > src/core/config.py << EOF
"""
Configuración del asistente
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.settings = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Cargar configuración desde archivo o usar defaults"""
        
        default_config = {
            "llm": {
                "model_path": "$MODEL_PATH",
                "llama_bin": "$LLAMA_CPP_PATH",
                "max_tokens": 1024,
                "temperature": 0.7
            },
            "assistant": {
                "safe_mode": True,
                "backup_files": True,
                "max_file_size": 1048576,  # 1MB
                "supported_extensions": [".py", ".js", ".ts", ".json", ".md", ".txt", ".sh"]
            },
            "logging": {
                "level": "INFO",
                "file": "logs/assistant.log"
            }
        }
        
        config_path = Path(self.config_file) if self.config_file else Path("config/settings.json")
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    # Merge con default
                    return {**default_config, **user_config}
            except Exception as e:
                print(f"Error cargando config: {e}, usando defaults")
        
        return default_config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtener valor de configuración usando dot notation"""
        keys = key.split('.')
        value = self.settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def save(self, filepath: Optional[str] = None):
        """Guardar configuración actual"""
        target = filepath or self.config_file or "config/settings.json"
        
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        
        with open(target, 'w') as f:
            json.dump(self.settings, f, indent=2)
EOF

    # Archivo de configuración con las rutas proporcionadas
    cat > config/settings.json << EOF
{
  "llm": {
    "model_path": "$MODEL_PATH",
    "llama_bin": "$LLAMA_CPP_PATH",
    "max_tokens": 1024,
    "temperature": 0.7
  },
  "assistant": {
    "safe_mode": true,
    "backup_files": true,
    "max_file_size": 1048576,
    "supported_extensions": [".py", ".js", ".ts", ".json", ".md", ".txt", ".sh"]
  },
  "logging": {
    "level": "INFO",
    "file": "logs/assistant.log"
  }
}
EOF

    # ... (el resto de archivos se mantienen igual)
    # [Aquí irían los demás archivos sin cambios]
    
    info "Archivos principales creados ✓"
}

# ... (las demás funciones se mantienen igual)

# Función principal
main() {
    trap cleanup EXIT
    
    # Obtener configuración primero
    get_configuration
    
    log "Iniciando setup del Asistente IA Local..."
    
    validar
    crear_estructura
    crear_archivos
    crear_init_files
    
    log "¡Setup completado exitosamente! 🎉"
    info "Próximo paso: cd $PROJECT_DIR && python3 src/main.py"
}

# Ejecutar
main "$@"
