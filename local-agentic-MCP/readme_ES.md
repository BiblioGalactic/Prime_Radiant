# 🤖 MCP Local - Chat IA con Herramientas del Sistema

> **Sistema completo de Model Context Protocol con 11 herramientas y modo agéntico para tu IA local**

```
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║       Transforma tu LLM local en un asistente poderoso     ║
║       con acceso a tu sistema operativo                    ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

## 📋 Tabla de Contenidos

- [¿Qué es esto?](#-qué-es-esto)
- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Uso Básico](#-uso-básico)
- [Modo Agéntico](#-modo-agéntico)
- [Las 11 Herramientas](#-las-11-herramientas)
- [Ejemplos Prácticos](#-ejemplos-prácticos)
- [Configuración Avanzada](#-configuración-avanzada)
- [Solución de Problemas](#-solución-de-problemas)
- [Arquitectura](#-arquitectura)
- [Créditos](#-créditos)

---

## 🎯 ¿Qué es esto?

**MCP Local** es un sistema que conecta tu modelo de lenguaje local (como Mistral, Llama, etc.) con **herramientas reales de tu sistema operativo**.

### Sin MCP:
```
👤 Usuario: "Lista mis archivos Python"
🤖 IA: "Lo siento, no puedo acceder a tu sistema de archivos"
```

### Con MCP:
```
👤 Usuario: "Lista mis archivos Python"
🤖 IA: [BUSCAR] ✓
       Encontré 12 archivos: main.py, utils.py, config.py...
```

**Es como darle manos a tu IA para que interactúe con tu computadora** 🦾

---

## ✨ Características

### 🔧 11 Herramientas Completas
- ✅ Leer y escribir archivos
- ✅ Ejecutar comandos bash
- ✅ Navegar directorios
- ✅ Buscar archivos y contenido
- ✅ Consultar APIs HTTP
- ✅ Descargar archivos desde URLs
- ✅ Comprimir/descomprimir (zip, tar, tar.gz)
- ✅ Operaciones Git (status, log, diff, branch)
- ✅ Monitoreo del sistema (RAM, CPU, disco)
- ✅ Búsqueda en contenido (grep)

### 🧠 Modo Agéntico
**¡La característica estrella!** La IA puede encadenar múltiples acciones automáticamente:

```
👤: "descarga el README de GitHub y comprime todos los markdown"

🤖 [MODO AGÉNTICO]
   📋 Plan: 3 pasos
   🔄 Descargando... ✅
   🔄 Buscando *.md... ✅  
   🔄 Comprimiendo... ✅
   
   ✅ Descargué el README (3.4KB), encontré 5 markdown
      y los comprimí en docs.zip (45KB)
```

### 🔒 Seguridad Integrada
- ❌ Comandos peligrosos bloqueados (rm, dd, sudo, etc.)
- 🛡️ Solo puede escribir en $HOME o /tmp
- ⏱️ Timeouts automáticos
- 📦 Límites de tamaño de archivo (10MB)

### 🎨 Interfaz Amigable
- 💬 Chat interactivo
- 📊 Modo verbose para debugging
- 🎯 Detección automática de modo agéntico
- ⚡ Respuestas rápidas y claras

---

## 📦 Requisitos

Antes de instalar, asegúrate de tener:

### Requisitos Obligatorios
```bash
✅ Python 3.8 o superior
✅ pip3
✅ Un modelo GGUF (Mistral, Llama, etc.)
✅ llama.cpp compilado con llama-cli
```

### Requisitos Opcionales
```bash
🔧 git (para herramienta Git)
🔧 curl/wget (ya incluidos en macOS/Linux)
```

### Sistema Operativo
- ✅ macOS (probado)
- ✅ Linux (probado)
- ⚠️ Windows (con WSL)

---

## 🚀 Instalación

### Paso 1: Descargar el instalador

```bash
# Opción A: Clonar el repositorio
git clone https://github.com/tu-repo/mcp-local.git
cd mcp-local

