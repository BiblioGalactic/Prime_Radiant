#!/bin/bash 🤖 === SETUP ASISTENTE IA MEJORADO ===
set -euo pipefail

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Variables configurables
PROJECT_DIR=""
MODEL_PATH=""
LLAMA_CPP_PATH=""

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

# Función de limpieza
cleanup() {
    log "Setup completado"
}

# Configuración interactiva
configurar_rutas() {
    echo
    echo -e "${GREEN}🤖 CONFIGURACIÓN DEL ASISTENTE IA LOCAL MEJORADO${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo
    
    # Directorio del proyecto
    default_project_dir="${HOME}/asistente-ia"
    PROJECT_DIR=$(ask "Directorio de instalación del proyecto:" "[${default_project_dir}]")
    PROJECT_DIR="${PROJECT_DIR:-$default_project_dir}"
    
    # Ruta del modelo GGUF
    default_model_path="${HOME}/modelo/modelos_grandes/M6/mistral-7b-instruct-v0.1.Q6_K.gguf"
    MODEL_PATH=$(ask "Ruta de tu modelo GGUF:" "[${default_model_path}]")
    MODEL_PATH="${MODEL_PATH:-$default_model_path}"
    
    # Ruta de llama-cli
    default_llama_path="${HOME}/modelo/llama.cpp/build/bin/llama-cli"
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
    
    if ! command -v python3 &> /dev/null; then
        error "Python3 no está instalado"
        exit 1
    fi
    
    if ! command -v pip3 &> /dev/null; then
        error "pip3 no está instalado"
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
    
    info "Estructura creada en: $PROJECT_DIR ✓"
}

# Crear archivos principales
crear_archivos_principales() {
    log "Creando archivos principales..."
    
    # main.py
    cat > src/main.py << 'EOF'
#!/usr/bin/env python3
"""
Asistente IA Local - Punto de entrada principal CON MODO AGÉNTICO
"""

import sys
import os
import argparse
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent))

from core.assistant import LocalAssistant
from core.config import Config
from core.agentic_extension import extend_assistant_with_agentic

def main():
    parser = argparse.ArgumentParser(description='Asistente IA Local con Capacidades Agénticas')
    parser.add_argument('--config', '-c', default='config/settings.json', help='Archivo de configuración')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo verbose')
    parser.add_argument('--agentic', '-a', action='store_true', help='Activar modo agéntico por defecto')
    parser.add_argument('command', nargs='*', help='Comando a ejecutar')
    
    args = parser.parse_args()
    
    # Inicializar configuración
    config = Config(args.config)
    
    # Extender asistente con capacidades agénticas
    AgenticAssistant = extend_assistant_with_agentic(LocalAssistant)
    
    # Crear asistente agéntico
    assistant = AgenticAssistant(config, verbose=args.verbose)
    
    # Activar modo agéntico si se especifica
    if args.agentic:
        assistant.toggle_agentic_mode(True)
    
    if args.command:
        # Modo comando único
        command_text = ' '.join(args.command)
        
        # Auto-detectar si necesita modo agéntico
        agentic_triggers = [
            'analiza completamente', 'investigación profunda', 'análisis exhaustivo',
            'modo agéntico', 'revisa todo', 'examina detalladamente'
        ]
        
        if any(trigger in command_text.lower() for trigger in agentic_triggers):
            assistant.toggle_agentic_mode(True)
            if args.verbose:
                print("🎯 Modo agéntico activado automáticamente")
        
        result = assistant.execute(command_text)
        print(result)
    else:
        # Modo interactivo
        assistant.interactive_mode()

if __name__ == "__main__":
    main()
