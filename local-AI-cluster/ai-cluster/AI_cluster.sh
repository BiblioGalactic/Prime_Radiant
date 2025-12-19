#!/bin/bash
# ===================================================================
# 🤖 AI CLUSTER - Sistema Distribuido de IA para Redes Locales
# ===================================================================
# Autor: BiblioGalactic (Gustavo Silva da Costa)
# Licencia: MIT
# GitHub: https://github.com/BiblioGalactic
#
# Descripción:
#   Sistema distribuido que permite ejecutar queries de IA en paralelo
#   usando múltiples máquinas en una red local (intranet).
#   
#   Perfecto para empresas que quieren aprovechar PCs ociosos
#   sin depender de cloud (privacidad, GDPR, costos).
#
# Requisitos:
#   - llama.cpp instalado localmente
#   - Modelo GGUF (Mistral, Llama, etc.)
#   - SSH entre máquinas (el script ayuda a configurarlo)
# ===================================================================

set -euo pipefail
IFS=$'\n\t'

# ===================================================================
# CONFIGURACIÓN GLOBAL
# ===================================================================

SCRIPT_VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/.ai_cluster_config"
RESULTS_DIR="${SCRIPT_DIR}/results_cluster"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ===================================================================
# FUNCIONES DE LOGGING
# ===================================================================

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $*"
}

success() {
    echo -e "${GREEN}[✓]${NC} $*"
}

error() {
    echo -e "${RED}[✗]${NC} $*" >&2
}

warning() {
    echo -e "${YELLOW}[!]${NC} $*"
}

info() {
    echo -e "${CYAN}[i]${NC} $*"
}

banner() {
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🤖 AI CLUSTER - Sistema Distribuido de IA 🤖          ║
║                                                           ║
║   Procesa queries en paralelo usando tu red local        ║
║   Sin cloud • Privado • Escalable • Open Source          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
    echo ""
    info "Versión: ${SCRIPT_VERSION}"
    info "By: BiblioGalactic (Gustavo Silva da Costa)"
    echo ""
}

# ===================================================================
# FUNCIONES DE CONFIGURACIÓN
# ===================================================================

cargar_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        source "$CONFIG_FILE"
        return 0
    else
        return 1
    fi
}

guardar_config() {
    cat > "$CONFIG_FILE" << EOF
# Configuración del Cluster de IA
# Generado automáticamente - No editar manualmente

# Máquina Local
LOCAL_LLAMA="$LOCAL_LLAMA"
LOCAL_MODEL="$LOCAL_MODEL"

# Máquinas Remotas (separadas por comas)
REMOTE_IPS="$REMOTE_IPS"
REMOTE_USER="$REMOTE_USER"
REMOTE_LLAMA="$REMOTE_LLAMA"
REMOTE_MODEL="$REMOTE_MODEL"

# Configuración
REMOTE_DELAY="${REMOTE_DELAY:-10}"
EOF
    success "Configuración guardada en: $CONFIG_FILE"
}

# ===================================================================
# WIZARD DE CONFIGURACIÓN
# ===================================================================

wizard_bienvenida() {
    clear
    banner
    log "🚀 Bienvenido al asistente de configuración"
    echo ""
    info "Este wizard te guiará paso a paso para configurar tu cluster de IA."
    info "Puedes cancelar en cualquier momento con Ctrl+C"
    echo ""
    read -p "Presiona Enter para continuar..."
}

