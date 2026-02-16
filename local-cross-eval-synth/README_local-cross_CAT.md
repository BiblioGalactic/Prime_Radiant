# 🤖 Local-CROS: Cross-Referential Optimization System

## Descripció

**Local-CROS** és un sistema avançat d'avaluació creuada per a models LLaMA locals que permet comparar respostes entre múltiples models i generar respostes optimitzades mitjançant síntesi intel·ligent. El sistema implementa un enfocament únic d'avaluació mútua on cada model avalua les respostes dels altres.

## Característiques Principals

### 🔄 Avaluació Creuada
- **Avaluació mútua**: Cada model avalua les respostes de tots els altres
- **Múltiples perspectives**: Obtingues diferents enfocaments per a la mateixa pregunta
- **Puntuació automàtica**: Sistema de scoring automàtic per a cada resposta
- **Historial complet**: Registre detallat de totes les interaccions

### 🎯 Síntesi Intel·ligent
- **Detecció automàtica del tipus de contingut**: Codi, llistes, poesia, diàlegs, etc.
- **Combinació optimitzada**: Fusiona les millors parts de cada resposta
- **Eliminació de redundàncies**: Evita informació repetida
- **Recomanacions contextuals**: Suggeriments específics segons el tipus de contingut

### 📊 Sistema d'Arxius Incrementals
- **Numeració automàtica**: `modelo1.txt`, `modelo2.txt`, etc.
- **Historial acumulatiu**: Totes les execucions en un arxiu central
- **Timestamps detallats**: Registre temporal de cada operació
- **Traçabilitat completa**: Seguiment de tota l'evolució

## Requisits del Sistema

- **llama.cpp** compilat i funcional
- **2-4 models GGUF** compatibles
- **Bash 4.0+**
- **Eines bàsiques**: `find`, `sed`, `sort`, `jq` (opcional)
- **Sistema operatiu**: macOS, Linux

## Instal·lació

### 1. Descàrrega
```bash
# Clonar repositori
git clone https://github.com/tu-usuario/local-cros.git
cd local-cros

# Fer executable
chmod +x local-cros.sh
```

### 2. Primera Configuració
```bash
# Executar per primera vegada (configuració interactiva)
./local-cros.sh
```

L'script et demanarà:
- **Ruta de llama-cli**: Ubicació del binari llama.cpp
- **Directori de treball**: On desar resultats
- **Configuració de models**: Nom i ruta de cada model (2-4 models)

### 3. Arxiu de Configuració Generat
```bash
# local-cros.conf
LLAMA_CLI_PATH="/path/to/llama-cli"
WORK_DIR="./results"

MODEL_1_NAME="mistral"
MODEL_1_PATH="/path/to/mistral.gguf"

MODEL_2_NAME="llama"
MODEL_2_PATH="/path/to/llama.gguf"
# ... etc
```

## Ús

### Mode Interactiu
```bash
./local-cros.sh
What do you need?
> Escriu un poema èpic sobre programació en Python
```

### Mode Comanda Directa
```bash
./local-cros.sh "Explica les diferències entre React i Vue.js"
```

### Exemple de Sortida
```
🤖 Starting model comparison for: "Explica programació funcional"

==> Consulting mistral...
[mistral] says: La programació funcional és un paradigma...
---

==> Consulting llama...
[llama] says: En programació funcional, les funcions són...
---

=== CROSS-EVALUATION BETWEEN MODELS ===
=== EVALUATION WITH MISTRAL ===
Evaluating llama: La resposta és precisa i ben estructurada...

=== COMBINING BEST RESPONSES ===
💻 Combined response generated and saved!
📋 Complete history in: ./results/complete_history.txt
```

## Estructura d'Arxius Generats

```
results/
├── responses/
│   ├── mistral1.txt, mistral2.txt, mistral3.txt...
│   ├── llama1.txt, llama2.txt, llama3.txt...
│   ├── codellama1.txt, codellama2.txt...
│   └── response_combined_final.txt
└── complete_history.txt
```

## Funcionalitats Avançades

### Detecció Automàtica del Tipus de Contingut

El sistema detecta automàticament el tipus de contingut i optimitza segons el context:

- **Codi**: `python`, `javascript`, `bash`, `c++`
- **Llistes**: Instruccions pas a pas
- **Poesia**: Haikus, versos, estrofes
- **Diàlegs**: Converses, guions
- **Text general**: Explicacions, assaigs

