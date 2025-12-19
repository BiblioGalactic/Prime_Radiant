# Local Git Commit AI

**Script interactiu de Git amb IA**  
Versió pública i portable per millorar els teus commits amb assistència d'intel·ligència artificial.

---

## 🧑‍💻 Autor
Gustavo Silva  
Data de creació: $(date +%F)

---

## 📌 Descripció

`local-Commit.sh` és un script de **Git interactiu amb IA** que et permet:

- Seleccionar fitxers per afegir (tots o individualment de forma interactiva amb `fzf`).
- Capturar el teu missatge de commit i **curar-lo automàticament** amb un model d'IA.
- Verificar que el commit curat **no canvia el significat original** utilitzant un altre model d'IA.
- Editar manualment el commit curat abans d'enviar-lo.
- Detectar automàticament la branca principal i fer **push** segur.
- Mantenir-ho tot **portable**: el script et demanarà les rutes a `llama-cli` i als models `.gguf`.

---

## ⚙️ Requisits

- Bash 5+  
- Git  
- `timeout`  
- `nl`  
- `fzf`  
- `llama-cli` i models `.gguf` (curació i verificació)  

---

## 📂 Instal·lació

1. Clona aquest repositori o descarrega el script.
2. Assegura't de tenir instal·lades les dependències (`git`, `timeout`, `nl`, `fzf`).
3. Prepara els teus models `.gguf` i `llama-cli` compilat.
4. Executa:


chmod +x local-Commit.sh
./local-Commit.sh

</file>
