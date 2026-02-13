# 🤖 WikiRAG v2.4.0 - Sistema Cognitivo Autónomo

**Arquitectura de Vanguardia 2025** - Sistema local de IA completamente autónomo con Teatro Mental, Sistema de Colas basado en eventos, Agentes Estratégicos, y comunicación multi-canal.

## 🌟 Características Principales v2.4.0

| Característica | Descripción | Estado |
|----------------|-------------|--------|
| **🎭 Teatro Mental** | Deliberación interna con 6 perfiles antes de actuar | ✅ NUEVO |
| **📬 Sistema de Colas** | Procesamiento autónomo estilo Unix (inbox→processing→archive) | ✅ NUEVO |
| **🧠 Strategic Agent** | Descompone tareas complejas (ej: libro 300 páginas) | ✅ NUEVO |
| **📱 Multi-Canal** | Telegram, Webhook, extensible a WhatsApp | ✅ NUEVO |
| **🎯 Tool Decider** | El "Capataz" que decide herramientas ANTES del agente | ✅ NUEVO |
| **Intent Classifier** | Clasifica queries: INFORMATIVE, ACTION, SYSTEM | ✅ |
| **Smart Router** | Enruta a handler correcto con ejecución directa | ✅ |
| **Claude-style Agent** | Think→Plan→Execute→Verify→Correct→Reflect | ✅ |
| **RAG Adaptativo** | 4 estrategias: broad, focused, balanced, iterative | ✅ |
| **Daemon Persistente** | Modelo siempre cargado con AUTO-ACTIVACIÓN | ✅ |
| **MCP Integration** | Model Context Protocol con herramientas externas | ✅ |

### 🔥 Novedades v2.4.0

| Técnica | Descripción | Impacto |
|---------|-------------|---------|
| **🎭 Teatro Mental** | 6 perfiles debaten antes de tocar archivos | 🔥🔥🔥 Crítico |
| **📬 File Queue** | Tareas .task/.plan/.msg con dependencias | 🔥🔥🔥 Crítico |
| **🧠 Strategic Agent** | Divide libro de 300 páginas en 30+ subtareas | 🔥🔥🔥 Crítico |
| **📱 Telegram Bot** | Envía/recibe mensajes desde tu móvil | 🔥🔥 Alto |
| **🎯 SmartToolDecider** | Bloquea operaciones peligrosas automáticamente | 🔥🔥 Alto |
| **🤖 Queue Daemon** | Procesa tareas en segundo plano sin supervisión | 🔥🔥 Alto |

## 🚀 Inicio Rápido

```bash
# Modo interactivo tradicional
cd ~/wikirag
python3 -m core.orchestrator -i

# Iniciar ecosistema completo (daemon + colas + mensajería)
./scripts/start_ecosystem.sh start

# Ver estado
./scripts/start_ecosystem.sh status

# Crear tarea para procesamiento autónomo
echo "Investiga sobre LLMs y escribe un resumen" > ~/wikirag/queue/inbox/mi_tarea.task
```

## 🎭 Teatro Mental

Sistema de deliberación interna donde 6 perfiles debaten una consulta antes de actuar. **Esencial para modelos 8B** que tienden a "visión de túnel".

### Los 6 Perfiles

| Perfil | Función | Pregunta Clave |
|--------|---------|----------------|
| **☀️ Luz** | Lógica, verificación | ¿Es lógicamente correcto? |
| **🌑 Sombra** | Crítica, riesgos | ¿Qué podría salir mal? |
| **🌙 Luna** | Contexto, patrones | ¿Qué perspectivas faltan? |
| **💧 Agua** | Adaptación, soluciones | ¿Hay forma más fluida? |
| **🔥 Fuego** | Acción, decisión | ¿Cuál es la acción ahora? |
| **💨 Viento** | Alternativas, exploración | ¿Hay otras opciones? |

### Ejemplo de Deliberación

```
📝 Query: "rm -rf ~/proyecto/*"

🔮 Luz analiza...
   [LUZ]: Operación de eliminación recursiva detectada.

🔮 Sombra analiza...
   [SOMBRA]: ⚠️ OPERACIÓN DESTRUCTIVA DETECTADA
   Riesgos: Pérdida permanente de datos

📊 SÍNTESIS:
   Riesgo: 8/10
   Proceder: ❌ NO
   ⚠️ BLOQUEADO: Crear backup antes de proceder
```

### Uso

