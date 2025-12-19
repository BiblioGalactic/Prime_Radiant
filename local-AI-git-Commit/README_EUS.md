# Tokiko Git Commit AI

**Git interaktiboa AI-rekin**  
Publiko eta eramangarri bertsioa zure commit-ak adimen artifizialaren laguntzaz hobetzeko.

---

## 🧑‍💻 Egilea
Gustavo Silva  
Sortze data: $(date +%F)

---

## 📌 Deskribapena

`local-Commit.sh` Git interaktiboko AI script bat da, hurrengo aukera hauekin:

- Gehitu nahi dituzun fitxategiak hautatu (denak edo banan-banako interaktibo moduan `fzf` erabiliz).
- Zure commit mezua hartu eta AI modelo batekin **automatikoki hobetu**.
- Hobetu den commit-a jatorrizko esanahia **aldatu gabe dagoela egiaztatu** beste AI modelo batekin.
- Commit hobetu hori eskuz editatu bidali aurretik.
- Adimen nagusia automatikoki detektatu eta **push** seguru bat egin.
- Guztia **eramangarria** izan dadin: script-ak `llama-cli` eta `.gguf` modeloen bideak eskatuko dizkizu.

---

## ⚙️ Eskakizunak

- Bash 5+  
- Git  
- `timeout`  
- `nl`  
- `fzf`  
- `llama-cli` eta `.gguf` modeloak (hobekuntza eta egiaztapena)  

---

## 📂 Instalazioa

1. Repo hau klonatu edo script-a deskargatu.
2. Ziurtatu mendekotasunak instalatuta dituzula (`git`, `timeout`, `nl`, `fzf`).
3. Prestatu zure `.gguf` modeloak eta `llama-cli` konpilatua.
4. Exekutatu:


chmod +x local-Commit.sh
./local-Commit.sh
