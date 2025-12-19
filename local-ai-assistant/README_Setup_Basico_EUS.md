# 🤖 Tokiko IA Laguntzailearen Instalazioa - Oinarrizko Konfiguradorea

## Deskribapena

Script automatizatua Tokiko IA Laguntzaile oinarrizko bat konfiguratzeko, llama.cpp modeloak erabiliz. Instaladore hau sinplea, zuzena eta erraza izan dadin diseinatuta dago, eta tokiko hizkuntza modeloekin elkarreragiteko oinarri sendoa eskaintzen du.

## Ezaugarri Nagusiak

### 🔧 Konfigurazio Sinple eta Intuitiboa
- **Instalazio gidatua**: Pauso-pausoko konfigurazio interaktiboa
- **Balidazio automatikoa**: Aurre-baldintzak eta bideak egiaztatzen ditu
- **Konfigurazio adaptatiboa**: Ingurune desberdinetara egokitzen da
- **Egitura modularra**: Arkitektura antolatua eta luzagarria

### 🎯 Funtzionalitate Nagusiak
- **LLM Bezeroa**: Komunikazio zuzena llama.cpp-rekin
- **Fitxategien kudeatzailea**: Irakurketa/idazketa seguruak
- **Agindu exekutorea**: Sistemaren exekuzio kontrolatua
- **Konfigurazio malgua**: JSON bidez konfiguragarria

### 📁 Arkitektura Modularra
```
src/
├── core/           # Laguntzailearen motor nagusia
├── llm/            # Bezeroa llama.cpp-rentzat
├── file_ops/       # Fitxategien kudeaketa
└── commands/       # Aginduak exekutatzea
```

## Sistemaren Baldintzak

- **Python 3.11+**
- **llama.cpp** konpilatua
- **GGUF Modeloa** bateragarria
- **pip3** Python mendekotasunetarako
- **Sistema eragilea**: macOS, Linux

## Instalazio Azkarra

### 1. Deskarga eta Exekuzioa
```bash
# Script-a deskargatu
curl -O https://raw.githubusercontent.com/tu-usuario/asistente-basico/main/setup_asistente_basico.sh

# Exekutagarria egin
chmod +x setup_asistente_basico.sh

# Instalazioa exekutatu
./setup_asistente_basico.sh
```

### 2. Konfigurazio Interaktiboa

Scriptak honako hau eskatu ahal dizu:

**Proiektuaren direktorioa:**
```
Proiektuaren direktorioa [/Users/tu-usuario/asistente-ia]: 
```

**GGUF modelaren bidea:**
```
GGUF modelaren bidea [/Users/tu-usuario/modelo/modelo.gguf]: 
```

**llama-cli bidea:**
```
llama.cpp bidea [/Users/tu-usuario/llama.cpp/build/bin/llama-cli]: 
```

### 3. Konfirmazioa
```
Hautatutako konfigurazioa:
Proiektuaren direktorioa: /Users/tu-usuario/asistente-ia
Modeloa: /Users/tu-usuario/modelo/modelo.gguf
Llama.cpp: /Users/tu-usuario/llama.cpp/build/bin/llama-cli

Jarraituko al duzu konfigurazio honekin? (y/N)
```

## Sortutako Egitura

```
asistente-ia/
├── src/
│   ├── main.py                 # Sarrera puntua
│   ├── core/
│   │   ├── assistant.py        # Laguntzailearen klase nagusia
│   │   └── config.py           # Konfigurazio kudeaketa
│   ├── llm/
│   │   └── client.py           # llama.cpp bezeroa
│   ├── file_ops/
│   │   └── manager.py          # Fitxategien kudeaketa
│   └── commands/
│       └── runner.py           # Aginduak exekutatzea
├── config/
│   └── settings.json           # Konfigurazio nagusia
├── tools/                      # Tresna gehigarriak
├── tests/                      # Sistema testak
├── logs/                       # Exekuzio log-ak
└── examples/                   # Erabilera adibideak
```

## Oinarrizko Erabilera

### Komando Nagusia
```bash
cd /ruta/a/tu/asistente-ia
python3 src/main.py "Zeintzuk dira proiektuko Python fitxategiak?"
```

### Modu Interaktiboa
```bash
python3 src/main.py
🤖 Tokiko IA Laguntzailea - Modu interaktiboa
Sartu 'exit' irteteko, 'help' laguntzarako

💬 > azaldu main.py fitxategia
🤖 main.py fitxategia sarrera puntua da...

💬 > exit
Agur! 👋
```

### Komando Lerroko Parametroak
```bash
# Konfigurazio zehatz bat erabili
python3 src/main.py --config config/custom.json "analiza ezazu proiektua"

# Modu verbose
python3 src/main.py --verbose "Python fitxategien zerrenda"

# Laguntza
python3 src/main.py --help
```

## Konfigurazioa

### Konfigurazio Fitxategia (config/settings.json)
```json
{
  "llm": {
    "model_path": "/ruta/a/tu/modelo.gguf",
    "llama_bin": "/ruta/a/llama-cli",
    "max_tokens": 1024,
    "temperature": 0.7
  },
  "assistant": {
    "safe_mode": true,
    "backup_files": true,
    "max_file_size": 1048576,
    "supported_extensions": [".py", ".js", ".ts", ".json", ".md", ".txt", ".sh"]
  },
  "logging": {
    "level": "INFO",
    "file": "logs/assistant.log"
  }
}
```

