# 🤖 MCP Local - AI Txata Sistema Tresnekin

> **Model Context Protocol sistema osoa 11 tresnarekin eta agente moduarekin (AI lokalarentzat)**

```
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║       Eraldatu zure LLM lokala laguntzaile indartsua     ║
║       sistema eragilearen sarbidearekin                    ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

## 📋 Aurkibidea

- [Zer da hau?](#-zer-da-hau)
- [Ezaugarriak](#-ezaugarriak)
- [Eskakizunak](#-eskakizunak)
- [Instalazioa](#-instalazioa)
- [Oinarrizko erabilera](#-oinarrizko-erabilera)
- [Agente modua](#-agente-modua)
- [11 tresnak](#-11-tresnak)
- [Adibide praktikoak](#-adibide-praktikoak)
- [Konfigurazio aurreratua](#-konfigurazio-aurreratua)
- [Arazo konponketa](#-arazo-konponketa)
- [Arkitektura](#-arkitektura)
- [Kredituak](#-kredituak)

---

## 🎯 Zer da hau?

**MCP Local** zure hizkuntza eredu lokalak (Mistral, Llama, etab.) **sistema eragilearen benetako tresnekin** konektatzen dituen sistema bat da.

### MCP gabe:
```
👤 Erabiltzailea: "Zerrendatu Python fitxategiak"
🤖 IA: "Barkatu, ezin dut fitxategi sistemara sartu"
```

### MCP-rekin:
```
👤 Erabiltzailea: "Zerrendatu Python fitxategiak"
🤖 IA: [Bilaketa] ✓
       12 fitxategi aurkitu ditut: main.py, utils.py, config.py...
```

**AI-ri eskuak ematea bezalakoa da, zure ordenagailuarekin elkarreragiteko** 🦾

---

## ✨ Ezaugarriak

### 🔧 11 Tresna Osoak
- ✅ Fitxategiak irakurri eta idatzi
- ✅ Bash komandoak exekutatu
- ✅ Direktorioen artean nabigatu
- ✅ Fitxategiak eta edukia bilatu
- ✅ HTTP APIak kontsultatu
- ✅ Fitxategiak deskargatu URLetatik
- ✅ Konprimatu/deskonprimatu (zip, tar, tar.gz)
- ✅ Git eragiketak (status, log, diff, branch)
- ✅ Sistema monitorizatu (RAM, CPU, diskoa)
- ✅ Edukia bilatu (grep)

### 🧠 Agente Modua
**Izar funtzionaltasuna!** AI-ak ekintza anitzak automatikoki kate dezake:

```
👤: "Deskargatu GitHub-eko README-a eta konprimatu markdown fitxategi guztiak"

🤖 [Agente Modua]
   📋 Plana: 3 pauso
   🔄 Deskargatzen... ✅
   🔄 *.md bilatzen... ✅  
   🔄 Konprimatzen... ✅
   
   ✅ README deskargatu dut (3.4KB), 5 markdown fitxategi aurkitu ditut
      eta docs.zip-en konprimatu ditut (45KB)
```

### 🔒 Integratutako Segurtasuna
- ❌ Komando arriskutsuak blokeatu (rm, dd, sudo, etab.)
- 🛡️ $HOME edo /tmp-n bakarrik idatzi ahal da
- ⏱️ Timeout automatikoa
- 📦 Fitxategi tamaina muga (10MB)

### 🎨 Erraz Erabiltzeko Interfazea
- 💬 Txat interaktiboa
- 📊 Modu verbose arazketa egiteko
- 🎯 Agente moduaren detekzio automatikoa
- ⚡ Erantzun azkar eta argiak

---

## 📦 Eskakizunak

Instalatu aurretik, ziurtatu hau duzula:

### Nahitaezko Eskakizunak
```bash
✅ Python 3.8 edo handiagoa
✅ pip3
✅ GGUF eredua (Mistral, Llama, etab.)
✅ llama.cpp konpilatu llama-cli-rekin
```

### Aukerako Eskakizunak
```bash
🔧 git (Git tresnetarako)
🔧 curl/wget (macOS/Linux-en sartuta)
```

### Sistema Eragileak
- ✅ macOS (frogatuta)
- ✅ Linux (frogatua)
- ⚠️ Windows (WSL-rekin)

---

## 🚀 Instalazioa

### 1. Pausoa: Instalatzailea Deskargatu

```bash
# A aukera: Erreposiorioa klonatu
git clone https://github.com/your-repo/mcp-local.git
cd mcp-local

