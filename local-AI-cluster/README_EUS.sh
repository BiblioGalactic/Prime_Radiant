# 🤖 AI Cluster - IA Sistema Banatua

**Prozesatu IA kontsultak paraleloan zure sare lokaleko (intranet) makina anitz erabiliz.**

Hodeiarik gabe • Pribatua • Eskalagarria • Kode irekia

---

## 📋 Deskribapena

AI Cluster sistema bat da zure sare lokaleko ordenagailu inaktiboek IA ereduak era banatuan exekutatzen laguntzen dizuna. Hau bilatzen duten enpresentzat ezin hobea:

- ✅ **Pribatutasun osoa** - Datuak ez dira inoiz zure saretik ateratzen
- ✅ **Hodei kostu zero** - Erabili zure dagoen hardwarea
- ✅ **GDPR betetzea** - Dena zure azpiegituran
- ✅ **Eskalagarria** - Gehitu makinak erraz
- ✅ **Paralelizazioa** - Exekutatu kontsultak aldi berean

---

## 🚀 Erabilera kasuak

### Enpresentzat
- Hainbat IA kontsulta prozesatzea bulegoko PCak erabiliz
- Dokumentuen azterketa banatua
- Eduki sorkuntza paraleloan
- Ataza errepikakorren automatizazioa

### Garatzaileentzat
- Sistema banatuekin esperimentatzea
- Paralelizazioa ikastea
- Ereduen errendimendu probak
- Soluzio azkarraren prototipazioa

---

## 🎯 Ezaugarriak

- ✨ **Morroi interaktiboa** - Konfigurazioa pausuz pauso gidatua
- 🔐 **SSH konfigurazio automatikoa** - Ezarri pasahitzik gabeko konexioak
- 🌐 **Makina anitza** - Sareko N ordenagailuen laguntza
- ⚖️ **Round-robin balantzea** - Banatu karga uniformeki
- 📊 **Estatistika xehatuak** - Monitorizatu prozesatzea
- 🛡️ **Errore kudeaketa sendoa** - Jarraitu makinak huts egiten badute ere

---

## 📦 Baldintzak

### Makina guztietan:

1. **llama.cpp konpilatua**
   ```bash
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp
   make
   ```

2. **GGUF eredua deskargatua**
   - Mistral, Llama, Qwen, etab.
   - Makina guztietan bide berdinean kokatuta

3. **SSH aktibatua** (urruneko makinetan soilik)
   ```bash
   # macOS
   sudo systemsetup -setremotelogin on
   
   # Linux
   sudo systemctl enable ssh
   sudo systemctl start ssh
   ```

---

## ⚙️ Instalazioa

### 1. Deskargatu scripta

```bash
# Klonatu errepositorioa
git clone https://github.com/BiblioGalactic/ai-cluster
cd ai-cluster

# Edo deskargatu zuzenean
curl -O https://raw.githubusercontent.com/BiblioGalactic/ai-cluster/main/ai-cluster.sh
chmod +x ai-cluster.sh
```

### 2. Hasierako konfigurazioa

```bash
./ai-cluster.sh setup
```

Morroiak gidatuko zaitu honetan:
- ✅ Detektatu llama.cpp eta eredu lokalak
- ✅ Konfiguratu urruneko makinen IPak
- ✅ Konfiguratu pasahitzik gabeko SSH
- ✅ Egiaztatu konexioak eta fitxategiak

---

## 📖 Erabilera

### Oinarrizko komandoa

```bash
./ai-cluster.sh run queries.txt
```

### Kontsulta fitxategia

Sortu `queries.txt` fitxategi bat zure galderekin, bakoitza lerro batean:

```
Azaldu iezadazu zer den sare neuronal bat
Laburtu erlatibitate teoria
Zein da Japoniaren hiriburua?
Idatzi teknologiari buruzko haiku bat
```

### Beste komandoak

```bash
# Erakutsi uneko konfigurazioa
./ai-cluster.sh config

# Probatu konexioak
./ai-cluster.sh test

# Birkonfiguratu
./ai-cluster.sh setup

# Laguntza
./ai-cluster.sh help
```

---

## 🏗️ Arkitektura

```
┌─────────────────────────────────────────────────┐
│        ai-cluster.sh (Orkestragailua)            │
└─────────────┬───────────────────────────────────┘
              │
      ┌───────┴────────┬──────────────┬──────────┐
      │                │              │          │
  ┌───▼────┐      ┌───▼────┐    ┌───▼────┐ ┌───▼────┐
  │ Lokala │      │ PC 1   │    │ PC 2   │ │ PC N   │
  │ (Mac)  │      │ (SSH)  │    │ (SSH)  │ │ (SSH)  │
  └────────┘      └────────┘    └────────┘ └────────┘
  Query1,5,9      Query2,6,10   Query3,7   Query4,8
```

**Round-Robin banaketa:**
- Kontsulta #1 → Makina lokala
- Kontsulta #2 → Urruneko makina 1
- Kontsulta #3 → Urruneko makina 2
- Kontsulta #4 → Urruneko makina 3
- Kontsulta #5 → Makina lokala (berriz hasita)

---

