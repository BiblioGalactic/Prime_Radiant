# 🤖 Local-CROS: Erreferentzia Gurutzatua Optimaziorako Sistema

## Deskribapena

**Local-CROS** LLaMA eredu lokaletarako ebaluazio gurutzatu aurreratua da, eredu anitzen arteko erantzunak konparatu eta sintesi adimentsu bidez erantzun optimizatuak sortzeko aukera ematen duena. Sistemak ebaluazio elkarrekiko ikuspegi berezia ezartzen du, non eredu bakoitzak beste guztien erantzunak ebaluatzen dituen.

## Ezaugarri Nagusiak

### 🔄 Ebaluazio Gurutzatua
- **Ebaluazio elkarrekia**: Eremu bakoitzak beste guztien erantzunak ebaluatzen ditu
- **Ikuspuntu anitz**: Galdera berari hainbat ikuspegi desberdin eskuratu
- **Puntuazio automatikoa**: Erantzun bakoitzarentzat puntuazio sistema automatikoa
- **Historia osoa**: Elkarreragin guztien erregistro zehatza

### 🎯 Sintesi Adimentsua
- **Eduki motaren detekzio automatikoa**: Kodea, zerrendak, poesia, elkarrizketak, etab.
- **Konbinazio optimizatua**: Erantzun onenak zatika fusionatu
- **Errepikapenak ezabatu**: Informazio errepikatuak saihestu
- **Testuinguruaren arabera gomendioak**: Eduki motaren arabera gomendio zehatzak

### 📊 Fitxategi Sistema Incrementala
- **Zenbaketa automatikoa**: `modelo1.txt`, `modelo2.txt`, etab.
- **Historia metatua**: Exekuzio guztiak fitxategi zentral batean
- **Timestamp zehatzak**: Operazio bakoitzaren denbora erregistroa
- **Jarraipena osoa**: Garapen osoaren jarraipena

## Sistemaren Eskakizunak

- **llama.cpp** konpilatua eta funtzionala
- **2-4 GGUF modelo** bateragarriak
- **Bash 4.0+**
- **Tresna oinarrizkoak**: `find`, `sed`, `sort`, `jq` (aukerakoa)
- **Sistema eragilea**: macOS, Linux

## Instalazioa

### 1. Deskarga
```bash
# Errepoa klonatu
git clone https://github.com/tu-usuario/local-cros.git
cd local-cros

# Exekutagarria egin
chmod +x local-cros.sh
```

### 2. Lehen Konfigurazioa
```bash
# Lehen aldiz exekutatu (konfigurazio interaktiboa)
./local-cros.sh
```

Scriptak honakoak eskatuko dizkizu:
- **llama-cli bidea**: llama.cpp binarioaren kokapena
- **Lan direktorioa**: emaitzak gordetzeko lekua
- **Modeloen konfigurazioa**: modelo bakoitzaren izena eta bidea (2-4 modelo)

### 3. Sortutako Konfigurazio Fitxategia
```bash
# local-cros.conf
LLAMA_CLI_PATH="/path/to/llama-cli"
WORK_DIR="./results"

MODEL_1_NAME="mistral"
MODEL_1_PATH="/path/to/mistral.gguf"

MODEL_2_NAME="llama"
MODEL_2_PATH="/path/to/llama.gguf"
# ... eta abar
```

## Erabilera

### Modu Interaktiboa
```bash
./local-cros.sh
Zer behar duzu?
> Idatzi Python programazioari buruzko poema epiko bat
```

### Komando zuzeneko modua
```bash
./local-cros.sh "React eta Vue.js arteko desberdintasunak azaldu"
```

### Irteeraren Adibidea
```
🤖 Hasierako eredu konparaketa: "Programazio funtzionala azaldu"

==> mistral kontsultatuz...
[mistral] dio: Programazio funtzionala paradigma bat da...
---

==> llama kontsultatuz...
[llama] dio: Programazio funtzionalean, funtzioak dira...
---

=== EREDUEN ARTEKO EBALUAZIOA ===
=== MISTRAL EKIN EBALUAZIOA ===
llama ebaluatzen: Erantzuna zehatza eta ondo egituratua da...

=== ERANTZUN ONEN KONBINAZIOA ===
💻 Erantzun konbinatu bat sortu eta gorde da!
📋 Historia osoa hemen: ./results/complete_history.txt
```

## Sortutako Fitxategien Egitura

```
results/
├── responses/
│   ├── mistral1.txt, mistral2.txt, mistral3.txt...
│   ├── llama1.txt, llama2.txt, llama3.txt...
│   ├── codellama1.txt, codellama2.txt...
│   └── response_combined_final.txt
└── complete_history.txt
```

## Funtzionalitate Aurreratuak

### Eduki Motaren Detekzio Automatikoa

Sistema automatikoki detektatzen du edukia eta testuinguruaren arabera optimizatzen du:

- **Kodea**: `python`, `javascript`, `bash`, `c++`
- **Zerrendak**: Pauso bakoitzeko argibideak
- **Poesia**: Haikuak, bertsoak, estrofa
- **Elkarrizketak**: Solasaldiak, gidoiak
- **Testu orokorra**: Azalpenak, saiakerak

