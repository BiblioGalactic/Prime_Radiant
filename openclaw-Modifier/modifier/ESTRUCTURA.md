# 📂 Estructura del Proyecto

Descripción detallada de cada archivo y directorio del Modificador.

## 🗂️ Estructura Completa

```
Modificador/
├── README.md                      # Documentación principal
├── INSTALL.md                     # Guía de instalación completa
├── ESTRUCTURA.md                  # Este archivo
├── CHANGELOG.md                   # Historial de versiones
├── LICENSE                        # Licencia MIT
│
├── scripts/                       # Scripts automatizados
│   ├── check_requirements.sh      # ✅ Verificador de requisitos
│   ├── start_single_agent.sh      # 🚀 Iniciar 1 agente
│   ├── start_multi_agent.sh       # 🚀 Iniciar 3 agentes
│   ├── stop_all.sh                # 🛑 Detener todos los servicios
│   ├── test_setup.sh              # 🧪 Tests automatizados
│   └── utils/                     # Utilidades compartidas
│       └── common.sh              # Funciones comunes
│
├── configs/                       # Configuraciones
│   ├── model_config.env           # ⚙️ Config principal del modelo
│   ├── model_config.env.example   # Plantilla de ejemplo
│   ├── single_agent.json          # Config OpenClaw 1 agente
│   ├── multi_agent.json           # Config OpenClaw 3 agentes
│   ├── generated/                 # Configs auto-generadas
│   └── templates/                 # Plantillas adicionales
│
├── workspaces/                    # Personalidades de agentes
│   ├── default/                   # Agente genérico
│   │   └── SOUL.md                # Personalidad base
│   ├── daneel/                    # Estratega Sereno
│   │   ├── SOUL.md                # Personalidad principal
│   │   ├── AGENTS.md              # Instrucciones de comportamiento
│   │   └── memory/                # Memoria (si está habilitada)
│   ├── dors/                      # Protectora Maternal
│   │   ├── SOUL.md
│   │   └── AGENTS.md
│   └── giskard/                   # Filósofo Dubitativo
│       ├── SOUL.md
│       └── AGENTS.md
│
├── docs/                          # Documentación
│   ├── GUIA_RAPIDA.md             # Setup en 15 minutos
│   ├── CONCEPTOS_BASICOS.md       # Explicación de conceptos
│   ├── FAQ.md                     # Preguntas frecuentes
│   ├── TROUBLESHOOTING.md         # Solución de problemas
│   ├── QUE_FUNCIONA.md            # Estado de testing
│   ├── ARQUITECTURA.md            # Arquitectura detallada
│   ├── CONFIGURACION_AVANZADA.md  # Opciones avanzadas
│   └── API.md                     # Referencia de API
│
├── examples/                      # Ejemplos funcionales
│   ├── single-agent-mistral/      # Ejemplo 1 agente
│   │   ├── README.md
│   │   └── config.json
│   ├── multi-agent-foundation/    # Ejemplo 3 agentes
│   │   ├── README.md
│   │   └── config.json
│   └── custom-personalities/      # Personalidades custom
│       └── README.md
│
└── tests/                         # Tests adicionales
    ├── integration/               # Tests de integración
    └── unit/                      # Tests unitarios
```

## 📄 Descripción de Archivos Clave

### 📘 Documentación

#### `README.md`
- **Propósito**: Entrada principal al proyecto
- **Contenido**: Overview, quick start, links a docs
- **Audiencia**: Todos los usuarios
- **Longitud**: ~300 líneas

#### `INSTALL.md`
- **Propósito**: Guía de instalación paso a paso
- **Contenido**: Desde cero hasta running
- **Audiencia**: Nuevos usuarios
- **Longitud**: ~500 líneas

#### `docs/GUIA_RAPIDA.md`
- **Propósito**: Setup en 15 minutos
- **Contenido**: 7 pasos para estar funcionando
- **Audiencia**: Usuarios con experiencia técnica
- **Longitud**: ~400 líneas

#### `docs/FAQ.md`
- **Propósito**: Preguntas frecuentes
- **Contenido**: 40+ preguntas con respuestas
- **Audiencia**: Todos
- **Longitud**: ~600 líneas

### 🔧 Scripts

#### `scripts/check_requirements.sh`
- **Función**: Verifica requisitos del sistema
- **Valida**:
  - Comandos necesarios (bash, curl, node)
  - Versiones correctas
  - llama.cpp instalado
  - Modelo descargado
  - Puertos disponibles
  - Permisos correctos
