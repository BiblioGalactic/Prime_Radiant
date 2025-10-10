# 🤖 MCP Local - Xat IA amb Eines de Sistema

> **Sistema complet de Model Context Protocol amb 11 eines i mode agent (per a IA local)**

```
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║       Transforma el teu LLM local en un assistent potent  ║
║       amb accés al sistema operatiu                        ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

## 📋 Índex

- [Què és això?](#-què-és-això)
- [Característiques](#-característiques)
- [Requisits](#-requisits)
- [Instal·lació](#-installació)
- [Ús bàsic](#-ús-bàsic)
- [Mode Agent](#-mode-agent)
- [Les 11 eines](#-les-11-eines)
- [Exemples pràctics](#-exemples-pràctics)
- [Configuració avançada](#-configuració-avançada)
- [Resolució de problemes](#-resolució-de-problemes)
- [Arquitectura](#-arquitectura)
- [Crèdits](#-crèdits)

---

## 🎯 Què és això?

**MCP Local** és un sistema que connecta els teus models de llenguatge locals (Mistral, Llama, etc.) amb **eines reals del sistema operatiu**.

### Sense MCP:
```
👤 Usuari: "Llista'm els fitxers Python"
🤖 IA: "Ho sento, no puc accedir al sistema de fitxers"
```

### Amb MCP:
```
👤 Usuari: "Llista'm els fitxers Python"
🤖 IA: [Cerca] ✓
       He trobat 12 fitxers: main.py, utils.py, config.py...
```

**És com donar mans a la IA per interactuar amb el teu ordinador** 🦾

---

## ✨ Característiques

### 🔧 11 Eines Completes
- ✅ Llegir i escriure fitxers
- ✅ Executar comandes bash
- ✅ Navegar per directoris
- ✅ Cercar fitxers i contingut
- ✅ Consultar APIs HTTP
- ✅ Descarregar fitxers des d'URLs
- ✅ Comprimir/descomprimir (zip, tar, tar.gz)
- ✅ Operacions Git (status, log, diff, branch)
- ✅ Monitoritzar sistema (RAM, CPU, disc)
- ✅ Cercar contingut (grep)

### 🧠 Mode Agent
**Funcionalitat estrella!** La IA pot encadenar múltiples accions automàticament:

```
👤: "Descarrega el README de GitHub i comprimeix tots els fitxers markdown"

🤖 [Mode Agent]
   📋 Pla: 3 passos
   🔄 Descarregant... ✅
   🔄 Cercant *.md... ✅  
   🔄 Comprimint... ✅
   
   ✅ He descarregat el README (3.4KB), he trobat 5 fitxers markdown
      i els he comprimit a docs.zip (45KB)
```

### 🔒 Seguretat Integrada
- ❌ Bloqueja comandes perilloses (rm, dd, sudo, etc.)
- 🛡️ Només permet escriure a $HOME o /tmp
- ⏱️ Timeout automàtic
- 📦 Límit de mida de fitxers (10MB)

### 🎨 Interfície Fàcil d'Usar
- 💬 Xat interactiu
- 📊 Mode verbose per a depuració
- 🎯 Detecció automàtica de mode agent
- ⚡ Respostes ràpides i clares

---

## 📦 Requisits

Abans d'instal·lar, assegura't de tenir:

### Requisits Obligatoris
```bash
✅ Python 3.8 o superior
✅ pip3
✅ Model GGUF (Mistral, Llama, etc.)
✅ llama.cpp compilat amb llama-cli
```

### Requisits Opcionals
```bash
🔧 git (per a eines Git)
🔧 curl/wget (inclòs a macOS/Linux)
```

### Sistemes Operatius
- ✅ macOS (provat)
- ✅ Linux (provat)
- ⚠️ Windows (amb WSL)

---

## 🚀 Instal·lació

### Pas 1: Descarregar l'Instal·lador

```bash
# Opció A: Clonar el repositori
git clone https://github.com/your-repo/mcp-local.git
cd mcp-local

# Opció B: Descarregar l'script directament
curl -O https://your-url/mcp_setup.sh
chmod +x mcp_setup.sh
```

### Pas 2: Executar l'Instal·lador

```bash
./mcp_setup.sh
```

### Pas 3: Configurar les Rutes

L'instal·lador et demanarà dues rutes:

```
🎯 Configuració Inicial
==========================================