EOF

    # config.py
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
        \"\"\"Cargar configuración desde archivo o usar defaults\"\"\"
        
        default_config = {
            "llm": {
                "model_path": "${MODEL_PATH}",
                "llama_bin": "${LLAMA_CPP_PATH}",
                "max_tokens": 1024,
                "temperature": 0.7
            },
            "assistant": {
                "safe_mode": False,
                "backup_files": True,
                "max_file_size": 1048576,
                "supported_extensions": [".py", ".js", ".ts", ".json", ".md", ".txt", ".sh", ".html", ".css"]
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
                    return {**default_config, **user_config}
            except Exception as e:
                print(f"Error cargando config: {e}, usando defaults")
        
        return default_config
    
    def get(self, key: str, default: Any = None) -> Any:
        \"\"\"Obtener valor de configuración usando dot notation\"\"\"
        keys = key.split('.')
        value = self.settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def save(self, filepath: Optional[str] = None):
        \"\"\"Guardar configuración actual\"\"\"
        target = filepath or self.config_file or "config/settings.json"
        
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        
        with open(target, 'w') as f:
            json.dump(self.settings, f, indent=2)
EOF

    # llm/client.py
    cat > src/llm/client.py << 'EOF'
"""
Cliente para comunicación con llama.cpp via API
"""

import subprocess
import json
import tempfile
from typing import Dict, List, Optional
from pathlib import Path

class LlamaClient:
    def __init__(self, model_path: str, llama_bin: str):
        self.model_path = Path(model_path)
        self.llama_bin = Path(llama_bin)
        self.validate_setup()
    
    def validate_setup(self):
        """Validar que llama.cpp y modelo existen"""
        if not self.llama_bin.exists():
            raise FileNotFoundError(f"llama-cli no encontrado: {self.llama_bin}")
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Modelo no encontrado: {self.model_path}")
    
    def generate(self, prompt: str, max_tokens: int = 1024, 
                temperature: float = 0.7) -> str:
        """Generar respuesta usando llama.cpp"""
        
        cmd = [
            str(self.llama_bin),
            "-m", str(self.model_path),
            "-p", prompt,
            "-n", str(max_tokens),
            "--temp", str(temperature),
            "--no-display-prompt"
        ]
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=120
            )
            
            if result.returncode != 0:
                raise Exception(f"LLM error: {result.stderr}")
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise Exception("LLM timeout - respuesta muy lenta")
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Simular chat format usando prompt simple"""
        
        # Convertir mensajes a formato de prompt
        prompt_parts = []
        for msg in messages:
            role = msg['role']
            content = msg['content']
            
            if role == 'system':
                prompt_parts.append(f"Sistema: {content}")
            elif role == 'user':
                prompt_parts.append(f"Usuario: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Asistente: {content}")
        
        prompt_parts.append("Asistente:")
        prompt = "\n\n".join(prompt_parts)
        
        return self.generate(prompt, **kwargs)
EOF

    info "Archivos principales creados ✓"
}

# Crear file manager
crear_file_manager() {
    log "Creando file manager..."
    
    cat > src/file_ops/manager.py << 'EOF'
"""
Gestor de operaciones de archivos para el asistente
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import fnmatch

class FileManager:
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or os.getcwd())
        self.ignored_patterns = {
            '.git/*', '*.pyc', '__pycache__/*', 
            'node_modules/*', '.DS_Store', '*.log'
        }
    
    def read_file(self, filepath: str) -> str:
        """Leer contenido de archivo"""
        full_path = self.project_root / filepath
        
        if not full_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {filepath}")
        
        if not self._is_safe_path(full_path):
            raise PermissionError(f"Acceso denegado: {filepath}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def write_file(self, filepath: str, content: str, backup: bool = True) -> bool:
        """Escribir contenido a archivo"""
        full_path = self.project_root / filepath
        
        # Crear backup si existe
        if backup and full_path.exists():
            backup_path = full_path.with_suffix(f'{full_path.suffix}.backup')
            shutil.copy2(full_path, backup_path)
        
        # Crear directorios padre si no existen
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    
    def list_files(self, pattern: str = "*", recursive: bool = True) -> List[str]:
        """Listar archivos en el proyecto"""
        files = []
        
        if recursive:
            for path in self.project_root.rglob(pattern):
                if path.is_file() and not self._is_ignored(path):
                    rel_path = path.relative_to(self.project_root)
                    files.append(str(rel_path))
        else:
            for path in self.project_root.glob(pattern):
                if path.is_file() and not self._is_ignored(path):
                    rel_path = path.relative_to(self.project_root)
                    files.append(str(rel_path))
        
        return sorted(files)
    
    def get_project_structure(self) -> Dict:
        """Obtener estructura del proyecto"""
        structure = {}
        
        for root, dirs, files in os.walk(self.project_root):
            # Filtrar directorios ignorados
            dirs[:] = [d for d in dirs if not self._is_ignored(Path(root) / d)]
            
            rel_root = Path(root).relative_to(self.project_root)
            if str(rel_root) == '.':
                rel_root = Path()
            
            structure[str(rel_root)] = {
                'dirs': dirs,
                'files': [f for f in files if not self._is_ignored(Path(root) / f)]
            }
        
        return structure
    
    def _is_safe_path(self, path: Path) -> bool:
        """Verificar que el path está dentro del proyecto"""
        try:
            path.resolve().relative_to(self.project_root.resolve())
            return True
        except ValueError:
            return False
    
    def _is_ignored(self, path: Path) -> bool:
        """Verificar si un archivo debe ser ignorado"""
        rel_path = str(path.relative_to(self.project_root))
        
        for pattern in self.ignored_patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
        
        return False
EOF

    info "File manager creado ✓"
}