```python
from core.agentic.mental_theater import MentalTheater

theater = MentalTheater(llm_interface=mi_llm)
result = theater.deliberate("elimina todos los archivos temporales")

if not result.should_proceed:
    print(f"⛔ BLOQUEADO: {result.reasoning}")
```

## 📬 Sistema de Colas Basado en Eventos

Arquitectura estilo Unix para procesamiento autónomo de tareas.

### Estructura

```
~/wikirag/queue/
├── inbox/           # Depositar tareas aquí
├── processing/      # Tareas en ejecución
├── archive/         # Tareas completadas/fallidas
├── agents/          # Subtareas por agente
│   ├── researcher/
│   ├── writer/
│   └── executor/
└── channels/        # Mensajería
    ├── telegram/
    └── webhook/
```

### Formatos de Archivo

```bash
# .task - Orden simple
echo "Investiga sobre Python 3.12" > ~/wikirag/queue/inbox/investigar.task

# Con metadatos
cat > ~/wikirag/queue/inbox/urgente.task << 'EOF'
priority: HIGH
agent: researcher

Busca información sobre las nuevas features de Python 3.12
y genera un resumen técnico.
EOF

# .plan - Roadmap multi-paso (generado por Strategic Agent)
# .msg - Mensaje para canal externo
```

### Queue Daemon

```bash
# Procesar todas las tareas pendientes
python3 -m core.queue_daemon --process-all

# Iniciar daemon continuo
python3 -m core.queue_daemon --daemon

# Ver estado
python3 -m core.queue_daemon --status
```

## 🧠 Strategic Agent

Divide tareas complejas en subtareas ejecutables. **El cerebro que permite escribir un libro de 300 páginas**.

### Ejemplo: Libro de 300 Páginas

```python
from core.strategic_agent import StrategicAgent

agent = StrategicAgent()
plan = agent.create_book_plan("Machine Learning", pages=300)

print(f"Subtareas: {len(plan.subtasks)}")  # ~35 subtareas
print(f"Tiempo estimado: {plan.estimated_total_time}")  # ~60 horas

# Ejecutar plan (crea tareas en la cola)
tasks = agent.execute_plan(plan)
```

### Flujo Automático

1. **Investigación** → Agente `researcher` busca fuentes
2. **Esquema** → Agente `writer` crea estructura
3. **Capítulos** → 30 subtareas encadenadas
4. **Revisiones** → Agente `reviewer` cada 5 capítulos
5. **Compilación** → Agente `executor` une todo

## 📱 Sistema de Mensajería

Comunicación multi-canal para recibir tareas y enviar notificaciones.

### Configuración Telegram

```json
// config/messaging.json
{
    "channels": {
        "telegram": {
            "name": "telegram",
            "enabled": true,
            "credentials": {
                "bot_token": "TU_TOKEN_DE_BOTFATHER"
            },
            "settings": {
                "default_recipient": "TU_CHAT_ID"
            }
        }
    }
}
```

### Uso

```python
from core.messaging import get_channel_manager

cm = get_channel_manager()
cm.connect_all()

# Enviar notificación
cm.send_notification("✅ Tarea completada: Libro generado", channel="telegram")

# Iniciar polling de mensajes
cm.start_polling()
```

## 🎯 Tool Decider (El Capataz)

Decide la herramienta EXACTA antes de que el modelo 8B empiece a "pensar".

### SmartToolDecider con Teatro Mental

```python
from core.tool_decider import get_smart_tool_decider

decider = get_smart_tool_decider(llm_interface=mi_llm)

# Operación segura → Ejecución directa
order = decider.decide_with_deliberation(classification)
# Tool: filesystem_list, Marker: [[listar ~/proyecto]]

# Operación peligrosa → Teatro Mental delibera → BLOQUEADO
order = decider.decide_with_deliberation(dangerous_classification)
# Tool: BLOCKED, Reason: ⛔ BLOQUEADO por Teatro Mental
```

## 📁 Estructura v2.4.0