# Opción B: Descargar el script directamente
curl -O https://tu-url/mcp_setup.sh
chmod +x mcp_setup.sh
```

### Paso 2: Ejecutar el instalador

```bash
./mcp_setup.sh
```

### Paso 3: Configurar rutas

El instalador te pedirá dos rutas:

```
🎯 CONFIGURACIÓN INICIAL
==========================================

📍 Paso 1/2: Ruta del ejecutable llama-cli
   Ejemplo: /usr/local/bin/llama-cli
   o: /Users/tu-usuario/llama.cpp/build/bin/llama-cli
   Ruta completa: _

📍 Paso 2/2: Ruta del modelo GGUF
   Ejemplo: /Users/tu-usuario/modelos/mistral-7b-instruct.gguf
   Ruta completa: _
```

### Paso 4: Instalación automática

El script hará automáticamente:
1. ✅ Crear entorno virtual Python
2. ✅ Instalar dependencias (flask, psutil, requests)
3. ✅ Generar servidor MCP (11 herramientas)
4. ✅ Generar cliente con modo agéntico
5. ✅ Guardar configuración

```
✅ INSTALACIÓN COMPLETADA

╔════════════════════════════════════════╗
║     MCP LOCAL - MENÚ PRINCIPAL         ║
║     💪 11 Herramientas + Agéntico      ║
╚════════════════════════════════════════╝

  1) 💬 Iniciar chat (con modo agéntico)
  2) 🔧 Ver herramientas MCP (11)
  3) ⚙️  Reconfigurar rutas
  4) 🚪 Salir
```

---

## 💬 Uso Básico

### Iniciar el Chat

```bash
./mcp_setup.sh
# Selecciona opción 1) Iniciar chat
```

### Comandos del Chat

```
👤 Tú: _

Comandos disponibles:
  agentico on/off  → Activar/desactivar modo agéntico
  verbose on/off   → Ver logs detallados
  herramientas     → Listar las 11 herramientas
  salir            → Cerrar el chat
```

### Ejemplo de Conversación Normal

```bash
👤 Tú: lista los archivos de mi escritorio

🤖 IA: [LISTAR] ✓
   Tienes 23 items en tu escritorio: Documents/, Downloads/,
   imagen.png, notas.txt...

👤 Tú: cuánta memoria RAM tengo libre?

🤖 IA: [MEMORIA] ✓
   Tienes 8.5GB de RAM disponible de un total de 16GB (53% libre)
```

---

## 🧠 Modo Agéntico

El modo agéntico permite que la IA **encadene múltiples acciones automáticamente** sin que tengas que dar comandos uno por uno.

### ¿Cómo Activarlo?

**Opción 1: Manual**
```bash
👤 Tú: agentico on
🤖 Modo agéntico: ACTIVADO
```

**Opción 2: Automático** (detecta estas palabras clave)
- `y luego`
- `después`
- `y comprime`
- `y busca`
- `completa todo`
- `haz todo`
- `automático`

### Ejemplo Completo

#### Sin Modo Agéntico (3 comandos separados):
```bash
👤: descarga el README
🤖: ✓

👤: busca todos los markdown
🤖: ✓

👤: comprime los archivos
🤖: ✓
```

#### Con Modo Agéntico (1 solo comando):
```bash
👤: descarga el README de GitHub y luego comprime todos los markdown

🤖 [MODO AGÉNTICO ACTIVADO]
📋 Plan: 3 pasos

🔄 Paso 1/3: DESCARGAR:https://raw.githubusercontent.com/...
   ✅ DESCARGAR

🔄 Paso 2/3: BUSCAR:~/Desktop:*.md
   ✅ BUSCAR

🔄 Paso 3/3: COMPRIMIR:comprimir:~/Desktop:~/Desktop/docs.zip
   ✅ COMPRIMIR

🔄 Sintetizando resultados...

✅ Tarea completada

🤖 He descargado el README (3456 bytes), encontrado 5 archivos 
   markdown en tu escritorio y los he comprimido en docs.zip 
   (45KB total). ¡Todo listo!