- **Salida**: ✅/❌ con detalles
- **Uso**: `./scripts/check_requirements.sh`

#### `scripts/start_single_agent.sh`
- **Función**: Inicia 1 llama-server + configura OpenClaw
- **Hace**:
  1. Valida configuración
  2. Inicia llama-server en background
  3. Espera a que esté ready
  4. Prueba health checks
  5. Copia workspace
  6. Genera config de OpenClaw
- **Salida**: Endpoints y comandos siguientes
- **Uso**: `./scripts/start_single_agent.sh`

#### `scripts/start_multi_agent.sh`
- **Función**: Inicia 3 llama-servers en paralelo
- **Hace**:
  1. Valida configuración
  2. Inicia 3 llama-servers (puertos 8080-8082)
  3. Espera a que todos estén ready
  4. Prueba cada uno
  5. Copia 3 workspaces
  6. Genera config multi-agent
- **Salida**: Info de los 3 agentes
- **Uso**: `./scripts/start_multi_agent.sh`

#### `scripts/stop_all.sh`
- **Función**: Detiene todos los servicios
- **Hace**:
  1. Lee PIDs guardados
  2. Mata procesos gracefully
  3. Busca procesos huérfanos
  4. Limpia archivos temporales
- **Uso**: `./scripts/stop_all.sh`

#### `scripts/test_setup.sh`
- **Función**: Tests automatizados
- **Prueba**:
  - Requisitos del sistema
  - Archivos de configuración
  - Workspaces existen
  - Puertos disponibles
  - Scripts ejecutables
  - llama-servers running (si están)
- **Salida**: N/M tests pasados
- **Uso**: `./scripts/test_setup.sh`

### ⚙️ Configuraciones

#### `configs/model_config.env`
- **Propósito**: Configuración principal
- **Variables clave**:
  - `MODEL_PATH`: Ruta al .gguf
  - `LLAMA_BIN`: Ruta a llama-server
  - `MODEL_NAME`: Identificador
  - `BASE_PORT`: Puerto inicial
  - `CONTEXT_SIZE`: Tamaño de contexto
  - `THREADS`: Threads de CPU
- **Formato**: Shell environment vars
- **Debe editarse**: Sí, obligatorio

#### `configs/single_agent.json`
- **Propósito**: Config OpenClaw para 1 agente
- **Contiene**:
  - 1 provider (OpenAI-compatible)
  - 1 agent (default)
  - Gateway settings
  - Logging config
- **Variables**: `{{MODEL_NAME}}`, `{{BASE_PORT}}`
- **Se copia a**: `~/.openclaw/openclaw.json`

#### `configs/multi_agent.json`
- **Propósito**: Config OpenClaw para 3 agentes
- **Contiene**:
  - 3 providers (puertos 8080-8082)
  - 3 agents (daneel, dors, giskard)
  - Bindings (WhatsApp→daneel, etc.)
  - Gateway settings
- **Se copia a**: `~/.openclaw/openclaw.json`

### 🤖 Workspaces

#### `workspaces/*/SOUL.md`
- **Propósito**: Personalidad base del agente
- **Se inyecta**: Como system prompt
- **Contenido**:
  - Identidad del agente
  - Estilo de pensamiento
  - Comunicación
  - Expertise
  - Frases características
- **Longitud**: ~200-500 líneas
- **Editable**: Sí, personalizable

#### `workspaces/daneel/SOUL.md`
- **Personalidad**: Estratega Sereno
- **Inspiración**: Daneel Olivaw (Asimov)
- **Características**:
  - Piensa en siglos
  - Analítico y lógico
  - Planificador estratégico
  - Sereno bajo presión
- **Especialización**: Análisis estratégico

#### `workspaces/dors/SOUL.md`
- **Personalidad**: Protectora Maternal
- **Inspiración**: Dors Venabili (Asimov)
- **Características**:
  - Instinto protector
  - Preventiva y cautelosa
  - Vigilante constante
  - Valida seguridad
- **Especialización**: Análisis de riesgos

#### `workspaces/giskard/SOUL.md`
- **Personalidad**: Filósofo Dubitativo
- **Inspiración**: Giskard Reventlov (Asimov)
- **Características**:
  - Cuestiona suposiciones
  - Socrático y reflexivo
  - Explora paradojas
  - Profundidad ética
- **Especialización**: Filosofía aplicada

## 🔀 Flujo de Datos

### Inicialización

