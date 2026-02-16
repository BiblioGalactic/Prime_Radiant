# ⚡ Prime Radiant - Colección de Asistentes de IA Local

> 🧠 **Automatizo ideas complejas con IA local. Desde Bash, para humanos.**
---

## 🌟 Qué es Prime Radiant

**Prime Radiant** es una colección de herramientas y configuraciones para trabajar con IA local. Este repositorio contiene scripts y sistemas para automatizar tareas usando modelos de lenguaje locales a través de llama.cpp.

### 🎯 Filosofía del Proyecto

- **Local First**: Toda la IA funciona en tu máquina
- **Bash Centered**: Scripts potentes y transparentes
- **Iterativo**: Mejora continua con cada experimento

---

## 📦 Herramientas Incluidas

### 🤖 [Local AI Assistant](./local-ai-assistant/)
**Configurador avanzado con capacidades agénticas**

- Instalación automatizada de asistente IA local
- Modo agéntico con planificación inteligente
- Gestión segura de archivos y código

```bash
./setup_asistente.sh
```

### ⚔️ [Local-CROS (Cross-Referential Optimization)](./local-agentic-assistant/)
**Sistema de evaluación cruzada entre modelos**

- Compara respuestas de múltiples modelos LLaMA
- Evaluación cruzada automática
- Síntesis inteligente de respuestas

```bash
./local-cros.sh "Tu pregunta aquí"
```

---

## 🚀 Inicio Rápido

### Prerrequisitos

- **llama.cpp** compilado y funcional
- **Modelos GGUF** (Mistral, LLaMA, etc.)
- **Bash 4.0+** en macOS/Linux

### Instalación Básica

```bash
git clone https://github.com/BiblioGalactic/Prime_Radiant.git
cd Prime_Radiant

# Explorar herramientas disponibles
ls -la
```

### Configuración

1. **Instala llama.cpp**:
```bash
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
make
```

2. **Descarga modelos GGUF**:
```bash
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q6_K.gguf
```

---

## 🛠️ Catálogo de Herramientas

| Herramienta | Propósito | Estado |
|-------------|-----------|--------|
| [Local AI Assistant](./local-ai-assistant/) | Asistente agéntico completo | ✅ Estable |
| [Local-CROS](./local-agentic-assistant/) | Comparador de modelos | ✅ Estable |

---

## 🎭 Filosofía de Diseño

### Por Qué Bash

- **Transparencia**: Puedes leer cada comando
- **Portabilidad**: Funciona en sistemas Unix
- **Simplicidad**: Sin dependencias complejas

### Por Qué Local

- **Privacidad**: Tus datos no salen de tu máquina
- **Control**: Decides qué modelos usar
- **Costo**: Sin límites de API

---

## 📄 Licencia

MIT License - Uso libre con atribución.

### Autor

**Gustavo Silva da Costa (Eto Demerzel)**  
🔗 [BiblioGalactic](https://github.com/BiblioGalactic)

---

*"El conocimiento más valioso es el que puedes controlar, mejorar y compartir libremente."*  
— Eto Demerzel, Prime Radiant
