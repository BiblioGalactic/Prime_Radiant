# 🤖 Configuració Assistente IA Local - Configurador Bàsic

## Descripció

Script d’instal·lació automatitzada per configurar un Assistente IA Local bàsic que utilitza models llama.cpp. Aquest instal·lador està dissenyat per ser simple, directe i fàcil d’utilitzar, proporcionant una base sòlida per interactuar amb models de llenguatge locals.

## Característiques Principals

### 🔧 Configuració Simple i Intuïtiva
- **Instal·lació guiada**: Configuració pas a pas interactiva
- **Validació automàtica**: Verificació de prerequisits i rutes
- **Configuració adaptativa**: S’ajusta a diferents entorns
- **Estructura modular**: Arquitectura organitzada i extensible

### 🎯 Funcionalitats Core
- **Client LLM**: Comunicació directa amb llama.cpp
- **Gestor d’arxius**: Operacions segures de lectura/escriptura
- **Executor de comandes**: Execució controlada del sistema
- **Configuració flexible**: JSON configurable

### 📁 Arquitectura Modular
```
src/
├── core/           # Motor principal de l’assistent
├── llm/            # Client per a llama.cpp
├── file_ops/       # Gestió d’arxius
└── commands/       # Execució de comandes
```

## Requisits del Sistema

- **Python 3.11+**
- **llama.cpp** compilat
- **Model GGUF** compatible
- **pip3** per a dependències Python
- **Sistema operatiu**: macOS, Linux

## Instal·lació Ràpida

### 1. Descàrrega i Execució
```bash
# Descarregar l’script
curl -O https://raw.githubusercontent.com/tu-usuario/asistente-basico/main/setup_asistente_basico.sh

# Fer executable
chmod +x setup_asistente_basico.sh

# Executar instal·lació
./setup_asistente_basico.sh
```

### 2. Configuració Interactiva

L’script et sol·licitarà:

**Directori del projecte:**
```
Directori del projecte [/Users/tu-usuario/asistente-ia]: 
```

**Ruta del model GGUF:**
```
Ruta del model GGUF [/Users/tu-usuario/modelo/modelo.gguf]: 
```

**Ruta de llama-cli:**
```
Ruta de llama.cpp [/Users/tu-usuario/llama.cpp/build/bin/llama-cli]: 
```

### 3. Confirmació
```
Configuració seleccionada:
Directori del projecte: /Users/tu-usuario/asistente-ia
Model: /Users/tu-usuario/modelo/modelo.gguf
Llama.cpp: /Users/tu-usuario/llama.cpp/build/bin/llama-cli

¿Continuar amb aquesta configuració? (y/N)
```

## Estructura Generada

```
asistente-ia/
├── src/
│   ├── main.py                 # Punt d’entrada principal
│   ├── core/
│   │   ├── assistant.py        # Classe principal de l’assistent
│   │   └── config.py           # Gestió de configuració
│   ├── llm/
│   │   └── client.py           # Client llama.cpp
│   ├── file_ops/
│   │   └── manager.py          # Gestió d’arxius
│   └── commands/
│       └── runner.py           # Execució de comandes
├── config/
│   └── settings.json           # Configuració principal
├── tools/                      # Eines addicionals
├── tests/                      # Tests del sistema
├── logs/                       # Arxius de log
└── examples/                   # Exemples d’ús
```

## Ús Bàsic

### Comanda Principal
```bash
cd /ruta/al/teu/asistente-ia
python3 src/main.py "Quins arxius Python hi ha en aquest projecte?"
```

### Mode Interactiu
```bash
python3 src/main.py
🤖 Assistente IA Local - Mode interactiu
Escriu 'exit' per sortir, 'help' per ajuda

💬 > explica l’arxiu main.py
🤖 L’arxiu main.py és el punt d’entrada...

💬 > exit
Fins aviat! 👋
```

### Paràmetres de Línia de Comandes
```bash
# Usar configuració específica
python3 src/main.py --config config/custom.json "analitza aquest projecte"

# Mode verbose
python3 src/main.py --verbose "llista arxius Python"

# Ajuda
python3 src/main.py --help
```

## Configuració

