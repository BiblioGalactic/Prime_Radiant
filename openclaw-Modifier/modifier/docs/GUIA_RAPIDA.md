# 🚀 Guía Rápida - Setup en 15 minutos

Esta guía te lleva paso a paso desde cero hasta tener OpenClaw funcionando con tu modelo local.

## 📋 Antes de empezar

### ¿Qué necesitas?

- ✅ **macOS** (Intel o Apple Silicon) o **Linux** (Ubuntu 20.04+)
- ✅ **8GB+ RAM** (16GB recomendado para multi-agente)
- ✅ **10GB espacio libre** en disco
- ✅ **Node.js 18+**
- ✅ **llama.cpp** compilado
- ✅ **Un modelo GGUF** (Mistral, Llama, etc.)

### ¿No tienes llama.cpp?

```bash
# Clonar repositorio
cd ~ && git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Compilar (macOS con Metal)
make

# Compilar (Linux)
make

# Verificar
./build/bin/llama-server --help
```

### ¿No tienes un modelo?

Descarga desde Hugging Face:

```bash
# Ejemplo: Mistral 7B Q6
mkdir -p ~/modelos
cd ~/modelos

# Usando huggingface-cli
huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.1-GGUF \
  mistral-7b-instruct-v0.1.Q6_K.gguf

# O descarga manual desde:
# https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF
```

## 🎯 Setup Paso a Paso

### Paso 1: Verificar requisitos

```bash
cd Modificador/scripts
./check_requirements.sh
```

**Si ves errores:**
- `llama-cli NO ENCONTRADO` → Instala llama.cpp (ver arriba)
- `Node.js v16` → Actualiza a Node.js 18+: `brew install node` o `nvm install 18`
- `Puerto 8080 en uso` → Detén el servicio que lo usa o cambia `BASE_PORT` en config

**Warnings que puedes ignorar:**
- `OpenClaw CLI: NO ENCONTRADO` → Se instalará después
- `jq: NO ENCONTRADO` → Es opcional

### Paso 2: Configurar tu modelo

```bash
# Editar configuración
nano configs/model_config.env

# O usar tu editor favorito
code configs/model_config.env
```

**Configuración mínima obligatoria:**

```bash
# 1. Ruta a tu modelo GGUF
MODEL_PATH="/ruta/completa/a/tu/modelo.gguf"

# 2. Ruta a llama-server
LLAMA_BIN="/ruta/a/llama.cpp/build/bin/llama-server"

# 3. Nombre identificador (sin espacios)
MODEL_NAME="mistral-7b"
```

**Ejemplo real (macOS):**

```bash
MODEL_PATH="/Users/gustavo/modelos/mistral-7b-instruct-v0.1.Q6_K.gguf"
LLAMA_BIN="/Users/gustavo/llama.cpp/build/bin/llama-server"
MODEL_NAME="mistral-7b"
BASE_PORT=8080
CONTEXT_SIZE=4096
THREADS=8
```

**💡 Tip:** Usa rutas absolutas (que empiecen con `/`), no relativas.

### Paso 3: Probar configuración

```bash
./scripts/test_setup.sh
```

Deberías ver:
```
✓ Pasados: 15
✗ Fallados: 0
✅ TODOS LOS TESTS PASARON
```

**Si hay tests fallados:**
- Revisa los mensajes de error
- Verifica las rutas en `model_config.env`
- Asegúrate que el modelo y llama-server existen

### Paso 4A: Iniciar single agent (recomendado para empezar)

```bash
./scripts/start_single_agent.sh
```

Espera hasta ver:
```
✅ SINGLE AGENT INICIADO CORRECTAMENTE

Endpoints:
  Health: http://127.0.0.1:8080/health
  Chat: http://127.0.0.1:8080/v1/chat/completions
```

**Prueba rápida:**

```bash
# En otra terminal
curl http://127.0.0.1:8080/health
# Debe responder: {"status":"ok"}

curl -X POST http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-model",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
# Debe responder con JSON que incluye "choices"
```

### Paso 4B: Iniciar multi-agente (alternativa avanzada)

```bash
./scripts/start_multi_agent.sh
```

Esto inicia **3 llama-servers** en paralelo:
- **Daneel** (puerto 8080) - Estratega
- **Dors** (puerto 8081) - Protectora
- **Giskard** (puerto 8082) - Filósofo

**⚠️ Nota:** Multi-agente requiere ~16GB RAM y consume más CPU.

### Paso 5: Instalar OpenClaw (si aún no lo tienes)

```bash
# Opción A: npm (recomendado)
npm install -g openclaw

# Opción B: desde el repositorio
cd /ruta/a/openclaw
npm install
npm run build
npm link

# Verificar instalación
openclaw --version
```

