#!/bin/bash 🤖
# ============================================================
# MCP Setup - Servidor + Cliente Chat con IA Local
# 11 HERRAMIENTAS + MODO AGÉNTICO
# ============================================================
set -euo pipefail

# === CONFIGURACIÓN ===
INSTALL_DIR="${HOME}/.mcp_local"
CONFIG_FILE="${INSTALL_DIR}/config.env"
PY_ENV="${INSTALL_DIR}/venv"
MCP_SERVER="${INSTALL_DIR}/mcp_server.py"
MCP_CLIENT="${INSTALL_DIR}/chat_mcp.py"
TEMP_FILES=()

# === TRAP PARA LIMPIEZA ===
trap cleanup EXIT

cleanup() {
  if [ ${#TEMP_FILES[@]} -gt 0 ]; then
    rm -rf "${TEMP_FILES[@]}" 2>/dev/null || true
  fi
}

# === FUNCIONES DE VALIDACIÓN ===
validar_comando() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "❌ Error: $cmd no está instalado." >&2
    return 1
  fi
  echo "✅ $cmd encontrado"
  return 0
}

validar_archivo() {
  local archivo="$1"
  local tipo="${2:-archivo}"
  
  if [ ! -e "$archivo" ]; then
    echo "❌ Error: $tipo no existe: $archivo" >&2
    return 1
  fi
  
  if [ "$tipo" == "ejecutable" ] && [ ! -x "$archivo" ]; then
    echo "❌ Error: $archivo no tiene permisos de ejecución" >&2
    return 1
  fi
  
  if [ "$tipo" == "modelo" ] && [ ! -r "$archivo" ]; then
    echo "❌ Error: No se puede leer el modelo: $archivo" >&2
    return 1
  fi
  
  echo "✅ $tipo válido: $archivo"
  return 0
}

# === CONFIGURACIÓN INICIAL ===
configurar_primera_vez() {
  echo ""
  echo "🎯 CONFIGURACIÓN INICIAL"
  echo "=========================================="
  echo ""
  
  echo "📍 Paso 1/2: Ruta del ejecutable llama-cli"
  echo "   Ejemplo: /usr/local/bin/llama-cli"
  echo "   o: $HOME/llama.cpp/build/bin/llama-cli"
  read -rp "   Ruta completa: " LLAMA_CLI
  
  if ! validar_archivo "$LLAMA_CLI" "ejecutable"; then
    echo "❌ No se puede continuar sin un ejecutable válido"
    exit 1
  fi
  
  echo ""
  echo "📍 Paso 2/2: Ruta del modelo GGUF"
  echo "   Ejemplo: $HOME/modelos/mistral-7b-instruct.gguf"
  read -rp "   Ruta completa: " MODELO_GGUF
  
  if ! validar_archivo "$MODELO_GGUF" "modelo"; then
    echo "❌ No se puede continuar sin un modelo válido"
    exit 1
  fi
  
  mkdir -p "$INSTALL_DIR"
  
  cat > "$CONFIG_FILE" <<EOF
# Configuración MCP Local
LLAMA_CLI="$LLAMA_CLI"
MODELO_GGUF="$MODELO_GGUF"
EOF
  
  chmod 600 "$CONFIG_FILE"
  echo ""
  echo "✅ Configuración guardada en: $CONFIG_FILE"
  echo ""
}

# === INSTALACIÓN DE DEPENDENCIAS ===
instalar_dependencias() {
  echo ""
  echo "📦 INSTALANDO DEPENDENCIAS"
  echo "=========================================="
  
  if ! validar_comando python3; then
    echo "❌ Instala Python 3 antes de continuar"
    exit 1
  fi
  
  if [ ! -d "$PY_ENV" ]; then
    echo "🔧 Creando entorno virtual Python..."
    python3 -m venv "$PY_ENV"
  fi
  
  source "$PY_ENV/bin/activate"
  
  echo "📥 Instalando paquetes Python..."
  pip install --quiet --upgrade pip
  pip install --quiet flask psutil requests
  
  if ! pip show flask >/dev/null 2>&1 || ! pip show psutil >/dev/null 2>&1 || ! pip show requests >/dev/null 2>&1; then
    echo "❌ Error instalando dependencias Python"
    deactivate
    exit 1
  fi
  
  echo "✅ Dependencias instaladas correctamente"
}

# === GENERAR SERVIDOR MCP (sin cambios, es el mismo) ===
generar_servidor() {
  if [ -f "$MCP_SERVER" ]; then
    echo "ℹ️  Servidor MCP ya existe, omitiendo..."
    return 0
  fi
  
  echo "🔨 Generando servidor MCP..."
  
  cat > "$MCP_SERVER" <<'EOFSERVER'
#!/usr/bin/env python3
"""
Servidor MCP - Model Context Protocol
11 Herramientas completas para IAs locales
"""
import sys
import json
import os
import logging
import subprocess
import psutil
import requests
from pathlib import Path
import fnmatch
import zipfile
import tarfile
import shutil
import re

DEBUG = bool(os.environ.get("MCP_DEBUG"))
logger = logging.getLogger("MCP")
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter("[MCP] %(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG if DEBUG else logging.WARNING)

COMANDOS_BLOQUEADOS = ['rm', 'dd', 'mkfs', 'format', ':(){:|:&};:', 'fork', '>()', 'sudo', 'su']
MAX_FILE_SIZE = 10 * 1024 * 1024

def debug(msg):
    if DEBUG:
        logger.debug(msg)

def send_response(id, result):
    resp = {"jsonrpc": "2.0", "id": id, "result": result}
    print(json.dumps(resp), flush=True)

def send_error(id, code, message):
    resp = {"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}}
    print(json.dumps(resp), flush=True)

def es_ruta_segura(ruta):
    try:
        ruta_abs = os.path.abspath(os.path.expanduser(ruta))
        home = os.path.expanduser("~")
        return ruta_abs.startswith(home) or ruta_abs.startswith("/tmp")
    except:
        return False

def read_file_safe(path, max_bytes=65536):
    if not path or not isinstance(path, str):
        return None, "Ruta inválida"
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return None, f"Archivo no encontrado: {path}"
    if not os.path.isfile(path):
        return None, f"No es un archivo: {path}"
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_bytes)
        return content, None
    except Exception as e:
        return None, f"Error: {str(e)}"

def consultar_memoria():
    result = {}
    try:
        mem = psutil.virtual_memory()
        result["memoria_total_gb"] = round(mem.total / (1024**3), 2)
        result["memoria_disponible_gb"] = round(mem.available / (1024**3), 2)
        result["memoria_usada_percent"] = mem.percent
    except Exception as e:
        result["memoria_error"] = str(e)
    try:
        cpu = psutil.cpu_percent(interval=1)
        result["cpu_percent"] = cpu
        result["cpu_count"] = psutil.cpu_count()
    except Exception as e:
        result["cpu_error"] = str(e)
    try:
        disk = psutil.disk_usage('/')
        result["disco_total_gb"] = round(disk.total / (1024**3), 2)
        result["disco_libre_gb"] = round(disk.free / (1024**3), 2)
        result["disco_usado_percent"] = disk.percent
    except Exception as e:
        result["disco_error"] = str(e)
    return result

def ejecutar_comando(comando, timeout=10):
    if not comando or not isinstance(comando, str):
        return None, "Comando inválido"
    comando_lower = comando.lower()
    for cmd_bloqueado in COMANDOS_BLOQUEADOS:
        if cmd_bloqueado in comando_lower:
            return None, f"Comando bloqueado por seguridad: {cmd_bloqueado}"
    try:
        result = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=timeout, cwd=os.path.expanduser("~"))
        output = {
            "stdout": result.stdout[:4096] if result.stdout else "",
            "stderr": result.stderr[:1024] if result.stderr else "",
            "returncode": result.returncode
        }
        return output, None
    except subprocess.TimeoutExpired:
        return None, f"Timeout: comando tardó más de {timeout}s"
    except Exception as e:
        return None, f"Error ejecutando comando: {str(e)}"

def listar_directorio(ruta, mostrar_ocultos=False):
    if not ruta:
        ruta = "~"
    ruta = os.path.expanduser(ruta)
    if not os.path.exists(ruta):
        return None, f"Directorio no encontrado: {ruta}"
    if not os.path.isdir(ruta):
        return None, f"No es un directorio: {ruta}"
    try:
        items = []
        for entry in os.listdir(ruta):
            if not mostrar_ocultos and entry.startswith('.'):
                continue
            full_path = os.path.join(ruta, entry)
            try:
                stat = os.stat(full_path)
                item = {
                    "nombre": entry,
                    "tipo": "directorio" if os.path.isdir(full_path) else "archivo",
                    "tamaño_bytes": stat.st_size if os.path.isfile(full_path) else 0,
                    "modificado": stat.st_mtime
                }
                items.append(item)
            except Exception:
                continue
        items.sort(key=lambda x: (x['tipo'] != 'directorio', x['nombre']))
        return {"ruta": ruta, "items": items[:100], "total": len(items)}, None
    except Exception as e:
        return None, f"Error listando directorio: {str(e)}"

def buscar_archivos(directorio, patron, max_resultados=50):
    if not directorio:
        directorio = "~"
    if not patron:
        return None, "Patrón de búsqueda requerido"
    directorio = os.path.expanduser(directorio)
    if not os.path.exists(directorio):
        return None, f"Directorio no encontrado: {directorio}"
    if not os.path.isdir(directorio):
        return None, f"No es un directorio: {directorio}"
    try:
        resultados = []
        path_obj = Path(directorio)
        for item in path_obj.rglob('*'):
            if len(resultados) >= max_resultados:
                break
            if fnmatch.fnmatch(item.name, patron):
                try:
                    stat = item.stat()
                    resultados.append({
                        "ruta": str(item),
                        "nombre": item.name,
                        "tipo": "directorio" if item.is_dir() else "archivo",
                        "tamaño_bytes": stat.st_size if item.is_file() else 0
                    })
                except Exception:
                    continue
        return {"directorio_base": directorio, "patron": patron, "resultados": resultados, "total_encontrado": len(resultados)}, None
    except Exception as e:
        return None, f"Error buscando archivos: {str(e)}"

def consultar_api(url, metodo="GET", headers=None, body=None, timeout=10):
    if not url or not isinstance(url, str):
        return None, "URL inválida"
    if not url.startswith(('http://', 'https://')):
        return None, "URL debe empezar con http:// o https://"
    metodo = metodo.upper()
    if metodo not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
        return None, f"Método HTTP no soportado: {metodo}"
    try:
        kwargs = {'timeout': timeout, 'headers': headers or {}}
        if body and metodo in ['POST', 'PUT', 'PATCH']:
            if isinstance(body, dict):
                kwargs['json'] = body
            else:
                kwargs['data'] = body
        response = requests.request(metodo, url, **kwargs)
        try:
            content = response.json()
        except:
            content = response.text[:4096]
        return {"status_code": response.status_code, "headers": dict(response.headers), "content": content, "ok": response.ok}, None
    except requests.Timeout:
        return None, f"Timeout: API tardó más de {timeout}s"
    except Exception as e:
        return None, f"Error consultando API: {str(e)}"

def escribir_archivo(ruta, contenido, modo="w"):
    if not ruta or not isinstance(ruta, str):
        return None, "Ruta inválida"
    if contenido is None:
        return None, "Contenido no puede ser None"
    ruta = os.path.expanduser(ruta)
    if not es_ruta_segura(ruta):
        return None, "Ruta no permitida (solo dentro de $HOME o /tmp)"
    if len(contenido) > MAX_FILE_SIZE:
        return None, f"Contenido excede límite de {MAX_FILE_SIZE/1024/1024}MB"
    if modo not in ['w', 'a']:
        return None, "Modo debe ser 'w' (escribir) o 'a' (añadir)"
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, modo, encoding="utf-8") as f:
            f.write(contenido)
        return {"ruta": ruta, "bytes_escritos": len(contenido.encode('utf-8')), "modo": modo}, None
    except Exception as e:
        return None, f"Error escribiendo archivo: {str(e)}"

def descargar_archivo(url, ruta_destino):
    if not url or not isinstance(url, str):
        return None, "URL inválida"
    if not ruta_destino or not isinstance(ruta_destino, str):
        return None, "Ruta destino inválida"
    if not url.startswith(('http://', 'https://')):
        return None, "URL debe empezar con http:// o https://"
    ruta_destino = os.path.expanduser(ruta_destino)
    if not es_ruta_segura(ruta_destino):
        return None, "Ruta destino no permitida (solo dentro de $HOME o /tmp)"
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > MAX_FILE_SIZE:
            return None, f"Archivo excede límite de {MAX_FILE_SIZE/1024/1024}MB"
        os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
        bytes_descargados = 0
        with open(ruta_destino, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                bytes_descargados += len(chunk)
                if bytes_descargados > MAX_FILE_SIZE:
                    f.close()
                    os.remove(ruta_destino)
                    return None, f"Descarga excede límite de {MAX_FILE_SIZE/1024/1024}MB"
                f.write(chunk)
        return {"url": url, "ruta_destino": ruta_destino, "bytes_descargados": bytes_descargados, "tipo_contenido": response.headers.get('content-type', 'desconocido')}, None
    except Exception as e:
        return None, f"Error descargando archivo: {str(e)}"

def comprimir_descomprimir(operacion, origen, destino=None, formato="zip"):
    if operacion not in ['comprimir', 'descomprimir']:
        return None, "Operación debe ser 'comprimir' o 'descomprimir'"
    if not origen or not isinstance(origen, str):
        return None, "Ruta origen inválida"
    origen = os.path.expanduser(origen)
    if not os.path.exists(origen):
        return None, f"Origen no encontrado: {origen}"
    if formato not in ['zip', 'tar', 'tar.gz']:
        return None, "Formato debe ser 'zip', 'tar' o 'tar.gz'"
    try:
        if operacion == 'comprimir':
            if not destino:
                destino = f"{origen}.{formato}"
            destino = os.path.expanduser(destino)
            if not es_ruta_segura(destino):
                return None, "Ruta destino no permitida"
            if formato == 'zip':
                with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as zf:
                    if os.path.isfile(origen):
                        zf.write(origen, os.path.basename(origen))
                    else:
                        for root, dirs, files in os.walk(origen):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, os.path.dirname(origen))
                                zf.write(file_path, arcname)
            elif formato in ['tar', 'tar.gz']:
                mode = 'w:gz' if formato == 'tar.gz' else 'w'
                with tarfile.open(destino, mode) as tf:
                    tf.add(origen, arcname=os.path.basename(origen))
            return {"operacion": "comprimir", "origen": origen, "destino": destino, "formato": formato, "tamaño_bytes": os.path.getsize(destino)}, None
        else:
            if not destino:
                destino = os.path.dirname(origen)
            destino = os.path.expanduser(destino)
            if not es_ruta_segura(destino):
                return None, "Ruta destino no permitida"
            os.makedirs(destino, exist_ok=True)
            if formato == 'zip':
                with zipfile.ZipFile(origen, 'r') as zf:
                    zf.extractall(destino)
            elif formato in ['tar', 'tar.gz']:
                with tarfile.open(origen, 'r:*') as tf:
                    tf.extractall(destino)
            return {"operacion": "descomprimir", "origen": origen, "destino": destino, "formato": formato}, None
    except Exception as e:
        return None, f"Error en compresión/descompresión: {str(e)}"

def git_operation(operacion, repo_path=None, args=None):
    if not operacion or not isinstance(operacion, str):
        return None, "Operación inválida"
    if not repo_path:
        repo_path = "."
    repo_path = os.path.expanduser(repo_path)
    operaciones_permitidas = ['status', 'log', 'diff', 'branch', 'remote']
    if operacion not in operaciones_permitidas:
        return None, f"Operación no permitida. Usa: {', '.join(operaciones_permitidas)}"
    try:
        cmd = ['git', operacion]
        if operacion == 'log':
            cmd.extend(['--oneline', '-10'])
        elif operacion == 'diff':
            cmd.append('--stat')
        if args and isinstance(args, list):
            cmd.extend(args)
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=10)
        return {"operacion": operacion, "repo_path": repo_path, "stdout": result.stdout[:4096], "stderr": result.stderr[:1024], "returncode": result.returncode}, None
    except subprocess.TimeoutExpired:
        return None, "Timeout: operación git tardó demasiado"
    except Exception as e:
        return None, f"Error en operación git: {str(e)}"