### Arxiu de Configuració (config/settings.json)
```json
{
  "llm": {
    "model_path": "/ruta/al/teu/model.gguf",
    "llama_bin": "/ruta/al/llama-cli",
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

### Personalització de Paràmetres LLM
- **max_tokens**: Longitud màxima de resposta
- **temperature**: Creativitat (0.0 = determinista, 1.0 = creatiu)
- **model_path**: Ruta al teu model GGUF
- **llama_bin**: Ruta al binari llama-cli

### Configuració de Seguretat
- **safe_mode**: Activar mode segur per a comandes
- **backup_files**: Crear còpies de seguretat abans de modificar
- **max_file_size**: Mida màxima d’arxiu a processar
- **supported_extensions**: Tipus d’arxiu suportats

## Funcionalitats Principals

### 1. Anàlisi d’Arxius
```bash
python3 src/main.py "explica què fa l’arxiu config.py"
```

### 2. Llistat d’Arxius
```bash
python3 src/main.py "mostra tots els arxius Python del projecte"
```

### 3. Anàlisi d’Estructura
```bash
python3 src/main.py "descriu l’arquitectura d’aquest projecte"
```

### 4. Ajuda amb Codi
```bash
python3 src/main.py "com puc millorar la funció load_config?"
```

## Comandes Disponibles

### Comandes d’Ajuda
- `help` - Mostrar ajuda completa
- `exit` - Sortir del mode interactiu

### Exemples de Consultes
- "explica l’arxiu X"
- "llista arxius de tipus Y"
- "descriu l’estructura del projecte"
- "com funciona la classe Z"
- "què fa la funció W"

## Validacions i Seguretat

### Validacions Automàtiques
- ✅ Verificació de Python 3.11+
- ✅ Verificació de pip3
- ✅ Validació de ruta de llama-cli
- ✅ Validació de model GGUF
- ⚠️ Advertències per arxius no trobats

### Mode Segur
```json
{
  "assistant": {
    "safe_mode": true,     // Restriccions de comandes
    "backup_files": true,  // Backups automàtics
    "max_file_size": 1048576  // Límits 1MB per arxiu
  }
}
```

## Extensió i Personalització

### Afegir Nous Tipus d’Arxiu
```json
{
  "assistant": {
    "supported_extensions": [".py", ".js", ".go", ".rust", ".cpp"]
  }
}
```

### Modificar Prompts
Edita `src/core/assistant.py` al mètode `_build_prompt()`:

```python
def _build_prompt(self, context: Dict, user_input: str) -> str:
    prompt = f"""Ets un assistent especialitzat en {tu_dominio}.
    
    CONTEXT: {context}
    CONSULTA: {user_input}
    
    Respon de forma {tu_estil}."""
    
    return prompt
```

### Afegir Nous Comandes
Modifica `src/commands/runner.py` per incloure nous comandes permeses:

```python
self.safe_commands = {
    'ls', 'cat', 'grep', 'find',  # Bàsics
    'git', 'npm', 'pip',          # Desenvolupament
    'tu_comando_personalizado'    # Nova comanda
}
```

## Solució de Problemes

### Error: "Python3 no està instal·lat"
```bash
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt update && sudo apt install python3.11
```

### Error: "llama-cli no trobat"
```bash
# Verificar instal·lació de llama.cpp
ls -la /ruta/al/llama.cpp/build/bin/llama-cli

# Actualitzar ruta a configuració
vim config/settings.json
```

### Error: "Model no trobat"
```bash
# Verificar model
ls -la /ruta/al/teu/model.gguf

# Descarregar model si cal
wget https://huggingface.co/modelo/resolve/main/modelo.gguf
```

### Problemes de Rendiment
```json
{
  "llm": {
    "max_tokens": 512,      // Reduir per respostes més ràpides
    "temperature": 0.3      // Menys creativitat = més ràpid
  }
}
```

## Integració amb Editors

### VSCode
```json
// tasks.json
{
    "label": "Consultar Assistente",
    "type": "shell",
    "command": "python3",
    "args": ["src/main.py", "${input:consulta}"],
    "group": "build"
}
```

### Vim/NeoVim
```vim
" Mapeig per consultar assistent
nnoremap <leader>ai :!python3 src/main.py "<C-R><C-W>"<CR>
```

## Contribució i Desenvolupament

### Estructura per Contribuir
1. Fork del repositori
2. Crear branca: `git checkout -b feature/nova-funcionalitat`
3. Desenvolupar en l’arquitectura modular existent
4. Afegir tests a `tests/`
5. Documentar a `examples/`
6. Crear Pull Request

### Guia de Desenvolupament
- Seguir l’arquitectura modular existent
- Afegir validacions per a noves funcionalitats
- Mantenir compatibilitat amb la configuració JSON
- Incloure logging apropiat

## Llicència

MIT License

## Autor

**Gustavo Silva da Costa (Eto Demerzel)**

## Versió

**1.0.0** - Configurador bàsic amb arquitectura modular sòlida

---

*Un assistent IA local simple però potent per potenciar el teu flux de treball de desenvolupament.*
