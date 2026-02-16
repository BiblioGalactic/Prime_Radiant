#!/usr/bin/env bash
# ============================================================
# 🧠 UNIVERSAL KNOWLEDGE RAG BUILDER v2
# by Eto Demerzel (BiblioGalactic)
# ============================================================
# Descarga, extrae e indexa fuentes de conocimiento como RAG
# local con FAISS + sentence-transformers
# ============================================================
# Fuentes: Wikipedia (30 idiomas), Wikisource, Wiktionary,
#           Arxiv abstracts, Project Gutenberg, Stack Overflow
# ============================================================
# Incluye: Buscador universal secuencial + Chat con llama-cli
# ============================================================
set -euo pipefail

# ============================================================
# 🎨 COLORES
# ============================================================
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
banner() {
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${BOLD}🧠 UNIVERSAL KNOWLEDGE RAG BUILDER v2${NC}"
    echo -e "${CYAN}   by Eto Demerzel (BiblioGalactic)${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""
}
info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[✅]${NC} $1"; }
warn()  { echo -e "${YELLOW}[⚠️]${NC} $1"; }
error() { echo -e "${RED}[❌]${NC} $1"; }
step()  { echo -e "\n${BOLD}${CYAN}═══ $1 ═══${NC}\n"; }

# ============================================================
# 📁 RUTAS
# ============================================================
BASE_DIR="$HOME/wikirag"
VENV_DIR="$BASE_DIR/entorno_rag"
LLAMA_CLI="$HOME/modelo/llama.cpp/build/bin/llama-cli"
MODELO="$HOME/modelo/modelos_grandes/M6/mistral-7b-instruct-v0.1.Q6_K.gguf"
TEMP_FILES=()