def buscar_en_contenido(directorio, patron, extension=None, max_resultados=50):
    if not directorio:
        directorio = "~"
    if not patron:
        return None, "Patrón de búsqueda requerido"
    directorio = os.path.expanduser(directorio)
    if not os.path.exists(directorio):
        return None, f"Directorio no encontrado: {directorio}"
    if not os.path.isdir(directorio):
        return None, f"No es un directorio: {directorio}"
    try:
        patron_regex = re.compile(patron, re.IGNORECASE)
        resultados = []
        for root, dirs, files in os.walk(directorio):
            if len(resultados) >= max_resultados:
                break
            for file in files:
                if len(resultados) >= max_resultados:
                    break
                if extension and not file.endswith(extension):
                    continue
                file_path = os.path.join(root, file)
                try:
                    if os.path.getsize(file_path) > 1024 * 1024:
                        continue
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for num_linea, linea in enumerate(f, 1):
                            if patron_regex.search(linea):
                                resultados.append({"archivo": file_path, "linea": num_linea, "contenido": linea.strip()[:200]})
                                if len(resultados) >= max_resultados:
                                    break
                except Exception:
                    continue
        return {"directorio": directorio, "patron": patron, "extension": extension, "resultados": resultados, "total_encontrado": len(resultados)}, None
    except Exception as e:
        return None, f"Error buscando en contenido: {str(e)}"