### Sistema d'Avaluació

Cada model avalua les respostes utilitzant criteris específics:
- **Precisió tècnica**
- **Claredat d'explicació**
- **Completesa de la resposta**
- **Rellevància al context**

### Recomanacions Contextuals

```bash
# Per a codi
💻 Recomanació: Executa 'python3 resposta_final.py' per provar

# Per a llistes
📋 Recomanació: Desa-ho com a PDF o compara com a instruccions

# Per a poesia
🎭 Recomanació: Perfecte per a anàlisi literari

# Per a diàlegs
🎬 Recomanació: Ideal per a guions o role-playing
```

## Configuració Avançada

### Paràmetres de Model
```bash
# Edita local-cros.sh per ajustar paràmetres
-n 200           # Nombre màxim de tokens
--temp 0.7       # Temperatura (creativitat)
--top-k 40       # Top-k sampling
--top-p 0.9      # Top-p sampling
--repeat-penalty 1.1  # Penalització per repetició
```

### Personalització de l'Avaluació
```bash
# Modificar el prompt d'avaluació en la funció evaluate_response()
local evaluation_prompt="Avalua aquesta resposta utilitzant aquests criteris..."
```

## Casos d'Ús

### 1. Desenvolupament de Programari
```bash
./local-cros.sh "Optimitza aquest algoritme d'ordenament bombolla"
# Obtingues múltiples enfocaments d'optimització
```

### 2. Escriptura Creativa
```bash
./local-cros.sh "Escriu un diàleg entre Sòcrates i Steve Jobs sobre ètica"
# Combina diferents estils narratius
```

### 3. Anàlisi Tècnica
```bash
./local-cros.sh "Explica els avantatges i desavantatges dels microserveis"
# Múltiples perspectives tècniques combinades
```

### 4. Resolució de Problemes
```bash
./local-cros.sh "Com debuggear un memory leak en C++"
# Diferents enfocaments de debugging
```

## Mètriques i Anàlisi

### Historial Complet
L'arxiu `complete_history.txt` conté:
```
#=== EXECUTION 2025-01-21 15:30:15 ===
MODEL: mistral1
QUESTION: ¿Què és machine learning?
RESPONSE: Machine learning és una branca de la IA...

#=== EVALUATION 2025-01-21 15:30:45 ===
EVALUATOR: llama
EVALUATING: Machine learning és una branca...
RESULT: Resposta precisa i ben estructurada...

#=== COMBINED RESPONSE 2025-01-21 15:31:00 ===
TYPE: text_general
COMBINATION: Machine learning és una disciplina...
```

### Anàlisi de Tendències
```bash
# Comptar respostes per model
grep -c "MODEL:" results/complete_history.txt

# Veure evolució temporal
grep "EXECUTION" results/complete_history.txt | tail -10
```

## Solució de Problemes

### Error: "llama-cli not found"
```bash
# Verificar instal·lació
which llama-cli

# Actualitzar configuració
vim local-cros.conf
```

### Error: "Model execution failed"
```bash
# Verificar model
ls -la /path/to/your/model.gguf

# Provar manualment
/path/to/llama-cli -m /path/to/model.gguf -p "test"
```

### Respostes de Baixa Qualitat
```bash
# Ajustar paràmetres en el script
--temp 0.5        # Menys creativitat, més precisió
-n 500            # Més tokens per a respostes completes
```

## Extensions i Plugins

### Afegir Nou Model
1. Edita `local-cros.conf`
2. Afegir `MODEL_N_NAME` i `MODEL_N_PATH`
3. Reiniciar script

### Integració amb APIs Externes
```bash
# Exemple: integrar amb Claude API per a avaluació externa
curl -X POST "https://api.anthropic.com/v1/messages" \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-3-sonnet", "messages": [...]}'
```

## Contribució

1. Fork del repositori
2. Crear branca: `git checkout -b feature/nova-funcionalitat`
3. Commit: `git commit -am 'Afegir funcionalitat X'`
4. Push: `git push origin feature/nova-funcionalitat`
5. Pull Request

## Llicència

MIT License

## Autor

**Gustavo Silva da Costa**

## Versió

**1.0.0** - Sistema d'avaluació creuada i síntesi intel·ligent

---

*Local-CROS: On múltiples ments artificials col·laboren per generar respostes superiors.*