```

### Modo Verbose (Debug)

Para ver el proceso interno:

```bash
👤 Tú: verbose on
📊 Modo verbose: ACTIVADO

👤 Tú: descarga X y comprime Y

🧠 Planificando pasos...
📋 Pasos planificados: ["DESCARGAR:...", "BUSCAR:...", "COMPRIMIR:..."]
🔍 Ejecutando: DESCARGAR:https://...
   ✅ DESCARGAR
🔍 Ejecutando: BUSCAR:~/Desktop:*.md
   ✅ BUSCAR
...
```

---

## 🛠️ Las 11 Herramientas

### 1. 📖 Leer Archivo
```bash
👤: lee el archivo README.md
🤖: [LEER] ✓
   El archivo contiene documentación sobre...
```
- 📦 Máximo: 64KB
- 🔒 Solo archivos de texto

### 2. ✍️ Escribir Archivo
```bash
👤: crea un archivo test.txt con "Hola Mundo"
🤖: [ESCRIBIR] ✓ (11 bytes)
   Archivo creado en ~/test.txt
```
- 📦 Máximo: 10MB
- 🔒 Solo en $HOME o /tmp
- 🔀 Modos: `w` (sobrescribir) o `a` (añadir)

### 3. 📁 Listar Directorio
```bash
👤: qué hay en mi carpeta Downloads?
🤖: [LISTAR] ✓
   45 items: documentos/, imagenes/, video.mp4...
```
- 📊 Muestra: nombre, tipo, tamaño, fecha
- 📦 Límite: 100 items

### 4. 🔍 Buscar Archivos
```bash
👤: encuentra todos mis archivos Python
🤖: [BUSCAR] ✓
   12 archivos encontrados: main.py, utils.py...
```
- 🌲 Búsqueda recursiva
- 🎯 Patrones glob: `*.py`, `test*.txt`, etc.
- 📦 Límite: 50 archivos

### 5. 🔎 Buscar en Contenido (Grep)
```bash
👤: busca "TODO" en archivos Python
🤖: [GREP] ✓ (8 coincidencias)
   main.py:42: # TODO: Implementar validación
   utils.py:15: # TODO: Optimizar algoritmo
```
- 📄 Solo archivos <1MB
- 🎯 Regex case-insensitive
- 📦 Límite: 50 coincidencias

### 6. ⚡ Ejecutar Comando
```bash
👤: ejecuta ls -la
🤖: [COMANDO] ✓
   total 256
   drwxr-xr-x  15 user  staff   480 Oct 10 10:30 .
   ...
```
- ❌ **Bloqueados**: rm, dd, sudo, su, mkfs
- ⏱️ Timeout: 10 segundos
- 📦 Output: 4KB máximo

### 7. 💾 Consultar Memoria
```bash
👤: cuántos recursos tengo disponibles?
🤖: [MEMORIA] ✓
   RAM: 8.5GB libre de 16GB
   CPU: 35% de uso (8 cores)
   Disco: 245GB libres de 500GB
```

### 8. 📥 Descargar Archivo
```bash
👤: descarga https://example.com/file.pdf
🤖: [DESCARGAR] ✓ (2.5MB)
   Archivo guardado en ~/Downloads/file.pdf
```
- 🌐 Solo http:// y https://
- 📦 Límite: 10MB
- ⏱️ Timeout: 30 segundos

### 9. 🗜️ Comprimir/Descomprimir
```bash
👤: comprime mi carpeta documentos
🤖: [COMPRIMIR] ✓
   Carpeta comprimida en documentos.zip (12MB)
```
- 📦 Formatos: zip, tar, tar.gz
- 🔄 Operaciones: comprimir, descomprimir

### 10. 🔧 Git Operations
```bash
👤: muestra el status de git
🤖: [GIT] ✓
   On branch main
   Changes not staged for commit:
     modified: src/main.py
