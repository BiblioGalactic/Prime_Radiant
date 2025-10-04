Versión en Español

Local AI MMAP Memory es un lanzador público en Bash + C para ejecutar LLaMA con múltiples perfiles modulares cargados directamente en memoria mediante mmap. Cada perfil representa un contexto IA distinto (técnico, filosófico, seguridad, etc.), permitiendo manejar prompts eficientemente sin archivos temporales.

Funcionalidades

Carga múltiples perfiles .txt en memoria.

Selección de perfil activo en tiempo de ejecución.

Ejecuta LLaMA de manera interactiva con el contexto cargado vía mmap.

Portable y open-source: el usuario introduce sus propias rutas.

Manejo de errores para archivos, mmap y lanzamiento de LLaMA.

Uso

./local-AI-MMAP-memory.sh

Sigue los pasos para:

Introducir tu archivo prompt (.txt)

Introducir la ruta al ejecutable llama-cli

Introducir la ruta de tu modelo .gguf

Introducir rutas de perfiles separadas por coma

Elegir el índice del perfil activo

Requisitos

Bash >=5

GCC

LLaMA CLI instalado

Modelo local .gguf

Licencia

Open-source. Úsalo libremente, modifícalo y compártelo.