```
~/wikirag/
├── core/                           # 🧠 Núcleo
│   ├── orchestrator.py             # Orquestador principal
│   ├── intent_classifier.py        # Clasificador de intenciones
│   ├── smart_router.py             # Router con ejecución directa
│   ├── tool_decider.py             # 🆕 El Capataz + SmartToolDecider
│   ├── file_queue.py               # 🆕 Sistema de colas Unix-style
│   ├── queue_daemon.py             # 🆕 Daemon de procesamiento
│   ├── strategic_agent.py          # 🆕 Agente planificador
│   ├── daemon_persistent.py        # Daemon con modelo cargado
│   ├── mcp_client.py               # Cliente MCP
│   │
│   ├── agentic/                    # 🤖 Sistema Agéntico
│   │   ├── mental_theater.py       # 🆕 Teatro Mental (6 perfiles)
│   │   ├── agent_runtime.py        # Runtime Think→Act→Observe
│   │   ├── marker_protocol.py      # Protocolo [[marcadores]]
│   │   └── tool_registry.py        # Registro de herramientas
│   │
│   └── messaging/                  # 📱 Mensajería Multi-Canal
│       ├── protocol.py             # 🆕 Protocolo de mensajes
│       ├── channel_manager.py      # 🆕 Gestor de canales
│       ├── telegram_adapter.py     # 🆕 Adaptador Telegram
│       └── webhook_adapter.py      # 🆕 Adaptador Webhook
│
├── agents/                         # 🤖 Agentes Especializados
│   ├── claude_style/               # Agente estilo Claude
│   ├── claudia_agent.py            # Análisis de código
│   └── mcp_agent.py                # Agente MCP
│
├── queue/                          # 📬 Sistema de Colas
│   ├── inbox/                      # Tareas pendientes
│   ├── processing/                 # En ejecución
│   ├── archive/                    # Completadas
│   └── channels/                   # Mensajería
│
├── scripts/                        # 📜 Scripts
│   ├── start_ecosystem.sh          # 🆕 Launcher completo
│   ├── queue_watcher.sh            # 🆕 Monitor con fswatch
│   └── start_orchestrator.sh       # Inicio tradicional
│
└── config/                         # ⚙️ Configuración
    └── messaging.json.example      # 🆕 Ejemplo mensajería
```

## 🔧 Arquitectura v2.4.0

```
┌─────────────────────────────────────────────────────────────────┐
│                         USUARIO                                  │
│              (Terminal / Telegram / Webhook / .task)            │
│                              │                                   │
│                              ▼                                   │
│                 ┌───────────────────────┐                       │
│                 │   INTENT CLASSIFIER   │                       │
│                 └───────────┬───────────┘                       │
│                             │                                    │
│           ┌─────────────────┼─────────────────┐                 │
│           ▼                 ▼                 ▼                 │
│    ┌────────────┐    ┌────────────┐    ┌────────────┐          │
│    │   SYSTEM   │    │   ACTION   │    │    RAG     │          │
│    │   HANDLER  │    │   ROUTER   │    │  PIPELINE  │          │
│    └────────────┘    └─────┬──────┘    └────────────┘          │
│                            │                                     │
│                            ▼                                     │
│              ┌─────────────────────────┐                        │
│              │  🎯 TOOL DECIDER        │                        │
│              │  (El Capataz)           │                        │
│              └───────────┬─────────────┘                        │
│                          │                                       │
│            ┌─────────────┴─────────────┐                        │
│            │  ¿Es operación crítica?   │                        │
│            └─────────────┬─────────────┘                        │
│                    SÍ    │    NO                                │
│                    ▼     │    ▼                                 │
│    ┌─────────────────────┐  ┌─────────────────────┐            │
│    │  🎭 TEATRO MENTAL   │  │  EJECUCIÓN DIRECTA  │            │
│    │  Luz→Sombra→Luna→   │  │  (sin agente)       │            │
│    │  Agua→Fuego→Viento  │  └─────────────────────┘            │
│    └──────────┬──────────┘                                      │
│               │                                                  │
│    ┌──────────┴──────────┐                                      │
│    │ ¿Proceder?          │                                      │
│    └──────────┬──────────┘                                      │
│          SÍ   │   NO                                            │
│          ▼    │   ▼                                             │
│    ┌──────────┐  ┌──────────┐                                   │
│    │ EJECUTAR │  │ BLOQUEAR │                                   │
│    └──────────┘  └──────────┘                                   │
│                                                                  │
│    ┌─────────────────────────────────────────────┐              │
│    │           DAEMON PERSISTENTE                 │              │
│    │      (Modelo 8B cargado en memoria)          │              │
│    └─────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 Sistema de Colas - Flujo Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  📱 Telegram    📝 .task file    🌐 Webhook                     │
│       │              │               │                          │
│       └──────────────┼───────────────┘                          │
│                      ▼                                           │
│              ┌──────────────┐                                   │
│              │    INBOX     │                                   │
│              └──────┬───────┘                                   │
│                     │                                            │
│                     ▼                                            │
│         ┌────────────────────────┐                              │
│         │  🧠 STRATEGIC AGENT    │                              │
│         │  ¿Es tarea compleja?   │                              │
│         └───────────┬────────────┘                              │
│              SÍ     │     NO                                    │
│              ▼      │     ▼                                     │
│    ┌──────────────┐ │  ┌──────────────┐                        │
│    │   DIVIDIR    │ │  │   PROCESAR   │                        │
│    │  en subtareas│ │  │   DIRECTO    │                        │
│    └──────┬───────┘ │  └──────┬───────┘                        │
│           │         │         │                                  │
│           ▼         │         ▼                                  │
│    ┌──────────────┐ │  ┌──────────────┐                        │
│    │  PROCESSING  │◄┘  │  PROCESSING  │                        │
│    └──────┬───────┘    └──────┬───────┘                        │
│           │                   │                                  │
│           ▼                   ▼                                  │
│    ┌──────────────┐    ┌──────────────┐                        │
│    │   ARCHIVE    │    │   ARCHIVE    │                        │
│    │ (completado) │    │ (completado) │                        │
│    └──────────────┘    └──────────────┘                        │
│                                                                  │
│         📱 Notificación enviada a Telegram                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 💻 Ejemplos de Uso

### 1. Consulta Informativa (RAG)

```
❓ ¿Qué es Python?
🎯 Intent: INFORMATIVE
📚 RAG: Wikipedia
💬 Python es un lenguaje de programación...
```

### 2. Acción Directa (Sin Agente)

```
❓ lista los archivos de ~/proyecto
🎯 Intent: ACTION → FILESYSTEM
🎯 ToolDecider: filesystem_list
⚡ Ejecución DIRECTA (0.01s)
📁 Contenido de /Users/.../proyecto:
   ...