📍 Pas 1/2: Ruta a l'executable llama-cli
   Exemple: /usr/local/bin/llama-cli
   O: /Users/el-teu-usuari/llama.cpp/build/bin/llama-cli
   Ruta completa: _

📍 Pas 2/2: Ruta al model GGUF
   Exemple: /Users/el-teu-usuari/models/mistral-7b-instruct.gguf
   Ruta completa: _
```

### Pas 4: Instal·lació Automàtica

L'script automàticament:
1. ✅ Crea l'entorn virtual Python
2. ✅ Instal·la dependències (flask, psutil, requests)
3. ✅ Genera el servidor MCP (11 eines)
4. ✅ Genera el client amb mode agent
5. ✅ Desa la configuració

```
✅ Instal·lació Completa

╔════════════════════════════════════════╗
║     MCP LOCAL - Menú Principal         ║
║     💪 11 Eines + Agent                ║
╚════════════════════════════════════════╝

  1) 💬 Iniciar xat (amb mode agent)
  2) 🔧 Mostrar eines MCP (11)
  3) ⚙️  Reconfigurar rutes
  4) 🚪 Sortir
```

---

## 💬 Ús Bàsic

### Iniciar el Xat

```bash
./mcp_setup.sh
# Selecciona opció 1) Iniciar xat
```

### Comandes del Xat

```
👤 Tu: _

Comandes disponibles:
  agentic on/off  → Activa/desactiva el mode agent
  verbose on/off  → Mostra logs detallats
  herramientas    → Llista les 11 eines
  salir           → Tanca el xat
```

### Exemple de Conversa Normal

```bash
👤 Tu: Llista els fitxers de l'escriptori

🤖 IA: [Llistat] ✓
   Hi ha 23 elements a l'escriptori: Documents/, Downloads/,
   imatge.png, notes.txt...

👤 Tu: Quanta RAM tinc lliure?

🤖 IA: [Memòria] ✓
   Tens 8.5GB de RAM lliure de 16GB totals (53% lliure)
```

---

## 🧠 Mode Agent

El mode agent permet que la IA **encadeni múltiples accions automàticament**, sense necessitat de donar comandes una per una.

### Com Activar-lo

**Opció 1: Manual**
```bash
👤 Tu: agentic on
🤖 Mode Agent: Activat
```

**Opció 2: Automàtic** (detecta aquestes paraules clau)
- `i`
- `després`
- `i comprimeix`
- `i cerca`
- `fes-ho tot`
- `executa tot`
- `automàtic`

### Exemple Complet

#### Sense Mode Agent (3 comandes separades):
```bash
👤: Descarrega el README
🤖: ✓

👤: Cerca tots els fitxers markdown
🤖: ✓

👤: Comprimeix els fitxers
🤖: ✓
```

#### Amb Mode Agent (1 sola comanda):
```bash
👤: Descarrega el README de GitHub i després comprimeix tots els fitxers markdown

🤖 [Mode Agent Activat]
📋 Pla: 3 passos

🔄 Pas 1/3: Descarregant https://raw.githubusercontent.com/...
   ✅ Descarregat

🔄 Pas 2/3: Cercant ~/Desktop:*.md
   ✅ Trobat

🔄 Pas 3/3: Comprimint ~/Desktop a ~/Desktop/docs.zip
   ✅ Comprimit

🔄 Integrant resultats...

✅ Tasca Completada

🤖 He descarregat el README (3456 bytes), he trobat 5 fitxers
   markdown a l'escriptori i els he comprimit a docs.zip
   (45KB total). Fet!
```

### Mode Verbose (Depuració)

Per veure el procés intern:

```bash
👤 Tu: verbose on
📊 Mode Verbose: Activat

👤 Tu: Descarrega X i comprimeix Y

🧠 Planejant passos...
📋 Passos planificats: ["download:...", "search:...", "compress:..."]
🔍 Executant: download:https://...
   ✅ Descarregat
🔍 Executant: search:~/Desktop:*.md
   ✅ Trobat
