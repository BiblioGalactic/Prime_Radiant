# Local Git Commit AI

**Script interactivo de Git con IA**  
Versión pública y portable para mejorar tus commits con asistencia de inteligencia artificial.

---

## 🧑‍💻 Autor
Gustavo Silva  
Fecha de creación: $(date +%F)

---

## 📌 Descripción

`local-Commit.sh` es un script de **Git interactivo con IA** que te permite:

- Seleccionar archivos a añadir (todos o individualmente de forma interactiva con `fzf`).
- Capturar tu mensaje de commit y **curarlo automáticamente** con un modelo de IA.
- Verificar que el commit curado **no cambia el significado original** usando otro modelo de IA.
- Editar manualmente el commit curado antes de enviarlo.
- Detectar automáticamente la rama principal y hacer **push** seguro.
- Mantener todo **portable**: el script te pedirá las rutas a `llama-cli` y a los modelos `.gguf`.

---

## ⚙️ Requisitos

- Bash 5+  
- Git  
- `timeout`  
- `nl`  
- `fzf`  
- `llama-cli` y modelos `.gguf` (curación y verificación)  

---

## 📂 Instalación

1. Clona este repositorio o descarga el script.
2. Asegúrate de tener instaladas las dependencias (`git`, `timeout`, `nl`, `fzf`).
3. Prepara tus modelos `.gguf` y `llama-cli` compilado.
4. Ejecuta:

```bash
chmod +x local-Commit.sh
./local-Commit.sh
