# 🤖 Setup Asistente IA Local - Configurador Básico

## Descripción

Script de instalación automatizada para configurar un Asistente IA Local básico que utiliza modelos llama.cpp. Este instalador está diseñado para ser simple, directo y fácil de usar, proporcionando una base sólida para interactuar con modelos de lenguaje locales.

## Características Principales

### 🔧 Configuración Simple e Intuitiva
- **Instalación guiada**: Configuración paso a paso interactiva
- **Validación automática**: Verificación de prerrequisitos y rutas
- **Configuración adaptativa**: Se ajusta a diferentes entornos
- **Estructura modular**: Arquitectura organizada y extensible

### 🎯 Funcionalidades Core
- **Cliente LLM**: Comunicación directa con llama.cpp
- **Gestor de archivos**: Operaciones seguras de lectura/escritura
- **Executor de comandos**: Ejecución controlada del sistema
- **Configuración flexible**: JSON configurable

### 📁 Arquitectura Modular
```
src/
├── core/           # Motor principal del asistente
├── llm/            # Cliente para llama.cpp
├── file_ops/       # Gestión de archivos
└── commands/       # Ejecución de comandos
```

## Requisitos del Sistema

- **Python 3.11+**
- **llama.cpp** compilado
- **Modelo GGUF** compatible
- **pip3** para dependencias Python
- **Sistema operativo**: macOS, Linux

## Instalación Rápida

### 1. Descarga y Ejecución
```bash
# Descargar el script
curl -O https://raw.githubusercontent.com/tu-usuario/asistente-basico/main/setup_asistente_basico.sh

# Hacer ejecutable
chmod +x setup_asistente_basico.sh

# Ejecutar instalación
./setup_asistente_basico.sh
```

### 2. Configuración Interactiva

El script te solicitará:

**Directorio del proyecto:**
```
Directorio del proyecto [/Users/tu-usuario/asistente-ia]: 
```

**Ruta del modelo GGUF:**
```
Ruta del modelo GGUF [/Users/tu-usuario/modelo/modelo.gguf]: 
```

**Ruta de llama-cli:**
```
Ruta de llama.cpp [/Users/tu-usuario/llama.cpp/build/bin/llama-cli]: 
```

### 3. Confirmación
```
Configuración seleccionada:
Directorio del proyecto: /Users/tu-usuario/asistente-ia
Modelo: /Users/tu-usuario/modelo/modelo.gguf
Llama.cpp: /Users/tu-usuario/llama.cpp/build/bin/llama-cli

¿Continuar con esta configuración? (y/N)
```

## Estructura Generada

```
asistente-ia/
├── src/
│   ├── main.py                 # Punto de entrada principal
│   ├── core/
│   │   ├── assistant.py        # Clase principal del asistente
│   │   └── config.py          # Gestión de configuración
│   ├── llm/
│   │   └── client.py          # Cliente llama.cpp
│   ├── file_ops/
│   │   └── manager.py         # Gestión de archivos
│   └── commands/
│       └── runner.py          # Ejecución de comandos
├── config/
│   └── settings.json          # Configuración principal
├── tools/                     # Herramientas adicionales
├── tests/                     # Tests del sistema
├── logs/                      # Archivos de log
└── examples/                  # Ejemplos de uso
```

## Uso Básico

### Comando Principal
```bash
cd /ruta/a/tu/asistente-ia
python3 src/main.py "¿Qué archivos Python hay en este proyecto?"
```

### Modo Interactivo
```bash
python3 src/main.py
🤖 Asistente IA Local - Modo interactivo
Escribe 'exit' para salir, 'help' para ayuda

💬 > explica el archivo main.py
🤖 El archivo main.py es el punto de entrada...

💬 > exit
¡Hasta luego! 👋
```

### Parámetros de Línea de Comandos
```bash
# Usar configuración específica
python3 src/main.py --config config/custom.json "analiza este proyecto"

# Modo verbose
python3 src/main.py --verbose "lista archivos Python"

# Ayuda
python3 src/main.py --help
```

## Configuración

### Archivo de Configuración (config/settings.json)
```json
{
  "llm": {
    "model_path": "/ruta/a/tu/modelo.gguf",
    "llama_bin": "/ruta/a/llama-cli",
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
```

### Personalización de Parámetros LLM
- **max_tokens**: Longitud máxima de respuesta
- **temperature**: Creatividad (0.0 = determinista, 1.0 = creativo)
- **model_path**: Ruta a tu modelo GGUF
- **llama_bin**: Ruta al binario llama-cli

