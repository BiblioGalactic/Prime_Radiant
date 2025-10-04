Versión en Español

Memoria IA Modular Local es un script público en Bash para generar y ejecutar un prompt completo con LLaMA a partir de tus notas en Markdown. Concatena todos los archivos .md de un directorio, los limpia y lanza una sesión interactiva de LLaMA.

Funcionalidades

Funciona con cualquier directorio de archivos .md.

Limpia espacios y líneas vacías manteniendo UTF-8.

Solicita rutas del modelo y del ejecutable llama-cli.

Actualización dinámica opcional antes de generar el prompt.

Uso

./local_ia_modular_memory.sh

Sigue las indicaciones:

Ingresa el directorio con tus .md.

Ingresa la ruta a tu modelo LLaMA (.gguf).

Ingresa la ruta al ejecutable llama-cli.

El script generará prompt_completo.txt y lanzará una sesión interactiva de LLaMA.

Requisitos

Bash >=5

LLaMA CLI instalado

Modelo local .gguf

Licencia

Open-source. Úsalo libremente, modifícalo y compártelo.