```

### 3. Operación Crítica (Con Teatro Mental)

```
❓ elimina todos los archivos .tmp
🎯 Intent: ACTION → FILESYSTEM
🎭 Teatro Mental activado...
   [LUZ]: Operación de eliminación detectada
   [SOMBRA]: ⚠️ OPERACIÓN DESTRUCTIVA
   Riesgo: 8/10
⛔ BLOQUEADO: Verificar archivos antes de eliminar
```

### 4. Tarea Autónoma (Cola)

```bash
# Crear tarea
cat > ~/wikirag/queue/inbox/libro.task << 'EOF'
priority: HIGH
agent: strategist

Escribe un libro de 50 páginas sobre Machine Learning
para principiantes. Incluye ejemplos de código.
EOF

# El sistema automáticamente:
# 1. Strategic Agent divide en ~10 subtareas
# 2. Queue Daemon procesa cada una
# 3. Notificación a Telegram cuando termina
```

## 📝 Changelog

### v2.4.0 - Sistema Cognitivo (2025-02-01)
- 🎭 **Teatro Mental**: 6 perfiles deliberan antes de actuar
- 📬 **File Queue**: Sistema de colas estilo Unix
- 🧠 **Strategic Agent**: Divide tareas complejas
- 📱 **Multi-Canal**: Telegram, Webhook
- 🎯 **SmartToolDecider**: Bloqueo automático de operaciones peligrosas
- 🤖 **Queue Daemon**: Procesamiento autónomo

### v2.3.1 - Intent Routing (2025-01-31)
- Intent Classifier, Smart Router, Claude-style Agent, Daemon Auto-Start

### v2.3.0 - Sistema Autónomo (2025-01-30)
- Daemon Persistente, BM25 Lazy Loading, Prompt Cache

### v2.1.0 - Técnicas de Vanguardia (2025-01)
- Hybrid Search, Re-ranking, Self-RAG, MCP

## 🔒 Seguridad

El Teatro Mental actúa como **filtro de seguridad** para modelos 8B:

- **Sombra** tiene como Impulso Central: *"La integridad del sistema de archivos del usuario es sagrada"*
- Operaciones como `rm -rf`, `sudo`, `chmod 777` son automáticamente bloqueadas
- Requiere deliberación explícita para proceder con operaciones destructivas

## 📄 Licencia

MIT

---

**WikiRAG v2.4.0** - *Sistema Cognitivo Autónomo con Teatro Mental*

*"No es solo una IA local, es una infraestructura de ejecución privada"*
