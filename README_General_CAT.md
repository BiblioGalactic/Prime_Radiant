# ⚡ Prime Radiant - Col·lecció d'Assistents d'IA Local

🧠 **Automatitzo idees complexes amb IA local. Des de Bash, per a humans.**
---

## 🌟 Què és Prime Radiant

**Prime Radiant** és una col·lecció d'eines i configuracions per treballar amb IA local. Aquest repositori conté scripts i sistemes per automatitzar tasques utilitzant models de llenguatge locals a través de llama.cpp.

### 🎯 Filosofia del Projecte

- **Local First**: Tota la IA funciona a la teva màquina
- **Bash Centered**: Scripts potents i transparents
- **Iteratiu**: Millora contínua amb cada experiment

---

## 📦 Eines Incloses

### 🤖 [Local AI Assistant](./local-ai-assistant/)
**Configurador avançat amb capacitats agèntiques**

- Instal·lació automatitzada d'assistant IA local
- Mode agèntic amb planificació intel·ligent
- Gestió segura d'arxius i codi

```
./setup_asistente.sh
```

### ⚔️ [Local-CROS (Cross-Referential Optimization)](./local-agentic-assistant/)
**Sistema d'avaluació creuada entre models**

- Compara respostes de múltiples models LLaMA
- Avaluació creuada automàtica
- Síntesi intel·ligent de respostes

```
./local-cros.sh "La teva pregunta aquí"
```

---

## 🚀 Inici Ràpid

### Prerrequisits

- **llama.cpp** compilat i funcional
- **Models GGUF** (Mistral, LLaMA, etc.)
- **Bash 4.0+** a macOS/Linux

### Instal·lació Bàsica

```
git clone https://github.com/BiblioGalactic/Prime_Radiant.git
cd Prime_Radiant

# Explorar eines disponibles
ls -la
```

### Configuració

1. **Instal·la llama.cpp**:
```
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
make
```

2. **Descarrega models GGUF**:
```
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q6_K.gguf
```

---

## 🛠️ Catàleg d'Eines

| Eina | Propòsit | Estat |
|-------------|-----------|--------|
| [Local AI Assistant](./local-ai-assistant/) | Assistant agèntic complet | ✅ Estable |
| [Local-CROS](./local-agentic-assistant/) | Comparador de models | ✅ Estable |

---

## 🎭 Filosofia de Disseny

### Per què Bash

- **Transparència**: Pots llegir cada ordre
- **Portabilitat**: Funciona en sistemes Unix
- **Simplicitat**: Sense dependències complexes

### Per què Local

- **Privacitat**: Les teves dades no surten de la teva màquina
- **Control**: Tu decideixes quins models utilitzar
- **Cost**: Sense límits d'API

---

## 📄 Llicència

MIT License - Ús lliure amb atribució.

### Autor

**Gustavo Silva da Costa (Eto Demerzel)**  
🔗 [BiblioGalactic](https://github.com/BiblioGalactic)

---

*"El coneixement més valuós és el que pots controlar, millorar i compartir lliurement."*  
— Eto Demerzel, Prime Radiant
