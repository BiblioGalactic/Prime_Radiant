# ❓ Preguntas Frecuentes (FAQ)

## General

### ¿Qué es este "Modificador"?

Es un paquete completo que te permite usar **OpenClaw con modelos locales** (llama.cpp) en lugar de la API de Claude. Incluye scripts automatizados, configuraciones listas, y soporte para múltiples agentes con personalidades diferentes.

### ¿Necesito saber programar?

No para el uso básico. Los scripts están automatizados. Solo necesitas:
1. Editar un archivo de configuración (rutas de archivos)
2. Ejecutar scripts bash
3. Usar la terminal

### ¿Es gratis?

Sí, completamente. Los modelos open-source son gratis, llama.cpp es open-source, y OpenClaw también.

### ¿Necesito GPU?

No es necesario, pero ayuda. llama.cpp puede usar:
- **CPU only**: Funciona, pero más lento
- **Apple Silicon** (M1/M2/M3): Usa Metal, muy rápido
- **NVIDIA GPU**: Usa CUDA, el más rápido
- **AMD GPU**: Usa ROCm, soporte limitado

## Instalación

### ¿Dónde consigo los modelos?

En [Hugging Face](https://huggingface.co/models?library=gguf):

**Modelos recomendados:**
- [Mistral 7B Instruct](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF)
- [Llama 2 7B Chat](https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF)
- [Qwen 1.5 7B Chat](https://huggingface.co/Qwen/Qwen1.5-7B-Chat-GGUF)

### ¿Qué es Q4, Q5, Q6?

Son niveles de **cuantización** (compresión):
- **Q2/Q3**: Muy comprimido, calidad baja, para testing
- **Q4**: Buen balance, calidad aceptable, rápido
- **Q5**: Mejor calidad, un poco más lento
- **Q6**: Casi sin pérdida de calidad, más lento
- **Q8/F16**: Máxima calidad, muy lento

**Recomendación:** Empieza con Q5_K_M o Q6_K.

### ¿Cuánto RAM necesito?

Depende del modelo y cuantización:

| Modelo | Q4 | Q5 | Q6 |
|--------|----|----|-----|
| 7B | ~4GB | ~5GB | ~6GB |
| 13B | ~7GB | ~9GB | ~11GB |
| 33B | ~18GB | ~22GB | ~26GB |

**Recomendación:**
- Single agent: 8GB RAM mínimo (16GB recomendado)
- Multi-agent (3x): 16GB RAM mínimo (32GB recomendado)

### ¿Puedo usar Windows?

Sí, pero con **WSL2** (Windows Subsystem for Linux):
1. Instala WSL2: `wsl --install`
2. Instala Ubuntu en WSL2
3. Sigue la guía de Linux

Alternativas:
- Docker Desktop con Linux containers
- MSYS2/MinGW (más complicado)

## Configuración

### ¿Dónde está el archivo de configuración principal?

Hay dos niveles:

1. **Del Modificador**: `configs/model_config.env`
   - Configuras rutas, puertos, threads

2. **De OpenClaw**: `~/.openclaw/openclaw.json`
   - Se genera automáticamente
   - Puedes editarlo manualmente si quieres

### ¿Puedo usar varios modelos a la vez?

Sí, en multi-agent. Cada agente puede usar un modelo diferente:

```bash
# En configs/multi_agent.json
"providers": {
  "daneel-local": {
    "baseUrl": "http://127.0.0.1:8080/v1"  # Mistral 7B
  },
  "dors-local": {
    "baseUrl": "http://127.0.0.1:8081/v1"  # Llama 2 7B
  },
  "giskard-local": {
    "baseUrl": "http://127.0.0.1:8082/v1"  # Qwen 7B
  }
}
```

Luego inicia cada llama-server con su modelo correspondiente.

### ¿Cómo cambio la personalidad de un agente?

Edita el workspace:

```bash
# Abrir el archivo SOUL.md del agente
nano ~/.openclaw/workspace-daneel/SOUL.md

# Cambiar el contenido
# Guardar y reiniciar OpenClaw
openclaw restart
```

El sistema prompt se regenera automáticamente.

## Uso

### ¿Cómo hablo con el agente?

Tres formas:

1. **Dashboard web**: http://localhost:3000
2. **CLI**: `openclaw message "Hola"`
3. **Canales** (WhatsApp/Telegram/Discord): Requiere configuración adicional

### ¿Las respuestas son privadas?

**Sí, 100% local** si:
- Usas modelos locales (llama.cpp)
- No configuras fallback a Claude API
- No expones puertos a internet

Todo queda en tu máquina. Verificación:
```bash
netstat -an | grep ESTABLISHED | grep -v "127.0.0.1"
# No deberías ver conexiones salientes
```

### ¿Por qué las respuestas son lentas?

Varias razones posibles:

1. **Primer request**: El modelo se carga en RAM
   - Solución: Pre-warm haciendo requests dummy

2. **Modelo muy grande**: Q6/Q8 son más lentos
   - Solución: Usa Q4 o Q5

3. **Pocos threads**: Solo usando 1-2 cores
   - Solución: Aumenta `THREADS` en config

4. **Poca RAM**: Sistema haciendo swap
   - Solución: Cierra programas, usa modelo más pequeño

5. **Sin GPU**: CPU-only es más lento
   - Solución: Compila llama.cpp con soporte GPU

### ¿Cómo mejoro la velocidad?

**Hardware:**
- Más RAM → Modelos más grandes
- Más CPU cores → Más threads
- GPU → Compilar con CUDA/Metal

**Software:**
- Usar Q4 en lugar de Q6
- Reducir `CONTEXT_SIZE` (4096 → 2048)
- Aumentar `THREADS` (8 → 16)
- Compilar llama.cpp optimizado

**Ejemplo config rápida:**
```bash
CONTEXT_SIZE=2048
THREADS=16
MODEL_PATH="/path/to/model-Q4_K_M.gguf"
```

### ¿Puedo usar múltiples usuarios a la vez?

Sí, OpenClaw maneja sesiones independientes. Cada usuario tiene:
- Su propia conversación
- Su propio contexto
- Su propia memoria (si está habilitada)

llama.cpp procesa requests secuencialmente (uno a la vez), pero OpenClaw puede encolar múltiples requests.

## Multi-Agente

### ¿Qué significa "multi-agente"?

3 llama-servers corriendo **en paralelo**, cada uno con:
- Su propio modelo (o el mismo modelo)
- Su propia personalidad (workspace diferente)
- Su propio puerto

OpenClaw enruta mensajes según canal:
- WhatsApp → Daneel
- Telegram → Dors
- Discord → Giskard

### ¿Necesito 3 modelos diferentes?

No, puedes usar el **mismo modelo** 3 veces:
- Mismo archivo .gguf
- 3 procesos llama-server diferentes
- 3 puertos diferentes
- 3 workspaces diferentes (personalidades)

### ¿Los agentes se hablan entre sí?

No en esta implementación. Cada agente trabaja independiente.

Para que colaboren, necesitarías:
- Lógica custom en OpenClaw
- Sistema de mensajería inter-agente
- Coordinador central

(Esto está fuera del scope del Modificador, pero es posible)

### ¿Cuál es la diferencia entre los agentes?

| Agente | Personalidad | Especialidad | Canal |
|--------|--------------|--------------|--------|
| Daneel | Estratega sereno | Análisis, planificación | WhatsApp |
| Dors | Protectora maternal | Seguridad, validación | Telegram |
| Giskard | Filósofo dubitativo | Ética, reflexión | Discord |

Pero puedes **personalizarlos** editando sus SOUL.md.

## Problemas Comunes

### "Port already in use"

```bash
# Ver qué usa el puerto
lsof -i :8080

# Matar el proceso
kill -9 <PID>

# O cambiar puerto
# Editar BASE_PORT en model_config.env
```

### "llama-server not found"

```bash
# Verificar ruta
ls -la ~/llama.cpp/build/bin/llama-server

# Si no existe, compilar llama.cpp
cd ~/llama.cpp
make

# Verificar nuevamente
./build/bin/llama-server --help
```

### "Model failed to load"

Posibles causas:
1. **Modelo corrupto**: Re-descarga
2. **Formato incorrecto**: Debe ser .gguf (no .bin)
3. **Ruta incorrecta**: Usa ruta absoluta, no relativa
4. **Sin RAM**: Cierra programas, usa modelo más pequeño

```bash
# Verificar tamaño del modelo
ls -lh /path/to/model.gguf

# Verificar RAM disponible
free -h  # Linux
vm_stat  # macOS

# Intentar modelo más pequeño (Q4)
```

### "OpenClaw can't connect to llama-server"

```bash
# 1. Verificar que llama-server está corriendo
curl http://127.0.0.1:8080/health

# 2. Verificar configuración de OpenClaw
cat ~/.openclaw/openclaw.json | grep baseUrl
# Debe ser: "http://127.0.0.1:8080/v1"

# 3. Verificar logs
tail -f ~/.openclaw/logs/llama-server-*.log
```

## Avanzado

### ¿Puedo exponer esto a internet?

**No recomendado** sin:
1. Autenticación (API keys)
2. Rate limiting
3. HTTPS/TLS
4. Firewall rules

Si lo necesitas:
- Usa nginx como reverse proxy
- Implementa OAuth o JWT
- Configura Cloudflare o similar
- Monitorea abuse

### ¿Puedo usar esto en Docker?

Sí, pero requiere configuración adicional:

```dockerfile
FROM ubuntu:22.04
# Instalar dependencias
# Compilar llama.cpp
# Copiar modelo
# Exponer puertos
```

No incluido en este Modificador (pull requests bienvenidos).

### ¿Cómo hago backup?

```bash
# Backup completo
tar -czf backup-$(date +%Y%m%d).tar.gz \
  ~/.openclaw/ \
  ~/Modificador/configs/

# Restore
tar -xzf backup-YYYYMMDD.tar.gz -C ~
```

Importante respaldar:
- `~/.openclaw/openclaw.json` → Configuración
- `~/.openclaw/workspace-*` → Personalidades
- `~/.openclaw/agents/*/sessions/` → Historial (si lo quieres)

### ¿Puedo contribuir mejoras?

¡Sí! Pull requests bienvenidos en:
- Nuevas personalidades
- Soporte para más modelos
- Optimizaciones
- Documentación
- Traducciones

Ver `CONTRIBUTING.md`

## Soporte

### ¿Dónde pido ayuda?

1. **FAQ** (este archivo) → Preguntas comunes
2. **TROUBLESHOOTING.md** → Problemas técnicos
3. **GitHub Issues** → Bugs y feature requests
4. **Discord** → Comunidad OpenClaw
5. **Email** → Para consultas privadas

### ¿Cómo reporto un bug?

Abre un issue en GitHub con:
1. **Descripción** del problema
2. **Pasos** para reproducir
3. **Logs** relevantes
4. **Configuración** (OS, RAM, modelo usado)
5. **Expectativa** vs realidad

Usa la plantilla de issue.

---

**¿No encontraste tu pregunta?**

- Revisa [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Abre un issue con la etiqueta `question`
- Pregunta en Discord

[⬆️ Volver al README principal](../README.md)