```
- ✅ Permitidos: status, log, diff, branch, remote
- ❌ **Bloqueados**: commit, push, pull (solo lectura)

### 11. 🌐 Consultar API
```bash
👤: consulta la API de ejemplo.com
🤖: [API] ✓ (200)
   Status: OK
   Respuesta: {"data": "ejemplo"}
```
- 📡 Métodos: GET, POST, PUT, DELETE, PATCH
- ⏱️ Timeout: 10 segundos
- 📦 Respuesta: 4KB máximo

---

## 💡 Ejemplos Prácticos

### Ejemplo 1: Análisis de Proyecto
```bash
👤: agentico on

👤: lista todos los archivos Python y busca TODOs pendientes

🤖 [MODO AGÉNTICO]
   Paso 1: Buscando *.py... ✅
   Paso 2: Buscando 'TODO'... ✅
   
   Encontré 12 archivos Python con 8 TODOs pendientes:
   - main.py: 3 TODOs
   - utils.py: 2 TODOs
   - config.py: 3 TODOs
```

### Ejemplo 2: Backup Automatizado
```bash
👤: busca todos los archivos importantes y comprimelos en un backup

🤖 [MODO AGÉNTICO]
   Paso 1: Buscando archivos... ✅
   Paso 2: Comprimiendo... ✅
   
   He creado backup.zip con 45 archivos (234MB total)
```

### Ejemplo 3: Monitoreo de Sistema
```bash
👤: muestra el estado de git y los recursos del sistema

🤖 [MODO AGÉNTICO]
   Paso 1: Git status... ✅
   Paso 2: Consultando recursos... ✅
   
   Git: 3 archivos modificados en rama main
   Sistema: RAM 45% libre, CPU 25%, Disco 50% libre
```

### Ejemplo 4: Workflow Completo
```bash
👤: descarga el README de GitHub, búscalo en mi escritorio 
    y comprime todos los markdown que encuentres

🤖 [MODO AGÉNTICO]
   📋 Plan: 3 pasos
   
   Paso 1: Descargando desde GitHub... ✅ (3.4KB)
   Paso 2: Buscando *.md en Desktop... ✅ (5 archivos)
   Paso 3: Comprimiendo archivos... ✅ (45KB)
   
   ✅ Descargué el README, encontré 5 markdown y los 
      comprimí en docs.zip. Todo está en tu escritorio.
```

---

## ⚙️ Configuración Avanzada

### Cambiar Modelo o Ruta de llama-cli

```bash
./mcp_setup.sh
# Selecciona opción 3) Reconfigurar rutas
```

### Editar Configuración Manual

```bash
nano ~/.mcp_local/config.env
```

```bash
# Configuración MCP Local
LLAMA_CLI="/ruta/a/tu/llama-cli"
MODELO_GGUF="/ruta/a/tu/modelo.gguf"
```

### Variables de Entorno

```bash
# Activar debug del servidor MCP
export MCP_DEBUG=1

# Ejecutar
./mcp_setup.sh
```

### Estructura de Archivos

```
~/.mcp_local/
├── config.env           # Tu configuración
├── venv/                # Entorno Python
├── mcp_server.py        # Servidor con 11 herramientas
└── chat_mcp.py          # Cliente con modo agéntico
```

---

## 🔧 Solución de Problemas

### Problema: "llama-cli no encontrado"

**Solución:**
```bash
# Verificar que llama.cpp esté compilado
cd ~/llama.cpp
cmake -B build
cmake --build build

# Verificar ruta
ls ~/llama.cpp/build/bin/llama-cli

# Reconfigurar MCP
./mcp_setup.sh
# Opción 3) Reconfigurar rutas
```

### Problema: "Modelo no encontrado"

**Solución:**
```bash
# Verificar que el modelo existe
ls ~/ruta/a/tu/modelo.gguf

# Si no tienes modelo, descarga uno
# Ejemplo: Mistral 7B
wget https://huggingface.co/...modelo.gguf