### Configuración de Seguridad
- **safe_mode**: Activar modo seguro para comandos
- **backup_files**: Crear copias de seguridad antes de modificar
- **max_file_size**: Tamaño máximo de archivo a procesar
- **supported_extensions**: Tipos de archivo soportados

## Funcionalidades Principales

### 1. Análisis de Archivos
```bash
python3 src/main.py "explica qué hace el archivo config.py"
```

### 2. Listado de Archivos
```bash
python3 src/main.py "muestra todos los archivos Python del proyecto"
```

### 3. Análisis de Estructura
```bash
python3 src/main.py "describe la arquitectura de este proyecto"
```

### 4. Ayuda con Código
```bash
python3 src/main.py "cómo puedo mejorar la función load_config?"
```

## Comandos Disponibles

### Comandos de Ayuda
- `help` - Mostrar ayuda completa
- `exit` - Salir del modo interactivo

### Ejemplos de Consultas
- "explica el archivo X"
- "lista archivos de tipo Y"
- "describe la estructura del proyecto"
- "cómo funciona la clase Z"
- "qué hace la función W"

## Validaciones y Seguridad

### Validaciones Automáticas
- ✅ Verificación de Python 3.11+
- ✅ Verificación de pip3
- ✅ Validación de ruta de llama-cli
- ✅ Validación de modelo GGUF
- ⚠️ Advertencias para archivos no encontrados

### Modo Seguro
```json
{
  "assistant": {
    "safe_mode": true,     // Restricciones de comandos
    "backup_files": true,  // Backups automáticos
    "max_file_size": 1048576  // Límite 1MB por archivo
  }
}
```

## Extensión y Personalización

### Añadir Nuevos Tipos de Archivo
```json
{
  "assistant": {
    "supported_extensions": [".py", ".js", ".go", ".rust", ".cpp"]
  }
}
```

### Modificar Prompts
Edita `src/core/assistant.py` en el método `_build_prompt()`:

```python
def _build_prompt(self, context: Dict, user_input: str) -> str:
    prompt = f"""Eres un asistente especializado en {tu_dominio}.
    
    CONTEXTO: {context}
    CONSULTA: {user_input}
    
    Responde de forma {tu_estilo}."""
    
    return prompt
```

### Añadir Nuevos Comandos
Modifica `src/commands/runner.py` para incluir nuevos comandos permitidos:

```python
self.safe_commands = {
    'ls', 'cat', 'grep', 'find',  # Básicos
    'git', 'npm', 'pip',          # Desarrollo
    'tu_comando_personalizado'    # Nuevo comando
}
```

## Solución de Problemas

### Error: "Python3 no está instalado"
```bash
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt update && sudo apt install python3.11
```

### Error: "llama-cli no encontrado"
```bash
# Verificar instalación de llama.cpp
ls -la /ruta/a/llama.cpp/build/bin/llama-cli

# Actualizar ruta en configuración
vim config/settings.json
```

### Error: "Modelo no encontrado"
```bash
# Verificar modelo
ls -la /ruta/a/tu/modelo.gguf

# Descargar modelo si es necesario
wget https://huggingface.co/modelo/resolve/main/modelo.gguf
```

### Problemas de Rendimiento
```json
{
  "llm": {
    "max_tokens": 512,      // Reducir para respuestas más rápidas
    "temperature": 0.3      // Menos creatividad = más rápido
  }
}
```

## Integración con Editores

### VSCode
```json
// tasks.json
{
    "label": "Consultar Asistente",
    "type": "shell",
    "command": "python3",
    "args": ["src/main.py", "${input:consulta}"],
    "group": "build"
}
```

### Vim/NeoVim
```vim
" Mapeo para consultar asistente
nnoremap <leader>ai :!python3 src/main.py "<C-R><C-W>"<CR>
```

## Contribución y Desarrollo

### Estructura para Contribuir
1. Fork del repositorio
2. Crear rama: `git checkout -b feature/nueva-funcionalidad`
3. Desarrollar en la arquitectura modular existente
4. Añadir tests en `tests/`
5. Documentar en `examples/`
6. Crear Pull Request

### Guía de Desarrollo
- Seguir la arquitectura modular existente
- Añadir validaciones para nuevas funcionalidades
- Mantener compatibilidad con la configuración JSON
- Incluir logging apropiado

## Licencia

MIT License

## Autor

**Gustavo Silva da Costa (Eto Demerzel)**

## Versión

**1.0.0** - Configurador básico con arquitectura modular sólida

---

*Un asistente IA local simple pero potente para potenciar tu flujo de trabajo de desarrollo.*