# B aukera: Script-a zuzenean deskargatu
curl -O https://your-url/mcp_setup.sh
chmod +x mcp_setup.sh
```

### 2. Pausoa: Instalatzailea Exekutatu

```bash
./mcp_setup.sh
```

### 3. Pausoa: Bideak Konfiguratu

Instalatzaileak bi bide eskatuko dizkizu:

```
🎯 Hasierako Konfigurazioa
==========================================

📍 1/2 Pausoa: llama-cli exekutagarriaren bidea
   Adibidea: /usr/local/bin/llama-cli
   Edo: /Users/zure-erabiltzailea/llama.cpp/build/bin/llama-cli
   Bide osoa: _

📍 2/2 Pausoa: GGUF ereduaren bidea
   Adibidea: /Users/zure-erabiltzailea/models/mistral-7b-instruct.gguf
   Bide osoa: _
```

### 4. Pausoa: Instalazio Automatikoa

Script-ak automatikoki:
1. ✅ Python ingurune birtuala sortzen du
2. ✅ Dependentziak instalatzen ditu (flask, psutil, requests)
3. ✅ MCP zerbitzaria sortzen du (11 tresna)
4. ✅ Bezeroa sortzen du agente moduarekin
5. ✅ Konfigurazioa gordetzen du

```
✅ Instalazioa Osatuta

╔════════════════════════════════════════╗
║     MCP LOCAL - Menu Nagusia           ║
║     💪 11 Tresna + Agentea             ║
╚════════════════════════════════════════╝

  1) 💬 Txata hasi (agente moduarekin)
  2) 🔧 MCP tresnak erakutsi (11)
  3) ⚙️  Bideak berkonfiguratu
  4) 🚪 Irten
```

---

## 💬 Oinarrizko Erabilera

### Txata Hasi

```bash
./mcp_setup.sh
# Aukeratu 1) aukera Txata hasi
```

### Txataren Komandoak

```
👤 Zu: _

Komando eskuragarriak:
  agentic on/off  → Agente modua aktibatu/desaktibatu
  verbose on/off  → Log zehatzak erakutsi
  herramientas    → 11 tresnak zerrendatu
  salir           → Txata itxi
```

### Ohiko Elkarrizketaren Adibidea

```bash
👤 Zu: Zerrendatu mahaigaineko fitxategiak

🤖 IA: [Zerrenda] ✓
   23 elementu daude mahaigainean: Documents/, Downloads/,
   irudia.png, oharrak.txt...

👤 Zu: Zenbat RAM daukat libre?

🤖 IA: [Memoria] ✓
   8.5GB RAM libre dituzu 16GB totaletik (%53 libre)
```

---

## 🧠 Agente Modua

Agente moduak AI-ak **ekintza anitzak automatikoki kateatzen** uzten du, komandoak bat bana eman beharrik gabe.

### Nola Aktibatu

**1 Aukera: Eskuz**
```bash
👤 Zu: agentic on
🤖 Agente Modua: Aktibatuta
```

**2 Aukera: Automatikoa** (hitz gako hauek detektatzen ditu)
- `eta`
- `gero`
- `eta konprimatu`
- `eta bilatu`
- `egin guztia`
- `exekutatu guztia`
- `automatikoa`

### Adibide Osoa

#### Agente Modurik gabe (3 komando banandu):
```bash
👤: Deskargatu README-a
🤖: ✓

👤: Bilatu markdown fitxategi guztiak
🤖: ✓

👤: Konprimatu fitxategiak
🤖: ✓
```

#### Agente Moduarekin (komando bakar bat):
```bash
👤: Deskargatu GitHub-eko README-a eta gero konprimatu markdown fitxategi guztiak