# Crear command runner extendido
crear_command_runner() {
    log "Creando command runner extendido..."
    
    cat > src/commands/runner.py << 'EOF'
"""
Ejecutor de comandos del sistema - VERSIÓN EXTENDIDA
"""

import subprocess
import os
import shlex
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class CommandRunner:
    def __init__(self, project_root: Optional[str] = None, safe_mode: bool = False):
        self.project_root = Path(project_root or os.getcwd())
        self.safe_mode = safe_mode
        
        # Comandos permitidos (ENORMEMENTE EXPANDIDO)
        self.safe_commands = {
            # Básicos del sistema
            'ls', 'cat', 'head', 'tail', 'grep', 'find', 'wc', 'sort', 'uniq',
            'awk', 'sed', 'cut', 'tr', 'tee', 'xargs', 'which', 'whereis',
            'file', 'stat', 'du', 'df', 'ps', 'top', 'htop', 'whoami', 'id',
            'pwd', 'cd', 'mkdir', 'touch', 'cp', 'mv', 'ln',
            
            # Git y control de versiones
            'git', 'svn', 'hg',
            
            # Lenguajes de programación y herramientas
            'python', 'python3', 'pip', 'pip3', 'node', 'npm', 'npx', 'yarn',
            'ruby', 'gem', 'php', 'java', 'javac', 'go', 'rust', 'cargo',
            
            # Build tools
            'make', 'cmake', 'ninja', 'gradle', 'maven',
            
            # Contenedores
            'docker', 'docker-compose', 'kubectl',
            
            # Redes y web
            'curl', 'wget', 'ping', 'traceroute', 'nslookup', 'dig',
            
            # Compresión
            'tar', 'gzip', 'gunzip', 'zip', 'unzip',
            
            # Herramientas de desarrollo
            'brew', 'lsof', 'netstat', 'watch',
        }
        
        # Comandos ABSOLUTAMENTE prohibidos
        self.forbidden_commands = {
            'rm', 'rmdir', 'dd', 'shred', 'wipe',
            'mkfs', 'fdisk', 'parted', 'chmod', 'chown',
            'kill', 'killall', 'pkill', 'reboot', 'shutdown',
            'sudo', 'su', 'mount', 'umount',
        }
    
    def execute(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """Ejecutar comando y retornar (código, stdout, stderr)"""
        
        if self.safe_mode and not self._is_safe_command(command):
            return 1, "", f"Comando no permitido en modo seguro: {command.split()[0]}"
        
        if self._is_forbidden_command(command):
            return 1, "", f"Comando prohibido por seguridad: {command.split()[0]}"
        
        try:
            result = subprocess.run(
                shlex.split(command),
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return 1, "", f"Timeout: comando tardó más de {timeout}s"
        except FileNotFoundError:
            return 1, "", f"Comando no encontrado: {command.split()[0]}"
        except Exception as e:
            return 1, "", f"Error ejecutando comando: {str(e)}"
    
    def _is_safe_command(self, command: str) -> bool:
        """Verificar si un comando es seguro"""
        cmd_name = command.split()[0]
        return cmd_name in self.safe_commands
    
    def _is_forbidden_command(self, command: str) -> bool:
        """Verificar si un comando está prohibido"""
        cmd_name = command.split()[0]
        
        if cmd_name in self.forbidden_commands:
            return True
        
        # Patrones peligrosos
        dangerous_patterns = ['rm -rf', '> /dev/', 'sudo ', '| sh']
        for pattern in dangerous_patterns:
            if pattern in command:
                return True
        
        return False
EOF

    info "Command runner extendido creado ✓"
}

# Crear asistente base
crear_asistente_base() {
    log "Creando asistente base..."
    
    cat > src/core/assistant.py << 'EOF'
"""
Asistente IA Local - Clase principal
"""

import sys
from typing import Optional, Dict, Any
from pathlib import Path

from llm.client import LlamaClient
from file_ops.manager import FileManager
from commands.runner import CommandRunner
from core.config import Config

class LocalAssistant:
    def __init__(self, config: Config, verbose: bool = False):
        self.config = config
        self.verbose = verbose
        
        # Inicializar componentes
        self.llm = LlamaClient(
            model_path=config.get('llm.model_path'),
            llama_bin=config.get('llm.llama_bin')
        )
        
        self.file_manager = FileManager()
        self.command_runner = CommandRunner(safe_mode=config.get('assistant.safe_mode', False))
        
        if verbose:
            print(f"✓ Asistente inicializado con modelo: {config.get('llm.model_path')}")
    
    def execute(self, user_input: str) -> str:
        """Ejecutar una instrucción del usuario"""
        
        # Obtener contexto del proyecto
        context = self._build_context()
        
        # Crear prompt con contexto + instrucción
        prompt = self._build_prompt(context, user_input)
        
        if self.verbose:
            print(f"Enviando prompt al LLM...")
        
        # Generar respuesta
        response = self.llm.generate(
            prompt, 
            max_tokens=self.config.get('llm.max_tokens', 1024),
            temperature=self.config.get('llm.temperature', 0.7)
        )
        
        return self._process_response(response, user_input)
    
    def interactive_mode(self):
        """Modo interactivo de conversación"""
        print("🤖 Asistente IA Local - Modo interactivo")
        print("Escribe 'exit' para salir, 'help' para ayuda")
        print()
        
        while True:
            try:
                user_input = input("💬 > ").strip()
                
                if user_input.lower() == 'exit':
                    print("¡Hasta luego! 👋")
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                elif user_input:
                    response = self.execute(user_input)
                    print(f"🤖 {response}")
                    print()
                    
            except KeyboardInterrupt:
                print("\n¡Hasta luego! 👋")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _build_context(self) -> Dict[str, Any]:
        """Construir contexto del proyecto actual"""
        return {
            'project_structure': self.file_manager.get_project_structure(),
            'current_directory': str(self.file_manager.project_root),
            'supported_files': self.file_manager.list_files()[:20]
        }
    
    def _build_prompt(self, context: Dict, user_input: str) -> str:
        """Construir prompt con contexto"""
        
        prompt = f"""Eres un asistente de programación que ayuda con tareas de código.

CONTEXTO DEL PROYECTO:
Directorio: {context['current_directory']}

ARCHIVOS DISPONIBLES:
{chr(10).join(context['supported_files'][:10])}

INSTRUCCIÓN DEL USUARIO:
{user_input}

Responde con una explicación clara de qué harías y qué archivos modificarías.
Si necesitas ver el contenido de algún archivo, dímelo específicamente.

Respuesta:"""
        
        return prompt
    
    def _process_response(self, llm_response: str, original_input: str) -> str:
        """Procesar respuesta del LLM"""
        return llm_response.strip()
    
    def _show_help(self):
        """Mostrar ayuda"""
        help_text = """
🤖 COMANDOS DISPONIBLES:

• Análisis de código:
  "explica el archivo main.py"
  "qué hace esta función?"

• Modificaciones:
  "refactoriza la clase User"
  "añade comentarios a este código"

• Comandos del sistema:
  "lista los archivos Python"
  "ejecuta los tests"

• Utilidades:
  "exit" - Salir
  "help" - Esta ayuda
        """
        print(help_text)
EOF

    info "Asistente base creado ✓"
}

# Crear extensión agéntica MEJORADA
crear_extension_agentica() {
    log "Creando extensión agéntica mejorada..."
    
    cat > src/core/agentic_extension.py << 'EOF'
"""
Extensión Agéntica para el Asistente IA Local - VERSIÓN MEJORADA
Basado en el patrón de agentic3 - multiples consultas, planificación y síntesis
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

class AgenticAssistant:
    """
    Extensión agéntica que permite al asistente hacer múltiples consultas,
    planificar subtareas y sintetizar respuestas como en agentic3
    """
    
    def __init__(self, base_assistant, max_iterations: int = 3, verbose: bool = False):
        self.assistant = base_assistant
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.interaction_logs = []
        self.learning_rate = 0.05
        
        # Parámetros adaptativos (como en agentic3)
        self.context_threshold = 3  # Mínimo contexto requerido
        self.quality_threshold = 0.7  # Umbral de calidad
        
    def plan_subtasks(self, user_input: str) -> List[str]:
        """
        Planifica subtareas basándose en la entrada del usuario - VERSIÓN MEJORADA
        """
        
        # Prompt mejorado con ejemplos específicos
        planning_prompt = f"""Eres un planificador experto. Descompón el request en subtareas específicas y únicas.

REQUEST: {user_input}

EJEMPLOS DE BUENA PLANIFICACIÓN:

Request: "analiza completamente la estructura del proyecto"
Subtareas: ["listar archivos y directorios", "examinar archivos de configuración", "identificar patrones y arquitectura"]

Request: "investigación profunda sobre errores"
Subtareas: ["revisar logs y archivos de error", "analizar código problemático", "identificar causas raíz"]

Request: "optimiza el rendimiento del código"
Subtareas: ["identificar cuellos de botella", "analizar algoritmos ineficientes", "sugerir optimizaciones específicas"]

INSTRUCCIONES:
- Máximo 3 subtareas específicas y diferentes
- Cada subtarea debe ser única y no repetir conceptos
- Enfócate en acciones concretas, no generalidades
- NO uses frases como "analizar contexto" o "verificar implementación"

Responde ÚNICAMENTE con el array JSON:
["subtarea_específica_1", "subtarea_específica_2", "subtarea_específica_3"]

JSON:"""

        response = self.assistant.llm.generate(planning_prompt, max_tokens=256, temperature=0.2)
        
        if self.verbose:
            print(f"🧠 Respuesta de planificación: {response[:200]}...")
        
        try:
            # Extraer lista JSON más robusta
            import re
            # Buscar array JSON más específicamente
            json_match = re.search(r'\[\s*"[^"]+"\s*(?:,\s*"[^"]+"\s*)*\]', response, re.DOTALL)
            if json_match:
                subtasks = json.loads(json_match.group())
                if isinstance(subtasks, list) and all(isinstance(s, str) for s in subtasks):
                    return subtasks[:3]  # Máximo 3 subtareas
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Error parseando JSON: {e}")
        
        # Fallback inteligente basado en palabras clave
        return self._intelligent_fallback(user_input)
    
    def _intelligent_fallback(self, user_input: str) -> List[str]:
        """Fallback inteligente basado en palabras clave del request"""
        user_lower = user_input.lower()
        
        if "estructura" in user_lower:
            return ["listar archivos y directorios", "examinar archivos principales", "evaluar organización del proyecto"]
        elif "error" in user_lower or "problema" in user_lower:
            return ["revisar archivos de log", "analizar código problemático", "identificar posibles soluciones"]
        elif "optimiz" in user_lower or "rendimiento" in user_lower:
            return ["identificar cuellos de botella", "analizar eficiencia del código", "proponer mejoras específicas"]
        elif "código" in user_lower:
            return ["examinar archivos de código principales", "analizar funciones críticas", "evaluar calidad y estilo"]
        else:
            # Fallback genérico pero mejor
            return ["examinar componentes principales", "analizar configuración y dependencias", "evaluar estado actual del proyecto"]
    
    def execute_subtask(self, subtask: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una subtarea específica - CON LECTURA AUTOMÁTICA DE ARCHIVOS
        """
        if self.verbose:
            print(f"🔍 Ejecutando subtarea: {subtask}")
        
        # Construir contexto enriquecido para la subtarea
        enriched_context = {**context}
        
        # MEJORA: Lectura automática más inteligente
        project_files = enriched_context.get('supported_files', [])
        
        # Si hay pocos archivos (menos de 10), leer algunos automáticamente
        if len(project_files) <= 10:
            for file_path in project_files[:5]:  # Máximo 5 archivos
                try:
                    if any(file_path.endswith(ext) for ext in ['.txt', '.md', '.json', '.py', '.js']):
                        content = self.assistant.file_manager.read_file(file_path)
                        enriched_context[f'file_{file_path}'] = content[:1500]
                        if self.verbose:
                            print(f"📄 Auto-leído: {file_path}")
                except:
                    pass
        
        # Si la subtarea menciona archivos específicos, leerlos también
        file_mentions = self._extract_file_mentions(subtask)
        for file_path in file_mentions:
            if f'file_{file_path}' not in enriched_context:
                try:
                    content = self.assistant.file_manager.read_file(file_path)
                    enriched_context[f'file_{file_path}'] = content[:2000]
                    if self.verbose:
                        print(f"📄 Leído por mención: {file_path}")
                except:
                    enriched_context[f'file_{file_path}'] = "ARCHIVO NO ENCONTRADO"
        
        # Ejecutar subtarea
        prompt = self._build_subtask_prompt(subtask, enriched_context)
        response = self.assistant.llm.generate(prompt, max_tokens=1024, temperature=0.5)
        
        # Evaluar calidad de la respuesta
        quality_score = self._evaluate_response_quality(subtask, response)
        
        result = {
            'subtask': subtask,
            'response': response,
            'quality_score': quality_score,
            'context_used': list(enriched_context.keys()),
            'timestamp': time.time()
        }
        
        if self.verbose:
            print(f"✅ Subtarea completada con calidad: {quality_score:.2f}")
        
        return result
    
    def synthesize_responses(self, original_request: str, subtask_results: List[Dict]) -> str:
        """
        Sintetiza múltiples respuestas de subtareas - MEJORADO SIN REDUNDANCIAS
        """
        
        if not subtask_results:
            return "No se pudieron ejecutar las subtareas solicitadas."
        
        # Filtrar respuestas por calidad
        high_quality_results = [r for r in subtask_results if r['quality_score'] >= 0.6]
        if not high_quality_results:
            high_quality_results = subtask_results  # Usar todas si ninguna es de alta calidad
        
        # Construir contexto de síntesis más inteligente
        synthesis_context = []
        seen_concepts = set()
        
        for i, result in enumerate(high_quality_results):
            # Evitar conceptos repetidos
            response_lower = result['response'].lower()
            response_words = set(response_lower.split())
            
            # Solo incluir si no hay mucha superposición conceptual
            overlap = len(seen_concepts.intersection(response_words))
            if overlap < len(response_words) * 0.7:  # Menos del 70% de superposición
                synthesis_context.append(f"""
ANÁLISIS {i+1}: {result['response']}
---""")
                seen_concepts.update(response_words)
        
        synthesis_prompt = f"""Eres un sintetizador experto. Crea una respuesta final coherente y sin redundancias.

REQUEST ORIGINAL: {original_request}

ANÁLISIS REALIZADOS:
{chr(10).join(synthesis_context)}

INSTRUCCIONES CRÍTICAS:
1. NO repitas información - cada dato debe aparecer solo UNA vez
2. Elimina contradicciones - usa la información más específica
3. Organiza la información de forma lógica y fluida
4. Si hay números/cantidades diferentes, usa el más preciso
5. Enfócate en dar valor práctico al usuario
6. Máximo 300 palabras, sé conciso pero completo

RESPUESTA FINAL SINTETIZADA:"""

        final_response = self.assistant.llm.generate(synthesis_prompt, max_tokens=800, temperature=0.3)
        
        # Log de la interacción para aprendizaje
        self._log_interaction(original_request, subtask_results, final_response)
        
        return final_response.strip()
    
    def execute_agentic(self, user_input: str) -> str:
        """
        Método principal: ejecuta el flujo agéntico completo
        """
        if self.verbose:
            print("🤖 Iniciando modo agéntico...")
            print(f"📋 Request original: {user_input}")
        
        # 1. Planificación
        subtasks = self.plan_subtasks(user_input)
        if self.verbose:
            print(f"🎯 Subtareas planificadas: {subtasks}")
        
        # 2. Obtener contexto base
        base_context = self.assistant._build_context()
        
        # 3. Ejecutar subtareas
        subtask_results = []
        for i, subtask in enumerate(subtasks):
            if self.verbose:
                print(f"🔄 Ejecutando subtarea {i+1}/{len(subtasks)}")
            
            result = self.execute_subtask(subtask, base_context)
            subtask_results.append(result)
            
            # Early stopping si la calidad es muy baja
            if result['quality_score'] < 0.3 and i == 0:
                if self.verbose:
                    print("⚠️  Calidad muy baja, usando modo normal")
                return self.assistant.execute(user_input)
        
        # 4. Síntesis final
        if self.verbose:
            print("🔄 Sintetizando respuestas...")
        
        final_response = self.synthesize_responses(user_input, subtask_results)
        
        # 5. Verificación final
        verification = self._verify_final_response(user_input, final_response)
        if verification['needs_fallback']:
            if self.verbose:
                print("⚠️  Verificación falló, usando respuesta de fallback")
            return self.assistant.execute(user_input)
        
        if self.verbose:
            print("✅ Modo agéntico completado")
        
        return final_response
    
    def _extract_file_mentions(self, text: str) -> List[str]:
        """Extrae menciones de archivos del texto"""
        import re
        
        # Patrones comunes para archivos
        patterns = [
            r'(\w+\.\w+)',  # archivo.ext
            r'src/(\w+/)*\w+\.\w+',  # src/path/file.ext
            r'(\w+/)*\w+\.\w+',  # path/file.ext
        ]
        
        files = set()
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                if isinstance(match, tuple):
                    file_path = ''.join(match)
                else:
                    file_path = match
                
                # Filtrar extensiones válidas
                valid_extensions = ['.py', '.js', '.ts', '.json', '.md', '.txt', '.sh', '.html', '.css']
                if any(file_path.endswith(ext) for ext in valid_extensions):
                    files.add(file_path)
        
        return list(files)[:3]  # Máximo 3 archivos
    
    def _build_subtask_prompt(self, subtask: str, context: Dict[str, Any]) -> str:
        """Construye el prompt para una subtarea específica"""
        
        context_str = ""
        file_count = 0
        for key, value in context.items():
            if key.startswith('file_'):
                filename = key.replace('file_', '')
                context_str += f"\nARCHIVO {filename}:\n{value}\n"
                file_count += 1
            elif key == 'project_structure':
                context_str += f"\nESTRUCTURA DEL PROYECTO:\n{json.dumps(value, indent=2)}\n"
        
        return f"""Eres un asistente especializado. Ejecuta esta subtarea específica con precisión.

SUBTAREA: {subtask}

CONTEXTO DISPONIBLE ({file_count} archivos leídos):
{context_str}

INSTRUCCIONES:
- Enfócate SOLO en esta subtarea específica
- Usa toda la información del contexto proporcionado
- Sé preciso, específico y detallado
- Si encuentras datos numéricos, repórtalos exactamente
- Si hay archivos, menciona sus nombres específicos

RESPUESTA:"""
    
    def _evaluate_response_quality(self, subtask: str, response: str) -> float:
        """Evalúa la calidad de una respuesta (0.0 - 1.0)"""
        
        # Criterios básicos de calidad
        score = 0.4  # Base reducido
        
        # Longitud apropiada
        words = len(response.split())
        if 30 < words < 400:
            score += 0.3
        elif 10 < words <= 30:
            score += 0.1
        
        # Contiene información específica
        specific_keywords = ['archivo', 'función', 'línea', 'directorio', 'configuración', 'estructura']
        if any(keyword in response.lower() for keyword in specific_keywords):
            score += 0.2
        
        # Contiene datos concretos (números, nombres de archivos)
        import re
        if re.search(r'\d+|\.py|\.js|\.json|\.txt|\.md', response):
            score += 0.1
        
        return min(score, 1.0)
    
    def _verify_final_response(self, original_request: str, final_response: str) -> Dict[str, Any]:
        """Verifica si la respuesta final es adecuada"""
        
        # Verificación simple sin LLM adicional para evitar recursión
        word_count = len(final_response.split())
        
        result = {
            'needs_fallback': False,
            'quality': 'OK',
            'verification_response': 'verificación automática'
        }
        
        # Criterios automáticos
        if word_count < 10:
            result['needs_fallback'] = True
            result['quality'] = 'FALLA'
        elif 'error' in final_response.lower() and 'no puedo' in final_response.lower():
            result['needs_fallback'] = True
            result['quality'] = 'FALLA'
        elif word_count < 30:
            result['quality'] = 'PARCIAL'
        
        return result
    
    def _log_interaction(self, request: str, subtask_results: List[Dict], final_response: str):
        """Log para aprendizaje futuro"""
        log_entry = {
            'timestamp': time.time(),
            'request': request,
            'subtasks_count': len(subtask_results),
            'avg_quality': sum(r['quality_score'] for r in subtask_results) / len(subtask_results) if subtask_results else 0,
            'final_response_length': len(final_response.split()),
            'success': True
        }
        
        self.interaction_logs.append(log_entry)
        
        # Mantener solo los últimos 50 logs
        if len(self.interaction_logs) > 50:
            self.interaction_logs = self.interaction_logs[-50:]


def extend_assistant_with_agentic(assistant_class):
    """
    Decorator para extender el asistente base con capacidades agénticas
    """
    
    class AgenticExtendedAssistant(assistant_class):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.agentic = AgenticAssistant(self, verbose=self.verbose)
            self._agentic_mode = False
        
        def toggle_agentic_mode(self, enabled: bool = True):
            """Activar/desactivar modo agéntico"""
            self._agentic_mode = enabled
            if self.verbose:
                mode = "ACTIVADO" if enabled else "DESACTIVADO"
                print(f"🤖 Modo agéntico {mode}")
        
        def execute(self, user_input: str) -> str:
            """Override del execute original para soportar modo agéntico"""
            
            # Detectar si el usuario quiere modo agéntico
            if any(keyword in user_input.lower() for keyword in ['analiza completamente', 'investigación profunda', 'modo agéntico', 'análisis exhaustivo']):
                self._agentic_mode = True
            
            if self._agentic_mode:
                try:
                    return self.agentic.execute_agentic(user_input)
                except Exception as e:
                    if self.verbose:
                        print(f"⚠️  Error en modo agéntico: {e}, usando modo normal")
                    return super().execute(user_input)
            else:
                return super().execute(user_input)
        
        def interactive_mode(self):
            """Override del modo interactivo con comandos agénticos"""
            print("🤖 Asistente IA Local - Modo interactivo CON CAPACIDADES AGÉNTICAS")
            print("Comandos especiales:")
            print("  'agentic on/off' - Activar/desactivar modo agéntico")
            print("  'analiza completamente X' - Fuerza modo agéntico para X")
            print("  'exit' para salir, 'help' para ayuda")
            print()
            
            while True:
                try:
                    user_input = input("💬 > ").strip()
                    
                    if user_input.lower() == 'exit':
                        print("¡Hasta luego! 👋")
                        break
                    elif user_input.lower().startswith('agentic '):
                        command = user_input.lower().split()[1]
                        if command == 'on':
                            self.toggle_agentic_mode(True)
                        elif command == 'off':
                            self.toggle_agentic_mode(False)
                        else:
                            print("Uso: 'agentic on' o 'agentic off'")
                        continue
                    elif user_input.lower() == 'help':
                        self._show_help()
                    elif user_input:
                        response = self.execute(user_input)
                        print(f"🤖 {response}")
                        print()
                        
                except KeyboardInterrupt:
                    print("\n¡Hasta luego! 👋")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        def _show_help(self):
            """Override help con comandos agénticos"""
            super()._show_help()
            print("""
🚀 COMANDOS AGÉNTICOS ADICIONALES:

• Activación:
  "agentic on/off" - Activar/desactivar modo agéntico
  "analiza completamente X" - Forzar análisis profundo de X

• Ejemplos agénticos:
  "analiza completamente la arquitectura del proyecto"
  "investigación profunda sobre el rendimiento"
  "modo agéntico: optimiza todo el código"

El modo agéntico hace múltiples consultas internas y sintetiza
una respuesta más completa y detallada.
            """)
    
    return AgenticExtendedAssistant
EOF

    info "Extensión agéntica mejorada creada ✓"
}

# Crear archivos __init__.py
crear_init_files() {
    log "Creando archivos __init__.py..."
    
    touch src/__init__.py
    touch src/core/__init__.py
    touch src/llm/__init__.py
    touch src/file_ops/__init__.py
    touch src/commands/__init__.py
    
    info "Archivos __init__.py creados ✓"
}

# Crear archivo de configuración
crear_configuracion() {
    log "Creando archivos de configuración..."
    
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

# Configurar aliases
configurar_aliases() {
    log "Configurando aliases..."
    
    # Detectar shell config
    shell_config="${HOME}/.zshrc"
    if [[ ! -f "$shell_config" ]]; then
        shell_config="${HOME}/.bashrc"
        touch "$shell_config"
    fi
    
    cat >> "$shell_config" << EOF

# === ASISTENTE IA LOCAL MEJORADO - ALIAS ===
alias claudia="python3 ${PROJECT_DIR}/src/main.py"
alias claudia-a="python3 ${PROJECT_DIR}/src/main.py --agentic"
alias claudia-deep="python3 ${PROJECT_DIR}/src/main.py --agentic --verbose"
alias claudia-help='echo "🤖 CLAUDIA - Asistente IA con modo agéntico mejorado

COMANDOS:
  claudia              → Modo normal
  claudia-a            → Modo agéntico (múltiples consultas inteligentes)
  claudia-deep         → Agéntico + verbose detallado
  
ACTIVACIÓN AUTOMÁTICA:
  \"analiza completamente X\"
  \"investigación profunda sobre Y\"
  \"modo agéntico: revisa Z\"
  
MEJORAS EN ESTA VERSIÓN:
  ✅ Planificación inteligente de subtareas
  ✅ Lectura automática de archivos
  ✅ Síntesis sin redundancias
  ✅ 50+ comandos del sistema habilitados
"'
EOF

    info "Aliases configurados ✓"
}

# Crear documentación y ejemplos
crear_documentacion() {
    log "Creando documentación..."
    
    cat > README.md << EOF
# 🤖 Asistente IA Local Mejorado

## Configuración
- **Directorio:** ${PROJECT_DIR}
- **Modelo:** ${MODEL_PATH}
- **Llama-cli:** ${LLAMA_CPP_PATH}

## Características Mejoradas

### 🧠 Modo Agéntico Inteligente
- Planificación automática de subtareas específicas
- Lectura automática de archivos relevantes
- Síntesis sin redundancias
- Verificación de calidad automática

### 🔧 Comandos Extendidos
- 50+ comandos habilitados (git, docker, npm, etc.)
- Protección contra comandos peligrosos
- Ejecución segura en contexto del proyecto

## Uso

### Básico
\`\`\`bash
claudia "explica este proyecto"
\`\`\`

### Agéntico
\`\`\`bash
claudia-a
💬 > analiza completamente la estructura del código

# O automático
claudia "analiza completamente el rendimiento"
\`\`\`

### Verbose (ver proceso interno)
\`\`\`bash
claudia-deep "investigación profunda sobre errores"
\`\`\`

## Ejemplos de Comandos Agénticos
- "analiza completamente la arquitectura del proyecto"
- "investigación profunda sobre el rendimiento"
- "modo agéntico: optimiza todo el código"
- "examina detalladamente los errores"

## Mejoras vs Versión Anterior
1. ✅ Subtareas más específicas (no genéricas)
2. ✅ Lectura automática de archivos pequeños
3. ✅ Síntesis inteligente sin repeticiones
4. ✅ Comandos del sistema extendidos
5. ✅ Verificación automática de calidad
EOF

    info "Documentación creada ✓"
}

# Mostrar resultado final
mostrar_resultado_final() {
    echo
    echo -e "${GREEN}🎉 ¡ASISTENTE IA LOCAL MEJORADO INSTALADO!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo
    echo -e "${CYAN}📋 CONFIGURACIÓN FINAL:${NC}"
    echo -e "Directorio: ${PROJECT_DIR}"
    echo -e "Modelo: ${MODEL_PATH}"
    echo -e "Llama-cli: ${LLAMA_CPP_PATH}"
    echo
    echo -e "${CYAN}🚀 COMANDOS DISPONIBLES:${NC}"
    echo -e "claudia      - Asistente normal"
    echo -e "claudia-a    - Modo agéntico mejorado"
    echo -e "claudia-deep - Modo agéntico + verbose"
    echo -e "claudia-help - Mostrar ayuda completa"
    echo
    echo -e "${CYAN}🎯 MEJORAS IMPLEMENTADAS:${NC}"
    echo -e "✅ Planificación inteligente de subtareas"
    echo -e "✅ Lectura automática de archivos"
    echo -e "✅ Síntesis sin redundancias"
    echo -e "✅ 50+ comandos del sistema"
    echo -e "✅ Verificación automática de calidad"
    echo
    echo -e "${YELLOW}📝 PRUEBA RÁPIDA:${NC}"
    echo -e "source ~/.zshrc"
    echo -e "cd ${PROJECT_DIR}"
    echo -e "claudia-deep \"analiza completamente este proyecto\""
    echo
    echo -e "${GREEN}¡Claudia está lista para ser tu asistente agéntico mejorado! 🤖✨${NC}"
}

# Función principal
main() {
    trap cleanup EXIT
    
    echo
    echo -e "${GREEN}🚀 INSTALADOR DEL ASISTENTE IA LOCAL MEJORADO${NC}"
    echo -e "${GREEN}===============================================${NC}"
    
    # Configuración
    configurar_rutas
    validar_prerrequisitos
    
    # Instalación
    crear_estructura
    crear_archivos_principales
    crear_file_manager
    crear_command_runner
    crear_asistente_base
    crear_extension_agentica
    crear_init_files
    crear_configuracion
    configurar_aliases
    crear_documentacion
    
    # Resultado
    mostrar_resultado_final
}

# Ejecutar instalación
main "$@"