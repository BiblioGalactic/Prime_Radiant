#!/bin/bash 🧑‍💻
# ======================================================================
# Script de Git Interactivo con IA - Versión pública y portable
# Autor: Gustavo Silva
# Fecha: $(date +%F)
# ======================================================================

set -euo pipefail
trap cleanup EXIT

# Variables globales para archivos temporales
readonly TMP_DIR="/tmp/git_ai_$$"
readonly COMMIT_FILE="$TMP_DIR/commit_msg.txt"

cleanup() {
    echo "✨ Limpiando archivos temporales en $TMP_DIR..."
    rm -rf "$TMP_DIR"
}

log_info() {
    echo "✅ [$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1"
}

log_error() {
    echo "❌ [$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
}

# Comprobar dependencias y archivos
check_dependencies() {
    local deps=("git" "timeout" "nl" "fzf")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "El comando '$dep' no está instalado. Por favor, instálalo."
            exit 1
        fi
    done
}

check_files() {
    local files=("$LLAMA_BIN" "$MODEL_CURACION" "$MODEL_VERIFICACION")
    for file in "${files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "El archivo o modelo '$file' no existe. Por favor, verifica la ruta."
            exit 1
        fi
        if [ ! -r "$file" ]; then
            log_error "No tienes permisos de lectura para el archivo '$file'."
            exit 1
        fi
    done
}

main() {
    mkdir -p "$TMP_DIR"
    check_dependencies

    # Pedir rutas al usuario para que sea portable
    read -p "Ruta al binario llama-cli: " LLAMA_BIN
    read -p "Ruta al modelo de curación (.gguf): " MODEL_CURACION
    read -p "Ruta al modelo de verificación (.gguf): " MODEL_VERIFICACION

    check_files

    log_info "Iniciando script de Git Interactivo con IA (publico y portable)"
    
    # 1️⃣ Pedir la carpeta del proyecto
    read -p "Introduce el nombre o ruta de la carpeta del proyecto: " carpeta

    if [ ! -d "$carpeta" ]; then
        log_error "La carpeta '$carpeta' no existe."
        exit 1
    fi

    cd "$carpeta" || exit 1
    log_info "Ahora estás en: $(pwd)"

    # 2️⃣ Validar que estamos en un repositorio Git
    if ! git rev-parse --git-dir &>/dev/null; then
        log_error "No estás en un repositorio Git."
        read -p "¿Quieres inicializar uno? (y/n): " init_git
        if [[ "$init_git" == "y" ]]; then
            git init
            log_info "Repositorio Git inicializado."
        else
            exit 1
        fi
    fi

    # 3️⃣ Menú de selección de archivos
    echo "Selecciona qué quieres añadir:"
    echo "1) Todo"
    echo "2) Seleccionar archivos (interactivo con fzf)"

    read -p "Opción [1/2]: " opcion

    if [[ "$opcion" == "1" ]]; then
        git add .
        log_info "Añadidos todos los archivos."
    elif [[ "$opcion" == "2" ]]; then
        echo "Selecciona los archivos con flechas y espacio (Enter para confirmar):"
        mapfile -t archivos_seleccionados < <(git status --porcelain | awk '{print $2}' | fzf -m)
        if [ ${#archivos_seleccionados[@]} -eq 0 ]; then
            log_error "No se seleccionó ningún archivo. Saliendo."
            exit 1
        fi
        for archivo in "${archivos_seleccionados[@]}"; do
            git add "$archivo"
            log_info "Añadido: $archivo"
        done
    else
        log_error "Opción inválida. Saliendo."
        exit 1
    fi

    # 4️⃣ Loop para captura, curación y verificación del commit
    local intentos=0
    readonly max_intentos=3
    local COMMIT_MSG COMMIT_CURADO

    while [ "$intentos" -lt "$max_intentos" ]; do
        read -p "Escribe tu mensaje de commit (intento $((intentos+1))/$max_intentos): " COMMIT_MSG
        
        if [ -z "$COMMIT_MSG" ]; then
            log_error "El mensaje no puede estar vacío"
            ((intentos++))
            continue
        fi

        log_info "🤖 Curando mensaje..."
        COMMIT_CURADO=$(timeout 30 "$LLAMA_BIN" -m "$MODEL_CURACION" -p "Actúa como corrector profesional de commits de Git. Corrige ortografía, gramática, puntuación y estilo para que sea claro y conciso. No cambies el significado. Devuelve solo el commit limpio sin comentarios extras:
Mensaje original: \"$COMMIT_MSG\"" -c 512 -n 128 --temp 0.1 --top-p 0.9 --repeat-penalty 1.1 --silent | head -n 1 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

        if [ -z "$COMMIT_CURADO" ]; then
            echo "⚠️ Error en la curación. Usando mensaje original."
            COMMIT_CURADO="$COMMIT_MSG"
        fi

        log_info "📝 Mensaje curado: $COMMIT_CURADO"

        read -p "¿Quieres editar el mensaje antes del commit? (y/n): " editar
        if [[ "$editar" == "y" ]]; then
            echo "$COMMIT_CURADO" > "$COMMIT_FILE"
            ${EDITOR:-vi} "$COMMIT_FILE"
            COMMIT_CURADO=$(cat "$COMMIT_FILE")
        fi

        log_info "🔍 Verificando..."
        VERIFICACION=$(timeout 15 "$LLAMA_BIN" -m "$MODEL_VERIFICACION" -p "Eres un verificador de commits. Compara el mensaje original y el curado:
Original: \"$COMMIT_MSG\"
Curado: \"$COMMIT_CURADO\"
Verifica que el curado no cambie el significado, esté correcto y no invente nada.
Responde solo OK o REINTENTAR." -c 256 -n 32 --temp 0.0 --top-p 0.9 --repeat-penalty 1.1 --silent | tr '[:lower:]' '[:upper:]' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

        if [[ "$VERIFICACION" =~ "OK" ]] || [ -z "$VERIFICACION" ]; then
            log_info "✅ Commit aprobado."
            git commit -m "$COMMIT_CURADO"
            break
        else
            log_error "Verificación falló: $VERIFICACION"
            echo "¿Quieres: (1) Reintentar (2) Usar así (3) Salir?)"
            read -p "> " decision
            case "$decision" in
                2) git commit -m "$COMMIT_CURADO"; break ;;
                3) exit 0 ;;
                *) ((intentos++)) ;;
            esac
        fi
    done

    if [ "$intentos" -eq "$max_intentos" ]; then
        log_error "Máximo de intentos alcanzado. Haciendo commit manual con el mensaje original."
        git commit -m "$COMMIT_MSG"
    fi

    # 5️⃣ Detección automática de la rama principal y push
    local BRANCH_PRINCIPAL
    BRANCH_PRINCIPAL=$(git remote show origin | grep "HEAD branch" | awk '{print $NF}')
    if [ -z "$BRANCH_PRINCIPAL" ]; then
        read -p "No se pudo detectar la rama principal automáticamente. Introduce el nombre de la rama principal: " BRANCH_PRINCIPAL
    fi

    echo "📊 Resumen del commit:"
    git show --stat HEAD

    read -p "¿Hacer push ahora? (y/n): " do_push
    if [[ "$do_push" == "y" ]]; then
        git pull origin "$BRANCH_PRINCIPAL" --rebase
        git push
        log_info "Push completado"
    else
        log_info "Commit local guardado. Push manual cuando quieras."
    fi
}

# Ejecutar el script
main