wizard_local() {
    clear
    log "📍 PASO 1/4: Configuración Local (esta máquina)"
    echo ""
    
    # Detecta llama-cli
    local llama_default="$HOME/modelo/llama.cpp/build/bin/llama-cli"
    if [[ -f "$llama_default" ]]; then
        success "llama-cli detectado: $llama_default"
        LOCAL_LLAMA="$llama_default"
    else
        warning "No se encontró llama-cli en la ruta por defecto"
        read -p "Ruta de llama-cli: " LOCAL_LLAMA
    fi
    
    # Verifica que exista
    if [[ ! -f "$LOCAL_LLAMA" ]]; then
        error "llama-cli no encontrado en: $LOCAL_LLAMA"
        exit 1
    fi
    
    echo ""
    
    # Detecta modelo
    local model_default="$HOME/modelo/modelos_grandes/M6/mistral-7b-instruct-v0.1.Q6_K.gguf"
    if [[ -f "$model_default" ]]; then
        success "Modelo detectado: $model_default"
        LOCAL_MODEL="$model_default"
    else
        warning "No se encontró modelo en la ruta por defecto"
        read -p "Ruta del modelo GGUF: " LOCAL_MODEL
    fi
    
    # Verifica que exista
    if [[ ! -f "$LOCAL_MODEL" ]]; then
        error "Modelo no encontrado en: $LOCAL_MODEL"
        exit 1
    fi
    
    success "Configuración local completada"
    echo ""
    read -p "Presiona Enter para continuar..."
}

wizard_remoto() {
    clear
    log "🌐 PASO 2/4: Máquinas Remotas"
    echo ""
    
    info "Introduce las IPs de las máquinas remotas que quieres usar"
    info "Ejemplo: 192.168.1.82,192.168.1.83"
    info "(Puedes añadir una o varias, separadas por comas)"
    echo ""
    
    read -p "IPs remotas: " REMOTE_IPS
    
    echo ""
    read -p "Usuario SSH (mismo en todas): " REMOTE_USER
    
    echo ""
    info "Rutas en las máquinas remotas (deben ser iguales en todas)"
    echo ""
    
    read -p "Ruta de llama-cli remoto [$LOCAL_LLAMA]: " input
    REMOTE_LLAMA="${input:-$LOCAL_LLAMA}"
    
    read -p "Ruta del modelo remoto [$LOCAL_MODEL]: " input
    REMOTE_MODEL="${input:-$LOCAL_MODEL}"
    
    read -p "Delay entre conexiones SSH (segundos) [10]: " input
    REMOTE_DELAY="${input:-10}"
    
    success "Configuración remota completada"
    echo ""
    read -p "Presiona Enter para continuar..."
}

wizard_ssh() {
    clear
    log "🔐 PASO 3/4: Configuración SSH"
    echo ""
    
    info "Vamos a configurar SSH sin contraseña para cada máquina remota"
    info "Esto permite que el cluster funcione automáticamente"
    echo ""
    
    # Verifica si ya tiene clave SSH
    if [[ ! -f "$HOME/.ssh/id_rsa" ]] && [[ ! -f "$HOME/.ssh/id_ed25519" ]]; then
        warning "No tienes clave SSH generada"
        read -p "¿Generar clave SSH ahora? (s/n): " respuesta
        
        if [[ "$respuesta" == "s" ]]; then
            log "Generando clave SSH..."
            ssh-keygen -t ed25519 -f "$HOME/.ssh/id_ed25519" -N ""
            success "Clave SSH generada"
        else
            error "No se puede continuar sin clave SSH"
            exit 1
        fi
    else
        success "Clave SSH encontrada"
    fi
    
    echo ""
    
    # Configura ssh-copy-id para cada IP
    IFS=',' read -ra IPS <<< "$REMOTE_IPS"
    for ip in "${IPS[@]}"; do
        log "Configurando acceso SSH a: $ip"
        
        # Prueba conexión
        if ssh -o BatchMode=yes -o ConnectTimeout=5 "${REMOTE_USER}@${ip}" "echo ok" &>/dev/null; then
            success "Ya tienes acceso sin contraseña a $ip"
        else
            warning "Necesitas configurar acceso a $ip"
            echo ""
            info "Se te pedirá la contraseña de ${REMOTE_USER}@${ip}"
            
            if ssh-copy-id "${REMOTE_USER}@${ip}" 2>/dev/null; then
                success "Acceso configurado para $ip"
            else
                error "No se pudo configurar acceso a $ip"
                error "Verifica que SSH esté activo en la máquina remota"
            fi
        fi
        echo ""
    done
    
    success "Configuración SSH completada"
    echo ""
    read -p "Presiona Enter para continuar..."
}