### Ebaluazio Sistema

Eredu bakoitzak berezitasun zehatzak dituzten irizpideekin ebaluatzen du erantzunak:
- **Teknika zehaztasuna**
- **Azalpen argitasuna**
- **Erantzunaren osotasuna**
- **Testuinguruarekiko egokitasuna**

### Testuinguruaren Araberako Gomendioak

```bash
# Kodearentzat
💻 Gomendioa: Exekutatu 'python3 respuesta_final.py' probatzeko

# Zerrendetarako
📋 Gomendioa: Gorde PDF moduan edo partekatu argibide moduan

# Poesiarentzat
🎭 Gomendioa: Literatur analisi perfektua

# Elkarrizketarako
🎬 Gomendioa: Gidoiak edo rol-jokoetarako aproposa
```

## Konfigurazio Aurreratua

### Ereduaren Parametroak
```bash
# local-cros.sh editatu parametroak aldatzeko
-n 200           # Token maximo kopurua
--temp 0.7       # Tenperatura (sormena)
--top-k 40       # Top-k sampling
--top-p 0.9      # Top-p sampling
--repeat-penalty 1.1  # Errepikapen zigorrak
```

### Ebaluazioaren Pertsonalizazioa
```bash
# evaluate_response() funtzioko ebaluazio prompta aldatu
local evaluation_prompt="Ebaluatu erantzun hau irizpide hauen arabera..."
```

## Kasu Erabilerak

### 1. Software Garapena
```bash
./local-cros.sh "Bubble sort algoritmo hau optimizatu"
# Optimiazio ikuspegi anitz lortu
```

### 2. Sorkuntza Idazketa
```bash
./local-cros.sh "Idatzi elkarrizketa Sócrates eta Steve Jobs artean, etikari buruz"
# Estilo narratibo desberdinak konbinatu
```

### 3. Azterketa Teknikoa
```bash
./local-cros.sh "Microservizioen abantaila eta desabantailak azaldu"
# Ikuspuntu tekniko anitz konbinatu
```

### 4. Arazoen Konponketa
```bash
./local-cros.sh "Nola debug egin C++ memory leak bat"
# Debugging ikuspegi desberdinak
```

## Metrixak eta Analisiak

### Historia Osoa
`complete_history.txt` fitxategiak honako hau dauka:
```
#=== EXEKUZIOA 2025-01-21 15:30:15 ===
EREDUA: mistral1
GALDERA: Zer da machine learning?
ERANTZUNA: Machine learning adimen artifizialaren adar bat da...

#=== EBALUAZIOA 2025-01-21 15:30:45 ===
EBALUATZAILEA: llama
EBALUATZEN: Machine learning adimen artifizialaren adar bat da...
EMAITZA: Erantzun zehatza eta ondo egituratua...

#=== ERANTZUN KONBINATUA 2025-01-21 15:31:00 ===
MOTA: testu_orokorra
KONBINAZIOA: Machine learning diziplina bat da...
```

### Joeren Analisia
```bash
# Erantzun kopurua eredu bakoitzeko kontatu
grep -c "EREDUA:" results/complete_history.txt

# Denbora eboluzioa ikusi
grep "EXEKUZIOA" results/complete_history.txt | tail -10
```

## Arazoen Konponketa

### Error: "llama-cli aurkitu ez da"
```bash
# Instalazioa egiaztatu
which llama-cli

# Konfigurazioa eguneratu
vim local-cros.conf
```

### Error: "Modeloa exekutatu ezin izan da"
```bash
# Modeloaren bidea egiaztatu
ls -la /path/to/your/model.gguf

# Eskuz probatu
/path/to/llama-cli -m /path/to/model.gguf -p "test"
```

### Kalitate txarreko erantzunak
```bash
# Scriptaren parametroak egokitu
--temp 0.5        # Sormen gutxiago, zehaztasun gehiago
-n 500            # Token gehiago erantzun osoagoak lortzeko
```

## Luzapenak eta Pluginak

### Eredu Berria Gehitu
1. `local-cros.conf` editatu
2. `MODEL_N_NAME` eta `MODEL_N_PATH` gehitu
3. Script berrabiarazi

### Kanpoko APIekin Integratzea
```bash
# Adibidea: Claude API-rekin ebaluazio kanpoko integrazioa
curl -X POST "https://api.anthropic.com/v1/messages" \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-3-sonnet", "messages": [...]}'
```

## Ekarpenak

1. Repositorioa forkatu
2. Adar berria sortu: `git checkout -b feature/funtzionalitate-berria`
3. Commit egin: `git commit -am 'Funtzionalitate X gehitu'`
4. Push egin: `git push origin feature/funtzionalitate-berria`
5. Pull Request sortu

## Lizentzia

MIT License

## Egilea

**Gustavo Silva da Costa**

## Bertsioa

**1.0.0** - Ebaluazio gurutzatu eta sintesi adimentsu sistema

---

*Local-CROS: Non burmuin artifizial anitz elkarlanean aritzen diren erantzun hobeak sortzeko.*
