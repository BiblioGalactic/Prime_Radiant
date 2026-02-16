#!/usr/bin/env bash
# ============================================================
# 🌐 WIKIPEDIA RAG BUILDER — by Eto Demerzel (BiblioGalactic)
# ============================================================
# Descarga, extrae e indexa Wikipedia en cualquier idioma
# como sistema RAG local con FAISS + sentence-transformers
# ============================================================
# Uso: ./wiki_rag_builder.sh
# ============================================================
set -euo pipefail

# ============================================================
# 📋 IDIOMAS DISPONIBLES
# ============================================================
declare -A LANGS
LANGS=(
    [en]="English"
    [es]="Español"
    [ca]="Català"
    [eu]="Euskara"
    [pt]="Português"
    [fr]="Français"
    [de]="Deutsch"
    [it]="Italiano"
    [nl]="Nederlands"
    [pl]="Polski"
    [ru]="Русский"
    [zh]="中文"
    [ja]="日本語"
    [ko]="한국어"
    [ar]="العربية"
    [sv]="Svenska"
    [fi]="Suomi"
    [da]="Dansk"
    [no]="Norsk"
    [uk]="Українська"
    [cs]="Čeština"
    [ro]="Română"
    [hu]="Magyar"
    [tr]="Türkçe"
    [el]="Ελληνικά"
    [he]="עברית"
    [hi]="हिन्दी"
    [th]="ไทย"
    [vi]="Tiếng Việt"
    [id]="Bahasa Indonesia"
    [simple]="Simple English"
)

# ============================================================
# 🎨 COLORES Y FORMATO
# ============================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

banner() {
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${BOLD}🌐 WIKIPEDIA RAG BUILDER${NC}"
    echo -e "${CYAN}    by Eto Demerzel (BiblioGalactic)${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""
}

info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
ok()      { echo -e "${GREEN}[✅]${NC} $1"; }
warn()    { echo -e "${YELLOW}[⚠️]${NC} $1"; }
error()   { echo -e "${RED}[❌]${NC} $1"; }
step()    { echo -e "\n${BOLD}${CYAN}═══ $1 ═══${NC}\n"; }

# ============================================================
# 📁 RUTAS BASE
# ============================================================
BASE_DIR="$HOME/wikirag"
VENV_DIR="$BASE_DIR/entorno_rag"