wizard_verificacion() {
    clear
    log "✅ PASO 4/4: Verificación"
    echo ""
    
    log "Verificando configuración completa..."
    echo ""
    
    # Verifica local
    info "Local:"
    echo "  llama-cli: $LOCAL_LLAMA"
    echo "  Modelo: $LOCAL_MODEL"
    echo ""
    
    # Verifica remotos
    info "Remotas:"
    IFS=',' read -ra IPS <<< "$REMOTE_IPS"
    local remotos_ok=0
    
    for ip in "${IPS[@]}"; do
        echo -n "  $ip ... "
        
        # Prueba SSH
        if ! ssh -o BatchMode=yes -o ConnectTimeout=5 \
             "${REMOTE_USER}@${ip}" "echo ok" &>/dev/null; then
            echo -e "${RED}SSH FALLO${NC}"
            continue
        fi
        
        # Verifica llama-cli
        if ! ssh -T -o BatchMode=yes "${REMOTE_USER}@${ip}" \
             "test -f $REMOTE_LLAMA" 2>/dev/null; then
            echo -e "${RED}llama-cli NO ENCONTRADO${NC}"
            continue
        fi
        
        # Verifica modelo
        if ! ssh -T -o BatchMode=yes "${REMOTE_USER}@${ip}" \
             "test -f $REMOTE_MODEL" 2>/dev/null; then
            echo -e "${RED}Modelo NO ENCONTRADO${NC}"
            continue
        fi
        
        echo -e "${GREEN}OK${NC}"
        ((remotos_ok++))
    done
    
    echo ""
    
    if (( remotos_ok > 0 )); then
        success "Cluster configurado: 1 local + $remotos_ok remota(s)"
        echo ""
        
        guardar_config
        
        echo ""
        success "🎉 ¡Configuración completada!"
        echo ""
        info "Ahora puedes ejecutar queries con:"
        echo "  $0 run queries.txt"
        echo ""
    else
        error "No se pudo configurar ninguna máquina remota"
        exit 1
    fi
}

# ===================================================================
# FUNCIONES DE PROCESAMIENTO
# ===================================================================

procesar_local() {
    local num="$1"
    local query="$2"
    local out="${RESULTS_DIR}/result_${num}_local.txt"
    
    log "💻 [Local] Query #${num}: ${query:0:50}..."
    
    "$LOCAL_LLAMA" -m "$LOCAL_MODEL" -p "$query" \
        --temp 0.7 --ctx-size 2048 -n 256 --threads 4 \
        > "$out" 2>&1
    
    success "[Local] Query #${num} completada"
}

procesar_remoto() {
    local num="$1"
    local query="$2"
    local ip="$3"
    local out="${RESULTS_DIR}/result_${num}_${ip//./}.txt"
    
    log "🌐 [${ip}] Query #${num}: ${query:0:50}..."
    log "⏸️  Delay de ${REMOTE_DELAY}s..."
    sleep "$REMOTE_DELAY"
    
    local escaped=$(echo "$query" | sed "s/'/'\\\\''/g")
    
    if ssh -T -q -o BatchMode=yes -o ConnectTimeout=10 \
        "${REMOTE_USER}@${ip}" \
        "$REMOTE_LLAMA -m $REMOTE_MODEL -p '$escaped' --temp 0.7 --ctx-size 2048 -n 256 --threads 4" \
        > "$out" 2>&1; then
        success "[${ip}] Query #${num} completada"
    else
        error "[${ip}] Query #${num} falló"
    fi
}

