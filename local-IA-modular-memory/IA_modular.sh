#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# === Script público para generar y ejecutar prompt con LLaMA ===

# 1) Solicitar directorio del usuario para el módulo de prompts
describe_prompt_dir() {
    read -p "Introduce la ruta del directorio con tus archivos .md: " PROMPT_DIR
    if [[ ! -d "$PROMPT_DIR" ]]; then
        echo "[⚠️] Directorio no existe: $PROMPT_DIR"
        exit 1
    fi
}

# 2) Solicitar ruta al modelo LLaMA
describe_model() {
    read -p "Introduce la ruta a tu modelo LLaMA (.gguf): " MODEL
    if [[ ! -f "$MODEL" ]]; then
        echo "[⚠️] Modelo no encontrado: $MODEL"
        exit 1
    fi
}

# 3) Solicitar ruta al ejecutable llama-cli
describe_llama_cli() {
    read -p "Introduce la ruta al ejecutable llama-cli: " LLAMA_CLI
    if [[ ! -x "$LLAMA_CLI" ]]; then
        echo "[⚠️] Ejecutable no encontrado o sin permisos: $LLAMA_CLI"
        exit 1
    fi
}

# 4) Generar prompt concatenando todos los .md en orden natural
generar_prompt() {
    TMPFILE=$(mktemp)
    PROMPT_FILE="$PROMPT_DIR/prompt_completo.txt"

    {
        printf "%s\n" "$PROMPT_DIR"/*.md | sort -V |
        while IFS= read -r file; do
            cat "$file"
        done
    } > "$PROMPT_FILE"

    # Limpiar espacios y líneas vacías
    sed -e 's/\r//g' \
        -e 's/^[[:space:]]\+//g' \
        -e 's/[[:space:]]\+$//g' \
        -e '/^[[:space:]]*$/d' \
        "$PROMPT_FILE" > "$TMPFILE" && mv "$TMPFILE" "$PROMPT_FILE"

    # Verificar que no esté vacío
    if [[ ! -s "$PROMPT_FILE" ]]; then
        echo "[⚠️] Prompt vacío. Abortando."
        exit 1
    fi

    PROMPT_CONTENT=$(< "$PROMPT_FILE")
}

# 5) Ejecutar LLaMA interactivo
ejecutar_llama() {
    "$LLAMA_CLI" \
        -m "$MODEL" \
        --ctx-size 30096 \
        --threads 6 \
        --color \
        --interactive \
        -p "$PROMPT_CONTENT"
}

# === Flujo principal ===
describe_prompt_dir
# Opción para actualizar estado dinámico si existe
dinamico_script="$PROMPT_DIR/estado_dinamico.sh"
[[ -x "$dinamico_script" ]] && bash "$dinamico_script"
describe_model
describe_llama_cli
generar_prompt
ejecutar_llama
