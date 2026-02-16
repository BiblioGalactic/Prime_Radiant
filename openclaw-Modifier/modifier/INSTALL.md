# 📦 Guía de Instalación Completa

Instalación paso a paso desde cero hasta tener OpenClaw funcionando con modelos locales.

## 🎯 Opciones de Instalación

### Opción A: Instalación Rápida (Recomendada)

```bash
# 1. Clona/descarga el Modificador
git clone https://github.com/BiblioGalactic/openclaw-modifier
cd openclaw-modifier/Modificador

# 2. Ejecuta el verificador
./scripts/check_requirements.sh

# 3. Sigue las instrucciones que te dé
```

Si todo está OK, ve directo a [Configuración](#configuración).

### Opción B: Instalación Manual Completa

Si check_requirements.sh falla, instala manualmente:

---

## 📋 Prerequisitos

### 1. Sistema Operativo

#### macOS
```bash
# Verifica la versión
sw_vers

# Mínimo: macOS 12 (Monterey)
# Recomendado: macOS 13+ (Ventura o Sonoma)
```

#### Linux (Ubuntu/Debian)
```bash
# Verifica la versión
lsb_release -a

# Mínimo: Ubuntu 20.04 LTS
# Recomendado: Ubuntu 22.04 LTS+
```

### 2. Herramientas Base

#### macOS
```bash
# Instalar Homebrew (si no lo tienes)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar herramientas esenciales
brew install curl git bash

# Verificar
which brew curl git bash
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y curl git build-essential

# Fedora/RHEL
sudo dnf install -y curl git gcc-c++ make
```

### 3. Node.js (versión 18+)

#### Opción A: nvm (Recomendado)
```bash
# Instalar nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Recargar shell
source ~/.bashrc  # o ~/.zshrc en macOS

# Instalar Node.js 18
nvm install 18
nvm use 18
nvm alias default 18

# Verificar
node --version  # Debe ser v18.x.x o superior
npm --version
```

#### Opción B: Homebrew (macOS)
```bash
brew install node@18
brew link --overwrite node@18

node --version
```

#### Opción C: apt (Ubuntu)
```bash
# Añadir repositorio NodeSource
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -

# Instalar
sudo apt install -y nodejs

# Verificar
node --version
```

---

## 🤖 llama.cpp

### Compilación desde Fuente

#### macOS (con Metal acceleration)
```bash
# Ir al home
cd ~

# Clonar repositorio
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Compilar con Metal (GPU de Apple Silicon)
make clean
make

# Verificar
./build/bin/llama-server --help

# Guardar la ruta (la necesitarás)
pwd  # Ejemplo: /Users/gustavo/llama.cpp
```

#### macOS (Intel, sin GPU)
```bash
cd ~
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Compilar CPU-only
make

./build/bin/llama-server --help
```

#### Linux (con CUDA - NVIDIA GPU)
```bash
cd ~
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Instalar CUDA toolkit primero
# Ver: https://developer.nvidia.com/cuda-downloads

# Compilar con CUDA
make LLAMA_CUBLAS=1

./build/bin/llama-server --help
```

#### Linux (CPU only)
```bash
cd ~
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

make

./build/bin/llama-server --help
```

### Pre-compilados (Alternativa)

Si no quieres compilar:
1. Descarga release desde: https://github.com/ggerganov/llama.cpp/releases
2. Extrae el archivo
3. Busca `llama-server` (o `llama-server.exe` en Windows)

---

## 📥 Descargar Modelos

### Opción A: Usando huggingface-cli

```bash
# Instalar huggingface-cli
pip install --break-system-packages huggingface-hub

# Crear directorio para modelos
mkdir -p ~/modelos
cd ~/modelos

# Descargar Mistral 7B (Q6_K - 5.9GB)
huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.1-GGUF \
  mistral-7b-instruct-v0.1.Q6_K.gguf \
  --local-dir . \
  --local-dir-use-symlinks False

# Verificar
ls -lh ~/modelos/mistral-7b-instruct-v0.1.Q6_K.gguf
```

### Opción B: Descarga Manual

1. Ve a: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF
2. Busca el archivo `mistral-7b-instruct-v0.1.Q6_K.gguf`
3. Click en "Download"
4. Mueve el archivo a `~/modelos/`

### Modelos Alternativos Recomendados

```bash
# Llama 2 7B Chat (Q5_K_M - 5.1GB)
huggingface-cli download TheBloke/Llama-2-7B-Chat-GGUF \
  llama-2-7b-chat.Q5_K_M.gguf \
  --local-dir ~/modelos \
  --local-dir-use-symlinks False

# Qwen 1.5 7B Chat (Q5_K_M - 5.2GB)
huggingface-cli download Qwen/Qwen1.5-7B-Chat-GGUF \
  qwen1_5-7b-chat-q5_k_m.gguf \
  --local-dir ~/modelos \
  --local-dir-use-symlinks False
```

---

## 🌐 OpenClaw

### Instalación

#### Opción A: npm global (Recomendado)
```bash
npm install -g openclaw

# Verificar
openclaw --version
```

#### Opción B: Desde el repositorio
```bash
cd ~
git clone https://github.com/openclaws/openclaw
cd openclaw

# Instalar dependencias
npm install

# Build
npm run build

# Enlazar globalmente
npm link

# Verificar
openclaw --version
```

#### Opción C: npx (sin instalación)
```bash
# Usar sin instalar
npx openclaw --version
npx openclaw start
```

---

## ⚙️ Configuración

### 1. Clonar/Descargar el Modificador

```bash
cd ~
git clone https://github.com/BiblioGalactic/openclaw-modifier
cd openclaw-modifier/Modificador
```

O descarga el ZIP y extrae.

### 2. Editar Configuración

```bash
cd Modificador
cp configs/model_config.env.example configs/model_config.env
nano configs/model_config.env
```

**Configuración mínima obligatoria:**

```bash
# Ruta absoluta a tu modelo
MODEL_PATH="/Users/gustavo/modelos/mistral-7b-instruct-v0.1.Q6_K.gguf"

# Ruta absoluta a llama-server
LLAMA_BIN="/Users/gustavo/llama.cpp/build/bin/llama-server"

# Nombre identificador
MODEL_NAME="mistral-7b"

# Puerto base
BASE_PORT=8080

# Contexto
CONTEXT_SIZE=4096

# Threads (usa número de cores de tu CPU)
THREADS=8
```

### 3. Verificar Setup

```bash
./scripts/check_requirements.sh
```

Si todo está OK:
```
✅ TODO LISTO - Puedes continuar con el setup
```

---

## 🚀 Iniciar Servicios

### Single Agent

```bash
# Terminal 1: Iniciar llama-server
cd Modificador
./scripts/start_single_agent.sh

# Espera a ver: ✅ SINGLE AGENT INICIADO CORRECTAMENTE
```

```bash
# Terminal 2: Iniciar OpenClaw
openclaw start

# Espera a ver: ✓ Gateway started on http://localhost:3000
```

### Multi-Agent

```bash
# Terminal 1: Iniciar 3 llama-servers
cd Modificador
./scripts/start_multi_agent.sh

# Espera a ver: ✅ MULTI-AGENT INICIADO CORRECTAMENTE
```

```bash
# Terminal 2: Iniciar OpenClaw
openclaw start
```

---

## ✅ Verificación

### 1. Test llama-server

```bash
# Health check
curl http://127.0.0.1:8080/health
# Respuesta: {"status":"ok"}

# Models endpoint
curl http://127.0.0.1:8080/v1/models
# Respuesta: JSON con modelo listado

# Chat completion
curl -X POST http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-model",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 20
  }'
# Respuesta: JSON con "choices"
```

### 2. Test OpenClaw

```bash
# Health
curl http://localhost:3000/api/health

# Dashboard
open http://localhost:3000  # macOS
# O abre en navegador manualmente
```

### 3. Test End-to-End

```bash
openclaw message "Hola, ¿cómo estás?"
```

Si recibes una respuesta coherente, **¡todo funciona!** 🎉

---

## 🛑 Detener Servicios

```bash
# Detener llama-servers
cd Modificador
./scripts/stop_all.sh

# Detener OpenClaw
pkill openclaw
# O Ctrl+C en la terminal donde corre
```

---

## 🔧 Troubleshooting Instalación

### Error: "Permission denied"

```bash
# Dar permisos de ejecución
chmod +x ~/llama.cpp/build/bin/llama-server
chmod +x Modificador/scripts/*.sh
```

### Error: "Command not found: node"

```bash
# Reiniciar shell
exec $SHELL

# O agregar al PATH manualmente
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Error: "Cannot find module"

```bash
# Reinstalar node_modules
cd ~/openclaw
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Error: Compilación de llama.cpp falla

```bash
# macOS: Instalar Xcode Command Line Tools
xcode-select --install

# Linux: Instalar build essentials
sudo apt install -y build-essential cmake

# Reintentar
cd ~/llama.cpp
make clean
make
```

---

## 📚 Siguientes Pasos

1. **Leer la Guía Rápida**: `docs/GUIA_RAPIDA.md`
2. **Explorar Personalidades**: `workspaces/*/SOUL.md`
3. **Configurar Canales**: WhatsApp/Telegram/Discord
4. **Experimentar con Modelos**: Probar otros modelos
5. **Personalizar Agentes**: Editar workspaces

---

## 🆘 ¿Problemas?

1. **FAQ**: `docs/FAQ.md`
2. **Troubleshooting**: `docs/TROUBLESHOOTING.md`
3. **Issues**: GitHub del proyecto
4. **Comunidad**: Discord de OpenClaw

---

**¡Instalación completa!** 🎉

[⬆️ Volver al README principal](README.md) | [▶️ Ver Guía Rápida](docs/GUIA_RAPIDA.md)