...
```

---

## 🛠️ Les 11 Eines

### 1. 📖 Llegir Fitxer
```bash
👤: Llegeix el fitxer README.md
🤖: [Lectura] ✓
   El fitxer conté documentació sobre...
```
- 📦 Màxim: 64KB
- 🔒 Només fitxers de text

### 2. ✍️ Escriure Fitxer
```bash
👤: Crea un fitxer test.txt amb "Hola Món"
🤖: [Escriptura] ✓ (11 bytes)
   Fitxer creat a ~/test.txt
```
- 📦 Màxim: 10MB
- 🔒 Només a $HOME o /tmp
- 🔀 Modes: `w` (sobreescriu) o `a` (afegeix)

### 3. 📁 Llistar Directori
```bash
👤: Què hi ha a la carpeta Downloads?
🤖: [Llistat] ✓
   45 elements: documents/, images/, video.mp4...
```
- 📊 Mostra: nom, tipus, mida, data
- 📦 Límit: 100 elements

### 4. 🔍 Cercar Fitxers
```bash
👤: Troba tots els fitxers Python
🤖: [Cerca] ✓
   He trobat 12 fitxers: main.py, utils.py...
```
- 🌲 Cerca recursiva
- 🎯 Patrons Glob: `*.py`, `test*.txt`, etc.
- 📦 Límit: 50 fitxers

### 5. 🔎 Cercar Contingut (Grep)
```bash
👤: Cerca "TODO" als fitxers Python
🤖: [GREP] ✓ (8 coincidències)
   main.py:42: # TODO: implementar validació
   utils.py:15: # TODO: optimitzar algorisme
```
- 📄 Només fitxers < 1MB
- 🎯 Regex insensible a majúscules
- 📦 Límit: 50 coincidències

### 6. ⚡ Executar Comanda
```bash
👤: Executa ls -la
🤖: [Comanda] ✓
   total 256
   drwxr-xr-x  15 user  staff   480 Oct 10 10:30 .
   ...
```
- ❌ **Bloquejades**: rm, dd, sudo, su, mkfs
- ⏱️ Timeout: 10 segons
- 📦 Sortida: màxim 4KB

### 7. 💾 Consultar Memòria
```bash
👤: Quants recursos tinc disponibles?
🤖: [Memòria] ✓
   RAM: 8.5GB lliure de 16GB
   CPU: 35% en ús (8 nuclis)
   Disc: 245GB lliure de 500GB
```

### 8. 📥 Descarregar Fitxer
```bash
👤: Descarrega https://example.com/file.pdf
🤖: [Descàrrega] ✓ (2.5MB)
   Fitxer desat a ~/Downloads/file.pdf
```
- 🌐 Només http:// i https://
- 📦 Límit: 10MB
- ⏱️ Timeout: 30 segons

### 9. 🗜️ Comprimir/Descomprimir
```bash
👤: Comprimeix la carpeta documents
🤖: [Compressió] ✓
   Carpeta comprimida a documents.zip (12MB)
```
- 📦 Formats: zip, tar, tar.gz
- 🔄 Operacions: comprimir, descomprimir

### 10. 🔧 Operacions Git
```bash
👤: Mostra l'estat de git
🤖: [GIT] ✓
   On branch main
   Changes not staged for commit:
     modified: src/main.py
```
- ✅ Permeses: status, log, diff, branch, remote
- ❌ **Bloquejades**: commit, push, pull (només lectura)

### 11. 🌐 Consultar API
```bash
👤: Consulta l'API d'example.com
🤖: [API] ✓ (200)
   Estat: OK
   Resposta: {"data": "exemple"}
```
- 📡 Mètodes: GET, POST, PUT, DELETE, PATCH
- ⏱️ Timeout: 10 segons
- 📦 Resposta: màxim 4KB

---

## 💡 Exemples Pràctics

### Exemple 1: Anàlisi de Projecte
```bash
👤: agentic on

👤: Llista tots els fitxers Python i cerca els TODOs pendents

🤖 [Mode Agent]
   Pas 1: Cercant *.py... ✅
   Pas 2: Cercant 'TODO'... ✅
   
   He trobat 12 fitxers Python amb 8 TODOs pendents:
   - main.py: 3 TODOs
   - utils.py: 2 TODOs
   - config.py: 3 TODOs