## 🔧 Konfigurazio aurreratua

### `.ai_cluster_config` fitxategia

Setup ostean, fitxategi hau sortzen da konfigurazioaren datuekin:

```bash
# Makina lokala
LOCAL_LLAMA="/Users/user/modelo/llama.cpp/build/bin/llama-cli"
LOCAL_MODEL="/Users/user/modelo/mistral-7b.gguf"

# Urruneko makinak (komaz bananduta)
REMOTE_IPS="192.168.1.82,192.168.1.83"
REMOTE_USER="username"
REMOTE_LLAMA="/home/user/llama.cpp/build/bin/llama-cli"
REMOTE_MODEL="/home/user/mistral-7b.gguf"

# SSH konexioen arteko atzerapena (segundoak)
REMOTE_DELAY=10
```

Behar izanez gero, eskuz editatu dezakezu.

---

## 📊 Irteera adibidea

```
╔═══════════════════════════════════════════════════════════╗
║     🤖 AI Cluster - IA Sistema Banatua 🤖                ║
║     Prozesamendu paraleloa sare lokala erabiliz          ║
╚═══════════════════════════════════════════════════════════╝

[17:30:00] 🎯 Kontsulta guztira: 20
[i] Makina erabilgarriak: 3 (1 lokala + 2 urrunekoak)

[17:30:00] 💻 [Lokala] Kontsulta #1: Sare neuronala...
[17:30:00] 🌐 [192.168.1.82] Kontsulta #2: Teoria...
[17:30:00] 🌐 [192.168.1.83] Kontsulta #3: Hiriburua...
[17:30:02] ✓ [Lokala] Kontsulta #1 osatuta
[17:30:15] ✓ [192.168.1.82] Kontsulta #2 osatuta
[17:30:18] ✓ [192.168.1.83] Kontsulta #3 osatuta

...

[17:35:00] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[17:35:00] ✓ ✨ Osatuta
[17:35:00] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[i] Prozesatutako guztira: 20 kontsulta
[i] Emaitzak hemen: results_cluster/
```

---

## 🐛 Arazoen konponketa

### SSH-k pasahitza eskatzen du beti

```bash
# Exekutatu setup berriro ssh-copy-id konfiguratzeko
./ai-cluster.sh setup
```

### "llama-cli not found" urruneko makinetan

Egiaztatu bideak `.ai_cluster_config`-en:

```bash
# Exekutatu urruneko makinan:
which llama-cli
# Edo bilatu:
find ~ -name "llama-cli" 2>/dev/null
```

### Kontsultak ez dira prozesatzen

```bash
# Probatu konexioak
./ai-cluster.sh test

# Berrikusi banakako logak
cat results_cluster/result_2_*.txt
```

### Scripta motela da Mac Minietan

`.zshrc`-ko script automatikoak SSH moteldu dezakete. Gehitu urruneko makinen `.zshrc`-ren hasieran:

```bash
# Isilik SSH ez-interaktiboa
[[ -n "$SSH_CONNECTION" ]] && [[ ! -t 0 ]] && return
```

---

## 🤝 Ekarpenak

Ekarpenak ongi etorriak dira!

1. Egin proiektuaren fork bat
2. Sortu ezaugarri adarra (`git checkout -b feature/EzaugarriIkaragarria`)
3. Commit aldaketak (`git commit -m 'Gehitu EzaugarriIkaragarri bat'`)
4. Push adarrean (`git push origin feature/EzaugarriIkaragarria`)
5. Ireki Pull Request bat

---

## 📝 Bide orria

- [ ] Denbora errealeko web dashboard-a
- [ ] Docker edukiontzien laguntza
- [ ] Sareko makinen auto-aurkikuntza
- [ ] Emaitzen cachea
- [ ] Lehentasun sistema
- [ ] Errendimendu metrikak
- [ ] Kubernetes integrazioa

---

## 📄 Lizentzia

MIT Lizentzia - ikusi [LICENSE](LICENSE) fitxategia

---

## 👨‍💻 Egilea

**Gustavo Silva da Costa** (BiblioGalactic)

- GitHub: [@BiblioGalactic](https://github.com/BiblioGalactic)
- Proiektua: Ziberrealismoa enpresa azpiegituretara aplikatua

---

## 🙏 Eskerrak

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Inferentzia motorea
- [Anthropic Claude](https://claude.ai) - Garapenean laguntza
- IA lokaleko kode irekiko komunitatea

---

## ⚠️ Lege abisua

Software hau "dagoen bezala" ematen da, bermerik gabe. Erabilera zure erantzukizunpekoa da. Egileak ez du erantzukizunik hartzen datu galera, hardware hutsegite edo software honen erabileratik eratorritako bestelako kalteen gainean.

---

## 📚 Baliabideak

- [llama.cpp dokumentazioa](https://github.com/ggerganov/llama.cpp)
- [GGUF eredu erabilgarriak](https://huggingface.co/models?library=gguf)
- [Pasahitzik gabeko SSH konfigurazioa](https://www.ssh.com/academy/ssh/copy-id)

---

**Proiektu honek lagundu badizu, eman ⭐ bat GitHub-en**