TOOLS = [
    {"name": "leer_archivo", "description": "Lee contenido de un archivo (máx 64KB)", "params": ["ruta"]},
    {"name": "consultar_memoria", "description": "Consulta recursos del sistema (RAM, CPU, disco)", "params": []},
    {"name": "ejecutar_comando", "description": "Ejecuta un comando bash (bloqueados: rm, dd, sudo, etc)", "params": ["comando", "timeout"]},
    {"name": "listar_directorio", "description": "Lista contenido de un directorio", "params": ["ruta", "mostrar_ocultos"]},
    {"name": "buscar_archivos", "description": "Busca archivos por patrón (glob) recursivamente", "params": ["directorio", "patron", "max_resultados"]},
    {"name": "consultar_api", "description": "Hace petición HTTP a una API (GET, POST, etc)", "params": ["url", "metodo", "headers", "body", "timeout"]},
    {"name": "escribir_archivo", "description": "Escribe contenido en un archivo (máx 10MB)", "params": ["ruta", "contenido", "modo"]},
    {"name": "descargar_archivo", "description": "Descarga archivo desde URL (máx 10MB)", "params": ["url", "ruta_destino"]},
    {"name": "comprimir_descomprimir", "description": "Comprime/descomprime archivos (zip, tar, tar.gz)", "params": ["operacion", "origen", "destino", "formato"]},
    {"name": "git_operation", "description": "Operaciones git (status, log, diff, branch, remote)", "params": ["operacion", "repo_path", "args"]},
    {"name": "buscar_en_contenido", "description": "Busca texto dentro de archivos (grep)", "params": ["directorio", "patron", "extension", "max_resultados"]}
]