# ============================================================
# 🧹 CLEANUP + TRAP
# ============================================================
cleanup() {
    local exit_code=$?
    if [ ${#TEMP_FILES[@]} -gt 0 ]; then
        for f in "${TEMP_FILES[@]}"; do
            [ -f "$f" ] && rm -f "$f" 2>/dev/null
            [ -d "$f" ] && rm -rf "$f" 2>/dev/null
        done
    fi
    # Desactivar entorno si está activo
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        deactivate 2>/dev/null || true
    fi
    if [ $exit_code -ne 0 ] && [ $exit_code -ne 130 ]; then
        echo ""
        error "Script interrumpido (código: $exit_code)"
        info "Los índices parciales con checkpoint se pueden retomar"
    elif [ $exit_code -eq 130 ]; then
        echo ""
        warn "Interrumpido por usuario (Ctrl+C)"
        info "Puedes retomar — el script detecta progreso existente"
    fi
}
trap cleanup EXIT

# ============================================================
# 📋 IDIOMAS WIKIPEDIA
# ============================================================
declare -A WIKI_LANGS
WIKI_LANGS=(
    [en]="English" [es]="Español" [ca]="Català" [eu]="Euskara"
    [pt]="Português" [fr]="Français" [de]="Deutsch" [it]="Italiano"
    [nl]="Nederlands" [pl]="Polski" [ru]="Русский" [zh]="中文"
    [ja]="日本語" [ko]="한국어" [ar]="العربية" [sv]="Svenska"
    [fi]="Suomi" [da]="Dansk" [no]="Norsk" [uk]="Українська"
    [cs]="Čeština" [ro]="Română" [hu]="Magyar" [tr]="Türkçe"
    [el]="Ελληνικά" [he]="עברית" [hi]="हिन्दी" [th]="ไทย"
    [vi]="Tiếng Việt" [id]="Bahasa Indonesia" [simple]="Simple English"
)

# ============================================================
# 🔍 VALIDAR DEPENDENCIAS
# ============================================================
validar_dependencias() {
    step "Verificando dependencias del sistema"
    local faltan=()
    local avisos=()

    # Python 3.10+
    local py_ok=false
    for v in 3.12 3.11 3.10; do
        if command -v "python$v" &>/dev/null; then py_ok=true; break; fi
        if [ -f "/opt/homebrew/bin/python$v" ]; then py_ok=true; break; fi
    done
    if $py_ok; then ok "Python 3.10+ encontrado"; else faltan+=("python@3.12"); fi

    # wget
    if command -v wget &>/dev/null; then
        ok "wget encontrado"
    else
        faltan+=("wget")
    fi

    # Espacio en disco
    local free_gb
    free_gb=$(df -g "$HOME" 2>/dev/null | tail -1 | awk '{print $4}' || echo "0")
    if [ "$free_gb" -lt 50 ]; then
        avisos+=("Espacio libre: ${free_gb}GB — Wikipedia EN necesita ~150GB total")
    else
        ok "Espacio libre: ${free_gb}GB"
    fi

    # RAM
    local ram_gb
    ram_gb=$(sysctl -n hw.memsize 2>/dev/null | awk '{printf "%.0f", $1/1073741824}' || echo "0")
    if [ "$ram_gb" -gt 0 ]; then
        ok "RAM total: ${ram_gb}GB"
        if [ "$ram_gb" -lt 8 ]; then
            avisos+=("RAM baja (${ram_gb}GB) — el indexado será lento")
        fi
    fi

    # Opcionales
    if command -v 7z &>/dev/null; then
        ok "7z encontrado (para Stack Overflow)"
    else
        avisos+=("7z no instalado — necesario para Stack Overflow (brew install p7zip)")
    fi

    if command -v caffeinate &>/dev/null; then
        ok "caffeinate encontrado"
    else
        avisos+=("caffeinate no encontrado — las descargas largas podrían pausarse por sleep")
    fi

    # llama-cli
    if [ -f "$LLAMA_CLI" ]; then
        ok "llama-cli encontrado"
    else
        avisos+=("llama-cli no encontrado en $LLAMA_CLI — chat con IA no disponible")
    fi

    # Mostrar avisos
    for a in "${avisos[@]:-}"; do
        [ -n "$a" ] && warn "$a"
    done

    # Errores fatales
    if [ ${#faltan[@]} -gt 0 ]; then
        echo ""
        error "Faltan dependencias obligatorias:"
        for dep in "${faltan[@]}"; do
            echo -e "  ${RED}•${NC} $dep → ${BOLD}brew install $dep${NC}"
        done
        exit 1
    fi

    ok "Dependencias verificadas"
}

# ============================================================
# 🐍 ENTORNO VIRTUAL
# ============================================================
crear_entorno() {
    step "Configurando entorno Python"
    mkdir -p "$BASE_DIR"

    if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
        ok "Entorno virtual existente activado"
    else
        local PY_BIN=""
        for v in 3.12 3.11 3.10; do
            if command -v "python$v" &>/dev/null; then PY_BIN="python$v"; break; fi
            local bp="/opt/homebrew/bin/python$v"
            if [ -f "$bp" ]; then PY_BIN="$bp"; break; fi
        done
        if [ -z "$PY_BIN" ]; then
            error "Se necesita Python 3.10-3.12 (brew install python@3.12)"; exit 1
        fi
        info "Creando entorno con $PY_BIN..."
        "$PY_BIN" -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
    fi

    # Instalar dependencias si faltan
    python3 -c "import faiss" 2>/dev/null || {
        info "Instalando dependencias..."
        pip install --upgrade pip -q
        pip install "numpy<2" sentence-transformers faiss-cpu wikiextractor -q
    }
    ok "Entorno listo"
}

# ============================================================
# 🔧 GENERAR SCRIPT INDEXADO WIKI-FORMAT
# ============================================================
generar_script_wiki() {
    local txt_dir="$1"
    local idx_dir="$2"
    local script="$3"
    local nombre="$4"

    cat > "$script" << 'PYEOF'
#!/usr/bin/env python3
# Indexador RAG: NOMBRE_PLACEHOLDER
import os, re, pickle, sys
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

print("Indexando: NOMBRE_PLACEHOLDER")
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
wiki_dir = "TXTDIR_PLACEHOLDER"
save_dir = "IDXDIR_PLACEHOLDER"
os.makedirs(save_dir, exist_ok=True)

files = []
for root, dirs, fnames in os.walk(wiki_dir):
    for fn in sorted(fnames):
        if fn.startswith("wiki_") or fn.endswith(".txt"):
            files.append(os.path.join(root, fn))
print(f"Encontrados {len(files)} archivos")
if not files:
    print("ERROR: Sin archivos"); sys.exit(1)

index = None; documents = []; metadata = []; batch_docs = []
for i, filepath in enumerate(files):
    fn = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as fh:
        title = None; body = []
        for line in fh:
            if line.startswith("<doc"):
                m = re.search(r'title="([^"]*)"', line)
                title = m.group(1) if m else fn; body = []
            elif line.startswith("</doc>"):
                if title and body:
                    text = " ".join(body)
                    text = re.sub(r'\[\d+\]', "", text)
                    text = re.sub(r'\s+', " ", text).strip()
                    if len(text) > 50:
                        words = text.split()
                        for j in range(0, len(words), 450):
                            chunk = " ".join(words[j:j+500])
                            if len(chunk) > 50:
                                batch_docs.append(chunk)
                                documents.append(chunk)
                                metadata.append({"title": title, "source": fn})
                title = None; body = []
            elif title is not None:
                s = line.strip()
                if len(s) > 5: body.append(s)
    if len(batch_docs) >= 1000:
        emb = model.encode(batch_docs, batch_size=64, show_progress_bar=False, convert_to_numpy=True)
        faiss.normalize_L2(emb)
        if index is None: index = faiss.IndexFlatIP(emb.shape[1])
        index.add(emb.astype("float32")); batch_docs = []
    if (i+1) % 100 == 0:
        print(f"Archivo {i+1}/{len(files)} - chunks: {len(documents)}")
    if (i+1) % 2000 == 0 and index is not None:
        faiss.write_index(index, os.path.join(save_dir, "faiss_index.index"))
        with open(os.path.join(save_dir, "documents.pkl"), "wb") as fp: pickle.dump(documents, fp)
        with open(os.path.join(save_dir, "metadata.pkl"), "wb") as fp: pickle.dump(metadata, fp)
        print(f"  Checkpoint: {len(documents)} chunks")
if batch_docs:
    emb = model.encode(batch_docs, batch_size=64, show_progress_bar=False, convert_to_numpy=True)
    faiss.normalize_L2(emb)
    if index is None: index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb.astype("float32"))
faiss.write_index(index, os.path.join(save_dir, "faiss_index.index"))
with open(os.path.join(save_dir, "documents.pkl"), "wb") as fp: pickle.dump(documents, fp)
with open(os.path.join(save_dir, "metadata.pkl"), "wb") as fp: pickle.dump(metadata, fp)
print(f"LISTO: {len(documents)} chunks en {save_dir}")
PYEOF

    # Sustituir placeholders
    sed -i.bak "s|NOMBRE_PLACEHOLDER|$nombre|g" "$script"
    sed -i.bak "s|TXTDIR_PLACEHOLDER|$txt_dir|g" "$script"
    sed -i.bak "s|IDXDIR_PLACEHOLDER|$idx_dir|g" "$script"
    rm -f "${script}.bak"
    ok "Script indexador generado: $script"
}

# ============================================================
# 🔧 GENERAR SCRIPT INDEXADO ARXIV
# ============================================================
generar_script_arxiv() {
    local json_file="$1"
    local idx_dir="$2"
    local script="$3"

    cat > "$script" << 'PYEOF'
#!/usr/bin/env python3
# Indexador RAG: Arxiv Abstracts
import os, json, pickle, re, sys
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

print("Indexando Arxiv abstracts...")
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
save_dir = "IDXDIR_PLACEHOLDER"
os.makedirs(save_dir, exist_ok=True)

index = None; documents = []; metadata = []; batch_docs = []; count = 0
with open("JSONFILE_PLACEHOLDER", "r", encoding="utf-8") as fh:
    for line in fh:
        try:
            paper = json.loads(line)
        except: continue
        abstract = paper.get("abstract", "").strip()
        title = paper.get("title", "").replace("\n", " ").strip()
        authors = paper.get("authors", "")
        categories = paper.get("categories", "")
        pid = paper.get("id", "")
        if len(abstract) < 50: continue
        abstract = re.sub(r"\s+", " ", abstract.replace("\n", " ")).strip()
        text = f"{title}. {abstract}"
        words = text.split()
        for j in range(0, len(words), 450):
            chunk = " ".join(words[j:j+500])
            if len(chunk) > 50:
                batch_docs.append(chunk)
                documents.append(chunk)
                metadata.append({"title": title, "authors": authors[:200], "categories": categories, "arxiv_id": pid})
        count += 1
        if len(batch_docs) >= 1000:
            emb = model.encode(batch_docs, batch_size=64, show_progress_bar=False, convert_to_numpy=True)
            faiss.normalize_L2(emb)
            if index is None: index = faiss.IndexFlatIP(emb.shape[1])
            index.add(emb.astype("float32")); batch_docs = []
        if count % 50000 == 0:
            print(f"Papers: {count} - chunks: {len(documents)}")
        if count % 500000 == 0 and index is not None:
            faiss.write_index(index, os.path.join(save_dir, "faiss_index.index"))
            with open(os.path.join(save_dir, "documents.pkl"), "wb") as fp: pickle.dump(documents, fp)
            with open(os.path.join(save_dir, "metadata.pkl"), "wb") as fp: pickle.dump(metadata, fp)
            print(f"  Checkpoint: {len(documents)} chunks")
if batch_docs:
    emb = model.encode(batch_docs, batch_size=64, show_progress_bar=False, convert_to_numpy=True)
    faiss.normalize_L2(emb)
    if index is None: index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb.astype("float32"))
faiss.write_index(index, os.path.join(save_dir, "faiss_index.index"))
with open(os.path.join(save_dir, "documents.pkl"), "wb") as fp: pickle.dump(documents, fp)
with open(os.path.join(save_dir, "metadata.pkl"), "wb") as fp: pickle.dump(metadata, fp)
print(f"LISTO: {count} papers, {len(documents)} chunks en {save_dir}")
PYEOF

    sed -i.bak "s|IDXDIR_PLACEHOLDER|$idx_dir|g" "$script"
    sed -i.bak "s|JSONFILE_PLACEHOLDER|$json_file|g" "$script"
    rm -f "${script}.bak"
    ok "Script indexador Arxiv generado"
}

# ============================================================
# 🔧 GENERAR SCRIPT INDEXADO GUTENBERG
# ============================================================
generar_script_gutenberg() {
    local txt_dir="$1"
    local idx_dir="$2"
    local script="$3"

    cat > "$script" << 'PYEOF'
#!/usr/bin/env python3
# Indexador RAG: Project Gutenberg
import os, re, pickle, sys
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

print("Indexando Project Gutenberg...")
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
txt_dir = "TXTDIR_PLACEHOLDER"
save_dir = "IDXDIR_PLACEHOLDER"
os.makedirs(save_dir, exist_ok=True)

files = []
for root, dirs, fnames in os.walk(txt_dir):
    for fn in sorted(fnames):
        if fn.endswith(".txt"):
            files.append(os.path.join(root, fn))
print(f"Encontrados {len(files)} libros")
if not files:
    print("ERROR: Sin archivos"); sys.exit(1)

def limpiar_gutenberg(text):
    start_markers = ["*** START OF", "***START OF"]
    end_markers = ["*** END OF", "***END OF", "End of the Project Gutenberg", "End of Project Gutenberg"]
    start = 0
    for marker in start_markers:
        idx = text.find(marker)
        if idx != -1:
            nl = text.find("\n", idx)
            if nl != -1: start = nl + 1
            break
    end = len(text)
    for marker in end_markers:
        idx = text.find(marker)
        if idx != -1: end = idx; break
    return text[start:end].strip()

index = None; documents = []; metadata = []; batch_docs = []
for i, filepath in enumerate(files):
    fn = os.path.basename(filepath)
    title = fn.replace(".txt", "")
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
        text = limpiar_gutenberg(text)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 100: continue
        words = text.split()
        for j in range(0, len(words), 450):
            chunk = " ".join(words[j:j+500])
            if len(chunk) > 50:
                batch_docs.append(chunk)
                documents.append(chunk)
                metadata.append({"title": title, "source": fn})
    except: continue
    if len(batch_docs) >= 1000:
        emb = model.encode(batch_docs, batch_size=64, show_progress_bar=False, convert_to_numpy=True)
        faiss.normalize_L2(emb)
        if index is None: index = faiss.IndexFlatIP(emb.shape[1])
        index.add(emb.astype("float32")); batch_docs = []
    if (i+1) % 500 == 0:
        print(f"Libro {i+1}/{len(files)} - chunks: {len(documents)}")
    if (i+1) % 5000 == 0 and index is not None:
        faiss.write_index(index, os.path.join(save_dir, "faiss_index.index"))
        with open(os.path.join(save_dir, "documents.pkl"), "wb") as fp: pickle.dump(documents, fp)
        with open(os.path.join(save_dir, "metadata.pkl"), "wb") as fp: pickle.dump(metadata, fp)
        print(f"  Checkpoint: {len(documents)} chunks")
if batch_docs:
    emb = model.encode(batch_docs, batch_size=64, show_progress_bar=False, convert_to_numpy=True)
    faiss.normalize_L2(emb)
    if index is None: index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb.astype("float32"))
faiss.write_index(index, os.path.join(save_dir, "faiss_index.index"))
with open(os.path.join(save_dir, "documents.pkl"), "wb") as fp: pickle.dump(documents, fp)
with open(os.path.join(save_dir, "metadata.pkl"), "wb") as fp: pickle.dump(metadata, fp)
print(f"LISTO: {len(files)} libros, {len(documents)} chunks en {save_dir}")
PYEOF

    sed -i.bak "s|TXTDIR_PLACEHOLDER|$txt_dir|g" "$script"
    sed -i.bak "s|IDXDIR_PLACEHOLDER|$idx_dir|g" "$script"
    rm -f "${script}.bak"
    ok "Script indexador Gutenberg generado"
}

# ============================================================
# 🔧 GENERAR SCRIPT INDEXADO STACKOVERFLOW
# ============================================================
generar_script_stackoverflow() {
    local xml_file="$1"
    local idx_dir="$2"
    local script="$3"

    cat > "$script" << 'PYEOF'
#!/usr/bin/env python3
# Indexador RAG: Stack Overflow (score > 5)
import os, re, pickle, html, sys
from xml.etree import ElementTree as ET
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

print("Indexando Stack Overflow...")
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
save_dir = "IDXDIR_PLACEHOLDER"
os.makedirs(save_dir, exist_ok=True)

def limpiar_html(text):
    text = re.sub(r"<code>.*?</code>", " [CODE] ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

index = None; documents = []; metadata = []; batch_docs = []
count = 0; skipped = 0

print("Parseando XML (esto tarda)...")
for event, elem in ET.iterparse("XMLFILE_PLACEHOLDER", events=("end",)):
    if elem.tag != "row": continue
    post_type = elem.get("PostTypeId", "")
    score = int(elem.get("Score", "0"))
    if post_type not in ("1", "2") or score < 5:
        elem.clear(); skipped += 1; continue
    body = elem.get("Body", "")
    title = elem.get("Title", "SO Post")
    tags = elem.get("Tags", "")
    text = limpiar_html(body)
    if len(text) < 50: elem.clear(); continue
    if title and post_type == "1":
        text = f"{title}. {text}"
    words = text.split()
    for j in range(0, len(words), 450):
        chunk = " ".join(words[j:j+500])
        if len(chunk) > 50:
            batch_docs.append(chunk)
            documents.append(chunk)
            metadata.append({"title": title, "tags": tags, "score": score, "type": "question" if post_type == "1" else "answer"})
    count += 1; elem.clear()
    if len(batch_docs) >= 1000:
        emb = model.encode(batch_docs, batch_size=64, show_progress_bar=False, convert_to_numpy=True)
        faiss.normalize_L2(emb)
        if index is None: index = faiss.IndexFlatIP(emb.shape[1])
        index.add(emb.astype("float32")); batch_docs = []
    if count % 50000 == 0:
        print(f"Posts: {count} (skip: {skipped}) - chunks: {len(documents)}")
    if count % 500000 == 0 and index is not None:
        faiss.write_index(index, os.path.join(save_dir, "faiss_index.index"))
        with open(os.path.join(save_dir, "documents.pkl"), "wb") as fp: pickle.dump(documents, fp)
        with open(os.path.join(save_dir, "metadata.pkl"), "wb") as fp: pickle.dump(metadata, fp)
        print(f"  Checkpoint: {len(documents)} chunks")
if batch_docs:
    emb = model.encode(batch_docs, batch_size=64, show_progress_bar=False, convert_to_numpy=True)
    faiss.normalize_L2(emb)
    if index is None: index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb.astype("float32"))
faiss.write_index(index, os.path.join(save_dir, "faiss_index.index"))
with open(os.path.join(save_dir, "documents.pkl"), "wb") as fp: pickle.dump(documents, fp)
with open(os.path.join(save_dir, "metadata.pkl"), "wb") as fp: pickle.dump(metadata, fp)
print(f"LISTO: {count} posts (score>5), {len(documents)} chunks en {save_dir}")
PYEOF

    sed -i.bak "s|IDXDIR_PLACEHOLDER|$idx_dir|g" "$script"
    sed -i.bak "s|XMLFILE_PLACEHOLDER|$xml_file|g" "$script"
    rm -f "${script}.bak"
    ok "Script indexador Stack Overflow generado"
}

# ============================================================
# 🔍 GENERAR BUSCADOR UNIVERSAL SECUENCIAL
# ============================================================
generar_query_universal() {
    local script="$BASE_DIR/query_universal_rag.py"

    step "Generando buscador universal secuencial"

    cat > "$script" << 'PYEOF'
#!/usr/bin/env python3
# ============================================================
# 🔍 UNIVERSAL RAG QUERY — Búsqueda secuencial multi-índice
# by Eto Demerzel (BiblioGalactic)
# ============================================================
# Abre UN índice a la vez → busca → acumula → cierra → siguiente
# Optimizado para RAM: nunca carga más de un índice simultáneo
# ============================================================
import os, sys, gc, pickle, glob, time
import numpy as np

os.environ['TOKENIZERS_PARALLELISM'] = 'false'

BASE_DIR = os.path.expanduser("~/wikirag")

# Colores
C = {
    'r': '\033[0;31m', 'g': '\033[0;32m', 'y': '\033[1;33m',
    'b': '\033[0;34m', 'c': '\033[0;36m', 'B': '\033[1m', 'n': '\033[0m'
}

def cprint(color, msg):
    print(f"{C.get(color, '')}{msg}{C['n']}")

def detectar_indices():
    """Detecta todos los index_* con faiss_index.index"""
    indices = []
    for d in sorted(glob.glob(os.path.join(BASE_DIR, "index_*"))):
        if os.path.isfile(os.path.join(d, "faiss_index.index")):
            nombre = os.path.basename(d).replace("index_", "")
            # Etiqueta legible
            if nombre.startswith("wikipedia_"):
                label = f"Wikipedia [{nombre.split('_')[1]}]"
                tipo = "wikipedia"
            elif nombre.startswith("wikisource_"):
                label = f"Wikisource [{nombre.split('_')[1]}]"
                tipo = "wikisource"
            elif nombre.startswith("wiktionary_"):
                label = f"Wiktionary [{nombre.split('_')[1]}]"
                tipo = "wiktionary"
            elif nombre == "arxiv":
                label = "Arxiv Papers"
                tipo = "arxiv"
            elif nombre == "gutenberg":
                label = "Project Gutenberg"
                tipo = "gutenberg"
            elif nombre == "stackoverflow":
                label = "Stack Overflow"
                tipo = "stackoverflow"
            else:
                label = nombre
                tipo = "otro"
            indices.append({"path": d, "nombre": nombre, "label": label, "tipo": tipo})
    return indices

def buscar_en_indice(idx_info, query_embedding, k=5):
    """Carga un índice, busca, devuelve resultados, libera RAM"""
    import faiss

    path = idx_info["path"]
    label = idx_info["label"]

    t0 = time.time()
    cprint('b', f"  📂 Cargando {label}...")

    try:
        index = faiss.read_index(os.path.join(path, "faiss_index.index"))
        with open(os.path.join(path, "documents.pkl"), "rb") as f:
            documents = pickle.load(f)
        with open(os.path.join(path, "metadata.pkl"), "rb") as f:
            metadata = pickle.load(f)
    except Exception as e:
        cprint('r', f"  ❌ Error cargando {label}: {e}")
        return []

    total_docs = len(documents)
    cprint('b', f"     {total_docs:,} chunks cargados ({time.time()-t0:.1f}s)")

    # Buscar
    q = query_embedding.copy().astype("float32").reshape(1, -1)
    faiss.normalize_L2(q)
    scores, ids = index.search(q, min(k, index.ntotal))

    resultados = []
    for score, idx in zip(scores[0], ids[0]):
        if idx < 0 or idx >= len(documents):
            continue
        meta = metadata[idx] if idx < len(metadata) else {}
        resultados.append({
            "score": float(score),
            "document": documents[idx],
            "metadata": meta,
            "source": label,
            "source_type": idx_info["tipo"]
        })

    cprint('g', f"  ✅ {label}: {len(resultados)} resultados (mejor: {resultados[0]['score']:.4f})" if resultados else f"  ⚠️ {label}: sin resultados")

    # LIBERAR RAM — esto es lo crítico
    del index, documents, metadata
    gc.collect()

    return resultados

def busqueda_universal(query, indices, k_por_indice=5, k_total=10):
    """Búsqueda secuencial: un índice a la vez"""
    from sentence_transformers import SentenceTransformer

    cprint('B', "\n🔍 Codificando consulta...")
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    query_emb = model.encode(query, convert_to_numpy=True)
    # Liberar modelo tras codificar
    del model
    gc.collect()

    todos_resultados = []
    t_total = time.time()

    cprint('c', f"\n═══ Buscando en {len(indices)} índices (secuencial) ═══\n")

    for i, idx_info in enumerate(indices, 1):
        cprint('B', f"[{i}/{len(indices)}] {idx_info['label']}")
        resultados = buscar_en_indice(idx_info, query_emb, k=k_por_indice)
        todos_resultados.extend(resultados)
        gc.collect()

    # Ordenar por score global y tomar top-K
    todos_resultados.sort(key=lambda x: x["score"], reverse=True)
    top = todos_resultados[:k_total]

    elapsed = time.time() - t_total
    cprint('c', f"\n═══ Búsqueda completada: {elapsed:.1f}s ═══")
    cprint('g', f"📊 {len(todos_resultados)} resultados totales → Top {len(top)} seleccionados\n")

    return top

def formatear_contexto(resultados):
    """Formatea resultados para IA con atribución de fuente"""
    partes = []
    for i, r in enumerate(resultados, 1):
        meta = r["metadata"]
        titulo = meta.get("title", "Sin título")
        fuente = r["source"]

        # Info extra según tipo
        extra = ""
        if r["source_type"] == "arxiv":
            aid = meta.get("arxiv_id", "")
            cats = meta.get("categories", "")
            extra = f" | arxiv:{aid} | {cats}" if aid else ""
        elif r["source_type"] == "stackoverflow":
            score = meta.get("score", 0)
            tags = meta.get("tags", "")
            extra = f" | score:{score} | {tags}" if tags else ""

        texto = r["document"][:600]
        partes.append(f"[{i}] [{fuente}] {titulo}{extra}\n{texto}")

    return "\n\n".join(partes)

def mostrar_resultados(resultados):
    """Muestra resultados formateados en terminal"""
    for i, r in enumerate(resultados, 1):
        meta = r["metadata"]
        titulo = meta.get("title", "Sin título")
        fuente = r["source"]
        score = r["score"]
        texto = r["document"][:300]

        cprint('B', f"📄 {i}. [{fuente}] {titulo}")
        cprint('b', f"   Score: {score:.4f}")
        print(f"   {texto}...")
        print(f"   {'─' * 60}")

# ============================================================
# 🚀 MODO INTERACTIVO
# ============================================================
def main():
    print()
    cprint('c', "============================================================")
    cprint('B', "🔍 UNIVERSAL RAG QUERY — Búsqueda Secuencial")
    cprint('c', "   by Eto Demerzel (BiblioGalactic)")
    cprint('c', "============================================================")

    indices = detectar_indices()
    if not indices:
        cprint('r', "❌ No hay índices en ~/wikirag/index_*")
        cprint('y', "   Ejecuta primero: ./universal_rag_builder.sh")
        sys.exit(1)

    print()
    cprint('B', f"📚 {len(indices)} índices disponibles:")
    for idx in indices:
        size = "?"
        try:
            total = sum(os.path.getsize(os.path.join(idx["path"], f))
                       for f in os.listdir(idx["path"])
                       if os.path.isfile(os.path.join(idx["path"], f)))
            size = f"{total / (1024**3):.1f}GB" if total > 1e9 else f"{total / (1024**2):.0f}MB"
        except: pass
        cprint('g', f"  ✅ {idx['label']} ({size})")

    print()
    cprint('y', "Comandos: 'salir' para terminar | 'json' para ver JSON crudo")
    print()

    modo_json = False
    while True:
        try:
            query = input(f"{C['B']}🔍 Consulta: {C['n']}").strip()
        except (EOFError, KeyboardInterrupt):
            print(); break

        if not query:
            continue
        if query.lower() in ('salir', 'exit', 'quit'):
            break
        if query.lower() == 'json':
            modo_json = not modo_json
            cprint('y', f"Modo JSON: {'ON' if modo_json else 'OFF'}")
            continue

        resultados = busqueda_universal(query, indices, k_por_indice=5, k_total=10)

        if modo_json:
            import json
            for r in resultados:
                r["document"] = r["document"][:500]
            print(json.dumps(resultados, ensure_ascii=False, indent=2))
        else:
            mostrar_resultados(resultados)
        print()

    cprint('c', "Hasta luego 🧠")

if __name__ == "__main__":
    main()
PYEOF

    chmod +x "$script"
    ok "Buscador universal generado: $script"
    info "Uso: source $VENV_DIR/bin/activate && python3 $script"
}

# ============================================================
# 💬 GENERAR CHAT UNIVERSAL CON LLAMA-CLI
# ============================================================
generar_chat_universal() {
    local script="$BASE_DIR/chat_universal_rag.py"

    step "Generando chat universal con llama-cli"

    cat > "$script" << PYEOF
#!/usr/bin/env python3
# ============================================================
# 💬 UNIVERSAL RAG CHAT — Chat con IA + RAG multi-fuente
# by Eto Demerzel (BiblioGalactic)
# ============================================================
# Busca secuencialmente en todos los índices RAG
# Construye contexto con atribución de fuentes
# Envía a llama-cli (Mistral) para respuesta informada
# ============================================================
import os, sys, gc, pickle, glob, time, subprocess, tempfile
import numpy as np

os.environ['TOKENIZERS_PARALLELISM'] = 'false'

BASE_DIR = os.path.expanduser("~/wikirag")
LLAMA_CLI = "$LLAMA_CLI"
MODELO = "$MODELO"

C = {
    'r': '\033[0;31m', 'g': '\033[0;32m', 'y': '\033[1;33m',
    'b': '\033[0;34m', 'c': '\033[0;36m', 'B': '\033[1m', 'n': '\033[0m'
}

def cprint(color, msg):
    print(f"{C.get(color, '')}{msg}{C['n']}")

# Importar funciones del query universal
sys.path.insert(0, BASE_DIR)
from query_universal_rag import detectar_indices, busqueda_universal, formatear_contexto

def llamar_ia(pregunta, contexto, tokens=800):
    """Llama a Mistral via llama-cli con contexto RAG"""

    if not os.path.isfile(LLAMA_CLI):
        cprint('r', f"❌ llama-cli no encontrado: {LLAMA_CLI}")
        return None
    if not os.path.isfile(MODELO):
        cprint('r', f"❌ Modelo no encontrado: {MODELO}")
        return None

    if contexto:
        prompt = f"""[INST] Tienes acceso a las siguientes fuentes de conocimiento. Usa la información relevante para responder. Cita la fuente entre corchetes cuando uses datos específicos.

FUENTES:
{contexto}

PREGUNTA: {pregunta} [/INST]"""
    else:
        prompt = f"[INST] {pregunta} [/INST]"

    # Escribir prompt a archivo temporal (evita problemas de escape)
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    tmp.write(prompt)
    tmp.close()

    try:
        cprint('b', "🤖 Generando respuesta...")
        result = subprocess.run(
            [LLAMA_CLI,
             "-m", MODELO,
             "-f", tmp.name,
             "-n", str(tokens),
             "--temp", "0.7",
             "-c", "4096",
             "-ngl", "1",
             "-t", "4",
             "-no-cnv"],
            capture_output=True, text=True, timeout=120
        )
        respuesta = result.stdout.strip()

        # Limpiar artefactos de llama-cli
        if "[/INST]" in respuesta:
            respuesta = respuesta.split("[/INST]")[-1].strip()
        # Quitar líneas de log
        lineas = []
        for line in respuesta.split("\n"):
            if not line.startswith("llama_") and not line.startswith("main:") and "sampling" not in line.lower():
                lineas.append(line)
        respuesta = "\n".join(lineas).strip()

        return respuesta if respuesta else "(sin respuesta)"
    except subprocess.TimeoutExpired:
        cprint('r', "⏰ Timeout — la IA tardó demasiado")
        return None
    except Exception as e:
        cprint('r', f"❌ Error: {e}")
        return None
    finally:
        os.unlink(tmp.name)

def main():
    print()
    cprint('c', "============================================================")
    cprint('B', "💬 UNIVERSAL RAG CHAT — IA + Conocimiento Multi-Fuente")
    cprint('c', "   by Eto Demerzel (BiblioGalactic)")
    cprint('c', "============================================================")

    indices = detectar_indices()
    if not indices:
        cprint('r', "❌ No hay índices — ejecuta primero el builder")
        sys.exit(1)

    cprint('g', f"\n📚 {len(indices)} fuentes de conocimiento disponibles")
    for idx in indices:
        cprint('b', f"  • {idx['label']}")

    print()
    cprint('y', "Comandos:")
    cprint('y', "  'salir'    → Terminar")
    cprint('y', "  'sin-rag'  → Siguiente pregunta sin buscar en RAG")
    cprint('y', "  'fuentes'  → Ver fuentes disponibles")
    print()

    stats = {"total": 0, "con_rag": 0, "sin_rag": 0}
    skip_rag = False

    while True:
        try:
            query = input(f"{C['B']}Tu: {C['n']}").strip()
        except (EOFError, KeyboardInterrupt):
            print(); break

        if not query:
            continue
        if query.lower() in ('salir', 'exit', 'quit'):
            break
        if query.lower() == 'sin-rag':
            skip_rag = True
            cprint('y', "[Modo sin RAG activado para la siguiente pregunta]")
            continue
        if query.lower() == 'fuentes':
            for idx in indices:
                cprint('g', f"  ✅ {idx['label']}")
            continue

        stats["total"] += 1
        contexto = ""

        if not skip_rag:
            stats["con_rag"] += 1
            resultados = busqueda_universal(query, indices, k_por_indice=3, k_total=8)
            if resultados:
                contexto = formatear_contexto(resultados)
                # Mostrar de dónde viene la info
                fuentes_usadas = list(set(r["source"] for r in resultados))
                cprint('g', f"📚 Contexto de: {', '.join(fuentes_usadas)}")
        else:
            stats["sin_rag"] += 1
            skip_rag = False
            cprint('y', "[Sin RAG]")

        respuesta = llamar_ia(query, contexto)
        if respuesta:
            print()
            cprint('B', f"IA: {respuesta}")
            print()

    # Resumen de sesión
    print()
    cprint('c', "════════════════════════════════")
    cprint('B', "📊 RESUMEN DE SESIÓN")
    cprint('c', "════════════════════════════════")
    cprint('b', f"  Total preguntas:  {stats['total']}")
    cprint('g', f"  Con RAG:          {stats['con_rag']}")
    cprint('y', f"  Sin RAG:          {stats['sin_rag']}")
    cprint('c', "════════════════════════════════")

if __name__ == "__main__":
    main()
PYEOF

    chmod +x "$script"
    ok "Chat universal generado: $script"
    info "Uso: source $VENV_DIR/bin/activate && python3 $script"
}

# ============================================================
# 📥 PROCESAR WIKIPEDIA / WIKISOURCE / WIKTIONARY
# ============================================================
procesar_wikimedia() {
    local project="$1"
    local lang="$2"
    local label="$3"

    case "$project" in
        wikipedia)  local prefix="${lang}wiki" ;;
        wikisource) local prefix="${lang}wikisource" ;;
        wiktionary) local prefix="${lang}wiktionary" ;;
    esac

    local data_dir="$BASE_DIR/${project}_${lang}"
    local txt_dir="$data_dir/txt"
    local idx_dir="$BASE_DIR/index_${project}_${lang}"
    local dump_file="${prefix}-latest-pages-articles.xml.bz2"
    local url="https://dumps.wikimedia.org/${prefix}/latest/${dump_file}"
    local script="$BASE_DIR/index_${project}_${lang}.py"

    step "Descargando $label"
    mkdir -p "$data_dir"
    cd "$data_dir"
    if [ ! -f "$dump_file" ]; then
        info "URL: $url"
        caffeinate -i wget -c --progress=bar:force "$url" || { error "Error descarga"; exit 1; }
    else
        ok "Dump ya existe: $dump_file"
    fi

    step "Extrayendo $label"
    if [ -d "$txt_dir" ] && [ "$(find "$txt_dir" -name "wiki_*" 2>/dev/null | head -1)" ]; then
        ok "Extracción ya existe"
    else
        caffeinate -i python3 -m wikiextractor.WikiExtractor "$dump_file" -o "$txt_dir" || { error "Error extracción"; exit 1; }
    fi

    step "Indexando $label"
    generar_script_wiki "$txt_dir" "$idx_dir" "$script" "$label"
    export TOKENIZERS_PARALLELISM=false; export OMP_NUM_THREADS=1
    caffeinate -i python3 "$script" || { error "Error indexando"; exit 1; }
    ok "$label indexado en $idx_dir"
}