# ============================================================
# 🔍 VALIDACIONES
# ============================================================
validar_dependencias() {
    step "Verificando dependencias del sistema"

    local faltan=()

    if ! command -v python3 &>/dev/null; then
        faltan+=("python3")
    fi

    if ! command -v wget &>/dev/null; then
        faltan+=("wget (instalar con: brew install wget)")
    fi

    if ! command -v git &>/dev/null; then
        faltan+=("git (instalar con: xcode-select --install)")
    fi

    if [ ${#faltan[@]} -gt 0 ]; then
        error "Faltan dependencias:"
        for dep in "${faltan[@]}"; do
            echo "   - $dep"
        done
        exit 1
    fi

    ok "Todas las dependencias del sistema encontradas"
}

# ============================================================
# 🗂 SELECCIÓN DE IDIOMA
# ============================================================
seleccionar_idioma() {
    step "Selecciona un idioma"

    # Ordenar por código
    local sorted_keys=($(echo "${!LANGS[@]}" | tr ' ' '\n' | sort))

    local i=1
    for key in "${sorted_keys[@]}"; do
        printf "  ${BOLD}%2d)${NC} %-8s %s\n" "$i" "[$key]" "${LANGS[$key]}"
        ((i++))
    done

    echo ""
    read -p "$(echo -e ${YELLOW})Elige número: $(echo -e ${NC})" seleccion

    # Validar
    if ! [[ "$seleccion" =~ ^[0-9]+$ ]] || [ "$seleccion" -lt 1 ] || [ "$seleccion" -gt ${#sorted_keys[@]} ]; then
        error "Selección inválida"
        exit 1
    fi

    LANG_CODE="${sorted_keys[$((seleccion-1))]}"
    LANG_NAME="${LANGS[$LANG_CODE]}"

    ok "Idioma seleccionado: $LANG_NAME [$LANG_CODE]"
}

# ============================================================
# 🐍 ENTORNO VIRTUAL
# ============================================================
crear_entorno() {
    step "Configurando entorno Python"

    mkdir -p "$BASE_DIR"

    if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
        info "Entorno virtual existente encontrado"
        source "$VENV_DIR/bin/activate"

        # Verificar paquetes
        local todo_ok=true
        for pkg in sentence_transformers faiss wikiextractor; do
            if ! python3 -c "import $pkg" 2>/dev/null; then
                todo_ok=false
                break
            fi
        done

        if $todo_ok; then
            ok "Entorno virtual listo con todos los paquetes"
            return
        else
            warn "Faltan paquetes, instalando..."
        fi
    else
        info "Creando entorno virtual..."

        # Buscar Python 3.10-3.12 (wikiextractor no soporta 3.13+)
        local PY_BIN=""
        for v in 3.12 3.11 3.10; do
            if command -v "python$v" &>/dev/null; then
                PY_BIN="python$v"
                break
            fi
            local brew_py="/opt/homebrew/bin/python$v"
            if [ -f "$brew_py" ]; then
                PY_BIN="$brew_py"
                break
            fi
        done

        if [ -z "$PY_BIN" ]; then
            error "Se necesita Python 3.10, 3.11 o 3.12"
            echo "  wikiextractor no es compatible con Python 3.13+"
            echo "  Instala con: brew install python@3.12"
            exit 1
        fi

        info "Usando $PY_BIN"
        "$PY_BIN" -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
    fi

    info "Instalando paquetes..."
    pip install --upgrade pip -q
    pip install "numpy<2" sentence-transformers faiss-cpu wikiextractor -q

    ok "Entorno virtual configurado"
}

# ============================================================
# 📥 DESCARGA
# ============================================================
descargar_dump() {
    step "Descargando Wikipedia [$LANG_CODE]"

    local wiki_dir="$BASE_DIR/wiki_${LANG_CODE}"
    local dump_file="${LANG_CODE}wiki-latest-pages-articles.xml.bz2"
    local url="https://dumps.wikimedia.org/${LANG_CODE}wiki/latest/$dump_file"

    mkdir -p "$wiki_dir"
    cd "$wiki_dir"

    if [ -f "$dump_file" ]; then
        local size=$(du -h "$dump_file" | cut -f1)
        warn "Dump ya existe ($size)"
        read -p "$(echo -e ${YELLOW})¿Reanudar/verificar descarga? [S/n]: $(echo -e ${NC})" resp
        if [[ "${resp:-S}" =~ ^[Nn]$ ]]; then
            ok "Usando dump existente"
            return
        fi
    fi

    info "URL: $url"
    info "Esto puede tardar desde minutos hasta horas según el idioma"
    echo ""

    caffeinate -i wget -c --progress=bar:force "$url" || {
        error "Error en la descarga"
        echo "  Puedes reiniciar el script, wget retomará donde lo dejó"
        exit 1
    }

    local final_size=$(du -h "$dump_file" | cut -f1)
    ok "Descarga completada: $final_size"
}

# ============================================================
# 📦 EXTRACCIÓN
# ============================================================
extraer_dump() {
    step "Extrayendo artículos con wikiextractor"

    local wiki_dir="$BASE_DIR/wiki_${LANG_CODE}"
    local dump_file="${LANG_CODE}wiki-latest-pages-articles.xml.bz2"
    local txt_dir="$wiki_dir/wiki_${LANG_CODE}_txt"

    cd "$wiki_dir"

    # Verificar si ya se extrajo
    if [ -d "$txt_dir" ]; then
        local num_files=$(find "$txt_dir" -name "wiki_*" -type f 2>/dev/null | wc -l | tr -d ' ')
        if [ "$num_files" -gt 0 ]; then
            warn "Extracción ya existe ($num_files archivos)"
            read -p "$(echo -e ${YELLOW})¿Volver a extraer? [s/N]: $(echo -e ${NC})" resp
            if [[ ! "${resp:-N}" =~ ^[Ss]$ ]]; then
                ok "Usando extracción existente"
                return
            fi
            rm -rf "$txt_dir"
        fi
    fi

    info "Extrayendo artículos (puede tardar horas para idiomas grandes)..."
    echo ""

    caffeinate -i python3 -m wikiextractor.WikiExtractor "$dump_file" -o "$txt_dir" || {
        error "Error en la extracción"
        exit 1
    }

    local num_files=$(find "$txt_dir" -name "wiki_*" -type f | wc -l | tr -d ' ')
    ok "Extracción completada: $num_files archivos"
}

# ============================================================
# 🧠 INDEXADO
# ============================================================
crear_indice() {
    step "Creando índice RAG con FAISS"

    local wiki_txt="$BASE_DIR/wiki_${LANG_CODE}/wiki_${LANG_CODE}_txt"
    local index_dir="$BASE_DIR/index_${LANG_CODE}"
    local script_file="$BASE_DIR/index_${LANG_CODE}.py"

    mkdir -p "$index_dir"

    # Verificar si ya existe un índice
    if [ -f "$index_dir/faiss_index.index" ] && [ -f "$index_dir/documents.pkl" ]; then
        warn "Índice existente encontrado en $index_dir"
        read -p "$(echo -e ${YELLOW})¿Regenerar índice? [s/N]: $(echo -e ${NC})" resp
        if [[ ! "${resp:-N}" =~ ^[Ss]$ ]]; then
            ok "Usando índice existente"
            return
        fi
    fi

    info "Generando script de indexado..."

    # Crear script Python de indexado
    python3 -c "
f = open('$script_file', 'w')
f.write('''#!/usr/bin/env python3
# Auto-generado por wiki_rag_builder.sh
# Idioma: ${LANG_CODE} (${LANG_NAME})
import os, re, pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

print(\"Iniciando indexado de Wikipedia [${LANG_CODE}]...\")
model = SentenceTransformer(\"sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2\")
wiki_dir = \"$wiki_txt\"
save_dir = \"$index_dir\"
os.makedirs(save_dir, exist_ok=True)

files = []
for root, dirs, fnames in os.walk(wiki_dir):
    for fn in sorted(fnames):
        if fn.startswith(\"wiki_\"):
            files.append(os.path.join(root, fn))
print(f\"Encontrados {len(files)} archivos\")

if len(files) == 0:
    print(\"ERROR: No se encontraron archivos wiki_* en \" + wiki_dir)
    exit(1)

index = None
documents = []
metadata = []
batch_docs = []

for i, filepath in enumerate(files):
    fn = os.path.basename(filepath)
    with open(filepath, \"r\", encoding=\"utf-8\") as fh:
        title = None
        body = []
        for line in fh:
            if line.startswith(\"<doc\"):
                m = re.search(r\x27title=\"([^\"]*)\"\x27, line)
                title = m.group(1) if m else fn
                body = []
            elif line.startswith(\"</doc>\"):
                if title and body:
                    text = \" \".join(body)
                    text = re.sub(r\x27\\\\[\\\\d+\\\\]\x27, \"\", text)
                    text = re.sub(r\x27\\\\s+\x27, \" \", text).strip()
                    if len(text) > 50:
                        words = text.split()
                        for j in range(0, len(words), 450):
                            chunk = \" \".join(words[j:j+500])
                            if len(chunk) > 50:
                                batch_docs.append(chunk)
                                documents.append(chunk)
                                metadata.append({\"title\": title, \"source\": fn})
                title = None
                body = []
            elif title is not None:
                stripped = line.strip()
                if len(stripped) > 5:
                    body.append(stripped)

    if len(batch_docs) >= 1000:
        emb = model.encode(batch_docs, batch_size=64, show_progress_bar=False, convert_to_numpy=True)
        faiss.normalize_L2(emb)
        if index is None:
            index = faiss.IndexFlatIP(emb.shape[1])
        index.add(emb.astype(\"float32\"))
        batch_docs = []

    if (i + 1) % 100 == 0:
        print(f\"Archivo {i+1}/{len(files)} - chunks: {len(documents)}\")
    if (i + 1) % 2000 == 0 and index is not None:
        faiss.write_index(index, os.path.join(save_dir, \"faiss_index.index\"))
        with open(os.path.join(save_dir, \"documents.pkl\"), \"wb\") as fp:
            pickle.dump(documents, fp)
        with open(os.path.join(save_dir, \"metadata.pkl\"), \"wb\") as fp:
            pickle.dump(metadata, fp)
        print(f\"  Checkpoint: {len(documents)} chunks\")

if batch_docs:
    emb = model.encode(batch_docs, batch_size=64, show_progress_bar=False, convert_to_numpy=True)
    faiss.normalize_L2(emb)
    if index is None:
        index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb.astype(\"float32\"))

faiss.write_index(index, os.path.join(save_dir, \"faiss_index.index\"))
with open(os.path.join(save_dir, \"documents.pkl\"), \"wb\") as fp:
    pickle.dump(documents, fp)
with open(os.path.join(save_dir, \"metadata.pkl\"), \"wb\") as fp:
    pickle.dump(metadata, fp)
print(f\"LISTO: {len(documents)} chunks indexados en {save_dir}\")
''')
f.close()
print('Script generado OK')
"

    ok "Script generado: $script_file"
    info "Iniciando indexado (puede tardar horas para idiomas grandes)..."
    info "El proceso guarda checkpoints cada 2000 archivos"
    info "Si se interrumpe, los datos parciales están en $index_dir"
    echo ""

    export TOKENIZERS_PARALLELISM=false
    export OMP_NUM_THREADS=1
    caffeinate -i python3 "$script_file" || {
        error "Error en el indexado"
        echo "  Los checkpoints guardados están en $index_dir"
        exit 1
    }

    ok "Índice RAG creado en $index_dir"
}

# ============================================================
# 📊 RESUMEN
# ============================================================
mostrar_resumen() {
    step "Resumen"

    local index_dir="$BASE_DIR/index_${LANG_CODE}"

    if [ -f "$index_dir/faiss_index.index" ]; then
        local idx_size=$(du -h "$index_dir/faiss_index.index" | cut -f1)
        local doc_size=$(du -h "$index_dir/documents.pkl" | cut -f1)
        local meta_size=$(du -h "$index_dir/metadata.pkl" | cut -f1)
        local total_size=$(du -sh "$index_dir" | cut -f1)

        echo -e "  ${BOLD}Idioma:${NC}             ${LANG_NAME} [${LANG_CODE}]"
        echo -e "  ${BOLD}Índice FAISS:${NC}       $idx_size"
        echo -e "  ${BOLD}Documentos:${NC}         $doc_size"
        echo -e "  ${BOLD}Metadata:${NC}           $meta_size"
        echo -e "  ${BOLD}Total:${NC}              $total_size"
        echo -e "  ${BOLD}Ruta:${NC}               $index_dir"
        echo ""
        echo -e "  ${BOLD}Para usar:${NC}"
        echo -e "    source $VENV_DIR/bin/activate"
        echo -e "    python3 -c \""
        echo -e "    from create_rag import WikipediaRAG"
        echo -e "    rag = WikipediaRAG()"
        echo -e "    rag.load_index('$index_dir')"
        echo -e "    results = rag.search('tu consulta aquí', k=5)"
        echo -e "    for r in results: print(r['metadata']['title'], r['score'])"
        echo -e "    \""
    else
        error "No se encontró el índice en $index_dir"
    fi

    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${BOLD}🌐 Wikipedia [$LANG_CODE] RAG completado${NC}"
    echo -e "${CYAN}============================================================${NC}"
}

# ============================================================
# 🚀 EJECUCIÓN PRINCIPAL
# ============================================================
main() {
    banner
    validar_dependencias
    seleccionar_idioma
    crear_entorno
    descargar_dump
    extraer_dump
    crear_indice
    mostrar_resumen
}

main "$@"