ejecutar_cluster() {
    local archivo="$1"
    
    banner
    
    if [[ ! -f "$archivo" ]]; then
        error "Archivo no encontrado: $archivo"
        exit 1
    fi
    
    mkdir -p "$RESULTS_DIR"
    
    # Lee queries
    local queries=()
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" ]] && continue
        queries+=("$line")
    done < "$archivo"
    
    local total=${#queries[@]}
    log "🎯 Total de queries: $total"
    
    # Calcula distribución
    IFS=',' read -ra IPS <<< "$REMOTE_IPS"
    local num_remotos=${#IPS[@]}
    local num_maquinas=$((1 + num_remotos))
    
    info "Máquinas disponibles: $num_maquinas (1 local + $num_remotos remotas)"
    echo ""
    
    # Distribuye queries
    local i=0
    while (( i < total )); do
        local query="${queries[$i]}"
        local num=$((i + 1))
        local machine_idx=$((i % num_maquinas))
        
        if (( machine_idx == 0 )); then
            # Local
            procesar_local "$num" "$query" &
        else
            # Remota
            local remote_ip="${IPS[$((machine_idx - 1))]}"
            procesar_remoto "$num" "$query" "$remote_ip" &
        fi
        
        ((i++))
        
        # Espera cada N procesos
        if (( i % num_maquinas == 0 )) || (( i == total )); then
            log "⏳ Esperando lote..."
            wait
            echo ""
        fi
    done
    
    # Estadísticas
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    success "✨ COMPLETADO"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    local count=$(ls "$RESULTS_DIR"/result_*.txt 2>/dev/null | wc -l | tr -d ' ')
    info "Total procesadas: $count queries"
    info "Resultados en: $RESULTS_DIR/"
}

# ===================================================================
# MENÚ PRINCIPAL
# ===================================================================

mostrar_ayuda() {
    banner
    cat << EOF
${CYAN}USO:${NC}
  $0 [COMANDO] [OPCIONES]

${CYAN}COMANDOS:${NC}
  ${GREEN}setup${NC}        Configurar cluster (primera vez)
  ${GREEN}run${NC} <archivo> Ejecutar queries en el cluster
  ${GREEN}config${NC}       Mostrar configuración actual
  ${GREEN}test${NC}         Probar conectividad
  ${GREEN}help${NC}         Mostrar esta ayuda

${CYAN}EJEMPLOS:${NC}
  $0 setup              # Configurar por primera vez
  $0 run queries.txt    # Procesar queries
  $0 test               # Verificar conexiones

${CYAN}ARCHIVOS:${NC}
  .ai_cluster_config    Configuración guardada
  results_cluster/      Resultados de queries
  queries.txt           Archivo con queries (una por línea)

${CYAN}MÁS INFO:${NC}
  GitHub: https://github.com/BiblioGalactic
  Documentación completa en el README

EOF
}

comando_setup() {
    wizard_bienvenida
    wizard_local
    wizard_remoto
    wizard_ssh
    wizard_verificacion
}

comando_config() {
    banner
    if cargar_config; then
        info "Configuración actual:"
        echo ""
        cat "$CONFIG_FILE"
    else
        warning "No hay configuración"
        info "Ejecuta: $0 setup"
    fi
}

comando_test() {
    banner
    if ! cargar_config; then
        error "No hay configuración. Ejecuta: $0 setup"
        exit 1
    fi
    
    log "Probando conectividad..."
    echo ""
    
    IFS=',' read -ra IPS <<< "$REMOTE_IPS"
    for ip in "${IPS[@]}"; do
        echo -n "  $ip ... "
        if ssh -o BatchMode=yes -o ConnectTimeout=5 \
           "${REMOTE_USER}@${ip}" "echo ok" &>/dev/null; then
            echo -e "${GREEN}OK${NC}"
        else
            echo -e "${RED}FALLO${NC}"
        fi
    done
}

# ===================================================================
# MAIN
# ===================================================================

main() {
    local comando="${1:-help}"
    
    case "$comando" in
        setup)
            comando_setup
            ;;
        run)
            if ! cargar_config; then
                error "No hay configuración. Ejecuta: $0 setup"
                exit 1
            fi
            
            local archivo="${2:-queries.txt}"
            ejecutar_cluster "$archivo"
            ;;
        config)
            comando_config
            ;;
        test)
            comando_test
            ;;
        help|-h|--help)
            mostrar_ayuda
            ;;
        *)
            error "Comando desconocido: $comando"
            echo ""
            mostrar_ayuda
            exit 1
            ;;
    esac
}

main "$@"