```

### Exemple 2: Còpia de Seguretat Automàtica
```bash
👤: Cerca tots els fitxers importants i comprimeix-los a backup

🤖 [Mode Agent]
   Pas 1: Cercant fitxers... ✅
   Pas 2: Comprimint... ✅
   
   He creat backup.zip amb 45 fitxers (234MB total)
```

### Exemple 3: Monitorització de Sistema
```bash
👤: Mostra l'estat de git i els recursos del sistema

🤖 [Mode Agent]
   Pas 1: Estat Git... ✅
   Pas 2: Consultant recursos... ✅
   
   Git: 3 fitxers modificats a la branca main
   Sistema: RAM 45% lliure, CPU 25%, Disc 50% lliure
```

### Exemple 4: Flux de Treball Complet
```bash
👤: Descarrega el README de GitHub, cerca'l a l'escriptori
    i comprimeix tots els fitxers markdown que trobis

🤖 [Mode Agent]
   📋 Pla: 3 passos
   
   Pas 1: Descarregant de GitHub... ✅ (3.4KB)
   Pas 2: Cercant *.md a l'escriptori... ✅ (5 fitxers)
   Pas 3: Comprimint fitxers... ✅ (45KB)
   
   ✅ He descarregat el README, he trobat 5 fitxers markdown
      i els he comprimit a docs.zip. Tot a l'escriptori.
```

---

## ⚙️ Configuració Avançada

### Canviar Model o Ruta llama-cli

```bash
./mcp_setup.sh
# Selecciona opció 3) Reconfigurar rutes
```

### Editar Configuració Manualment

```bash
nano ~/.mcp_local/config.env
```

```bash
# Configuració MCP Local
LLAMA_CLI="/ruta/al/teu/llama-cli"
MODELO_GGUF="/ruta/al/teu/model.gguf"
```

### Variables d'Entorn

```bash
# Activar depuració del servidor MCP
export MCP_DEBUG=1

# Executar
./mcp_setup.sh
```

### Estructura de Fitxers

```
~/.mcp_local/
├── config.env           # La teva configuració
├── venv/                # Entorn Python
├── mcp_server.py        # Servidor amb 11 eines
└── chat_mcp.py          # Client amb mode agent
```

---

## 🔧 Resolució de Problemes

### Problema: "No es troba llama-cli"

**Solució:**
```bash
# Verifica que llama.cpp estigui compilat
cd ~/llama.cpp
cmake -B build
cmake --build build

# Verifica la ruta
ls ~/llama.cpp/build/bin/llama-cli

# Reconfigura MCP
./mcp_setup.sh
# Opció 3) Reconfigurar rutes
```

### Problema: "No es troba el model"

**Solució:**
```bash
# Verifica que el model existeixi
ls ~/ruta/al/teu/model.gguf

# Si no tens model, descarrega'n un
# Exemple: Mistral 7B
wget https://huggingface.co/...model.gguf

# Reconfigura
./mcp_setup.sh
# Opció 3) Reconfigurar rutes
```

### Problema: "Error instal·lant dependències Python"

**Solució:**
```bash
# Verifica Python
python3 --version  # Ha de ser 3.8+

# Neteja l'entorn virtual
rm -rf ~/.mcp_local/venv

# Reinstal·la
./mcp_setup.sh
```

### Problema: "El mode agent no funciona bé"

**Solució:**
```bash
# Utilitza el mode verbose per veure què passa
👤: verbose on
👤: la comanda problemàtica

# El mode agent depèn de la qualitat del model
# Models recomanats:
# - Mistral 7B Instruct (mínim)
# - Llama 3 8B Instruct (millor)
# - Mixtral 8x7B (òptim)
```

### Problema: "Timeout en consultes"

**Solució:**
```bash
# Si el model és molt lent, augmenta el timeout
# Edita ~/.mcp_local/chat_mcp.py

# A la línia ~40:
IA_CMD = [
    config.get('LLAMA_CLI', 'llama-cli'),
    "--model", config.get('MODELO_GGUF', ''),
    "--n-predict", "512",
    "--temp", "0.7",
    "--ctx-size", "4096"
]