def handle_request(req):
    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params") or {}
    debug(f"Request: {method}")
    
    if method == "initialize":
        send_response(req_id, {"status": "ok", "version": "3.0", "tools": len(TOOLS)})
    elif method == "tools/list":
        send_response(req_id, TOOLS)
    elif method == "leer_archivo":
        ruta = params.get("ruta")
        if not ruta:
            send_error(req_id, -32602, "Parámetro 'ruta' requerido")
            return
        contenido, err = read_file_safe(ruta)
        if err:
            send_error(req_id, -32001, err)
        else:
            send_response(req_id, {"ruta": ruta, "contenido": contenido})
    elif method == "consultar_memoria":
        data = consultar_memoria()
        send_response(req_id, data)
    elif method == "ejecutar_comando":
        comando = params.get("comando")
        timeout = params.get("timeout", 10)
        if not comando:
            send_error(req_id, -32602, "Parámetro 'comando' requerido")
            return
        result, err = ejecutar_comando(comando, timeout)
        if err:
            send_error(req_id, -32002, err)
        else:
            send_response(req_id, result)
    elif method == "listar_directorio":
        ruta = params.get("ruta", "~")
        mostrar_ocultos = params.get("mostrar_ocultos", False)
        result, err = listar_directorio(ruta, mostrar_ocultos)
        if err:
            send_error(req_id, -32003, err)
        else:
            send_response(req_id, result)
    elif method == "buscar_archivos":
        directorio = params.get("directorio", "~")
        patron = params.get("patron")
        max_resultados = params.get("max_resultados", 50)
        if not patron:
            send_error(req_id, -32602, "Parámetro 'patron' requerido")
            return
        result, err = buscar_archivos(directorio, patron, max_resultados)
        if err:
            send_error(req_id, -32004, err)
        else:
            send_response(req_id, result)
    elif method == "consultar_api":
        url = params.get("url")
        metodo = params.get("metodo", "GET")
        headers = params.get("headers")
        body = params.get("body")
        timeout = params.get("timeout", 10)
        if not url:
            send_error(req_id, -32602, "Parámetro 'url' requerido")
            return
        result, err = consultar_api(url, metodo, headers, body, timeout)
        if err:
            send_error(req_id, -32005, err)
        else:
            send_response(req_id, result)
    elif method == "escribir_archivo":
        ruta = params.get("ruta")
        contenido = params.get("contenido")
        modo = params.get("modo", "w")
        if not ruta or contenido is None:
            send_error(req_id, -32602, "Parámetros 'ruta' y 'contenido' requeridos")
            return
        result, err = escribir_archivo(ruta, contenido, modo)
        if err:
            send_error(req_id, -32006, err)
        else:
            send_response(req_id, result)
    elif method == "descargar_archivo":
        url = params.get("url")
        ruta_destino = params.get("ruta_destino")
        if not url or not ruta_destino:
            send_error(req_id, -32602, "Parámetros 'url' y 'ruta_destino' requeridos")
            return
        result, err = descargar_archivo(url, ruta_destino)
        if err:
            send_error(req_id, -32007, err)
        else:
            send_response(req_id, result)
    elif method == "comprimir_descomprimir":
        operacion = params.get("operacion")
        origen = params.get("origen")
        destino = params.get("destino")
        formato = params.get("formato", "zip")
        if not operacion or not origen:
            send_error(req_id, -32602, "Parámetros 'operacion' y 'origen' requeridos")
            return
        result, err = comprimir_descomprimir(operacion, origen, destino, formato)
        if err:
            send_error(req_id, -32008, err)
        else:
            send_response(req_id, result)
    elif method == "git_operation":
        operacion = params.get("operacion")
        repo_path = params.get("repo_path")
        args = params.get("args")
        if not operacion:
            send_error(req_id, -32602, "Parámetro 'operacion' requerido")
            return
        result, err = git_operation(operacion, repo_path, args)
        if err:
            send_error(req_id, -32009, err)
        else:
            send_response(req_id, result)
    elif method == "buscar_en_contenido":
        directorio = params.get("directorio", "~")
        patron = params.get("patron")
        extension = params.get("extension")
        max_resultados = params.get("max_resultados", 50)
        if not patron:
            send_error(req_id, -32602, "Parámetro 'patron' requerido")
            return
        result, err = buscar_en_contenido(directorio, patron, extension, max_resultados)
        if err:
            send_error(req_id, -32010, err)
        else:
            send_response(req_id, result)
    else:
        send_error(req_id, -32601, f"Método desconocido: {method}")

