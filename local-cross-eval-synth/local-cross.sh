#!/bin/bash
# ==================================================================================
# LLAMA MODEL COMPARATOR - Cross-Model Evaluation System
# ==================================================================================
# Compare responses across multiple LLaMA models with cross-evaluation and response
# combination. Supports automatic setup and model configuration.
# 
# Author: Gustavo Silva da Costa
# License: MIT
# Version: 1.0.0
# ==================================================================================

# Colores ANSI
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Variables globales de configuración
CONFIG_FILE=""
LLAMA_CLI_PATH=""
MODEL_1_PATH=""
MODEL_2_PATH=""
MODEL_3_PATH=""
MODEL_4_PATH=""
WORK_DIR=""
RESPONSES_DIR=""
HISTORY_FILE=""

# Nombres de modelos (configurables)
MODEL_1_NAME="model1"
MODEL_2_NAME="model2" 
MODEL_3_NAME="model3"
MODEL_4_NAME="model4"

# Colores por modelo
color_model1=$GREEN
color_model2=$BLUE
color_model3=$YELLOW
color_model4=$MAGENTA

# ==================================================================================
# FUNCIONES DE CONFIGURACIÓN E INSTALACIÓN
# ==================================================================================

show_banner() {
    echo -e "${CYAN}==================================================================================${NC}"
    echo -e "${WHITE} LLAMA MODEL COMPARATOR v1.0.0${NC}"
    echo -e "${CYAN} Cross-Model Evaluation and Response Combination System${NC}"
    echo -e "${CYAN}==================================================================================${NC}"
    echo ""
}

check_dependencies() {
    local missing_deps=()
    
    # Verificar comandos básicos
    for cmd in find sed sort tail head mktemp cat date; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${RED}❌ Missing dependencies: ${missing_deps[*]}${NC}"
        echo -e "${YELLOW}Please install missing commands and try again.${NC}"
        exit 1
    fi
}

create_config() {
    local config_file="$1"
    
    echo -e "${YELLOW}🔧 Creating configuration file...${NC}"
    
    # Solicitar rutas de forma interactiva
    echo ""
    echo -e "${WHITE}Please provide the following paths:${NC}"
    
    # llama-cli path
    echo -e "${GREEN}1. Path to llama-cli binary:${NC}"
    echo -e "${CYAN}   Example: /usr/local/bin/llama-cli${NC}"
    echo -e "${CYAN}   Example: ./llama.cpp/build/bin/llama-cli${NC}"
    read -p "llama-cli path: " LLAMA_CLI_PATH
    
    # Validar que existe llama-cli
    if [[ ! -f "$LLAMA_CLI_PATH" && ! $(command -v "$LLAMA_CLI_PATH") ]]; then
        echo -e "${RED}❌ llama-cli not found at: $LLAMA_CLI_PATH${NC}"
        echo -e "${YELLOW}Please check the path and try again.${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}2. Work directory (where results will be stored):${NC}"
    echo -e "${CYAN}   Example: ./results${NC}"
    echo -e "${CYAN}   Example: /tmp/llama-comparator${NC}"
    read -p "Work directory: " WORK_DIR
    
    # Crear directorio si no existe
    mkdir -p "$WORK_DIR"
    
    echo ""
    echo -e "${GREEN}3. Model configuration:${NC}"
    
    # Modelo 1
    echo -e "${GREEN}Model 1 name: ${NC}"
    read -p "Name (default: model1): " MODEL_1_NAME
    MODEL_1_NAME=${MODEL_1_NAME:-model1}
    
    echo -e "${GREEN}Model 1 path: ${NC}"
    read -p "Path to .gguf file: " MODEL_1_PATH
    
    # Modelo 2
    echo -e "${GREEN}Model 2 name: ${NC}"
    read -p "Name (default: model2): " MODEL_2_NAME
    MODEL_2_NAME=${MODEL_2_NAME:-model2}
    
    echo -e "${GREEN}Model 2 path: ${NC}"
    read -p "Path to .gguf file: " MODEL_2_PATH
    
    # Modelo 3 (opcional)
    echo -e "${GREEN}Model 3 name (optional, press Enter to skip): ${NC}"
    read -p "Name: " MODEL_3_NAME
    if [[ -n "$MODEL_3_NAME" ]]; then
        echo -e "${GREEN}Model 3 path: ${NC}"
        read -p "Path to .gguf file: " MODEL_3_PATH
    fi
    
    # Modelo 4 (opcional)
    echo -e "${GREEN}Model 4 name (optional, press Enter to skip): ${NC}"
    read -p "Name: " MODEL_4_NAME
    if [[ -n "$MODEL_4_NAME" ]]; then
        echo -e "${GREEN}Model 4 path: ${NC}"
        read -p "Path to .gguf file: " MODEL_4_PATH
    fi
    
    # Crear archivo de configuración
    cat > "$config_file" << EOF
# LLAMA Model Comparator Configuration
# Generated on $(date)

# Paths
LLAMA_CLI_PATH="$LLAMA_CLI_PATH"
WORK_DIR="$WORK_DIR"

# Models
MODEL_1_NAME="$MODEL_1_NAME"
MODEL_1_PATH="$MODEL_1_PATH"

MODEL_2_NAME="$MODEL_2_NAME"
MODEL_2_PATH="$MODEL_2_PATH"

MODEL_3_NAME="$MODEL_3_NAME"
MODEL_3_PATH="$MODEL_3_PATH"

MODEL_4_NAME="$MODEL_4_NAME" 
MODEL_4_PATH="$MODEL_4_PATH"
EOF
    
    echo -e "${GREEN}✅ Configuration saved to: $config_file${NC}"
}