# Si tens GPU disponible, afegeix:
# "--n-gpu-layers", "35"
```

### Problema: "Comanda bloquejada per seguretat"

**Solució:**
Això és intencional. Les comandes perilloses estan bloquejades:
- ❌ `rm -rf`
- ❌ `dd`
- ❌ `sudo`
- ❌ `su`

Si necessites executar comandes privilegiades, fes-ho manualment fora de MCP.

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────┐
│           👤 Usuari (tu)                    │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│      💬 Client Xat (chat_mcp.py)            │
│  ┌────────────────────────────────────┐     │
│  │  🧠 Mode Agent                     │     │
│  │  - Planificació de passos          │     │
│  │  - Execució seqüencial             │     │
│  │  - Integració de resultats         │     │
│  └────────────────────────────────────┘     │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│        🤖 Model LLM Local                   │
│     (Mistral, Llama, Mixtral, etc.)         │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│   🔧 Servidor MCP (mcp_server.py)           │
│  ┌────────────────────────────────────┐     │
│  │  11 eines:                         │     │
│  │  ✓ Fitxers (llegir/escriure)       │     │
│  │  ✓ Sistema (memòria/comandes)      │     │
│  │  ✓ Xarxa (API/descàrregues)        │     │
│  │  ✓ Cerca (fitxers/contingut)       │     │
│  │  ✓ Utilitats (git/compressió)      │     │
│  └────────────────────────────────────┘     │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│     💻 El teu Sistema Operatiu              │
│  (fitxers, comandes, recursos)              │
└─────────────────────────────────────────────┘
```

### Flux de Consulta Normal

```
1. L'usuari introdueix una comanda
   👤 "Llista fitxers Python"
   
2. El client consulta el LLM
   💬 → 🤖 "Quina eina utilitzar?"
   
3. El LLM decideix l'eina
   🤖 → 💬 "[Ús eina:cerca:.:*.py]"
   
4. El client crida el servidor MCP
   💬 → 🔧 {"method": "search_files", ...}
   
5. El servidor executa l'eina
   🔧 → 💻 Cerca real al sistema
   
6. El servidor retorna resultats
   🔧 → 💬 {"result": ["main.py", ...]}
   
7. El client envia resultats al LLM
   💬 → 🤖 "Fitxers trobats: ..."
   
8. El LLM genera resposta natural
   🤖 → 💬 "He trobat 12 fitxers Python: ..."
   
9. L'usuari veu la resposta
   💬 → 👤 "He trobat 12 fitxers Python: ..."
```

### Flux Mode Agent

```
1. L'usuari introdueix comanda complexa
   👤 "Descarrega X i després comprimeix Y"
   
2. El client detecta mode agent
   💬 [Detecta paraula clau "i després"]
   
3. El LLM planifica passos
   💬 → 🤖 "Descompon en passos"
   🤖 → 💬 ["download:...", "search:...", "compress:..."]
   
4. El client executa passos seqüencialment
   💬 → 🔧 Pas 1: Descàrrega ✅
   💬 → 🔧 Pas 2: Cerca ✅
   💬 → 🔧 Pas 3: Compressió ✅
   
5. El LLM integra resultats
   💬 → 🤖 "Resume tot l'executat"
   🤖 → 💬 "He descarregat, cercat i comprimit..."
   
6. L'usuari veu el resum final
   💬 → 👤 "✅ Tasca completada: ..."
```

---

## 📚 Recursos Addicionals

