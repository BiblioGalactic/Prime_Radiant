# 🤖 AI Cluster - Sistema d'IA Distribuït

**Processa consultes d'IA en paral·lel utilitzant múltiples màquines a la teva xarxa local (intranet).**

Sense núvol • Privat • Escalable • Codi obert

---

## 📋 Descripció

AI Cluster és un sistema que et permet aprofitar ordinadors inactius a la teva xarxa local per executar models d'IA de manera distribuïda. Ideal per a empreses que busquen:

- ✅ **Privadesa total** - Les dades mai surten de la teva xarxa
- ✅ **Zero costos de núvol** - Utilitza el teu hardware existent
- ✅ **Compliment GDPR** - Tot dins la teva infraestructura
- ✅ **Escalable** - Afegeix màquines fàcilment
- ✅ **Paral·lelització** - Executa consultes simultàniament

---

## 🚀 Casos d'ús

### Per a empreses
- Processament de múltiples consultes d'IA utilitzant PCs d'oficina
- Anàlisi distribuïda de documents
- Generació de contingut en paral·lel
- Automatització de tasques repetitives

### Per a desenvolupadors
- Experimentació amb sistemes distribuïts
- Aprenentatge de paral·lelització
- Proves de rendiment de models
- Prototipat ràpid de solucions

---

## 🎯 Característiques

- ✨ **Assistent interactiu** - Configuració guiada pas a pas
- 🔐 **Configuració SSH automàtica** - Estableix connexions sense contrasenya
- 🌐 **Multi-màquina** - Suporta N ordinadors a la xarxa
- ⚖️ **Balanceig round-robin** - Distribueix la càrrega uniformement
- 📊 **Estadístiques detallades** - Monitoritza el processament
- 🛡️ **Gestió robusta d'errors** - Continua encara que fallin màquines

---

## 📦 Requisits

### A totes les màquines:

1. **llama.cpp compilat**
   ```bash
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp
   make
   ```

2. **Model GGUF descarregat**
   - Mistral, Llama, Qwen, etc.
   - Ubicat al mateix path a totes les màquines

3. **SSH activat** (només màquines remotes)
   ```bash
   # macOS
   sudo systemsetup -setremotelogin on
   
   # Linux
   sudo systemctl enable ssh
   sudo systemctl start ssh
   ```

---

## ⚙️ Instal·lació

### 1. Descarrega l'script

```bash
# Clona el repositori
git clone https://github.com/BiblioGalactic/ai-cluster
cd ai-cluster

# O descarrega directament
curl -O https://raw.githubusercontent.com/BiblioGalactic/ai-cluster/main/ai-cluster.sh
chmod +x ai-cluster.sh
```

### 2. Configuració inicial

```bash
./ai-cluster.sh setup
```

L'assistent et guiarà per:
- ✅ Detectar llama.cpp i models locals
- ✅ Configurar IPs de màquines remotes
- ✅ Configurar SSH sense contrasenya
- ✅ Verificar connexions i arxius

---

## 📖 Ús

### Comanda bàsica

```bash
./ai-cluster.sh run queries.txt
```

### Arxiu de consultes

Crea un arxiu `queries.txt` amb les teves preguntes, una per línia:

```
Explica'm què és una xarxa neuronal
Resumeix la teoria de la relativitat
Quina és la capital del Japó?
Escriu un haiku sobre tecnologia
```

### Altres comandes

```bash
# Mostra la configuració actual
./ai-cluster.sh config

# Prova les connexions
./ai-cluster.sh test

# Reconfigura
./ai-cluster.sh setup

# Ajuda
./ai-cluster.sh help
```

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────┐
│        ai-cluster.sh (Orquestrador)              │
└─────────────┬───────────────────────────────────┘
              │
      ┌───────┴────────┬──────────────┬──────────┐
      │                │              │          │
  ┌───▼────┐      ┌───▼────┐    ┌───▼────┐ ┌───▼────┐
  │ Local  │      │ PC 1   │    │ PC 2   │ │ PC N   │
  │ (Mac)  │      │ (SSH)  │    │ (SSH)  │ │ (SSH)  │
  └────────┘      └────────┘    └────────┘ └────────┘
  Query1,5,9      Query2,6,10   Query3,7   Query4,8
```

**Distribució Round-Robin:**
- Consulta #1 → Màquina local
- Consulta #2 → Màquina remota 1
- Consulta #3 → Màquina remota 2
- Consulta #4 → Màquina remota 3
- Consulta #5 → Màquina local (torna a començar)

---

## 🔧 Configuració avançada

### Arxiu `.ai_cluster_config`

Després del setup, es crea aquest arxiu amb la configuració:

```bash
# Màquina local
LOCAL_LLAMA="/Users/user/modelo/llama.cpp/build/bin/llama-cli"
LOCAL_MODEL="/Users/user/modelo/mistral-7b.gguf"

