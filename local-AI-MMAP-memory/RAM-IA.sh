#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# === 🧠 PUBLIC LLaMA CHAT WITH MMAP MEMORY ===
# Adapted for open-source modular use

# 1) Ask user for prompt file and verify
read -p "Enter path to your prompt file (.txt): " PROMPT_FILE
[[ ! -f "$PROMPT_FILE" ]] && echo "❌ Prompt file not found: $PROMPT_FILE" && exit 1

# 2) Ask user for LLaMA binary
read -p "Enter path to llama-cli executable: " MAIN_BINARY
[[ ! -x "$MAIN_BINARY" ]] && echo "❌ Executable not found or no permission: $MAIN_BINARY" && exit 1

# 3) Ask user for model path
read -p "Enter path to your .gguf model: " MODELO_PATH
[[ ! -f "$MODELO_PATH" ]] && echo "❌ Model not found: $MODELO_PATH" && exit 1

# 4) Ask user for profile paths
read -p "Enter paths to profile files, comma separated (e.g., tecnico.txt,filosofico.txt,seguridad.txt): " PROFILE_INPUT
IFS=',' read -ra PERFIL_PATHS <<< "$PROFILE_INPUT"

# 5) Ask which profile to use
read -p "Select active profile index (0-$(( ${#PERFIL_PATHS[@]} - 1 ))): " PERFIL_ACTIVO

# 6) Create temporary C file for mmap wrapper
MMAP_WRAPPER=$(mktemp).c

cat > "$MMAP_WRAPPER" <<EOF
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

int main() {
    const char *perfil_paths[] = {
EOF

for p in "${PERFIL_PATHS[@]}"; do
    echo "        \"$p\"," >> "$MMAP_WRAPPER"
done

cat >> "$MMAP_WRAPPER" <<EOF
    };
    const int perfil_activo = $PERFIL_ACTIVO;

    int fd = open(perfil_paths[perfil_activo], O_RDONLY);
    if (fd == -1) {
        perror("❌ Error opening selected profile");
        exit(EXIT_FAILURE);
    }

    struct stat st;
    if (fstat(fd, &st) == -1) {
        perror("❌ Error getting file info");
        close(fd);
        exit(EXIT_FAILURE);
    }

    char *prompt = mmap(NULL, st.st_size, PROT_READ, MAP_SHARED, fd, 0);
    if (prompt == MAP_FAILED) {
        perror("❌ Error mapping file with mmap");
        close(fd);
        exit(EXIT_FAILURE);
    }

    execl("$MAIN_BINARY", "$MAIN_BINARY",
          "-m", "$MODELO_PATH",
          "--ctx-size", "4096",
          "--n-predict", "512",
          "--color",
          "--temp", "1.0",
          "--threads", "6",
          "--interactive",
          "--prompt", prompt,
          NULL);

    perror("❌ execl failed");
    munmap(prompt, st.st_size);
    close(fd);
    return 1;
}
EOF

# 7) Compile and run
gcc "$MMAP_WRAPPER" -o /tmp/mmap_launcher && /tmp/mmap_launcher
rm -f "$MMAP_WRAPPER"