### Model Context Protocol (MCP)
- 📖 [Especificació MCP](https://spec.modelcontextprotocol.io/)
- 🔗 [Anthropic MCP GitHub](https://github.com/anthropics/mcp)

### Models Recomanats
- 🦙 [Llama 3 8B Instruct](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct)
- 🌟 [Mistral 7B Instruct](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.1)
- 🚀 [Mixtral 8x7B](https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1)

### llama.cpp
- 🔗 [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- 📖 [Documentació](https://github.com/ggerganov/llama.cpp/blob/master/README.md)

---

## 🎓 Casos d'Ús

### Per a Desenvolupadors
- ✅ Automatitzar tasques repetitives
- ✅ Analitzar codi i cercar TODOs
- ✅ Gestionar repositoris Git
- ✅ Generar documentació
- ✅ Monitoritzar recursos del sistema

### Per a Administradors de Sistemes
- ✅ Automatitzar còpies de seguretat
- ✅ Monitoritzar logs
- ✅ Gestionar fitxers de configuració
- ✅ Cercar informació als logs
- ✅ Comprimir/descomprimir arxius

### Per a Usuaris Avançats
- ✅ Organitzar fitxers automàticament
- ✅ Descarregar i processar contingut web
- ✅ Cercar informació en documents
- ✅ Automatitzar fluxos de treball complexos
- ✅ Integrar amb APIs externes

---

## 🤝 Contribucions

Tens idees per millorar MCP Local? Contribueix!

### Idees per a Noves Eines
- 📧 Client de correu
- 📅 Integració amb calendari
- 🗄️ Operacions de base de dades
- 🐳 Integració amb Docker
- 📊 Generació d'informes

### Com Contribuir
1. Fes fork del projecte
2. Crea una branca (`git checkout -b feature/nova-eina`)
3. Fes commit dels canvis (`git commit -am 'Afegeix nova eina X'`)
4. Puja a la branca (`git push origin feature/nova-eina`)
5. Obre un Pull Request

---

## 📄 Llicència

Aquest projecte està sota llicència MIT. Utilitza'l, modifica'l i comparteix-lo lliurement.

```
Llicència MIT

Copyright (c) 2025 Gustavo Silva Da Costa

Es concedeix permís gratuït a qualsevol persona que obtingui una còpia
d'aquest programari i dels fitxers de documentació associats (el "Programari")
per tractar el Programari sense restriccions, incloent sense limitació els
drets d'usar, copiar, modificar, fusionar, publicar, distribuir, sublicenciar
i/o vendre còpies del Programari, i permetre a les persones a les quals se'ls
proporcioni el Programari fer-ho, subjecte a les següents condicions:

L'avís de copyright anterior i aquest avís de permís s'han d'incloure en
totes les còpies o parts substancials del Programari.

EL PROGRAMARI ES PROPORCIONA "TAL QUAL", SENSE GARANTIA DE CAP TIPUS, EXPLÍCITA
O IMPLÍCITA, INCLOENT PERÒ NO LIMITAT A LES GARANTIES DE COMERCIABILITAT,
IDONEÏTAT PER A UN PROPÒSIT PARTICULAR I NO INFRACCIÓ. EN CAP CAS ELS AUTORS
O TITULARS DEL COPYRIGHT SERAN RESPONSABLES DE CAP RECLAMACIÓ, DANYS O ALTRA
RESPONSABILITAT, JA SIGUI EN UNA ACCIÓ CONTRACTUAL, GREUGE O D'ALTRA MANERA,
QUE SORGEIXI DE, FORA DE O EN CONNEXIÓ AMB EL PROGRAMARI O L'ÚS O ALTRES
TRACTAMENTS DEL PROGRAMARI.
```

---

## 🙏 Agraïments

- Anthropic per proporcionar el concepte de Model Context Protocol
- La comunitat llama.cpp per fer possible l'execució de LLMs localment
- Tothom qui contribueix a l'ecosistema d'IA de codi obert

---

## 📞 Suport

Tens problemes? Preguntes? Suggeriments?

- 📧 Correu: gsilvadacosta0@gmail.com 
- 🆇 L'antic Twitter 😂: https://x.com/bibliogalactic

---

<div align="center">

## ⭐ Si t'agrada aquest projecte, dona-li una estrella a GitHub ⭐

```
╔════════════════════════════════════════════════════════╗
║                                                        ║
║   Creat amb ❤️ per a la comunitat d'IA local          ║
║                                                        ║
║   "Donant mans a la IA, una eina cada cop"            ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

### 👨‍💻 Autor

**Gustavo Silva Da Costa** (Eto Demerzel) 🤫

🚀 *Transformant IA local en assistents potents*

</div>

---

**Versió:** 1.0.0  
**Última actualització:** Octubre 2025  
**Estat:** ✅ Producció

---