🤖 [Agente Modua Aktibatuta]
📋 Plana: 3 pauso

🔄 1/3 Pausoa: Deskargatzen https://raw.githubusercontent.com/...
   ✅ Deskargatuta

🔄 2/3 Pausoa: Bilatzen ~/Desktop:*.md
   ✅ Aurkituta

🔄 3/3 Pausoa: Konprimatzen ~/Desktop ~/Desktop/docs.zip-era
   ✅ Konprimatuta

🔄 Emaitzak integratzen...

✅ Zeregina Osatuta

🤖 README deskargatu dut (3456 byte), 5 markdown fitxategi
   aurkitu ditut mahaigainean eta docs.zip-en konprimatu ditut
   (45KB guztira). Eginda!
```

### Modu Verbose (Arazketa)

Barne prozesua ikusteko:

```bash
👤 Zu: verbose on
📊 Modu Verbose: Aktibatuta

👤 Zu: Deskargatu X eta konprimatu Y

🧠 Pausoak planeatu...
📋 Planeatutako pausoak: ["download:...", "search:...", "compress:..."]
🔍 Exekutatzen: download:https://...
   ✅ Deskargatuta
🔍 Exekutatzen: search:~/Desktop:*.md
   ✅ Aurkituta
...
```

---

## 🛠️ 11 Tresnak

### 1. 📖 Fitxategia Irakurri
```bash
👤: Irakurri README.md fitxategia
🤖: [Irakurketa] ✓
   Fitxategiak...ri buruzko dokumentazioa dauka
```
- 📦 Maximoa: 64KB
- 🔒 Testu fitxategiak bakarrik

### 2. ✍️ Fitxategian Idatzi
```bash
👤: Sortu test.txt fitxategi bat "Kaixo Mundua"-rekin
🤖: [Idazketa] ✓ (11 byte)
   Fitxategia sortuta ~/test.txt-n
```
- 📦 Maximoa: 10MB
- 🔒 $HOME edo /tmp-n bakarrik
- 🔀 Moduak: `w` (gainidatzi) edo `a` (gehitu)

### 3. 📁 Direktorioa Zerrendatu
```bash
👤: Zer dago Downloads karpetan?
🤖: [Zerrenda] ✓
   45 elementu: documents/, images/, video.mp4...
```
- 📊 Erakusten du: izena, mota, tamaina, data
- 📦 Muga: 100 elementu

### 4. 🔍 Fitxategiak Bilatu
```bash
👤: Aurkitu Python fitxategi guztiak
🤖: [Bilaketa] ✓
   12 fitxategi aurkitu ditut: main.py, utils.py...
```
- 🌲 Bilaketa errekurtsiboa
- 🎯 Glob ereduak: `*.py`, `test*.txt`, etab.
- 📦 Muga: 50 fitxategi

### 5. 🔎 Edukia Bilatu (Grep)
```bash
👤: Bilatu "TODO" Python fitxategietan
🤖: [GREP] ✓ (8 bat-etortze)
   main.py:42: # TODO: balidazioa inplementatu
   utils.py:15: # TODO: algoritmoa optimizatu
```
- 📄 < 1MB fitxategiak bakarrik
- 🎯 Maiuskulak kontuan hartu gabeko regex
- 📦 Muga: 50 bat-etortze

### 6. ⚡ Komandoa Exekutatu
```bash
👤: Exekutatu ls -la
🤖: [Komandoa] ✓
   total 256
   drwxr-xr-x  15 user  staff   480 Oct 10 10:30 .
   ...
```
- ❌ **Blokeatuta**: rm, dd, sudo, su, mkfs
- ⏱️ Timeout: 10 segundo
- 📦 Irteera: gehienez 4KB

### 7. 💾 Memoria Kontsultatu
```bash
👤: Zenbat baliabide ditut eskuragarri?
🤖: [Memoria] ✓
   RAM: 8.5GB libre 16GB-tik
   CPU: %35 erabileran (8 nukleo)
   Diskoa: 245GB libre 500GB-tik