load_config() {
    local config_file="$1"
    
    if [[ ! -f "$config_file" ]]; then
        echo -e "${RED}❌ Configuration file not found: $config_file${NC}"
        return 1
    fi
    
    # Cargar configuración
    source "$config_file"
    
    # Configurar rutas derivadas
    RESPONSES_DIR="$WORK_DIR/responses"
    HISTORY_FILE="$WORK_DIR/complete_history.txt"
    
    # Crear directorios necesarios
    mkdir -p "$RESPONSES_DIR"
    
    echo -e "${GREEN}✅ Configuration loaded from: $config_file${NC}"
    return 0
}

setup_environment() {
    local script_dir="$(cd "$(dirname "$0")" && pwd)"
    CONFIG_FILE="$script_dir/model-comparator.conf"
    
    show_banner
    check_dependencies
    
    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo -e "${YELLOW}⚙️  First time setup required.${NC}"
        create_config "$CONFIG_FILE"
    fi
    
    if ! load_config "$CONFIG_FILE"; then
        echo -e "${RED}❌ Failed to load configuration${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}🚀 Environment ready!${NC}"
    echo ""
}

# ==================================================================================
# FUNCIONES DEL CORE DEL COMPARADOR  
# ==================================================================================

get_next_number() {
    local model_name=$1
    local last_num=$(find "$RESPONSES_DIR" -name "${model_name}[0-9]*.txt" 2>/dev/null | sed "s/.*${model_name}\([0-9]*\)\.txt/\1/" | sort -n | tail -1)
    if [[ -z "$last_num" ]]; then
        echo 1
    else
        echo $((last_num + 1))
    fi
}

execute_model() {
    local llama_cli=$1
    local model_path=$2
    local question=$3
    
    # Usar archivo temporal para prompt seguro
    local temp_file=$(mktemp)
    echo "$question" > "$temp_file"
    
    # Ejecutar modelo con parámetros optimizados
    local response
    response=$($llama_cli -m "$model_path" --prompt "$(cat "$temp_file")" -n 200 --temp 0.7 --top-k 40 --top-p 0.9 --repeat-penalty 1.1 2>/dev/null || echo "Error: Model execution failed")
    
    # Limpiar archivo temporal
    rm -f "$temp_file"
    
    echo "$response"
}

get_model_color() {
    case $1 in
        "$MODEL_1_NAME") echo $color_model1 ;;
        "$MODEL_2_NAME") echo $color_model2 ;;
        "$MODEL_3_NAME") echo $color_model3 ;;
        "$MODEL_4_NAME") echo $color_model4 ;;
        *) echo $WHITE ;;
    esac
}

