#!/bin/bash
# ============================================================
# 🧠 BIBLIOGALACTIC — LOCAL AI CHAT
# ============================================================
# 1. Detecta o pregunta por llama-cli y modelo .gguf
# 2. Escribe el gateway Python
# 3. Lo arranca en background
# 4. llama-cli genera el HTML del chat
# 5. Abre el chat en el navegador
# ============================================================
# Requisitos: llama.cpp compilado, python3, modelo .gguf
# https://github.com/BiblioGalactic
# ============================================================

set -euo pipefail
trap cleanup EXIT

# ── CONFIG ─────────────────────────────────────────────────
GW="/tmp/gw_bibliogalactic.py"
HTML="/tmp/chat_ia.html"
GW_PID=""
LLAMA=""
MODELO=""

# ── BÚSQUEDA AUTOMÁTICA ────────────────────────────────────
buscar_llama() {
  find "$HOME" /usr/local /opt -name "llama-cli" -type f 2>/dev/null | head -1
}

buscar_modelos() {
  find "$HOME" -name "*.gguf" -type f 2>/dev/null | head -10
}

# ── CONFIGURAR RUTAS ───────────────────────────────────────
configurar() {
  echo ""
  echo "╔══════════════════════════════════════════╗"
  echo "║   🧠 BIBLIOGALACTIC — LOCAL AI CHAT      ║"
  echo "╚══════════════════════════════════════════╝"
  echo ""

  # ── llama-cli
  local auto_llama
  auto_llama=$(buscar_llama || echo "")

  if [[ -n "$auto_llama" ]]; then
    echo "✅ llama-cli encontrado: $auto_llama"
    read -rp "   ¿Usar este? [S/n]: " confirm
    [[ "${confirm,,}" != "n" ]] && LLAMA="$auto_llama"
  fi

  if [[ -z "$LLAMA" ]]; then
    read -rp "📂 Ruta a llama-cli: " LLAMA
  fi

  [[ ! -f "$LLAMA" ]] && { echo "❌ llama-cli no encontrado: $LLAMA"; exit 1; }

  # ── Modelo .gguf
  echo ""
  local modelos
  modelos=$(buscar_modelos || echo "")

  if [[ -n "$modelos" ]]; then
    echo "📦 Modelos .gguf encontrados:"
    local i=1
    while IFS= read -r m; do
      echo "   [$i] $m"
      ((i++))
    done <<< "$modelos"
    echo ""
    read -rp "   Número (o Enter para ruta manual): " sel
    if [[ -n "$sel" && "$sel" =~ ^[0-9]+$ ]]; then
      MODELO=$(echo "$modelos" | sed -n "${sel}p")
    fi
  fi

  if [[ -z "$MODELO" ]]; then
    read -rp "📂 Ruta al modelo .gguf: " MODELO
  fi

  [[ ! -f "$MODELO" ]] && { echo "❌ Modelo no encontrado: $MODELO"; exit 1; }

  echo ""
  echo "✅ llama-cli : $LLAMA"
  echo "✅ Modelo    : $MODELO"
  echo ""
}

# ── VALIDAR ────────────────────────────────────────────────
validar() {
  command -v python3 &>/dev/null || { echo "❌ python3 no instalado"; exit 1; }
  echo "✅ python3 OK"
}

# ── GATEWAY ────────────────────────────────────────────────
escribir_gateway() {
  cat > "$GW" << PYEOF
import subprocess, json
from http.server import HTTPServer, BaseHTTPRequestHandler

LLAMA = "$LLAMA"
MODELO = "$MODELO"

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','POST')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()
    def do_POST(self):
        n = int(self.headers['Content-Length'])
        msg = json.loads(self.rfile.read(n)).get('msg','')
        r = subprocess.run(
            [LLAMA,'-m',MODELO,'-p',msg,'-n','300','--temp','0.7','-no-cnv'],
            capture_output=True, text=True
        )
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        self.wfile.write(json.dumps({'reply':r.stdout.strip()}).encode())

HTTPServer(('localhost',8080),Handler).serve_forever()
PYEOF
  echo "📝 Gateway listo"
}

# ── EJECUTAR ───────────────────────────────────────────────
ejecutar() {
  python3 "$GW" &
  GW_PID=$!
  echo "🌐 Gateway corriendo (PID $GW_PID) en localhost:8080"
  sleep 1

  echo "🤖 Generando interfaz de chat..."
  "$LLAMA" \
    -m "$MODELO" \
    -p "Genera un chat HTML oscuro estilo terminal. El botón enviar hace POST a http://localhost:8080 con JSON {msg:'...'} y muestra la respuesta. Solo código HTML, sin explicaciones." \
    -n 2000 --temp 0.7 -no-cnv > "$HTML"
  echo "✅ HTML generado"

  open "$HTML" 2>/dev/null || xdg-open "$HTML" 2>/dev/null || echo "📂 Abre manualmente: $HTML"
  echo "🚀 Chat abierto — Ctrl+C para cerrar todo"

  wait "$GW_PID"
}

# ── CLEANUP ────────────────────────────────────────────────
cleanup() {
  echo ""
  echo "👋 Cerrando gateway..."
  [[ -n "$GW_PID" ]] && kill "$GW_PID" 2>/dev/null || true
  rm -f "$GW" "$HTML"
  echo "🗑️  Temporales eliminados"
}

# ── MAIN ───────────────────────────────────────────────────
configurar
validar
escribir_gateway
ejecutar
