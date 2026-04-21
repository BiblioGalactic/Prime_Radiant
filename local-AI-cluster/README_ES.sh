#!/usr/bin/env bash
cat <<'EOF'
# 🤖 AI Cluster - Sistema Distribuido de IA

**Procesa queries de IA en paralelo usando múltiples máquinas en tu red local (intranet).**

Sin cloud • Privado • Escalable • Open Source

---

## 📋 Descripción

AI Cluster es un sistema que permite aprovechar ordenadores ociosos en una red local para ejecutar modelos de IA de forma distribuida. Perfecto para empresas que quieren:

- ✅ **Privacidad total** - Los datos nunca salen de tu red
- ✅ **Sin costos de cloud** - Usa hardware existente
- ✅ **Cumplimiento GDPR** - Todo en tu infraestructura
- ✅ **Escalable** - Añade más máquinas fácilmente
- ✅ **Procesamiento paralelo** - Queries ejecutadas simultáneamente

---

## 🚀 Casos de Uso

### Para Empresas
- Procesar múltiples consultas a IA usando PCs de oficina
- Análisis de documentos distribuido
- Generación de contenido en paralelo
- Automatización de tareas repetitivas

### Para Desarrolladores
- Experimentar con sistemas distribuidos
- Aprender sobre paralelización
- Testear rendimiento de modelos
- Prototipado rápido de soluciones

---

## 🎯 Características

- ✨ **Wizard interactivo** - Configuración guiada paso a paso
- 🔐 **Setup SSH automático** - Configura conexiones sin contraseña
- 🌐 **Multi-máquina** - Soporta N ordenadores en la red
- ⚖️ **Balanceo round-robin** - Distribuye carga equitativamente
- 📊 **Estadísticas detalladas** - Monitorea el procesamiento
- 🛡️ **Manejo de errores robusto** - Continúa aunque falle una máquina

---

## 📦 Requisitos

### En TODAS las máquinas:

1. **llama.cpp compilado**
   ```bash
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp
   make
   ```

2. **Modelo GGUF descargado**
   - Mistral, Llama, Qwen, etc.
   - Ubicado en la misma ruta en todas las máquinas

3. **SSH activo** (solo en máquinas remotas)
   ```bash
   # macOS
   sudo systemsetup -setremotelogin on
   
   # Linux
   sudo systemctl enable ssh
   sudo systemctl start ssh
   ```

---

## ⚙️ Instalación

### 1. Descarga el script

```bash
# Clona el repositorio
git clone https://github.com/BiblioGalactic/ai-cluster
cd ai-cluster

# O descarga directamente
curl -O https://raw.githubusercontent.com/BiblioGalactic/ai-cluster/main/ai-cluster.sh
chmod +x ai-cluster.sh
```

### 2. Primera configuración

```bash
./ai-cluster.sh setup
```

El wizard te guiará a través de:
- ✅ Detectar llama.cpp y modelos locales
- ✅ Configurar IPs de máquinas remotas
- ✅ Configurar SSH sin contraseña
- ✅ Verificar conectividad y archivos

---

## 📖 Uso

### Comando básico

```bash
./ai-cluster.sh run queries.txt
```

### Archivo de queries

Crea un archivo `queries.txt` con tus preguntas (una por línea):

```
Explica qué es una red neuronal
Resume la teoría de la relatividad
¿Cuál es la capital de Japón?
Escribe un haiku sobre la tecnología
```

### Otros comandos

```bash
# Ver configuración actual
./ai-cluster.sh config

# Probar conectividad
./ai-cluster.sh test

# Reconfigurar
./ai-cluster.sh setup

# Ayuda
./ai-cluster.sh help
```

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────┐
│           ai-cluster.sh (Orquestador)           │
└─────────────┬───────────────────────────────────┘
              │
      ┌───────┴────────┬──────────────┬──────────┐
      │                │              │          │
  ┌───▼────┐      ┌───▼────┐    ┌───▼────┐ ┌───▼────┐
  │ Local  │      │ PC 1   │    │ PC 2   │ │ PC N   │
  │ (Mac)  │      │ (SSH)  │    │ (SSH)  │ │ (SSH)  │
  └────────┘      └────────┘    └────────┘ └────────┘
  Query 1,5,9     Query 2,6,10  Query 3,7  Query 4,8