# ============================================================
# 📥 PROCESAR ARXIV
# ============================================================
procesar_arxiv() {
    local data_dir="$BASE_DIR/arxiv"
    local idx_dir="$BASE_DIR/index_arxiv"
    local json_file="$data_dir/arxiv-metadata-oai-snapshot.json"
    local script="$BASE_DIR/index_arxiv.py"

    step "Arxiv Abstracts"
    mkdir -p "$data_dir"

    if [ -f "$json_file" ]; then
        ok "Metadata ya existe: $json_file"
    else
        echo ""
        echo -e "${YELLOW}Arxiv requiere descarga manual desde Kaggle:${NC}"
        echo ""
        echo -e "  1. Ve a: ${BOLD}https://www.kaggle.com/datasets/Cornell-University/arxiv${NC}"
        echo -e "  2. Descarga ${BOLD}arxiv-metadata-oai-snapshot.json${NC} (~4GB)"
        echo -e "  3. Colócalo en: ${BOLD}$data_dir/${NC}"
        echo ""
        read -p "$(echo -e ${YELLOW})Pulsa Enter cuando lo tengas listo (o 'q' para saltar): $(echo -e ${NC})" resp
        if [[ "$resp" == "q" ]]; then return; fi
        if [ ! -f "$json_file" ]; then
            error "No encontrado: $json_file"; return
        fi
    fi

    step "Indexando Arxiv"
    generar_script_arxiv "$json_file" "$idx_dir" "$script"
    export TOKENIZERS_PARALLELISM=false; export OMP_NUM_THREADS=1
    caffeinate -i python3 "$script" || { error "Error indexando"; exit 1; }
    ok "Arxiv indexado en $idx_dir"
}