```

### 8. 📥 Fitxategia Deskargatu
```bash
👤: Deskargatu https://example.com/file.pdf
🤖: [Deskarga] ✓ (2.5MB)
   Fitxategia gordeta ~/Downloads/file.pdf-n
```
- 🌐 http:// eta https:// bakarrik
- 📦 Muga: 10MB
- ⏱️ Timeout: 30 segundo

### 9. 🗜️ Konprimatu/Deskonprimatu
```bash
👤: Konprimatu documents karpeta
🤖: [Konpresioa] ✓
   Karpeta konprimatuta documents.zip-en (12MB)
```
- 📦 Formatuak: zip, tar, tar.gz
- 🔄 Eragiketak: konprimatu, deskonprimatu

### 10. 🔧 Git Eragiketak
```bash
👤: Erakutsi git-en egoera
🤖: [GIT] ✓
   On branch main
   Changes not staged for commit:
     modified: src/main.py
```
- ✅ Baimenduta: status, log, diff, branch, remote
- ❌ **Blokeatuta**: commit, push, pull (irakurketa soilik)

### 11. 🌐 APIa Kontsultatu
```bash
👤: Kontsultatu example.com APIa
🤖: [API] ✓ (200)
   Egoera: OK
   Erantzuna: {"data": "adibidea"}
```
- 📡 Metodoak: GET, POST, PUT, DELETE, PATCH
- ⏱️ Timeout: 10 segundo
- 📦 Erantzuna: gehienez 4KB

---

## 💡 Adibide Praktikoak

### 1. Adibidea: Proiektuaren Analisia
```bash
👤: agentic on

👤: Zerrendatu Python fitxategi guztiak eta bilatu zain dauden TODOak

🤖 [Agente Modua]
   1. Pausoa: *.py bilatzen... ✅
   2. Pausoa: 'TODO' bilatzen... ✅
   
   12 Python fitxategi aurkitu ditut 8 TODO zainarekin:
   - main.py: 3 TODO
   - utils.py: 2 TODO
   - config.py: 3 TODO
```

### 2. Adibidea: Babeskopia Automatikoa
```bash
👤: Bilatu fitxategi garrantzitsu guztiak eta konprimatu backup-en

🤖 [Agente Modua]
   1. Pausoa: Fitxategiak bilatzen... ✅
   2. Pausoa: Konprimatzen... ✅
   
   backup.zip sortu dut 45 fitxategirekin (234MB guztira)
```

### 3. Adibidea: Sistemaren Monitorizazioa
```bash
👤: Erakutsi git-en egoera eta sistemaren baliabideak

🤖 [Agente Modua]
   1. Pausoa: Git Egoera... ✅
   2. Pausoa: Baliabideak kontsultatzen... ✅
   
   Git: 3 fitxategi aldatu main adarrean
   Sistema: RAM %45 libre, CPU %25, Diskoa %50 libre
```

### 4. Adibidea: Lan Fluxu Osoa
```bash
👤: Deskargatu GitHub-eko README-a, bilatu mahaigainean
    eta konprimatu aurkitzen dituzun markdown fitxategi guztiak

🤖 [Agente Modua]
   📋 Plana: 3 pauso
   
   1. Pausoa: GitHub-etik deskargatzen... ✅ (3.4KB)
   2. Pausoa: *.md bilatzen mahaigainean... ✅ (5 fitxategi)
   3. Pausoa: Fitxategiak konprimatzen... ✅ (45KB)
   
   ✅ README deskargatu dut, 5 markdown fitxategi aurkitu ditut
      eta docs.zip-en konprimatu ditut. Dena mahaigainean.
```

---

## ⚙️ Konfigurazio Aurreratua

### Eredua edo llama-cli Bidea Aldatu

```bash
./mcp_setup.sh
# Aukeratu 3) aukera Bideak berkonfiguratu
```

### Konfigurazioa Eskuz Editatu

```bash
nano ~/.mcp_local/config.env
```

```bash
# MCP Local Konfigurazioa
LLAMA_CLI="/zure/llama-cli-rako/bidea"
MODELO_GGUF="/zure/eredurako/bidea.gguf"
```

### Ingurune Aldagaiak

```bash
# MCP zerbitzariaren arazketa aktibatu
export MCP_DEBUG=1

