#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# === 🧠 PUBLIC LLaMA CHAT WITH MMAP MEMORY ===
# Adapted for open-source modular use

# ============================================================
# 🔒 SANITIZACIÓN DE INPUT
# ============================================================
sanitize_path() {
    local input="$1"
    local label="$2"
    # Rechazar caracteres peligrosos para inyección en C/shell
    if [[ "$input" =~ [\"\\$\`\;|\&\>\<\!\(\)\{\}\[\]] ]]; then
        echo "❌ Ruta inválida para $label: caracteres prohibidos detectados" >&2
        exit 1
    fi
    # Rechazar cadenas vacías
    if [[ -z "$input" ]]; then
        echo "❌ Ruta vacía para $label" >&2
        exit 1
    fi
    echo "$input"
}

sanitize_integer() {
    local input="$1"
    local label="$2"
    if ! [[ "$input" =~ ^[0-9]+$ ]]; then
        echo "❌ $label debe ser un número entero positivo, recibido: '$input'" >&2
        exit 1
    fi
    echo "$input"
}

# ============================================================
# 🧹 CLEANUP + TRAP
# ============================================================
MMAP_WRAPPER=""
cleanup() {
    [[ -n "$MMAP_WRAPPER" && -f "$MMAP_WRAPPER" ]] && rm -f "$MMAP_WRAPPER"
    [[ -f /tmp/mmap_launcher ]] && rm -f /tmp/mmap_launcher
}
trap cleanup EXIT

# ============================================================
# 📥 INPUT DEL USUARIO (CON VALIDACIÓN)
# ============================================================

# 1) Ask user for prompt file and verify
read -p "Enter path to your prompt file (.txt): " PROMPT_FILE_RAW
PROMPT_FILE=$(sanitize_path "$PROMPT_FILE_RAW" "prompt file")
[[ ! -f "$PROMPT_FILE" ]] && echo "❌ Prompt file not found: $PROMPT_FILE" && exit 1

# 2) Ask user for LLaMA binary
read -p "Enter path to llama-cli executable: " MAIN_BINARY_RAW
MAIN_BINARY=$(sanitize_path "$MAIN_BINARY_RAW" "llama-cli binary")
[[ ! -x "$MAIN_BINARY" ]] && echo "❌ Executable not found or no permission: $MAIN_BINARY" && exit 1

# 3) Ask user for model path
read -p "Enter path to your .gguf model: " MODELO_PATH_RAW
MODELO_PATH=$(sanitize_path "$MODELO_PATH_RAW" "model path")
[[ ! -f "$MODELO_PATH" ]] && echo "❌ Model not found: $MODELO_PATH" && exit 1

# 4) Ask user for profile paths
read -p "Enter paths to profile files, comma separated (e.g., tecnico.txt,filosofico.txt,seguridad.txt): " PROFILE_INPUT
IFS=',' read -ra PERFIL_PATHS_RAW <<< "$PROFILE_INPUT"

PERFIL_PATHS=()
for p in "${PERFIL_PATHS_RAW[@]}"; do
    p_clean=$(sanitize_path "$(echo "$p" | xargs)" "profile path")
    [[ ! -f "$p_clean" ]] && echo "❌ Profile file not found: $p_clean" && exit 1
    PERFIL_PATHS+=("$p_clean")
done

if [[ ${#PERFIL_PATHS[@]} -eq 0 ]]; then
    echo "❌ No profile paths provided" && exit 1
fi

# 5) Ask which profile to use
read -p "Select active profile index (0-$(( ${#PERFIL_PATHS[@]} - 1 ))): " PERFIL_ACTIVO_RAW
PERFIL_ACTIVO=$(sanitize_integer "$PERFIL_ACTIVO_RAW" "profile index")

if [[ "$PERFIL_ACTIVO" -ge "${#PERFIL_PATHS[@]}" ]]; then
    echo "❌ Profile index out of range (max: $(( ${#PERFIL_PATHS[@]} - 1 )))" && exit 1
fi

# ============================================================
# 🔧 GENERAR WRAPPER C (CON INPUT SANITIZADO)
# ============================================================
MMAP_WRAPPER=$(mktemp /tmp/mmap_wrapper_XXXXXX.c)

cat > "$MMAP_WRAPPER" <<'CEOF'
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <profile_path> <binary_path> <model_path>\n", argv[0]);
        return 1;
    }
    const char *profile_path = argv[1];
    const char *binary_path = argv[2];
    const char *model_path = argv[3];

    int fd = open(profile_path, O_RDONLY);
    if (fd == -1) {
        perror("Error opening selected profile");
        exit(EXIT_FAILURE);
    }

    struct stat st;
    if (fstat(fd, &st) == -1) {
        perror("Error getting file info");
        close(fd);
        exit(EXIT_FAILURE);
    }

    char *prompt = mmap(NULL, st.st_size, PROT_READ, MAP_SHARED, fd, 0);
    if (prompt == MAP_FAILED) {
        perror("Error mapping file with mmap");
        close(fd);
        exit(EXIT_FAILURE);
    }

    execl(binary_path, binary_path,
          "-m", model_path,
          "--ctx-size", "4096",
          "--n-predict", "512",
          "--color",
          "--temp", "1.0",
          "--threads", "6",
          "--interactive",
          "--prompt", prompt,
          NULL);

    perror("execl failed");
    munmap(prompt, st.st_size);
    close(fd);
    return 1;
}
CEOF

# ============================================================
# 🚀 COMPILAR Y EJECUTAR (rutas como argumentos, no embebidas en C)
# ============================================================
gcc "$MMAP_WRAPPER" -o /tmp/mmap_launcher || { echo "❌ Compilation failed"; exit 1; }
/tmp/mmap_launcher "${PERFIL_PATHS[$PERFIL_ACTIVO]}" "$MAIN_BINARY" "$MODELO_PATH"