# ============================================================
# 📥 PROCESAR GUTENBERG
# ============================================================
procesar_gutenberg() {
    local data_dir="$BASE_DIR/gutenberg"
    local zip_dir="$data_dir/zips"
    local txt_dir="$data_dir/txt"
    local idx_dir="$BASE_DIR/index_gutenberg"
    local script="$BASE_DIR/index_gutenberg.py"

    step "Project Gutenberg"
    mkdir -p "$zip_dir" "$txt_dir"

    if [ "$(ls -A "$txt_dir" 2>/dev/null)" ]; then
        local num=$(find "$txt_dir" -name "*.txt" | wc -l | tr -d ' ')
        ok "Textos ya existen: $num libros"
    else
        info "Descargando libros (esto tarda 24-48h, sé cortés con Gutenberg)"
        info "Se puede interrumpir y retomar sin problema"
        cd "$zip_dir"
        caffeinate -i wget -w 2 -m -H -nd \
            "https://www.gutenberg.org/robot/harvest?filetypes[]=txt&langs[]=en" \
            2>&1 | tail -1 || true
        rm -f robots.txt harvest* *.html 2>/dev/null || true
        info "Descomprimiendo..."
        cd "$zip_dir"
        for z in *.zip; do
            [ -f "$z" ] && unzip -o -q "$z" -d "$txt_dir" 2>/dev/null || true
        done
        cd "$txt_dir"
        ls | grep "\-8\.txt" | xargs rm -f 2>/dev/null || true
        ls | grep "\-0\.txt" | xargs rm -f 2>/dev/null || true
        local num=$(find "$txt_dir" -name "*.txt" | wc -l | tr -d ' ')
        ok "Descarga completada: $num libros"
    fi

    step "Indexando Gutenberg"
    generar_script_gutenberg "$txt_dir" "$idx_dir" "$script"
    export TOKENIZERS_PARALLELISM=false; export OMP_NUM_THREADS=1
    caffeinate -i python3 "$script" || { error "Error indexando"; exit 1; }
    ok "Gutenberg indexado en $idx_dir"
}