# Exekutatu
./mcp_setup.sh
```

### Fitxategi Egitura

```
~/.mcp_local/
├── config.env           # Zure konfigurazioa
├── venv/                # Python ingurunea
├── mcp_server.py        # Zerbitzaria 11 tresnarekin
└── chat_mcp.py          # Bezeroa agente moduarekin
```

---

## 🔧 Arazo Konponketa

### Arazoa: "llama-cli ez da aurkitu"

**Konponbidea:**
```bash
# Egiaztatu llama.cpp konpilatuta dagoela
cd ~/llama.cpp
cmake -B build
cmake --build build

# Egiaztatu bidea
ls ~/llama.cpp/build/bin/llama-cli

# Berkonfiguratu MCP
./mcp_setup.sh
# 3) aukera Bideak berkonfiguratu
```

### Arazoa: "Eredua ez da aurkitu"

**Konponbidea:**
```bash
# Egiaztatu eredua existitzen dela
ls ~/zure/eredurako/bidea.gguf

# Ez baduzu eredurik, deskargatu bat
# Adibidea: Mistral 7B
wget https://huggingface.co/...model.gguf

# Berkonfiguratu
./mcp_setup.sh
# 3) aukera Bideak berkonfiguratu
```

### Arazoa: "Errorea Python dependentziak instalatzean"

**Konponbidea:**
```bash
# Egiaztatu Python
python3 --version  # 3.8+ izan behar du

# Garbitu ingurune birtuala
rm -rf ~/.mcp_local/venv

# Berrinst alatu
./mcp_setup.sh
```

### Arazoa: "Agente modua ez dabil ondo"

**Konponbidea:**
```bash
# Erabili verbose modua zer gertatzen den ikusteko
👤: verbose on
👤: arazo duen komandoa

# Agente modua ereduaren kalitatearen menpekoa da
# Gomendatutako ereduak:
# - Mistral 7B Instruct (minimoa)
# - Llama 3 8B Instruct (hobea)
# - Mixtral 8x7B (optimoa)
```

### Arazoa: "Timeout konsultetan"

**Konponbidea:**
```bash
# Eredua oso motela bada, handitu timeout-a
# Editatu ~/.mcp_local/chat_mcp.py

# ~40. lerroan:
IA_CMD = [
    config.get('LLAMA_CLI', 'llama-cli'),
    "--model", config.get('MODELO_GGUF', ''),
    "--n-predict", "512",
    "--temp", "0.7",
    "--ctx-size", "4096"
]

# GPU eskuragarri baduzu, gehitu:
# "--n-gpu-layers", "35"
```

### Arazoa: "Komandoa segurtasunagatik blokeatuta"

**Konponbidea:**
Hau nahita da. Komando arriskutsuak blokeatuta daude:
- ❌ `rm -rf`
- ❌ `dd`
- ❌ `sudo`
- ❌ `su`

Komando pribilegiatuak exekutatu behar badituzu, egin eskuz MCP-tik kanpo.

---

## 🏗️ Arkitektura

```
┌─────────────────────────────────────────────┐
│           👤 Erabiltzailea (zu)             │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│      💬 Txat Bezeroa (chat_mcp.py)          │
│  ┌────────────────────────────────────┐     │
│  │  🧠 Agente Modua                   │     │
│  │  - Pausoen plangintza              │     │
│  │  - Sekuentziazko exekuzioa         │     │
│  │  - Emaitzen integrazioa            │     │
│  └────────────────────────────────────┘     │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│        🤖 LLM Eredu Lokala                  │
│     (Mistral, Llama, Mixtral, etab.)        │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│   🔧 MCP Zerbitzaria (mcp_server.py)        │
│  ┌────────────────────────────────────┐     │
│  │  11 tresna:                        │     │
│  │  ✓ Fitxategiak (irakurri/idatzi)  │     │
│  │  ✓ Sistema (memoria/komandoak)     │     │
│  │  ✓ Sarea (API/deskargak)           │     │
│  │  ✓ Bilaketa (fitxategiak/edukia)  │     │
│  │  ✓ Utilitateak (git/konpresioa)   │     │
│  └────────────────────────────────────┘     │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│     💻 Zure Sistema Eragilea                │
│  (fitxategiak, komandoak, baliabideak)      │
└─────────────────────────────────────────────┘
```

### Ohiko Kontsulta Fluxua

```
1. Erabiltzaileak komandoa sartzen du
   👤 "Zerrendatu Python fitxategiak"
   
