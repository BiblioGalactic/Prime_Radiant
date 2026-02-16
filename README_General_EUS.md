# ⚡ Prime Radiant - AI Laguntzaile Lokalen Bilduma

🧠 **Ideia konplexuak automatizatzen ditut AI lokalarekin. Bash-etik, gizakientzat.**
---

## 🌟 Zer da Prime Radiant

**Prime Radiant** AI lokalarekin lan egiteko tresna eta konfigurazioen bilduma bat da. Repositorio honek script eta sistemak ditu llama.cpp-ren bidez hizkuntza-modelo lokalak erabiliz zereginak automatizatzeko.

### 🎯 Proiektuaren Filosofia

- **Local First**: AI guztia zure makinan funtzionatzen du
- **Bash Centered**: Script boteretsua eta gardenak
- **Iteratiboa**: Esperimentu bakoitzarekin etengabeko hobekuntza

---

## 📦 Barne Hartutako Tresnak

### 🤖 [Local AI Assistant](./local-ai-assistant/)
**Gaitasun agentikoak dituen konfiguratzaile aurreratua**

- AI laguntzaile lokalaren instalazio automatizatua
- Planifikazio adimentsua duen modu agentikoa
- Fitxategi eta kodearen kudeaketa segurua

```
./setup_asistente.sh
```

### ⚔️ [Local-CROS (Cross-Referential Optimization)](./local-agentic-assistant/)
**Modeloen arteko gurutzatutako ebaluazio sistema**

- LLaMA modelo anitzen erantzunak konparatzen ditu
- Gurutzatutako ebaluazio automatikoa
- Erantzunen sintesi adimentsua

```
./local-cros.sh "Zure galdera hemen"
```

---

## 🚀 Hasiera Bizkorra

### Aurrebaldintzak

- **llama.cpp** konpilatuta eta funtzionala
- **GGUF modeloak** (Mistral, LLaMA, etab.)
- **Bash 4.0+** macOS/Linux-en

### Oinarrizko Instalazioa

```
git clone https://github.com/BiblioGalactic/Prime_Radiant.git
cd Prime_Radiant

# Erabilgarri dauden tresnak arakatu
ls -la
```

### Konfigurazioa

1. **llama.cpp instalatu**:
```
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
make
```

2. **GGUF modeloak deskargatu**:
```
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q6_K.gguf
```

---

## 🛠️ Tresnen Katalogoa

| Tresna | Helburua | Egoera |
|-------------|-----------|--------|
| [Local AI Assistant](./local-ai-assistant/) | Laguntzaile agentiko osoa | ✅ Egonkorra |
| [Local-CROS](./local-agentic-assistant/) | Modelen konparatzailea | ✅ Egonkorra |

---

## 🎭 Diseinu Filosofia

### Zergatik Bash

- **Gardentasuna**: Komando bakoitza irakurri dezakezu
- **Eramangarritasuna**: Unix sistemetan funtzionatzen du
- **Sinpletasuna**: Mendekotasun konplexurik gabe

### Zergatik Lokala

- **Pribatutasuna**: Zure datuak ez dira zure makinatik ateratzen
- **Kontrola**: Zuk erabakitzen duzu zer modelo erabili
- **Kostua**: APIaren mugarik gabe

---

## 📄 Lizentzia

MIT License - Erabilera librea atribuzioarekin.

### Egilea

**Gustavo Silva da Costa (Eto Demerzel)**  
🔗 [BiblioGalactic](https://github.com/BiblioGalactic)

---

*"Ezagutza baliotsuena kontrolatu, hobetu eta libreki parteka dezakezuna da."*  
— Eto Demerzel, Prime Radiant
