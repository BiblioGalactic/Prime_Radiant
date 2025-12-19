# 🤖 Setup Assistent IA Local Millorat

## Descripció

Sistema d’instal·lació automatitzada per a un Assistent IA Local amb capacitats agèntiques avançades. Aquest script configura un entorn complet de desenvolupament per a interactuar amb models LLaMA locals, proporcionant funcionalitats d’anàlisi de codi, gestió d’arxius i execució de comandes del sistema.

## Característiques Principals

### 🧠 Mode Agèntic Intel·ligent
- **Planificació automàtica**: Descompon tasques complexes en subtasques específiques
- **Lectura automàtica d’arxius**: Analitza automàticament arxius rellevants del projecte
- **Síntesi sense redundàncies**: Combina múltiples anàlisis eliminant informació repetida
- **Verificació de qualitat**: Sistema automàtic de control de qualitat de respostes

### 🔧 Funcionalitats Avançades
- **50+ comandes habilitades**: Git, Docker, NPM, Python, i més
- **Protecció contra comandes perilloses**: Sistema de seguretat integrat
- **Gestió intel·ligent d’arxius**: Lectura, escriptura i anàlisi de codi
- **Configuració adaptativa**: S’ajusta automàticament a l’entorn

### 🎯 Arquitectura Modular
- **Core**: Motor principal de l’assistent
- **LLM Client**: Comunicació amb models llama.cpp
- **File Manager**: Gestió segura d’arxius
- **Command Runner**: Execució controlada de comandes
- **Agentic Extension**: Capacitats agèntiques avançades

## Requisits del Sistema

- **Python 3.11+**
- **llama.cpp** compilat i funcional
- **Model GGUF** compatible
- **Bash 4.0+**
- **Sistema operatiu**: macOS, Linux

## Instal·lació

### 1. Descàrrega i Instal·lació
```bash
# Descarregar l’script
curl -O https://raw.githubusercontent.com/tu-usuario/setup-asistente/main/setup_asistente.sh

# Fer executable
chmod +x setup_asistente.sh

# Executar instal·lació
./setup_asistente.sh
```

### 2. Configuració Interactiva
L’script et demanarà:
- **Directori d’instal·lació**: On s’instal·larà el projecte
- **Ruta del model GGUF**: El teu model de llenguatge local
- **Ruta de llama-cli**: Binari de llama.cpp

### 3. Estructura Generada
```
asistente-ia/
├── src/
│   ├── core/              # Motor principal
│   ├── llm/               # Client LLM
│   ├── file_ops/          # Gestió d’arxius
│   └── commands/          # Execució de comandes
├── config/                # Configuració
├── tools/                 # Eines addicionals
├── tests/                 # Tests del sistema
├── logs/                  # Logs d’execució
└── examples/              # Exemples d’ús
```

## Ús

### Comandes Bàsiques
```bash
# Assistent normal
claudia "explica aquest projecte"

# Mode agèntic
claudia-a "analitza completament l’arquitectura"

# Mode verbose (veure procés intern)
claudia-deep "investigació profunda sobre errors"

# Ajuda completa
claudia-help
```

### Exemples de Comandes Agèntiques
- `"analitza completament l’estructura del codi"`
- `"investigació profunda sobre el rendiment"`
- `"mode agèntic: optimitza tot el codi"`
- `"examina detalladament els errors"`

### Mode Interactiu
```bash
claudia
💬 > agentic on
💬 > analitza completament aquest projecte
💬 > exit
```

## Configuració Avançada

### Arxiu de Configuració
```json
{
  "llm": {
    "model_path": "/ruta/a/tu/modelo.gguf",
    "llama_bin": "/ruta/a/llama-cli",
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

### Personalització
- **Models**: Canvia la ruta del model a `config/settings.json`
- **Comandes**: Modifica la llista de comandes permeses a `commands/runner.py`
- **Extensions**: Afegeix nous tipus d’arxiu suportats

## Arquitectura del Sistema

### Components Principals

1. **LocalAssistant**: Classe principal que coordina tots els components
2. **AgenticAssistant**: Extensió que proporciona capacitats agèntiques
3. **LlamaClient**: Interfície amb models llama.cpp
4. **FileManager**: Gestió segura d’arxius del projecte
5. **CommandRunner**: Execució controlada de comandes del sistema

### Flux Agèntic

1. **Planificació**: Descompon la tasca en subtasques específiques
2. **Execució**: Executa cada subtasca amb context enriquit
3. **Síntesi**: Combina resultats eliminant redundàncies
4. **Verificació**: Valida la qualitat de la resposta final

## Seguretat

### Comandes Prohibides
- `rm`, `rmdir`, `dd`, `shred`
- `sudo`, `su`, `chmod`, `chown`
- `kill`, `reboot`, `shutdown`

### Comandes Permeses
- Eines de desenvolupament: `git`, `npm`, `pip`, `docker`
- Anàlisi d’arxius: `cat`, `grep`, `find`, `head`, `tail`
- Compilació: `make`, `cmake`, `gradle`, `maven`

## Solució de Problemes

### Error: "llama-cli no trobat"
```bash
# Verificar instal·lació de llama.cpp
which llama-cli

# Actualitzar ruta a config
vim config/settings.json
```

### Error: "Model no trobat"
```bash
# Verificar ruta del model
ls -la /ruta/a/tu/modelo.gguf

# Actualitzar configuració
claudia --config config/settings.json
```

### Mode Agèntic no Funciona
```bash
# Verificar mode verbose
claudia-deep "test simple"

# Veure logs
tail -f logs/assistant.log
```

## Contribució

1. Fork del repositori
2. Crear branca per a la teva feature: `git checkout -b feature/nova-funcionalitat`
3. Commit de canvis: `git commit -am 'Afegir nova funcionalitat'`
4. Push a la branca: `git push origin feature/nova-funcionalitat`
5. Crear Pull Request

## Llicència

MIT License - Veure arxiu LICENSE per a detalls.

## Autor

**Gustavo Silva da Costa (Eto Demerzel)**

## Versió

**2.0.0** - Sistema agèntic millorat amb planificació intel·ligent i síntesi sense redundàncies.

---

*Per a suport addicional, crea un issue al repositori del projecte.*