# Reconfigurar
./mcp_setup.sh
# Opción 3) Reconfigurar rutas
```

### Problema: "Error instalando dependencias Python"

**Solución:**
```bash
# Verificar Python
python3 --version  # Debe ser 3.8+

# Limpiar entorno virtual
rm -rf ~/.mcp_local/venv

# Reinstalar
./mcp_setup.sh
```

### Problema: "Modo agéntico no funciona bien"

**Solución:**
```bash
# Usar modo verbose para ver qué pasa
👤: verbose on
👤: tu comando problemático

# El modo agéntico depende de la calidad del modelo
# Modelos recomendados:
# - Mistral 7B Instruct (mínimo)
# - Llama 3 8B Instruct (mejor)
# - Mixtral 8x7B (óptimo)
```

### Problema: "Timeout en consultas"

**Solución:**
```bash
# Si el modelo es muy lento, aumentar timeout
# Editar ~/.mcp_local/chat_mcp.py

# Línea ~40:
IA_CMD = [
    config.get('LLAMA_CLI', 'llama-cli'),
    "--model", config.get('MODELO_GGUF', ''),
    "--n-predict", "512",
    "--temp", "0.7",
    "--ctx-size", "4096"
]

# Agregar GPU si está disponible:
# "--n-gpu-layers", "35"
```

### Problema: "Comando bloqueado por seguridad"

**Solución:**
Esto es intencional. Comandos peligrosos están bloqueados:
- ❌ `rm -rf`
- ❌ `dd`
- ❌ `sudo`
- ❌ `su`

Si realmente necesitas ejecutar comandos privilegiados, hazlo manualmente fuera del MCP.

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────┐
│           👤 Usuario (TÚ)                   │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│      💬 Cliente Chat (chat_mcp.py)          │
│  ┌────────────────────────────────────┐     │
│  │  🧠 Modo Agéntico                  │     │
│  │  - Planificación de pasos          │     │
│  │  - Ejecución secuencial            │     │
│  │  - Síntesis de resultados          │     │
│  └────────────────────────────────────┘     │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│        🤖 Modelo LLM Local                  │
│     (Mistral, Llama, Mixtral, etc.)         │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│   🔧 Servidor MCP (mcp_server.py)           │
│  ┌────────────────────────────────────┐     │
│  │  11 Herramientas:                  │     │
│  │  ✓ Archivos (leer/escribir)        │     │
│  │  ✓ Sistema (memoria/comandos)      │     │
│  │  ✓ Red (API/descargas)             │     │
│  │  ✓ Búsqueda (archivos/contenido)   │     │
│  │  ✓ Utilidades (git/comprimir)      │     │
│  └────────────────────────────────────┘     │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│     💻 Tu Sistema Operativo                 │
│  (Archivos, Comandos, Recursos)             │
└─────────────────────────────────────────────┘
```

### Flujo de una Consulta Normal

```
1. Usuario escribe comando
   👤 "lista archivos Python"
   
2. Cliente consulta al LLM
   💬 → 🤖 "¿Qué herramienta usar?"
   
3. LLM decide herramienta
   🤖 → 💬 "[USAR_HERRAMIENTA:BUSCAR:.:*.py]"
   
4. Cliente llama al servidor MCP
   💬 → 🔧 {"method": "buscar_archivos", ...}
   
5. Servidor ejecuta herramienta
   🔧 → 💻 Búsqueda real en el sistema
   
6. Servidor devuelve resultados
   🔧 → 💬 {"result": ["main.py", ...]}
   
7. Cliente envía resultados al LLM
   💬 → 🤖 "Archivos encontrados: ..."
   
8. LLM genera respuesta natural
   🤖 → 💬 "Encontré 12 archivos Python: ..."
   
9. Usuario ve la respuesta
   💬 → 👤 "Encontré 12 archivos Python: ..."
```

### Flujo del Modo Agéntico

