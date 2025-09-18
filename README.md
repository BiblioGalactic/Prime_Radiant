Setup Automatizado para Asistente IA Local

Descripción

Este script de instalación automatizada configura un Asistente IA Local completo que utiliza modelos de lenguaje locales a través de llama.cpp. El asistente está inspirado en Claude Code pero funciona completamente offline con modelos GGUF.

Características del Asistente

Interfaz interactiva: Modo conversacional con historial de diálogo
Ejecución de comandos: Capacidad para ejecutar comandos del sistema de forma segura
Gestión de archivos: Lectura, escritura y análisis de código fuente
Configuración flexible: Adaptable a diferentes modelos y configuraciones
Sistema de logs: Registro detallado de todas las operaciones
Requisitos

Entorno de llama.cpp: Debe tener compilado el proyecto y disponer del binario llama-cli
Modelo GGUF: Necesitará un modelo de lenguaje en formato .gguf (Mistral, Llama2, etc.)
Python 3.11+: Intérprete de Python con pip para gestionar dependencias
Herramientas básicas: bash, git, y herramientas de compilación para posibles extensiones
Estructura del Proyecto

El script crea la siguiente estructura de directorios:

text
asistente-ia/
├── src/
│   ├── core/           # Núcleo del asistente (assistant.py, config.py)
│   ├── llm/            # Cliente para llama.cpp (client.py)
│   ├── file_ops/       # Gestión de archivos (manager.py)
│   └── commands/       # Ejecutor de comandos (runner.py)
├── config/
│   ├── settings.json   # Configuración principal
│   └── prompts/        # Plantillas de prompts
├── tools/              # Herramientas adicionales
├── tests/              # Tests unitarios
├── logs/               # Logs de ejecución
└── examples/           # Ejemplos de uso
Instalación

Para utilizar el asistente, ejecute el script de instalación:

bash
# Dar permisos de ejecución
chmod +x setup_asistente.sh

# Ejecutar el script
./setup_asistente.sh
Durante la instalación, el script solicitará:

Directorio del proyecto: Donde se instalará el asistente
Ruta del modelo GGUF: Ubicación de su modelo de lenguaje
Ruta de llama-cli: Ubicación del binario de llama.cpp
Uso

Una vez instalado, puede utilizar el asistente de varias formas:

Modo interactivo

bash
cd asistente-ia
python3 src/main.py
Ejecución de comando único

bash
python3 src/main.py "explica el archivo main.py"
Con configuración personalizada

bash
python3 src/main.py -c config/mi_config.json
Configuración

El archivo principal de configuración (config/settings.json) incluye:

Rutas a modelo y binario de llama.cpp
Parámetros del modelo (temperatura, tokens máximos)
Modo seguro para ejecución de comandos
Extensiones de archivo soportadas
Configuración de logging
Personalización de Rutas

Los scripts usan rutas absolutas para mayor flexibilidad. Si necesita modificar las rutas después de la instalación:

Edite el archivo config/settings.json
O ejecute nuevamente el script de setup para reconfigurar
Descarga de Modelos

Si no tiene un modelo GGUF, puede descargar uno desde:

Hugging Face
TheBloke's models
Recomendamos modelos como:

Mistral-7B-Instruct-v0.1
Llama-2-7B-Chat
CodeLlama-7B-Instruct
Notas Técnicas

El asistente funciona completamente offline una vez instalado
Todos los procesamientos se realizan localmente
Los logs se guardan con marcas de tiempo para diagnóstico
El modo seguro restringe comandos potencialmente peligrosos
Solución de Problemas

Error: "llama-cli no encontrado"

Verifique que llama.cpp esté compilado correctamente:

bash
cd llama.cpp
make clean
make
Error: "Modelo no encontrado"

Descargue un modelo GGUF y actualice la ruta en config/settings.json

Error: Dependencias faltantes

Instale las dependencias requeridas:

bash
pip install -r requirements.txt
Contribución

Este proyecto sigue normas estrictas de estilo para:

Cabeceras de scripts y documentación
Validaciones y comprobaciones de errores
Gestión segura de recursos
Limpieza y mantenimiento de código
Licencia

Proyecto de código abierto para uso educativo y experimental.

Para más información, consulte los archivos README.md específicos en cada directorio del proyecto.