### Paso 6: Iniciar OpenClaw Gateway

```bash
# En una nueva terminal
openclaw start
```

Deberías ver:
```
✓ Gateway started on http://localhost:3000
✓ Using config from ~/.openclaw/openclaw.json
```

### Paso 7: Abrir Dashboard

Abre tu navegador en:
```
http://localhost:3000
```

Deberías ver el dashboard de OpenClaw con:
- **Estado del gateway**: Online
- **Modelos disponibles**: Tu modelo local
- **Agentes configurados**: default (o daneel/dors/giskard si usaste multi-agent)

## ✅ Verificación Final

### Test completo

```bash
# Verificar llama-server
curl http://127.0.0.1:8080/health

# Verificar OpenClaw
curl http://localhost:3000/api/health

# Verificar agentes
openclaw agents list
```

### Hacer una prueba

Desde el dashboard o CLI:

```bash
openclaw message "Hola, ¿cómo estás?"
```

Si recibes una respuesta, **¡todo funciona!** 🎉

## 🛑 Detener todo

```bash
# Detener llama-servers y OpenClaw
./scripts/stop_all.sh

# O manualmente
pkill llama-server
pkill openclaw
```

## 🔧 Problemas comunes

### "Puerto 8080 ya está en uso"

```bash
# Ver qué proceso lo usa
lsof -i :8080

# Matar el proceso
kill -9 <PID>

# O cambiar puerto en model_config.env
BASE_PORT=8090
```

### "llama-server no respondió a tiempo"

```bash
# Ver el log
tail -f ~/.openclaw/logs/llama-server-*.log

# Posibles causas:
# - Modelo corrupto → Re-descarga el modelo
# - Sin RAM suficiente → Reduce CONTEXT_SIZE
# - Modelo muy grande → Usa un modelo más pequeño (Q4 en lugar de Q6)
```

### "OpenClaw no encuentra el modelo"

```bash
# Verificar configuración
cat ~/.openclaw/openclaw.json

# Debe tener algo como:
# "baseUrl": "http://127.0.0.1:8080/v1"

# Re-generar configuración
./scripts/start_single_agent.sh
```

### "Respuestas muy lentas"

```bash
# Opciones:
# 1. Aumentar threads en model_config.env
THREADS=16  # Usa más cores de CPU

# 2. Usar modelo más pequeño
# Q6 → Q5 → Q4 → Q3  (menor calidad, mayor velocidad)

# 3. Reducir contexto
CONTEXT_SIZE=2048  # En lugar de 4096
```

## 📈 Siguientes pasos

### 1. Conectar canales

Configura WhatsApp, Telegram, Discord para hablar con tu agente:
- Ver: `docs/CONFIGURACION_AVANZADA.md`

### 2. Personalizar el agente

Edita el workspace para cambiar la personalidad:
- `~/.openclaw/workspace-*/SOUL.md` → Personalidad base
- `~/.openclaw/workspace-*/AGENTS.md` → Comportamientos

### 3. Experimentar con otros modelos

Cambia el modelo en `model_config.env` y reinicia:
```bash
./scripts/stop_all.sh
# Editar MODEL_PATH
./scripts/start_single_agent.sh
```

### 4. Explorar multi-agente

Prueba el setup de 3 agentes:
```bash
./scripts/start_multi_agent.sh
```

## 💡 Tips Pro

### Monitoreo en tiempo real

```bash
# Ver logs de llama-server
tail -f ~/.openclaw/logs/llama-server-*.log

# Ver logs de OpenClaw
tail -f ~/.openclaw/logs/gateway.log

# Ver uso de recursos
htop  # o top en macOS
```

### Scripts útiles

```bash
# Status rápido
openclaw status

# Ver agentes
openclaw agents list

# Ver sesiones activas
openclaw sessions list

# Ver configuración
openclaw config show
```

### Backup de tu configuración

```bash
# Backup completo
tar -czf openclaw-backup-$(date +%Y%m%d).tar.gz ~/.openclaw/

# Restore
tar -xzf openclaw-backup-YYYYMMDD.tar.gz -C ~
```

## 🆘 ¿Necesitas ayuda?

1. **Documentación completa**: `docs/`
2. **Troubleshooting**: `docs/TROUBLESHOOTING.md`
3. **FAQ**: `docs/FAQ.md`
4. **Issues**: GitHub del proyecto
5. **Discord**: Comunidad OpenClaw

---

**¡Felicidades!** 🎉 Ya tienes OpenClaw funcionando con tu modelo local.

[⬆️ Volver al README principal](../README.md)