```

**Distribución round-robin:**
- Query #1 → Máquina Local
- Query #2 → Máquina Remota 1
- Query #3 → Máquina Remota 2
- Query #4 → Máquina Remota 3
- Query #5 → Máquina Local (vuelve al inicio)

---

## 🔧 Configuración Avanzada

### Archivo `.ai_cluster_config`

Después del setup, se crea este archivo con tu configuración:

```bash
# Máquina Local
LOCAL_LLAMA="/Users/user/modelo/llama.cpp/build/bin/llama-cli"
LOCAL_MODEL="/Users/user/modelo/mistral-7b.gguf"

# Máquinas Remotas (separadas por comas)
REMOTE_IPS="192.168.1.82,192.168.1.83"
REMOTE_USER="username"
REMOTE_LLAMA="/home/user/llama.cpp/build/bin/llama-cli"
REMOTE_MODEL="/home/user/mistral-7b.gguf"

# Delay entre conexiones SSH (segundos)
REMOTE_DELAY=10
```

Puedes editarlo manualmente si necesitas cambios.

---

## 📊 Ejemplo de Salida

```
╔═══════════════════════════════════════════════════════════╗
║     🤖 AI CLUSTER - Sistema Distribuido de IA 🤖          ║
║   Procesa queries en paralelo usando tu red local        ║
╚═══════════════════════════════════════════════════════════╝

[17:30:00] 🎯 Total de queries: 20
[i] Máquinas disponibles: 3 (1 local + 2 remotas)

[17:30:00] 💻 [Local] Query #1: Explica qué es una red neuronal...
[17:30:00] 🌐 [192.168.1.82] Query #2: Resume la teoría...
[17:30:00] 🌐 [192.168.1.83] Query #3: ¿Cuál es la capital...
[17:30:02] ✓ [Local] Query #1 completada
[17:30:15] ✓ [192.168.1.82] Query #2 completada
[17:30:18] ✓ [192.168.1.83] Query #3 completada

...

[17:35:00] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[17:35:00] ✓ ✨ COMPLETADO
[17:35:00] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[i] Total procesadas: 20 queries
[i] Resultados en: results_cluster/
```

---

## 🐛 Troubleshooting

### SSH pide contraseña cada vez

```bash
# Ejecuta de nuevo el setup para configurar ssh-copy-id
./ai-cluster.sh setup
```

### "llama-cli no encontrado" en máquina remota

Verifica que la ruta en `.ai_cluster_config` sea correcta:

```bash
# En la máquina remota, ejecuta:
which llama-cli
# O busca:
find ~ -name "llama-cli" 2>/dev/null
```

### Queries no se procesan

```bash
# Prueba conectividad
./ai-cluster.sh test

# Verifica logs individuales
cat results_cluster/result_2_*.txt
```

### Script lento en Mac Mini

Los scripts automáticos en `.zshrc` pueden ralentizar SSH. Añade al inicio de `.zshrc` en máquinas remotas:

```bash
# Silenciar para SSH no interactivo
[[ -n "$SSH_CONNECTION" ]] && [[ ! -t 0 ]] && return
```

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📝 Roadmap

- [ ] Dashboard web en tiempo real
- [ ] Soporte para Docker containers
- [ ] Auto-detección de máquinas en red
- [ ] Caché de resultados
- [ ] Sistema de prioridades
- [ ] Métricas de rendimiento
- [ ] Integración con Kubernetes

---

## 📄 Licencia

MIT License - ver archivo [LICENSE](LICENSE)

---

## 👨‍💻 Autor

**Gustavo Silva da Costa** (BiblioGalactic)

- GitHub: [@BiblioGalactic](https://github.com/BiblioGalactic)
- Proyecto: Ciberrealismo aplicado a infraestructura corporativa

---

## 🙏 Agradecimientos

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Motor de inferencia
- [Anthropic Claude](https://claude.ai) - Asistencia en desarrollo
- Comunidad open source de IA local

---

## ⚠️ Disclaimer

Este software se proporciona "tal cual", sin garantías. Úsalo bajo tu propia responsabilidad. Los autores no se responsabilizan de pérdida de datos, mal funcionamiento de hardware, o cualquier daño derivado del uso de este software.

---

## 📚 Recursos

- [Documentación de llama.cpp](https://github.com/ggerganov/llama.cpp)
- [Modelos GGUF disponibles](https://huggingface.co/models?library=gguf)
- [Configuración SSH sin contraseña](https://www.ssh.com/academy/ssh/copy-id)

---

**Si este proyecto te resulta útil, dale una ⭐ en GitHub**
EOF