# Màquines remotes (separades per comes)
REMOTE_IPS="192.168.1.82,192.168.1.83"
REMOTE_USER="username"
REMOTE_LLAMA="/home/user/llama.cpp/build/bin/llama-cli"
REMOTE_MODEL="/home/user/mistral-7b.gguf"

# Retard entre connexions SSH (segons)
REMOTE_DELAY=10
```

Pots editar-lo manualment si cal.

---

## 📊 Exemple de sortida

```
╔═══════════════════════════════════════════════════════════╗
║     🤖 AI Cluster - Sistema d'IA Distribuït 🤖           ║
║     Processament paral·lel utilitzant xarxa local        ║
╚═══════════════════════════════════════════════════════════╝

[17:30:00] 🎯 Total consultes: 20
[i] Màquines disponibles: 3 (1 local + 2 remotes)

[17:30:00] 💻 [Local] Consulta #1: Xarxa neuronal...
[17:30:00] 🌐 [192.168.1.82] Consulta #2: Teoria...
[17:30:00] 🌐 [192.168.1.83] Consulta #3: Capital...
[17:30:02] ✓ [Local] Consulta #1 completada
[17:30:15] ✓ [192.168.1.82] Consulta #2 completada
[17:30:18] ✓ [192.168.1.83] Consulta #3 completada

...

[17:35:00] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[17:35:00] ✓ ✨ Completat
[17:35:00] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[i] Total processades: 20 consultes
[i] Resultats a: results_cluster/
```

---

## 🐛 Resolució de problemes

### SSH demana contrasenya cada vegada

```bash
# Torna a executar setup per configurar ssh-copy-id
./ai-cluster.sh setup
```

### "llama-cli not found" a màquines remotes

Verifica els paths a `.ai_cluster_config`:

```bash
# Executa a la màquina remota:
which llama-cli
# O cerca:
find ~ -name "llama-cli" 2>/dev/null
```

### Les consultes no es processen

```bash
# Prova les connexions
./ai-cluster.sh test

# Revisa els logs individuals
cat results_cluster/result_2_*.txt
```

### L'script va lent al Mac Mini

Scripts automàtics al `.zshrc` poden alentir SSH. Afegeix al principi del `.zshrc` de les màquines remotes:

```bash
# Silencia SSH no interactiu
[[ -n "$SSH_CONNECTION" ]] && [[ ! -t 0 ]] && return
```

---

## 🤝 Contribucions

Les contribucions són benvingudes!

1. Fes fork del projecte
2. Crea una branca de característica (`git checkout -b feature/CaracteristicaIncreiblé`)
3. Commit els canvis (`git commit -m 'Afegeix alguna CaracteristicaIncreiblé'`)
4. Push a la branca (`git push origin feature/CaracteristicaIncreiblé`)
5. Obre un Pull Request

---

## 📝 Full de ruta

- [ ] Dashboard web en temps real
- [ ] Suport per contenidors Docker
- [ ] Auto-descobriment de màquines a la xarxa
- [ ] Caché de resultats
- [ ] Sistema de prioritats
- [ ] Mètriques de rendiment
- [ ] Integració amb Kubernetes

---

## 📄 Llicència

Llicència MIT - veure arxiu [LICENSE](LICENSE)

---

## 👨‍💻 Autor

**Gustavo Silva da Costa** (BiblioGalactic)

- GitHub: [@BiblioGalactic](https://github.com/BiblioGalactic)
- Projecte: Ciberrealisme aplicat a infraestructures empresarials

---

## 🙏 Agraïments

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Motor d'inferència
- [Anthropic Claude](https://claude.ai) - Assistència en el desenvolupament
- Comunitat de codi obert d'IA local

---

## ⚠️ Avís legal

Aquest programari es proporciona "tal qual", sense garanties. L'ús és sota la teva responsabilitat. L'autor no es fa responsable de pèrdua de dades, fallades de hardware o altres danys derivats de l'ús d'aquest programari.

---

## 📚 Recursos

- [Documentació llama.cpp](https://github.com/ggerganov/llama.cpp)
- [Models GGUF disponibles](https://huggingface.co/models?library=gguf)
- [Configuració SSH sense contrasenya](https://www.ssh.com/academy/ssh/copy-id)

---

**Si aquest projecte t'ha estat útil, considera donar-li una ⭐ a GitHub**