# ============================================================
# 📥 PROCESAR STACKOVERFLOW
# ============================================================
procesar_stackoverflow() {
    local data_dir="$BASE_DIR/stackoverflow"
    local idx_dir="$BASE_DIR/index_stackoverflow"
    local posts_xml="$data_dir/Posts.xml"
    local script="$BASE_DIR/index_stackoverflow.py"

    step "Stack Overflow"
    mkdir -p "$data_dir"

    if [ -f "$posts_xml" ]; then
        ok "Posts.xml ya existe"
    else
        echo ""
        echo -e "${YELLOW}Stack Overflow requiere descarga manual:${NC}"
        echo ""
        echo -e "  1. Ve a: ${BOLD}https://archive.org/details/stackexchange_20251231${NC}"
        echo -e "  2. Descarga ${BOLD}stackoverflow.com-Posts.7z${NC} (~20GB)"
        echo -e "  3. Extrae con: ${BOLD}7z x stackoverflow.com-Posts.7z -o$data_dir${NC}"
        echo -e "     (instalar 7z: brew install p7zip)"
        echo ""
        read -p "$(echo -e ${YELLOW})Pulsa Enter cuando lo tengas listo (o 'q' para saltar): $(echo -e ${NC})" resp
        if [[ "$resp" == "q" ]]; then return; fi
        if [ ! -f "$posts_xml" ]; then
            error "No encontrado: $posts_xml"; return
        fi
    fi

    step "Indexando Stack Overflow (solo posts score > 5)"
    generar_script_stackoverflow "$posts_xml" "$idx_dir" "$script"
    export TOKENIZERS_PARALLELISM=false; export OMP_NUM_THREADS=1
    caffeinate -i python3 "$script" || { error "Error indexando"; exit 1; }
    ok "Stack Overflow indexado en $idx_dir"
}

