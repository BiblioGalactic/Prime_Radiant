# 🤖 Setup Asistente IA Local Mejorado

## Descripción

Sistema de instalación automatizada para un Asistente IA Local con capacidades agénticas avanzadas. Este script configura un entorno completo de desarrollo para interactuar con modelos LLaMA locales, proporcionando funcionalidades de análisis de código, gestión de archivos y ejecución de comandos del sistema.

## Características Principales

### 🧠 Modo Agéntico Inteligente
- **Planificación automática**: Descompone tareas complejas en subtareas específicas
- **Lectura automática de archivos**: Analiza automáticamente archivos relevantes del proyecto
- **Síntesis sin redundancias**: Combina múltiples análisis eliminando información repetida
- **Verificación de calidad**: Sistema automático de control de calidad de respuestas

### 🔧 Funcionalidades Avanzadas
- **50+ comandos habilitados**: Git, Docker, NPM, Python, y más
- **Protección contra comandos peligrosos**: Sistema de seguridad integrado
- **Gestión inteligente de archivos**: Lectura, escritura y análisis de código
- **Configuración adaptativa**: Se ajusta automáticamente al entorno

### 🎯 Arquitectura Modular
- **Core**: Motor principal del asistente
- **LLM Client**: Comunicación con modelos llama.cpp
- **File Manager**: Gestión segura de archivos
- **Command Runner**: Ejecución controlada de comandos
- **Agentic Extension**: Capacidades agénticas avanzadas

## Requisitos del Sistema

- **Python 3.11+**
- **llama.cpp** compilado y funcional
- **Modelo GGUF** compatible
- **Bash 4.0+**
- **Sistema operativo**: macOS, Linux

## Instalación

### 1. Descarga e Instalación
```bash
# Descargar el script
curl -O https://raw.githubusercontent.com/tu-usuario/setup-asistente/main/setup_asistente.sh

# Hacer ejecutable
chmod +x setup_asistente.sh

# Ejecutar instalación
./setup_asistente.sh
```

### 2. Configuración Interactiva
El script te pedirá:
- **Directorio de instalación**: Donde se instalará el proyecto
- **Ruta del modelo GGUF**: Tu modelo de lenguaje local
- **Ruta de llama-cli**: Binario de llama.cpp

### 3. Estructura Generada
```
asistente-ia/
├── src/
│   ├── core/              # Motor principal
│   ├── llm/               # Cliente LLM
│   ├── file_ops/          # Gestión de archivos
│   └── commands/          # Ejecución de comandos
├── config/                # Configuración
├── tools/                 # Herramientas adicionales
├── tests/                 # Tests del sistema
├── logs/                  # Logs de ejecución
└── examples/              # Ejemplos de uso
```

## Uso

### Comandos Básicos
```bash
# Asistente normal
claudia "explica este proyecto"

# Modo agéntico
claudia-a "analiza completamente la arquitectura"

# Modo verbose (ver proceso interno)
claudia-deep "investigación profunda sobre errores"

# Ayuda completa
claudia-help
```

### Ejemplos de Comandos Agénticos
- `"analiza completamente la estructura del código"`
- `"investigación profunda sobre el rendimiento"`
- `"modo agéntico: optimiza todo el código"`
- `"examina detalladamente los errores"`

### Modo Interactivo
```bash
claudia
💬 > agentic on
💬 > analiza completamente este proyecto
💬 > exit
```

## Configuración Avanzada

### Archivo de Configuración
```json
{
  "llm": {
    "model_path": "/ruta/a/tu/modelo.gguf",
    "llama_bin": "/ruta/a/llama-cli",
    "max_tokens": 1024,
    "temperature": 0.7
  },
  "assistant": {
    "safe_mode": false,
    "backup_files": true,
    "supported_extensions": [".py", ".js", ".json", ".md"]
  }
}
```

### Personalización
- **Modelos**: Cambia la ruta del modelo en `config/settings.json`
- **Comandos**: Modifica la lista de comandos permitidos en `commands/runner.py`
- **Extensiones**: Añade nuevos tipos de archivo soportados

## Arquitectura del Sistema

### Componentes Principales

1. **LocalAssistant**: Clase principal que coordina todos los componentes
2. **AgenticAssistant**: Extensión que proporciona capacidades agénticas
3. **LlamaClient**: Interface con modelos llama.cpp
4. **FileManager**: Gestión segura de archivos del proyecto
5. **CommandRunner**: Ejecución controlada de comandos del sistema

### Flujo Agéntico

1. **Planificación**: Descompone la tarea en subtareas específicas
2. **Ejecución**: Ejecuta cada subtarea con contexto enriquecido
3. **Síntesis**: Combina resultados eliminando redundancias
4. **Verificación**: Valida la calidad de la respuesta final

## Seguridad

### Comandos Prohibidos
- `rm`, `rmdir`, `dd`, `shred`
- `sudo`, `su`, `chmod`, `chown`
- `kill`, `reboot`, `shutdown`

### Comandos Permitidos
- Herramientas de desarrollo: `git`, `npm`, `pip`, `docker`
- Análisis de archivos: `cat`, `grep`, `find`, `head`, `tail`
- Compilación: `make`, `cmake`, `gradle`, `maven`

## Solución de Problemas

### Error: "llama-cli no encontrado"
```bash
# Verificar instalación de llama.cpp
which llama-cli

# Actualizar ruta en config
vim config/settings.json
```

### Error: "Modelo no encontrado"
```bash
# Verificar ruta del modelo
ls -la /ruta/a/tu/modelo.gguf

# Actualizar configuración
claudia --config config/settings.json
```

### Modo Agéntico no Funciona
```bash
# Verificar modo verbose
claudia-deep "test simple"

# Ver logs
tail -f logs/assistant.log
```

## Contribución

1. Fork del repositorio
2. Crear rama para tu feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit de cambios: `git commit -am 'Añadir nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## Licencia

MIT License - Ver archivo LICENSE para detalles.

## Autor

**Gustavo Silva da Costa (Eto Demerzel)**

## Versión

**2.0.0** - Sistema agéntico mejorado con planificación inteligente y síntesis sin redundancias.

---

*Para soporte adicional, crear un issue en el repositorio del proyecto.*