2. Bezeroak LLMa kontsultatzen du
   💬 → 🤖 "Zein tresna erabili?"
   
3. LLMak tresna erabakitzen du
   🤖 → 💬 "[Tresna erabili:bilatu:.:*.py]"
   
4. Bezeroak MCP zerbitzaria deitzen du
   💬 → 🔧 {"method": "search_files", ...}
   
5. Zerbitzariak tresna exekutatzen du
   🔧 → 💻 Bilaketa erreala sisteman
   
6. Zerbitzariak emaitzak itzultzen ditu
   🔧 → 💬 {"result": ["main.py", ...]}
   
7. Bezeroak emaitzak LLMra bidaltzen ditu
   💬 → 🤖 "Aurkitutako fitxategiak: ..."
   
8. LLMak erantzun naturala sortzen du
   🤖 → 💬 "12 Python fitxategi aurkitu ditut: ..."
   
9. Erabiltzaileak erantzuna ikusten du
   💬 → 👤 "12 Python fitxategi aurkitu ditut: ..."
```

### Agente Modu Fluxua

```
1. Erabiltzaileak komando konplexua sartzen du
   👤 "Deskargatu X eta gero konprimatu Y"
   
2. Bezeroak agente modua detektatzen du
   💬 [Hitz gakoa detektatu "eta gero"]
   
3. LLMak pausoak planeatzen ditu
   💬 → 🤖 "Deskonposatu pausotan"
   🤖 → 💬 ["download:...", "search:...", "compress:..."]
   
4. Bezeroak pausoak sekuentzialki exekutatzen ditu
   💬 → 🔧 1. Pausoa: Deskarga ✅
   💬 → 🔧 2. Pausoa: Bilaketa ✅
   💬 → 🔧 3. Pausoa: Konpresioa ✅
   
5. LLMak emaitzak integratzen ditu
   💬 → 🤖 "Labur ezazu exekutatutako guztia"
   🤖 → 💬 "Deskargatu, bilatu eta konprimatu dut..."
   
6. Erabiltzaileak azken laburpena ikusten du
   💬 → 👤 "✅ Zeregina osatuta: ..."
```

---

## 📚 Baliabide Gehigarriak

### Model Context Protocol (MCP)
- 📖 [MCP Zehaztapena](https://spec.modelcontextprotocol.io/)
- 🔗 [Anthropic MCP GitHub](https://github.com/anthropics/mcp)

### Gomendatutako Ereduak
- 🦙 [Llama 3 8B Instruct](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct)
- 🌟 [Mistral 7B Instruct](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.1)
- 🚀 [Mixtral 8x7B](https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1)

### llama.cpp
- 🔗 [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- 📖 [Dokumentazioa](https://github.com/ggerganov/llama.cpp/blob/master/README.md)

---

## 🎓 Erabilera Kasuak

### Garatzaileentzat
- ✅ Errepikatzen diren zereginak automatizatu
- ✅ Kodea analizatu eta TODOak bilatu
- ✅ Git biltegiak kudeatu
- ✅ Dokumentazioa sortu
- ✅ Sistemaren baliabideak monitorizatu

### Sistema Administratzaileentzat
- ✅ Babeskopiak automatizatu
- ✅ Logak monitorizatu
- ✅ Konfigurazio fitxategiak kudeatu
- ✅ Informazioa bilatu logetan
- ✅ Artxiboak konprimatu/deskonprimatu

### Erabiltzaile Aurreratuentzat
- ✅ Fitxategiak automatikoki antolatu
- ✅ Web edukia deskargatu eta prozesatu
- ✅ Dokumentuetan informazioa bilatu
- ✅ Lan fluxu konplexuak automatizatu
- ✅ Kanpoko APIekin integratu

---

## 🤝 Ekarpenak

MCP Local hobetzeko ideiarik al duzu? Ekarri!

### Tresna Berrien Ideiak
- 📧 Posta bezeroa
- 📅 Egutegi integrazioa
- 🗄️ Datu base eragiketak
- 🐳 Docker integrazioa
- 📊 Txosten sorkuntza

### Nola Ekarri
1. Egin proiektuaren fork
2. Sortu adar bat (`git checkout -b feature/tresna-berria`)
3. Egin aldaketen commit (`git commit -am 'Gehitu X tresna berria'`)
4. Igo adarrera (`git push origin feature/tresna-berria`)
5. Ireki Pull Request bat

---

## 📄 Lizentzia

Proiektu hau MIT lizentziaaren pean dago. Erabili, aldatu eta partekatu libreki.

```
MIT Lizentzia