```
Usuario ejecuta script
  ↓
Script lee model_config.env
  ↓
Valida configuración
  ↓
Inicia llama-server(s)
  ↓
Espera health checks
  ↓
Copia workspace(s) a ~/.openclaw/
  ↓
Genera openclaw.json desde plantilla
  ↓
Listo para usar
```

### Runtime (Single Agent)

```
Usuario → OpenClaw Gateway (localhost:3000)
             ↓
       Lee openclaw.json
             ↓
       Identifica provider: "local"
             ↓
       Lee workspace: ~/.openclaw/workspace-default/
             ↓
       Construye prompt: SOUL.md + mensaje
             ↓
       HTTP POST → llama-server (localhost:8080)
             ↓
       llama-server procesa con modelo
             ↓
       Respuesta ← llama-server
             ↓
       Respuesta → Usuario
             ↓
       Guarda sesión (opcional)
```

### Runtime (Multi-Agent)

```
Usuario → OpenClaw Gateway
             ↓
       Identifica canal (WhatsApp/Telegram/Discord)
             ↓
       Routing por bindings:
         - WhatsApp → daneel (8080)
         - Telegram → dors (8081)
         - Discord → giskard (8082)
             ↓
       Lee workspace específico
             ↓
       Construye prompt con SOUL.md del agente
             ↓
       HTTP POST → llama-server correspondiente
             ↓
       Respuesta procesada
             ↓
       Respuesta → Usuario vía canal original
```

## 📊 Tamaños de Archivos

### Scripts
- `check_requirements.sh`: ~8KB (~250 líneas)
- `start_single_agent.sh`: ~12KB (~350 líneas)
- `start_multi_agent.sh`: ~15KB (~450 líneas)
- `stop_all.sh`: ~3KB (~90 líneas)
- `test_setup.sh`: ~10KB (~300 líneas)

### Configuraciones
- `model_config.env`: ~2KB (~60 líneas)
- `single_agent.json`: ~500B (~20 líneas)
- `multi_agent.json`: ~1.5KB (~60 líneas)

### Workspaces
- `default/SOUL.md`: ~2KB (~60 líneas)
- `daneel/SOUL.md`: ~8KB (~250 líneas)
- `dors/SOUL.md`: ~7KB (~230 líneas)
- `giskard/SOUL.md`: ~8KB (~260 líneas)

### Documentación
- `README.md`: ~15KB (~300 líneas)
- `INSTALL.md`: ~25KB (~500 líneas)
- `GUIA_RAPIDA.md`: ~20KB (~400 líneas)
- `FAQ.md`: ~30KB (~600 líneas)

### Total
- **Scripts**: ~50KB
- **Configs**: ~5KB
- **Workspaces**: ~30KB
- **Docs**: ~100KB
- **TOTAL**: ~200KB (sin node_modules ni modelos)

## 🎯 Archivos que Debes Editar

### Obligatorio
1. `configs/model_config.env` → Rutas a tu sistema

### Opcional (personalización)
2. `workspaces/*/SOUL.md` → Cambiar personalidades
3. `configs/*_agent.json` → Ajustar configuración avanzada

### NO edites (auto-generados)
- `configs/generated/*`
- `~/.openclaw/openclaw.json` (se sobreescribe)

## 🔒 Archivos Sensibles

### Nunca versionar
- `~/.openclaw/credentials/` → Tokens OAuth
- `~/.openclaw/*.key` → Keys privadas
- `.env` con API keys

### OK versionar
- `configs/model_config.env` (sin secrets)
- `workspaces/*/SOUL.md`
- Scripts

## 📦 Dependencias

### Scripts
- `bash` 4.0+
- `curl`
- `lsof`
- `grep`, `sed`, `awk`
- `jq` (opcional)

### Runtime
- `llama.cpp` (llama-server)
- `node` 18+
- `openclaw`

### Modelos
- Archivos `.gguf` (5-30GB c/u)
- Descargados por el usuario

## 🗺️ Roadmap de Archivos

### v1.0 (Actual)
- ✅ Scripts básicos
- ✅ 3 personalidades
- ✅ Docs principales
- ✅ Configs single/multi

### v1.1 (Próximo)
- 🔜 Docker support
- 🔜 systemd services
- 🔜 Auto-update script
- 🔜 Más personalidades

### v2.0 (Futuro)
- 🔮 Web UI para config
- 🔮 Metrics dashboard
- 🔮 Plugin system
- 🔮 Cloud sync opcional

---

[⬆️ Volver al README principal](README.md)