def main():
    debug("Servidor MCP iniciado (stdin/stdout) - 11 herramientas")
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            req = json.loads(line)
            handle_request(req)
        except json.JSONDecodeError as e:
            send_error(None, -32700, f"JSON inválido: {str(e)}")
        except Exception as e:
            send_error(None, -32099, f"Error interno: {str(e)}")

if __name__ == "__main__":
    main()
EOFSERVER
  
  chmod +x "$MCP_SERVER"
  echo "✅ Servidor MCP generado (11 herramientas)"
}

# === GENERAR CLIENTE CON MODO AGÉNTICO ===
generar_cliente() {
  if [ -f "$MCP_CLIENT" ]; then
    echo "ℹ️  Cliente chat ya existe, omitiendo..."
    return 0
  fi
  
  echo "🔨 Generando cliente de chat CON MODO AGÉNTICO..."
  
  cat > "$MCP_CLIENT" <<'EOFCLIENT'
#!/usr/bin/env python3
"""
Cliente Chat MCP - 11 Herramientas + MODO AGÉNTICO
Puede encadenar múltiples acciones automáticamente
"""
import subprocess
import json
import re
import sys
import os
import time

# === Cargar configuración ===
CONFIG_FILE = os.path.expanduser("~/.mcp_local/config.env")
config = {}

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                config[key] = value.strip('"')

IA_CMD = [
    config.get('LLAMA_CLI', 'llama-cli'),
    "--model", config.get('MODELO_GGUF', ''),
    "--n-predict", "512",
    "--temp", "0.7",
    "--ctx-size", "4096"
]

MCP_SERVER = os.path.expanduser("~/.mcp_local/mcp_server.py")

# Estado global
MODO_AGENTICO = False
VERBOSE = False

# === Funciones MCP ===
def llamar_mcp(metodo, params=None):
    params = params or {}
    request = {"jsonrpc": "2.0", "id": 1, "method": metodo, "params": params}
    
    try:
        proc = subprocess.Popen(
            ["python3", MCP_SERVER],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, _ = proc.communicate(json.dumps(request), timeout=20)
        
        for line in stdout.strip().split('\n'):
            if line.startswith('{'):
                return json.loads(line)
        return None
    except Exception as e:
        if VERBOSE:
            print(f"❌ Error MCP: {e}", file=sys.stderr)
        return None

# === IA ===
def consultar_ia(prompt):
    try:
        result = subprocess.run(
            IA_CMD + ["--prompt", prompt],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "⏱️ Timeout - la IA tardó demasiado"
    except Exception as e:
        return f"❌ Error: {e}"

# === SISTEMA AGÉNTICO ===
def planificar_pasos(user_input):
    """Planifica los pasos necesarios para completar una tarea compleja"""
    
    planning_prompt = f"""Eres un planificador experto de tareas. Descompón la siguiente solicitud en pasos ESPECÍFICOS Y ÚNICOS.

SOLICITUD: {user_input}

HERRAMIENTAS DISPONIBLES:
- LEER:ruta - Leer archivo
- MEMORIA - Consultar recursos del sistema
- COMANDO:cmd - Ejecutar comando bash
- LISTAR:dir - Listar directorio
- BUSCAR:dir:patron - Buscar archivos
- API:url:metodo - Consultar API
- ESCRIBIR:ruta:contenido:modo - Escribir archivo
- DESCARGAR:url:destino - Descargar archivo
- COMPRIMIR:op:origen:destino:fmt - Comprimir/descomprimir
- GIT:operacion:path - Operaciones git
- GREP:dir:patron:ext - Buscar en contenido

INSTRUCCIONES CRÍTICAS:
- Máximo 4 pasos específicos y diferentes
- Cada paso debe ser una acción concreta con herramienta específica
- NO repitas conceptos ni acciones similares
- Usa el formato EXACTO: "HERRAMIENTA:parametros"

EJEMPLOS BUENOS:
Request: "descarga el README de github y comprime todos los markdown del escritorio"
Pasos: ["DESCARGAR:https://raw.githubusercontent.com/...:~/Desktop/README.md", "BUSCAR:~/Desktop:*.md", "COMPRIMIR:comprimir:~/Desktop:~/Desktop/docs.zip:zip"]

Request: "lista los archivos Python y busca TODOs en ellos"
Pasos: ["BUSCAR:.:*.py", "GREP:.:TODO:.py"]

Responde SOLO con el array JSON de pasos:
["PASO1", "PASO2", "PASO3"]

JSON:"""

    if VERBOSE:
        print("🧠 Planificando pasos...")
    
    response = consultar_ia(planning_prompt)
    
    try:
        json_match = re.search(r'\[\s*"[^"]+"\s*(?:,\s*"[^"]+"\s*)*\]', response, re.DOTALL)
        if json_match:
            pasos = json.loads(json_match.group())
            if isinstance(pasos, list) and all(isinstance(p, str) for p in pasos):
                if VERBOSE:
                    print(f"📋 Pasos planificados: {pasos}")
                return pasos[:4]
    except Exception as e:
        if VERBOSE:
            print(f"⚠️ Error parseando plan: {e}")
    
    # Fallback inteligente
    return fallback_planner(user_input)

def fallback_planner(user_input):
    """Fallback cuando el LLM no genera plan válido"""
    user_lower = user_input.lower()
    
    if "descargar" in user_lower and ("buscar" in user_lower or "comprimir" in user_lower):
        return ["DESCARGAR:url:destino", "BUSCAR:directorio:patron", "COMPRIMIR:comprimir:origen:destino:zip"]
    elif "lista" in user_lower and "busca" in user_lower:
        return ["LISTAR:directorio", "GREP:directorio:patron:extension"]
    elif "git" in user_lower:
        return ["GIT:status:.", "GIT:log:."]
    else:
        # Intento genérico
        return ["LISTAR:.", "BUSCAR:.:*"]

def ejecutar_paso(paso_str, contexto_previo):
    """Ejecuta un paso específico y retorna el resultado"""
    
    if VERBOSE:
        print(f"🔍 Ejecutando: {paso_str}")
    
    # Parsear paso
    partes = paso_str.split(':', 4)
    if not partes:
        return {"error": "Paso inválido", "paso": paso_str}
    
    herramienta = partes[0]
    
    resultado = {"paso": paso_str, "herramienta": herramienta, "exito": False}
    
    try:
        if herramienta == "LEER" and len(partes) >= 2:
            ruta = partes[1]
            result = llamar_mcp("leer_archivo", {"ruta": ruta})
            if result and 'result' in result:
                resultado["exito"] = True
                resultado["data"] = result['result'].get('contenido', '')[:500]
        
        elif herramienta == "MEMORIA":
            result = llamar_mcp("consultar_memoria")
            if result and 'result' in result:
                resultado["exito"] = True
                resultado["data"] = result['result']
        
        elif herramienta == "COMANDO" and len(partes) >= 2:
            comando = ':'.join(partes[1:])
            result = llamar_mcp("ejecutar_comando", {"comando": comando})
            if result and 'result' in result:
                resultado["exito"] = True
                resultado["data"] = result['result'].get('stdout', '')[:500]
        
        elif herramienta == "LISTAR" and len(partes) >= 2:
            ruta = partes[1] if partes[1] else "."
            result = llamar_mcp("listar_directorio", {"ruta": ruta})
            if result and 'result' in result:
                resultado["exito"] = True
                items = result['result'].get('items', [])
                resultado["data"] = [i['nombre'] for i in items[:10]]
        
        elif herramienta == "BUSCAR" and len(partes) >= 3:
            directorio = partes[1] if partes[1] else "."
            patron = partes[2] if len(partes) > 2 else "*"
            result = llamar_mcp("buscar_archivos", {"directorio": directorio, "patron": patron})
            if result and 'result' in result:
                resultado["exito"] = True
                archivos = result['result'].get('resultados', [])
                resultado["data"] = [a['nombre'] for a in archivos[:10]]
                resultado["rutas_completas"] = [a['ruta'] for a in archivos[:10]]
        
        elif herramienta == "API" and len(partes) >= 2:
            url = partes[1]
            metodo = partes[2] if len(partes) > 2 else "GET"
            result = llamar_mcp("consultar_api", {"url": url, "metodo": metodo})
            if result and 'result' in result:
                resultado["exito"] = True
                resultado["data"] = {"status": result['result'].get('status_code'), "content": str(result['result'].get('content', ''))[:300]}
        
        elif herramienta == "ESCRIBIR" and len(partes) >= 3:
            ruta = partes[1]
            contenido = partes[2] if len(partes) > 2 else ""
            modo = partes[3] if len(partes) > 3 else "w"
            result = llamar_mcp("escribir_archivo", {"ruta": ruta, "contenido": contenido, "modo": modo})
            if result and 'result' in result:
                resultado["exito"] = True
                resultado["data"] = f"Escritos {result['result'].get('bytes_escritos', 0)} bytes"
        
        elif herramienta == "DESCARGAR" and len(partes) >= 3:
            url = partes[1]
            destino = partes[2]
            result = llamar_mcp("descargar_archivo", {"url": url, "ruta_destino": destino})
            if result and 'result' in result:
                resultado["exito"] = True
                resultado["data"] = f"Descargados {result['result'].get('bytes_descargados', 0)} bytes a {destino}"
        
        elif herramienta == "COMPRIMIR" and len(partes) >= 3:
            operacion = partes[1] if len(partes) > 1 else "comprimir"
            origen = partes[2] if len(partes) > 2 else "."
            destino = partes[3] if len(partes) > 3 else None
            formato = partes[4] if len(partes) > 4 else "zip"
            # Usar contexto previo si hay archivos encontrados
            if not destino and 'rutas_completas' in contexto_previo:
                origen = contexto_previo['rutas_completas'][0] if contexto_previo['rutas_completas'] else origen
            result = llamar_mcp("comprimir_descomprimir", {"operacion": operacion, "origen": origen, "destino": destino, "formato": formato})
            if result and 'result' in result:
                resultado["exito"] = True
                resultado["data"] = f"Operación completada: {result['result'].get('destino', 'archivo comprimido')}"
        
        elif herramienta == "GIT" and len(partes) >= 2:
            operacion = partes[1] if len(partes) > 1 else "status"
            repo_path = partes[2] if len(partes) > 2 else "."
            result = llamar_mcp("git_operation", {"operacion": operacion, "repo_path": repo_path})
            if result and 'result' in result:
                resultado["exito"] = True
                resultado["data"] = result['result'].get('stdout', '')[:500]
        
        elif herramienta == "GREP" and len(partes) >= 3:
            directorio = partes[1] if len(partes) > 1 else "."
            patron = partes[2] if len(partes) > 2 else ""
            extension = partes[3] if len(partes) > 3 else None
            result = llamar_mcp("buscar_en_contenido", {"directorio": directorio, "patron": patron, "extension": extension})
            if result and 'result' in result:
                resultado["exito"] = True
                total = result['result'].get('total_encontrado', 0)
                resultado["data"] = f"Encontradas {total} coincidencias"
        
        if VERBOSE:
            estado = "✅" if resultado["exito"] else "❌"
            print(f"   {estado} {herramienta}")
        
    except Exception as e:
        resultado["error"] = str(e)
        if VERBOSE:
            print(f"   ❌ Error: {e}")
    
    return resultado

def sintetizar_resultados(user_input, resultados_pasos):
    """Sintetiza los resultados de todos los pasos ejecutados"""
    
    if not resultados_pasos:
        return "No se pudieron ejecutar los pasos solicitados."
    
    # Construir resumen de acciones
    acciones_exitosas = [r for r in resultados_pasos if r.get('exito')]
    
    if not acciones_exitosas:
        return "No se pudo completar ningún paso de la tarea solicitada."
    
    resumen_context = []
    for i, res in enumerate(acciones_exitosas):
        herramienta = res.get('herramienta', 'desconocida')
        data = res.get('data', 'sin datos')
        resumen_context.append(f"Paso {i+1} ({herramienta}): {data}")
    
    synthesis_prompt = f"""Resume de forma concisa y clara lo que se hizo.

SOLICITUD ORIGINAL: {user_input}

ACCIONES REALIZADAS:
{chr(10).join(resumen_context)}

Responde en 2-3 frases máximo, siendo específico sobre qué se hizo y el resultado.

RESUMEN:"""

    resumen = consultar_ia(synthesis_prompt)
    return resumen.strip()

def ejecutar_agentico(user_input):
    """Modo agéntico: planifica y ejecuta múltiples pasos automáticamente"""
    
    print("🤖 [MODO AGÉNTICO ACTIVADO]")
    
    # 1. Planificar
    pasos = planificar_pasos(user_input)
    print(f"📋 Plan: {len(pasos)} pasos")
    
    # 2. Ejecutar pasos secuencialmente
    resultados = []
    contexto = {}
    
    for i, paso in enumerate(pasos):
        print(f"🔄 Paso {i+1}/{len(pasos)}: {paso[:50]}...")
        resultado = ejecutar_paso(paso, contexto)
        resultados.append(resultado)
        
        # Actualizar contexto para el siguiente paso
        if resultado.get('exito') and 'data' in resultado:
            contexto = {**contexto, **resultado}
        
        time.sleep(0.1)
    
    # 3. Sintetizar
    print("🔄 Sintetizando resultados...")
    resumen_final = sintetizar_resultados(user_input, resultados)
    
    print(f"\n✅ Tarea completada\n")
    return resumen_final

# === Sistema prompt ===
SYSTEM_PROMPT = """Eres un asistente con 11 herramientas del sistema.

Herramientas:
- [LEER:ruta] - Leer archivo
- [MEMORIA] - Recursos del sistema
- [COMANDO:cmd] - Ejecutar bash
- [LISTAR:dir] - Listar directorio
- [BUSCAR:dir:patron] - Buscar archivos
- [API:url:metodo] - Consultar API
- [ESCRIBIR:ruta:contenido:modo] - Escribir archivo
- [DESCARGAR:url:destino] - Descargar
- [COMPRIMIR:op:origen:destino:fmt] - Comprimir/descomprimir
- [GIT:op:path] - Git operations
- [GREP:dir:patron:ext] - Buscar en contenido

Para usar: [USAR_HERRAMIENTA:nombre:parametros]
"""

# === Chat ===
def main():
    global MODO_AGENTICO, VERBOSE
    
    print("╔════════════════════════════════════════╗")
    print("║  🤖 Chat MCP con MODO AGÉNTICO         ║")
    print("║  💪 11 Herramientas + Auto-ejecución   ║")
    print("╚════════════════════════════════════════╝")
    print("")
    print("Comandos:")
    print("  'agentico on/off' - Activar modo agéntico")
    print("  'verbose on/off' - Activar logs detallados")
    print("  'salir' - Terminar")
    print("  'herramientas' - Listar herramientas")
    print("")
    print("💡 Modo agéntico: encadena múltiples acciones automáticamente")
    print("   Ejemplo: 'descarga X, búscalo y comprime todo'")
    print("")
    
    conversacion = []
    
    while True:
        try:
            user_input = input("👤 Tú: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['salir', 'exit', 'quit']:
                print("\n👋 ¡Hasta luego!")
                break
            
            if user_input.lower().startswith('agentico '):
                cmd = user_input.split()[1]
                MODO_AGENTICO = (cmd == 'on')
                print(f"🤖 Modo agéntico: {'ACTIVADO' if MODO_AGENTICO else 'DESACTIVADO'}")
                continue
            
            if user_input.lower().startswith('verbose '):
                cmd = user_input.split()[1]
                VERBOSE = (cmd == 'on')
                print(f"📊 Modo verbose: {'ACTIVADO' if VERBOSE else 'DESACTIVADO'}")
                continue
            
            if user_input.lower() == 'herramientas':
                result = llamar_mcp("tools/list")
                if result and 'result' in result:
                    print("\n🔧 Herramientas MCP (11):")
                    for i, tool in enumerate(result['result'], 1):
                        print(f"   {i}. {tool['name']}: {tool['description']}")
                print()
                continue
            
            # Detectar si debe usar modo agéntico
            triggers_agentico = [
                'y luego', 'después', 'y comprime', 'y busca', 
                'completa todo', 'haz todo', 'automático'
            ]
            
            usar_agentico = MODO_AGENTICO or any(t in user_input.lower() for t in triggers_agentico)
            
            if usar_agentico:
                # MODO AGÉNTICO
                respuesta = ejecutar_agentico(user_input)
                print(f"🤖 {respuesta}\n")
                conversacion.append(f"Usuario: {user_input}\nAsistente: {respuesta}")
            else:
                # MODO NORMAL (una sola herramienta)
                conversacion.append(f"Usuario: {user_input}")
                contexto = SYSTEM_PROMPT + "\n\n" + "\n".join(conversacion[-10:])
                
                print("🤖 IA: ", end="", flush=True)
                respuesta = consultar_ia(contexto + "\nAsistente:")
                
                match = re.search(r'\[USAR_HERRAMIENTA:(\w+):([^\]]*)\]', respuesta)
                
                if match:
                    herramienta = match.group(1)
                    parametros = match.group(2)
                    
                    print(f"[{herramienta}]", end=" ", flush=True)
                    
                    # Ejecutar usando el sistema de pasos
                    paso_str = f"{herramienta}:{parametros}"
                    resultado = ejecutar_paso(paso_str, {})
                    
                    if resultado.get('exito'):
                        print("✓")
                        data_str = str(resultado.get('data', ''))[:300]
                        nuevo_prompt = f"{contexto}\nAsistente: {respuesta}\n\n[RESULTADO]: {data_str}\n\nAsistente (responde brevemente):"
                        respuesta_final = consultar_ia(nuevo_prompt)
                        print(respuesta_final)
                        conversacion.append(f"Asistente: {respuesta_final}")
                    else:
                        print("✗")
                        print(f"Error: {resultado.get('error', 'desconocido')}")
                else:
                    print(respuesta)
                    conversacion.append(f"Asistente: {respuesta}")
                
                print()
        
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    main()
EOFCLIENT
  
  chmod +x "$MCP_CLIENT"
  echo "✅ Cliente de chat con modo agéntico generado"
}

# === MENÚ Y RESTO DE FUNCIONES (sin cambios) ===
mostrar_menu() {
  echo ""
  echo "╔════════════════════════════════════════╗"
  echo "║     MCP LOCAL - MENÚ PRINCIPAL         ║"
  echo "║     💪 11 Herramientas + Agéntico      ║"
  echo "╚════════════════════════════════════════╝"
  echo ""
  echo "  1) 💬 Iniciar chat (con modo agéntico)"
  echo "  2) 🔧 Ver herramientas MCP (11)"
  echo "  3) ⚙️  Reconfigurar rutas"
  echo "  4) 🚪 Salir"
  echo ""
  read -rp "Selecciona opción [1-4]: " opcion
  
  case $opcion in
    1)
      source "$PY_ENV/bin/activate"
      python3 "$MCP_CLIENT"
      deactivate
      ;;
    2)
      source "$PY_ENV/bin/activate"
      echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python3 "$MCP_SERVER" 2>/dev/null | grep -E '^\{' | python3 -m json.tool
      deactivate
      mostrar_menu
      ;;
    3)
      rm -f "$CONFIG_FILE"
      configurar_primera_vez
      mostrar_menu
      ;;
    4)
      echo "👋 ¡Adiós!"
      exit 0
      ;;
    *)
      echo "❌ Opción inválida"
      mostrar_menu
      ;;
  esac
}

main() {
  echo ""
  echo "╔════════════════════════════════════════╗"
  echo "║    🤖 MCP LOCAL - INSTALADOR          ║"
  echo "║    11 Herramientas + MODO AGÉNTICO     ║"
  echo "╚════════════════════════════════════════╝"
  
  if [ ! -f "$CONFIG_FILE" ]; then
    configurar_primera_vez
  else
    echo ""
    echo "ℹ️  Configuración existente detectada"
    source "$CONFIG_FILE"
    echo "   IA: $LLAMA_CLI"
    echo "   Modelo: $MODELO_GGUF"
  fi
  
  instalar_dependencias
  generar_servidor
  generar_cliente
  
  echo ""
  echo "✅ INSTALACIÓN COMPLETADA"
  echo ""
  
  mostrar_menu
}

main