Copyright (c) 2025 Gustavo Silva Da Costa

Software honen kopia bat eta dokumentazio fitxategi lotuen kopia bat
(Software-a) lortzen duen edozeini baimena ematen zaio, mugarik gabe
Software-a erabiltzeko, kopiatzeko, aldatzeko, bateratzeko, argitaratzeko,
banatzeko, azpilizentzia emateko eta/edo saltzeko, eta Software-a ematen
zaien pertsonei hori egiteko baimena emateko, baldintza hauei jarraituz:

Goiko copyright abisuak eta baimen abisu hau Software-aren kopia edo
zati garrantzitsu guztietan sartu behar dira.

SOFTWARE-A "DAGOEN BEZALA" EMATEN DA, INONGO BERMERIK GABE, ESPLIZITUA
EDO INPLIZITUA, MERKATURATZEKO, HELBURU JAKIN BATERAKO EGOKITASUNAREN ETA
EZ URRATZEAREN BERMEAK BARNE, BAINA HAUETARA MUGATU GABE. INOLA ERE EZ DIRA
EGILEAK EDO COPYRIGHT JABEAK ERANTZULE IZANGO INOLAKO ERREKLAMAZIORIK,
KALTERIK EDO BESTE ERANTZUKIZUNIK, KONTRATUZKO EKINTZA BATEAN, LEGEZ
KANPOKO EKINTZAN EDO BESTE MODUREN BATEAN, SOFTWARE-TZETIK, EDO SOFTWARE-AREN
ERABILERA EDO BESTE TRANSAKZIO BATZUETATIK ONDORIOZTATUZ EDO HAIEKIN
LOTUTA.
```

---

## 🙏 Eskerrak

- Anthropic Model Context Protocol kontzeptua eskainteagatik
- llama.cpp komunitatea LLMak lokalean exekutatzea posible egiteagatik
- Kode irekiko AI ekosistemari laguntzen dien guztiak

---

## 📞 Laguntza

Arazorik al duzu? Galderak? Proposamenak?

- 📧 Posta: gsilvadacosta0@gmail.com 
- 🆇 Lehen Twitter 😂: https://x.com/bibliogalactic

---

<div align="center">

## ⭐ Proiektu hau gustatzen bazaizu, eman izar bat GitHub-en ⭐

```
╔════════════════════════════════════════════════════════╗
║                                                        ║
║   ❤️-rekin sortua AI lokal komunitatearentzat         ║
║                                                        ║
║   "AI-ri eskuak ematen, tresna bat bakoitzean"        ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

### 👨‍💻 Egilea

**Gustavo Silva Da Costa** (Eto Demerzel) 🤫

🚀 *AI lokala laguntzaile indartsuak bihurtzen*

</div>

---

**Bertsioa:** 1.0.0  
**Azken eguneratzea:** 2025eko urria  
**Egoera:** ✅ Produkzioan

---