# ============================================================
# 📊 RESUMEN
# ============================================================
mostrar_resumen() {
    step "Índices disponibles"
    local count=0
    for dir in "$BASE_DIR"/index_*; do
        [ -d "$dir" ] || continue
        if [ -f "$dir/faiss_index.index" ]; then
            local total=$(du -sh "$dir" | cut -f1)
            local name=$(basename "$dir" | sed 's/index_//')
            echo -e "  ${GREEN}✅${NC} ${BOLD}$name${NC} — $total"
            ((count++))
        fi
    done
    if [ $count -eq 0 ]; then
        warn "No hay índices construidos aún"
    fi
    echo ""
    echo -e "  ${BOLD}Total:${NC}     $count índices"
    echo -e "  ${BOLD}Ruta base:${NC} $BASE_DIR"

    # Mostrar scripts de consulta
    echo ""
    if [ -f "$BASE_DIR/query_universal_rag.py" ]; then
        echo -e "  ${GREEN}✅${NC} Buscador universal: ${BOLD}query_universal_rag.py${NC}"
    else
        echo -e "  ${YELLOW}⚠️${NC} Buscador universal: no generado (opción 8)"
    fi
    if [ -f "$BASE_DIR/chat_universal_rag.py" ]; then
        echo -e "  ${GREEN}✅${NC} Chat con IA:        ${BOLD}chat_universal_rag.py${NC}"
    else
        echo -e "  ${YELLOW}⚠️${NC} Chat con IA: no generado (opción 9)"
    fi

    echo -e "\n${CYAN}============================================================${NC}"
}

