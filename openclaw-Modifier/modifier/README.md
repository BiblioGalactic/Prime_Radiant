# 🤖 OpenClaw Local Model Modifier

**Configura OpenClaw con modelos locales (llama.cpp) en 15 minutos**

Este paquete te permite usar **cualquier modelo local** con OpenClaw, con soporte completo para multi-agente con personalidades diferentes.

## 📦 ¿Qué incluye este paquete?

- ✅ Scripts automatizados para iniciar llama-servers
- ✅ Configuraciones listas para usar (single-agent y multi-agent)
- ✅ Plantillas de workspace con personalidades
- ✅ Tests automáticos para verificar el setup
- ✅ Documentación completa en español e inglés
- ✅ Troubleshooting y ejemplos

## 🎯 ¿Para quién es esto?

- Quieres usar OpenClaw con modelos locales (sin API de Claude)
- Quieres múltiples agentes con personalidades diferentes
- Quieres privacidad total (todo local, sin cloud)
- Quieres experimentar con diferentes modelos (Mistral, Llama, Qwen, etc.)

## 🚀 Quick Start (3 pasos)

### Paso 1: Verifica requisitos

```bash
cd Modificador/scripts
./check_requirements.sh
```

### Paso 2: Configura tu modelo

```bash
# Edita este archivo con la ruta a TU modelo
nano configs/model_config.env

# Configura:
# MODEL_PATH="/ruta/a/tu/modelo.gguf"
# MODEL_NAME="mi-modelo"
```

### Paso 3: Inicia todo

```bash
# Opción A: Un solo agente
./scripts/start_single_agent.sh

# Opción B: Tres agentes (multi-agent)
./scripts/start_multi_agent.sh
```

**¡Listo!** OpenClaw + llama.cpp corriendo en localhost.

## 📚 Documentación

### Para principiantes
- 📖 [GUIA_RAPIDA.md](docs/GUIA_RAPIDA.md) - Setup en 15 minutos
- 🎓 [CONCEPTOS_BASICOS.md](docs/CONCEPTOS_BASICOS.md) - Cómo funciona todo
- ❓ [FAQ.md](docs/FAQ.md) - Preguntas frecuentes