### LLM Parametroen Pertsonalizazioa
- **max_tokens**: Erantzunaren gehienezko luzera
- **temperature**: Sortzeko gaitasuna (0.0 = deterministikoa, 1.0 = sortzailea)
- **model_path**: GGUF modelorako bidea
- **llama_bin**: llama-cli binarioaren bidea

### Segurtasun Konfigurazioa
- **safe_mode**: Komandoen segurtasun modua aktibatzea
- **backup_files**: Aldaketak egin aurretik kopia seguruak sortzea
- **max_file_size**: Prozesatuko fitxategiaren gehienezko tamaina
- **supported_extensions**: Onartutako fitxategi motak

## Funtzionalitate Nagusiak

### 1. Fitxategien Analisia
```bash
python3 src/main.py "azaldu config.py fitxategiak egiten duena"
```

### 2. Fitxategien Zerrenda
```bash
python3 src/main.py "proiektuko Python fitxategi guztiak erakutsi"
```

### 3. Egituren Analisia
```bash
python3 src/main.py "deskribatu proiektu honen arkitektura"
```

### 4. Kode Laguntza
```bash
python3 src/main.py "nola hobetu dezaket load_config funtzioa?"
```

## Eskuragarri dauden Komandoak

### Laguntza Komandoak
- `help` - Laguntza osoa erakutsi
- `exit` - Modu interaktibotik irten

### Kontsulta Adibideak
- "X fitxategia azaldu"
- "Y motako fitxategiak zerrendatu"
- "proiektuaren egitura deskribatu"
- "Z klasea nola funtzionatzen duen"
- "W funtzioa zer egiten duen"

## Balidazioak eta Segurtasuna

### Balidazio Automatikoak
- ✅ Python 3.11+ egiaztapena
- ✅ pip3 egiaztapena
- ✅ llama-cli bidearen egiaztapena
- ✅ GGUF modeloa egiaztapena
- ⚠️ Fitxategiak aurkitu ez direnean oharrak

### Modu Seguru
```json
{
  "assistant": {
    "safe_mode": true,     // Komandoen murrizketak
    "backup_files": true,  // Backup automatikoak
    "max_file_size": 1048576  // 1MB-ko mugak fitxategi bakoitzeko
  }
}
```

## Luzapena eta Pertsonalizazioa

### Fitxategi Motak Gehitu
```json
{
  "assistant": {
    "supported_extensions": [".py", ".js", ".go", ".rust", ".cpp"]
  }
}
```

### Promptak Aldatu
Editatu `src/core/assistant.py` `_build_prompt()` metodoan:

```python
def _build_prompt(self, context: Dict, user_input: str) -> str:
    prompt = f"""Tokiko {tu_dominio} aditua den laguntzaile bat zara.
    
    TESTU TESTUA: {context}
    KONTSULTA: {user_input}
    
    Erantzun {tu_estilo} moduan."""
    
    return prompt
```

### Komando Berriak Gehitu
`src/commands/runner.py` aldatu, onartutako komando berriak gehitzeko:

```python
self.safe_commands = {
    'ls', 'cat', 'grep', 'find',  # Oinarrizkoak
    'git', 'npm', 'pip',          # Garapena
    'zure_komando_pertsonalizatua' # Komando berria
}
```

## Arazoak Konpontzea

### Error: "Python3 ez dago instalatuta"
```bash
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt update && sudo apt install python3.11
```

### Error: "llama-cli ez aurkitu"
```bash
# llama.cpp instalazioa egiaztatu
ls -la /ruta/a/llama.cpp/build/bin/llama-cli

# Konfigurazioan bidea eguneratu
vim config/settings.json
```

### Error: "Modeloa ez aurkitu"
```bash
# Modeloa egiaztatu
ls -la /ruta/a/tu/modelo.gguf

# Deskargatu behar izanez gero
wget https://huggingface.co/modelo/resolve/main/modelo.gguf
```

### Errendimendu Arazoak
```json
{
  "llm": {
    "max_tokens": 512,      // Erantzun azkarragoak lortzeko murriztu
    "temperature": 0.3      // Sormen gutxiago = azkarrago
  }
}
```

## Editoreen Integrazioa

### VSCode
```json
// tasks.json
{
    "label": "Laguntzailea Kontsultatu",
    "type": "shell",
    "command": "python3",
    "args": ["src/main.py", "${input:consulta}"],
    "group": "build"
}
```

### Vim/NeoVim
```vim
" Laguntzailea kontsultatzeko mapaketa
nnoremap <leader>ai :!python3 src/main.py "<C-R><C-W>"<CR>
```

## Kontribuzioa eta Garapena

### Kontribuitzeko Egitura
1. Repositorioa fork egin
2. Adar berria sortu: `git checkout -b feature/ezaugarri-berria`
3. Arkitektura modularrean garatu
4. `tests/`-ean testak gehitu
5. `examples/`-ean dokumentatu
6. Pull Request sortu

### Garapen Gida
- Arkitektura modularra jarraitu
- Ezaugarri berriak balidazioekin gehitu
- JSON konfigurazioarekin bateragarritasuna mantendu
- Logging egokia sartu

## Lizentzia

MIT License

## Egilea

**Gustavo Silva da Costa (Eto Demerzel)**

## Bertsioa

**1.0.0** - Oinarrizko konfiguradorea arkitektura modular sendoarekin

---

*Tokiko IA laguntzaile sinple baina indartsua zure garapen-fluxua hobetzeko.*