# ============================================================
# 🗂 MENÚ PRINCIPAL
# ============================================================
menu_principal() {
    banner

    echo -e "  ${BOLD}FUENTES DISPONIBLES:${NC}\n"
    echo -e "  ${CYAN}Wikipedia / Wikimedia:${NC}"
    echo -e "    ${BOLD}1)${NC} Wikipedia          (30 idiomas)"
    echo -e "    ${BOLD}2)${NC} Wikisource         (textos originales)"
    echo -e "    ${BOLD}3)${NC} Wiktionary         (diccionario completo)"
    echo ""
    echo -e "  ${CYAN}Ciencia y Técnica:${NC}"
    echo -e "    ${BOLD}4)${NC} Arxiv Abstracts    (2.4M papers científicos)"
    echo -e "    ${BOLD}5)${NC} Stack Overflow     (Q&A técnico, score>5)"
    echo ""
    echo -e "  ${CYAN}Literatura:${NC}"
    echo -e "    ${BOLD}6)${NC} Project Gutenberg  (70.000+ libros clásicos)"
    echo ""
    echo -e "  ${CYAN}Herramientas:${NC}"
    echo -e "    ${BOLD}7)${NC} Ver índices existentes"
    echo -e "    ${BOLD}8)${NC} Generar buscador universal  ${CYAN}(query_universal_rag.py)${NC}"
    echo -e "    ${BOLD}9)${NC} Generar chat con IA + RAG   ${CYAN}(chat_universal_rag.py)${NC}"
    echo -e "    ${BOLD}0)${NC} Salir"
    echo ""
    read -p "$(echo -e ${YELLOW})Elige opción: $(echo -e ${NC})" opcion

    case "$opcion" in
        1)
            crear_entorno
            local sorted_keys=($(echo "${!WIKI_LANGS[@]}" | tr ' ' '\n' | sort))
            echo ""; echo -e "  ${BOLD}Idiomas:${NC}"
            local i=1
            for key in "${sorted_keys[@]}"; do
                printf "    ${BOLD}%2d)${NC} %-8s %s\n" "$i" "[$key]" "${WIKI_LANGS[$key]}"
                ((i++))
            done
            echo ""; read -p "$(echo -e ${YELLOW})Elige idioma: $(echo -e ${NC})" sel
            local code="${sorted_keys[$((sel-1))]}"
            local name="${WIKI_LANGS[$code]}"
            procesar_wikimedia "wikipedia" "$code" "Wikipedia $name [$code]"
            ;;
        2)
            crear_entorno
            read -p "$(echo -e ${YELLOW})Código de idioma (en/es/fr/de...): $(echo -e ${NC})" lang
            procesar_wikimedia "wikisource" "$lang" "Wikisource [$lang]"
            ;;
        3)
            crear_entorno
            read -p "$(echo -e ${YELLOW})Código de idioma (en/es/fr/de...): $(echo -e ${NC})" lang
            procesar_wikimedia "wiktionary" "$lang" "Wiktionary [$lang]"
            ;;
        4)  crear_entorno; procesar_arxiv ;;
        5)  crear_entorno; procesar_stackoverflow ;;
        6)  crear_entorno; procesar_gutenberg ;;
        7)  mostrar_resumen ;;
        8)  generar_query_universal ;;
        9)  generar_chat_universal ;;
        0)  echo "Hasta luego 🧠"; exit 0 ;;
        *)  error "Opción inválida" ;;
    esac
}

# ============================================================
# 🚀 EJECUCIÓN
# ============================================================
validar_dependencias
menu_principal "$@"