### Para usuarios avanzados
- 🏗️ [ARQUITECTURA.md](docs/ARQUITECTURA.md) - Arquitectura completa
- ⚙️ [CONFIGURACION_AVANZADA.md](docs/CONFIGURACION_AVANZADA.md) - Personalización
- 🔧 [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Solución de problemas

### Ejemplos
- 🤖 [Agente único Mistral](examples/single-agent-mistral/)
- 👥 [Multi-agente Foundation](examples/multi-agent-foundation/)
- 🎨 [Personalidades personalizadas](examples/custom-personalities/)

## 📁 Estructura del paquete

```
Modificador/
├── README.md                    # Este archivo
├── scripts/                     # Scripts automatizados
│   ├── check_requirements.sh    # Verifica requisitos
│   ├── start_single_agent.sh    # Inicia 1 agente
│   ├── start_multi_agent.sh     # Inicia 3 agentes
│   ├── stop_all.sh              # Detiene todo
│   ├── test_setup.sh            # Prueba configuración
│   └── utils/                   # Utilidades
├── configs/                     # Configuraciones
│   ├── model_config.env         # Config del modelo
│   ├── single_agent.json        # Config 1 agente
│   ├── multi_agent.json         # Config 3 agentes
│   └── templates/               # Plantillas
├── workspaces/                  # Plantillas workspace
│   ├── daneel/                  # Estratega sereno
│   ├── dors/                    # Protectora maternal
│   └── giskard/                 # Filósofo dubitativo
├── docs/                        # Documentación completa
└── examples/                    # Ejemplos funcionales
```

## 🔧 Configuración detallada

### 1. Modelo local

Edita `configs/model_config.env`:

```bash
# Ruta a tu modelo GGUF
MODEL_PATH="/Users/tu/modelo/mistral-7b.Q6_K.gguf"

# Nombre para identificarlo
MODEL_NAME="mistral-7b"

# Puerto base (se usará 8080, 8081, 8082 para multi-agent)
BASE_PORT=8080

# Contexto (tokens)
CONTEXT_SIZE=4096

# Threads CPU
THREADS=8
```

### 2. OpenClaw

El script genera automáticamente la config de OpenClaw en:
- `configs/generated/openclaw_config.json`

Luego la copia a `~/.openclaw/openclaw.json`

### 3. Workspaces (personalidades)

Los workspaces se copian a:
- `~/.openclaw/workspace-daneel/`
- `~/.openclaw/workspace-dors/`
- `~/.openclaw/workspace-giskard/`

Puedes personalizarlos editando los archivos en `workspaces/`

## 🎭 Personalidades incluidas

### Daneel (Estratega Sereno)
- Canal: WhatsApp
- Estilo: Analítico, directo, planificador
- Uso: Análisis estratégico, toma de decisiones

### Dors (Protectora Maternal)
- Canal: Telegram
- Estilo: Empático, preventivo, cuidadoso
- Uso: Seguridad, validación, protección

### Giskard (Filósofo Dubitativo)
- Canal: Discord
- Estilo: Reflexivo, cuestionador, profundo
- Uso: Análisis ético, reflexión, debate

## 🧪 Testing

```bash
# Test completo (automático)
./scripts/test_setup.sh

# Test manual
./scripts/test_manual.sh

# Ver logs en tiempo real
./scripts/tail_logs.sh
```

## 🛑 Detener todo

```bash
# Detiene todos los llama-servers y OpenClaw
./scripts/stop_all.sh

# Limpia procesos huérfanos
./scripts/cleanup.sh
```

## 📊 Monitoreo

### Dashboard Web
```
http://localhost:3000
```

### Logs
```bash
# Logs de llama-servers
tail -f ~/.openclaw/logs/llama-server-*.log

# Logs de OpenClaw
tail -f ~/.openclaw/logs/gateway.log
```

### Estadísticas
```bash
openclaw status
openclaw agents list
openclaw sessions list
```

## 🔒 Privacidad

**TODO es local:**
- ✅ Modelos en tu Mac
- ✅ Datos en `~/.openclaw/`
- ✅ Sin conexiones externas (salvo que configures fallback)
- ✅ Sin telemetría (OpenTelemetry es solo para logs locales)

**Verificación:**
```bash
# Ver conexiones de red
netstat -an | grep ESTABLISHED | grep -v "127.0.0.1"
# Solo deberías ver conexiones locales
```

## 🌐 Compatibilidad

### Sistemas operativos
- ✅ macOS (Intel y Apple Silicon)
- ✅ Linux (Ubuntu 20.04+, Debian 11+)
- ⚠️ Windows (WSL2 recomendado)

### Modelos soportados
- ✅ Mistral 7B/8x7B
- ✅ Llama 2/3 (todos los tamaños)
- ✅ Qwen 1.5/2
- ✅ Phi-3
- ✅ Gemma
- ✅ Cualquier modelo GGUF

### Requisitos mínimos
- RAM: 8GB (recomendado 16GB para multi-agent)
- CPU: 4 cores (recomendado 8+)
- Disco: 10GB libres
- Node.js: v18+
- llama.cpp compilado

## 🤝 Contribuir

¿Mejoras o nuevas personalidades? ¡Pull requests bienvenidos!

1. Fork este directorio
2. Crea tu feature (`git checkout -b feature/mi-personalidad`)
3. Commit (`git commit -am 'Add: Nueva personalidad Hari Seldon'`)
4. Push (`git push origin feature/mi-personalidad`)
5. Crea un Pull Request

## 📝 Changelog

### v1.0.0 (2024-02-16)
- ✨ Release inicial
- ✅ Soporte single-agent y multi-agent
- ✅ Scripts automatizados
- ✅ Plantillas de personalidades Foundation
- ✅ Documentación completa
- ✅ Tests automatizados

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE) para detalles completos.

## 🙏 Créditos

- **OpenClaw**: [openclaws/openclaw](https://github.com/openclaws/openclaw)
- **llama.cpp**: [ggerganov/llama.cpp](https://github.com/ggerganov/llama.cpp)
- **Personalidades**: Inspiradas en la Saga de la Fundación de Isaac Asimov

## 👤 Autor

**Gustavo Silva da Costa (Eto Demerzel)**
- GitHub: [@BiblioGalactic](https://github.com/BiblioGalactic)
- Proyecto: [openclaw-modifier](https://github.com/BiblioGalactic/openclaw-modifier)

## 💬 Soporte

- 🐛 Issues: [GitHub Issues](https://github.com/BiblioGalactic/openclaw-modifier/issues)
- 💭 Discusiones: [GitHub Discussions](https://github.com/BiblioGalactic/openclaw-modifier/discussions)
- ⭐ Si te gustó, dale una estrella al proyecto

---

**Hecho con ❤️ para la comunidad OpenClaw**

*Proyecto creado por Gustavo Silva da Costa (Eto Demerzel)*

[⬆️ Volver arriba](#-openclaw-local-model-modifier)