```
1. Usuario da comando complejo
   👤 "descarga X y luego comprime Y"
   
2. Cliente detecta modo agéntico
   💬 [Detecta palabras clave "y luego"]
   
3. LLM planifica pasos
   💬 → 🤖 "Descompón en pasos"
   🤖 → 💬 ["DESCARGAR:...", "BUSCAR:...", "COMPRIMIR:..."]
   
4. Cliente ejecuta pasos secuencialmente
   💬 → 🔧 Paso 1: DESCARGAR ✅
   💬 → 🔧 Paso 2: BUSCAR ✅
   💬 → 🔧 Paso 3: COMPRIMIR ✅
   
5. LLM sintetiza resultados
   💬 → 🤖 "Resume todo lo hecho"
   🤖 → 💬 "Descargué, busqué y comprimí..."
   
6. Usuario ve resumen final
   💬 → 👤 "✅ Tarea completada: ..."
```

---

## 📚 Recursos Adicionales

### Model Context Protocol (MCP)
- 📖 [Especificación MCP](https://spec.modelcontextprotocol.io/)
- 🔗 [GitHub de Anthropic MCP](https://github.com/anthropics/mcp)

### Modelos Recomendados
- 🦙 [Llama 3 8B Instruct](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct)
- 🌟 [Mistral 7B Instruct](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.1)
- 🚀 [Mixtral 8x7B](https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1)

### llama.cpp
- 🔗 [GitHub llama.cpp](https://github.com/ggerganov/llama.cpp)
- 📖 [Documentación](https://github.com/ggerganov/llama.cpp/blob/master/README.md)

---

## 🎓 Casos de Uso

### Para Desarrolladores
- ✅ Automatizar tareas repetitivas
- ✅ Analizar código y buscar TODOs
- ✅ Gestionar repositorios Git
- ✅ Generar documentación
- ✅ Monitorear recursos del sistema

### Para Administradores de Sistemas
- ✅ Automatizar backups
- ✅ Monitorear logs
- ✅ Gestionar archivos de configuración
- ✅ Buscar información en logs
- ✅ Comprimir/descomprimir archivos

### Para Usuarios Avanzados
- ✅ Organizar archivos automáticamente
- ✅ Descargar y procesar contenido web
- ✅ Buscar información en documentos
- ✅ Automatizar workflows complejos
- ✅ Integrar con APIs externas

---

## 🤝 Contribuir

¿Tienes ideas para mejorar MCP Local? ¡Contribuye!

### Ideas de Nuevas Herramientas
- 📧 Cliente de email
- 📅 Integración con calendario
- 🗄️ Operaciones con bases de datos
- 🐳 Integración con Docker
- 📊 Generación de reportes

### Cómo Contribuir
1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-herramienta`)
3. Commit tus cambios (`git commit -am 'Añade nueva herramienta X'`)
4. Push a la rama (`git push origin feature/nueva-herramienta`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Úsalo libremente, modifícalo y compártelo.

```
MIT License

Copyright (c) 2025 Gustavo Silva Da Costa

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Agradecimientos

- Anthropic por el concepto de Model Context Protocol
- Comunidad de llama.cpp por hacer posible ejecutar LLMs localmente
- Todos los que contribuyen al ecosistema de IA open source

---

## 📞 Soporte

¿Problemas? ¿Preguntas? ¿Sugerencias?

- 📧 Email: gsilvadacosta0@gmail.com 
- 🆇 Antiguo twitter 😂: https://x.com/bibliogalactic

---

<div align="center">

## ⭐ Si te gusta este proyecto, dale una estrella en GitHub ⭐

```
╔════════════════════════════════════════════════════════╗
║                                                        ║
║   Hecho con ❤️ para la comunidad de IA local          ║
║                                                        ║
║   "Dando manos a las IAs, una herramienta a la vez"   ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

### 👨‍💻 Creado por

**Gustavo Silva Da Costa** (Eto Demerzel) 🤫

🚀 *Transformando IAs locales en asistentes poderosos*

</div>

---

**Versión:** 1.0.0  
**Última actualización:** Octubre 2025  
**Estado:** ✅ Producción

---
