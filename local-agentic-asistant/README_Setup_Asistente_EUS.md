# 🤖 Tokiko Hobetutako IA Laguntzailearen Ezarpenerako Gida

## Deskribapena

Automatizatutako instalazio sistema bat, agentzia gaitasun aurreratuak dituen Tokiko IA Laguntzaile bat ezartzeko. Script honek LLaMA modelo lokalekin elkarreragiteko garapen-ingurune oso bat konfiguratzen du, kodearen analisia, fitxategien kudeaketa eta sistemako komandoen exekuzioa ahalbidetuz.

## Ezaugarri Nagusiak

### 🧠 Adimen Agentzial Modua
- **Planifikazio automatikoa**: Lan konplexuak azpi-lan espezifikoetan zatitzen ditu
- **Fitxategi irakurketa automatikoa**: Proiektuaren fitxategi garrantzitsuen analisia automatikoki egiten du
- **Redundantziarik gabeko sintesia**: Analisien emaitzak konbinatzen ditu informazio errepikatu gabe
- **Kalitate egiaztapena**: Erantzunen kalitatea automatikoki kontrolatzen duen sistema

### 🔧 Funtzionalitate Aurreratuak
- **50+ komando gaituta**: Git, Docker, NPM, Python eta gehiago
- **Arriskutsuak diren komandoen babesa**: Segurtasun sistema integratua
- **Fitxategi kudeaketa adimentsua**: Irakurketa, idazketa eta kode analisia
- **Konfigurazio egokitua**: Ingurunean automatikoki egokitzen da

### 🎯 Arkitektura Modularra
- **Core**: Laguntzailearen motor nagusia
- **LLM Bezeroa**: llama.cpp modeloekin komunikazioa
- **Fitxategi Kudeatzailea**: Fitxategi seguruen kudeaketa
- **Komando Exekutorea**: Komandoen exekuzio kontrolatua
- **Agentzial Luzapena**: Agentzia gaitasun aurreratuak

## Sistemaren Baldintzak

- **Python 3.11+**
- **llama.cpp** konpilatua eta funtzionala
- **GGUF Modeloa** bateragarria
- **Bash 4.0+**
- **Sistema eragilea**: macOS, Linux

## Instalazioa

### 1. Deskarga eta Instalazioa
```bash
# Script-a deskargatu
curl -O https://raw.githubusercontent.com/tu-usuario/setup-asistente/main/setup_asistente.sh

# Exekutagarria egin
chmod +x setup_asistente.sh

# Instalazioa exekutatu
./setup_asistente.sh
```

### 2. Konfigurazio Interaktiboa
Script-ak honakoak galdetuko dizkizu:
- **Instalazio direktorioa**: Proiektua non instalatuko den
- **GGUF modelaren bidea**: Tokiko hizkuntza modeloa
- **llama-cli bidea**: llama.cpp binarioa

### 3. Sortutako Egitura
```
asistente-ia/
├── src/
│   ├── core/              # Motor nagusia
│   ├── llm/               # LLM bezeroa
│   ├── file_ops/          # Fitxategi kudeaketa
│   └── commands/          # Komando exekuzioa
├── config/                # Konfigurazioa
├── tools/                 # Tresna osagarriak
├── tests/                 # Sistemaren testak
├── logs/                  # Exekuzio log-ak
└── examples/              # Erabilera adibideak
```

## Erabilera

### Oinarrizko Komandoak
```bash
# Laguntzaile arrunta
claudia "proiektu hau azaldu"

# Agentzial modua
claudia-a "arkitektura osoa aztertu"

# Verbose modua (barne prozesua ikusi)
claudia-deep "akatsen ikerketa sakona"

# Laguntza osoa
claudia-help
```

### Agentzial Komando Adibideak
- `"kode egitura osoa aztertu"`
- `"errendimenduaren ikerketa sakona"`
- `"agentzial modua: kode guztia optimizatu"`
- `"akatsak xehetasunez aztertu"`

### Elkarreragile Modua
```bash
claudia
💬 > agentic on
💬 > proiektu hau oso aztertu
💬 > exit
```

## Konfigurazio Aurreratua

### Konfigurazio Fitxategia
```json
{
  "llm": {
    "model_path": "/zure/bidea/modelo.gguf",
    "llama_bin": "/zure/bidea/llama-cli",
    "max_tokens": 1024,
    "temperature": 0.7
  },
  "assistant": {
    "safe_mode": false,
    "backup_files": true,
    "supported_extensions": [".py", ".js", ".json", ".md"]
  }
}
```

### Pertsonalizazioa
- **Modeloak**: Modeloren bidea aldatu `config/settings.json` fitxategian
- **Komandoak**: Onartutako komandoen zerrenda aldatu `commands/runner.py` fitxategian
- **Luzapenak**: Fitxategi mota berriak gehitu

## Sistemaren Arkitektura

### Osagai Nagusiak

1. **LocalAssistant**: Osagai nagusia, osagai guztiak koordinatzen dituena
2. **AgenticAssistant**: Agentzial gaitasunak ematen dituen luzapena
3. **LlamaClient**: llama.cpp modeloekin interfazea
4. **FileManager**: Proiektuaren fitxategi seguruen kudeaketa
5. **CommandRunner**: Sistemako komandoen exekuzio kontrolatua

### Agentzial Fluxua

1. **Planifikazioa**: Lan nagusia azpi-lan espezifikoetan zatitzen du
2. **Exekuzioa**: Azpi-lan bakoitza testuinguru aberatsarekin exekutatzen du
3. **Sintesia**: Emaitzak konbinatzen ditu redundantziarik gabe
4. **Egiaztapena**: Azken erantzunaren kalitatea baliozkotzen du

## Segurtasuna

### Debekatutako Komandoak
- `rm`, `rmdir`, `dd`, `shred`
- `sudo`, `su`, `chmod`, `chown`
- `kill`, `reboot`, `shutdown`

### Onartutako Komandoak
- Garapen tresnak: `git`, `npm`, `pip`, `docker`
- Fitxategi analisia: `cat`, `grep`, `find`, `head`, `tail`
- Konpilazioa: `make`, `cmake`, `gradle`, `maven`

## Arazoen Konponbidea

### Error: "llama-cli ez da aurkitu"
```bash
# llama.cpp instalazioa egiaztatu
which llama-cli

# Bidea konfigurazioan eguneratu
vim config/settings.json
```

### Error: "Modeloa ez da aurkitu"
```bash
# Modelaren bidea egiaztatu
ls -la /zure/bidea/modelo.gguf

# Konfigurazioa eguneratu
claudia --config config/settings.json
```

### Agentzial Moduak Ez Ditu Funtzionatzen
```bash
# Verbose modua egiaztatu
claudia-deep "test sinplea"

# Log-ak ikusi
tail -f logs/assistant.log
```

## Kontribuzioa

1. Repositorioa forkatu
2. Zure feature-rako adarra sortu: `git checkout -b feature/funtzionalitate-berria`
3. Aldaketak commit egin: `git commit -am 'Funtzionalitate berria gehitu'`
4. Adarra push egin: `git push origin feature/funtzionalitate-berria`
5. Pull Request sortu

## Lizentzia

MIT License - xehetasunetarako LICENSE fitxategia ikusi.

## Egilea

**Gustavo Silva da Costa (Eto Demerzel)**

## Bertsioa

**2.0.0** - Agentzial sistema hobetua planifikazio adimentsuarekin eta redundantziarik gabeko sintesiarekin.

---

*Laguntza gehiago behar baduzu, sortu issue bat proiektuaren repositorioan.*