query_model() {
    local model_name=$1
    local model_path=$2
    local question=$3
    
    if [[ -z "$model_path" || -z "$model_name" ]]; then
        return 0  # Skip if model not configured
    fi
    
    local color=$(get_model_color "$model_name")
    local number=$(get_next_number "$model_name")
    local output_file="${RESPONSES_DIR}/${model_name}${number}.txt"
    
    echo -e "${color}==> Consulting $model_name...${NC}"
    
    # Ejecutar modelo
    local response=$(execute_model "$LLAMA_CLI_PATH" "$model_path" "$question")
    local clean_response=$(echo "$response" | sed "s/^.*$question//g" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    
    echo -e "${color}[$model_name] says: $clean_response${NC}"
    echo -e "${color}---${NC}"
    
    # Guardar respuesta numerada
    echo "$clean_response" > "$output_file"
    
    # Añadir al historial completo
    {
        echo "#=== EXECUTION $(date '+%Y-%m-%d %H:%M:%S') ==="
        echo "MODEL: ${model_name}${number}"
        echo "QUESTION: $question"
        echo "RESPONSE: $clean_response"
        echo ""
    } >> "$HISTORY_FILE"
}

evaluate_response() {
    local evaluator_model_path=$1
    local response=$2
    local original_question=$3
    local evaluator_name=$4
    
    if [[ -z "$evaluator_model_path" ]]; then
        return 0
    fi
    
    # Crear prompt de evaluación seguro
    local evaluation_prompt="Evaluate this response: $response. Does it adequately answer the question '$original_question'? Respond concisely in Spanish."
    
    # Usar archivo temporal
    local temp_file=$(mktemp)
    echo "$evaluation_prompt" > "$temp_file"
    
    # Ejecutar evaluación
    local evaluation
    evaluation=$($LLAMA_CLI_PATH -m "$evaluator_model_path" --prompt "$(cat "$temp_file")" -n 50 --temp 0.3 2>/dev/null || echo "Evaluation failed")
    
    # Limpiar
    rm -f "$temp_file"
    
    # Mostrar evaluación
    echo "$evaluation"
    
    # Añadir evaluación al historial
    {
        echo "#=== EVALUATION $(date '+%Y-%m-%d %H:%M:%S') ==="
        echo "EVALUATOR: $evaluator_name" 
        echo "EVALUATING: $response"
        echo "RESULT: $evaluation"
        echo ""
    } >> "$HISTORY_FILE"
}

# ==================================================================================
# FUNCIÓN PRINCIPAL
# ==================================================================================

run_comparison() {
    local question="$1"
    
    if [[ -z "$question" ]]; then
        echo -e "${WHITE}What do you need?${NC}"
        read question
    fi
    
    echo -e "${CYAN}🤖 Starting model comparison for: \"$question\"${NC}"
    echo ""
    
    # Array de modelos configurados
    declare -a models_names=()
    declare -a models_paths=()
    
    [[ -n "$MODEL_1_PATH" ]] && models_names+=("$MODEL_1_NAME") && models_paths+=("$MODEL_1_PATH")
    [[ -n "$MODEL_2_PATH" ]] && models_names+=("$MODEL_2_NAME") && models_paths+=("$MODEL_2_PATH")
    [[ -n "$MODEL_3_PATH" ]] && models_names+=("$MODEL_3_NAME") && models_paths+=("$MODEL_3_PATH")
    [[ -n "$MODEL_4_PATH" ]] && models_names+=("$MODEL_4_NAME") && models_paths+=("$MODEL_4_PATH")
    
    # Consultar cada modelo
    for i in "${!models_names[@]}"; do
        query_model "${models_names[$i]}" "${models_paths[$i]}" "$question"
    done
    
    # Evaluación cruzada
    echo -e "${WHITE}=== CROSS-EVALUATION BETWEEN MODELS ===${NC}"
    
    for eval_idx in "${!models_names[@]}"; do
        local evaluator_name="${models_names[$eval_idx]}"
        local evaluator_path="${models_paths[$eval_idx]}"
        local color=$(get_model_color "$evaluator_name")
        
        echo -e "${color}=== EVALUATION WITH ${evaluator_name^^} ===${NC}"
        
        for target_idx in "${!models_names[@]}"; do
            if [[ $target_idx -ne $eval_idx ]]; then
                local target_name="${models_names[$target_idx]}"
                local target_number=$(get_next_number "$target_name")
                target_number=$((target_number - 1))
                
                if [[ -f "${RESPONSES_DIR}/${target_name}${target_number}.txt" ]]; then
                    local response=$(cat "${RESPONSES_DIR}/${target_name}${target_number}.txt")
                    local target_color=$(get_model_color "$target_name")
                    
                    echo -e "${target_color}Evaluating $target_name:${NC}"
                    evaluate_response "$evaluator_path" "$response" "$question" "$evaluator_name"
                    echo -e "${target_color}---${NC}"
                fi
            fi
        done
    done
    
    echo -e "${GREEN}✅ All responses saved in: $RESPONSES_DIR${NC}"
    echo -e "${GREEN}📋 Complete history in: $HISTORY_FILE${NC}"
}

# ==================================================================================
# PUNTO DE ENTRADA PRINCIPAL
# ==================================================================================

main() {
    # Setup del entorno
    setup_environment
    
    # Verificar argumentos de línea de comandos
    if [[ $# -gt 0 ]]; then
        run_comparison "$*"
    else
        run_comparison
    fi
}

# Verificar si el script se ejecuta directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
