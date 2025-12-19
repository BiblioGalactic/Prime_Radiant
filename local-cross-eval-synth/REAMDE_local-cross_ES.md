# 🤖 Local-CROS: Cross-Referential Optimization System

## Descripción

**Local-CROS** es un sistema avanzado de evaluación cruzada para modelos LLaMA locales que permite comparar respuestas entre múltiples modelos y generar respuestas optimizadas mediante síntesis inteligente. El sistema implementa un enfoque único de evaluación mutua donde cada modelo evalúa las respuestas de los demás.

## Características Principales

### 🔄 Evaluación Cruzada
- **Evaluación mutua**: Cada modelo evalúa las respuestas de todos los otros
- **Múltiples perspectivas**: Obtén diferentes enfoques para la misma pregunta
- **Puntuación automática**: Sistema de scoring automático para cada respuesta
- **Historial completo**: Registro detallado de todas las interacciones

### 🎯 Síntesis Inteligente
- **Detección automática de tipo de contenido**: Código, listas, poesía, diálogos, etc.
- **Combinación optimizada**: Fusiona las mejores partes de cada respuesta
- **Eliminación de redundancias**: Evita información repetida
- **Recomendaciones contextuales**: Sugerencias específicas según el tipo de contenido

### 📊 Sistema de Archivos Incrementales
- **Numeración automática**: `modelo1.txt`, `modelo2.txt`, etc.
- **Historial acumulativo**: Todas las ejecuciones en un archivo central
- **Timestamps detallados**: Registro temporal de cada operación
- **Trazabilidad completa**: Seguimiento de toda la evolución

## Requisitos del Sistema

- **llama.cpp** compilado y funcional
- **2-4 modelos GGUF** compatibles
- **Bash 4.0+**
- **Herramientas básicas**: `find`, `sed`, `sort`, `jq` (opcional)
- **Sistema operativo**: macOS, Linux

## Instalación

### 1. Descarga
```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/local-cros.git
cd local-cros

# Hacer ejecutable
chmod +x local-cros.sh
```

### 2. Primera Configuración
```bash
# Ejecutar por primera vez (configuración interactiva)
./local-cros.sh
```

El script te pedirá:
- **Ruta de llama-cli**: Ubicación del binario llama.cpp
- **Directorio de trabajo**: Donde guardar resultados
- **Configuración de modelos**: Nombre y ruta de cada modelo (2-4 modelos)

### 3. Archivo de Configuración Generado
```bash
# local-cros.conf
LLAMA_CLI_PATH="/path/to/llama-cli"
WORK_DIR="./results"

MODEL_1_NAME="mistral"
MODEL_1_PATH="/path/to/mistral.gguf"

MODEL_2_NAME="llama"
MODEL_2_PATH="/path/to/llama.gguf"
# ... etc
```

## Uso

### Modo Interactivo
```bash
./local-cros.sh
What do you need?
> Escribe un poema épico sobre programación en Python
```

### Modo Comando Directo
```bash
./local-cros.sh "Explica las diferencias entre React y Vue.js"
```

### Ejemplo de Salida
```
🤖 Starting model comparison for: "Explica programación funcional"

==> Consulting mistral...
[mistral] says: La programación funcional es un paradigma...
---

==> Consulting llama...
[llama] says: En programación funcional, las funciones son...
---

=== CROSS-EVALUATION BETWEEN MODELS ===
=== EVALUATION WITH MISTRAL ===
Evaluating llama: La respuesta es precisa y bien estructurada...

=== COMBINING BEST RESPONSES ===
💻 Combined response generated and saved!
📋 Complete history in: ./results/complete_history.txt
```

## Estructura de Archivos Generados

```
results/
├── responses/
│   ├── mistral1.txt, mistral2.txt, mistral3.txt...
│   ├── llama1.txt, llama2.txt, llama3.txt...
│   ├── codellama1.txt, codellama2.txt...
│   └── response_combined_final.txt
└── complete_history.txt
```

## Funcionalidades Avanzadas

### Detección Automática de Tipo de Contenido

El sistema detecta automáticamente el tipo de contenido y optimiza según el contexto:

- **Código**: `python`, `javascript`, `bash`, `c++`
- **Listas**: Instrucciones paso a paso
- **Poesía**: Haikus, versos, estrofas
- **Diálogos**: Conversaciones, guiones
- **Texto general**: Explicaciones, ensayos

### Sistema de Evaluación

Cada modelo evalúa las respuestas usando criterios específicos:
- **Precisión técnica**
- **Claridad de explicación**
- **Completitud de la respuesta**
- **Relevancia al contexto**

### Recomendaciones Contextuales

```bash
# Para código
💻 Recomendación: Ejecuta 'python3 respuesta_final.py' para probar

# Para listas
📋 Recomendación: Guarda como PDF o comparte como instrucciones

# Para poesía
🎭 Recomendación: Perfecto para análisis literario

# Para diálogos
🎬 Recomendación: Ideal para guiones o role-playing
```

## Configuración Avanzada

### Parámetros de Modelo
```bash
# Editar local-cros.sh para ajustar parámetros
-n 200           # Número máximo de tokens
--temp 0.7       # Temperatura (creatividad)
--top-k 40       # Top-k sampling
--top-p 0.9      # Top-p sampling
--repeat-penalty 1.1  # Penalización por repetición
```

### Personalización de Evaluación
```bash
# Modificar el prompt de evaluación en la función evaluate_response()
local evaluation_prompt="Evalúa esta respuesta usando estos criterios..."
```

## Casos de Uso

### 1. Desarrollo de Software
```bash
./local-cros.sh "Optimiza este algoritmo de ordenamiento burbuja"
# Obtén múltiples enfoques de optimización
```

### 2. Escritura Creativa
```bash
./local-cros.sh "Escribe un diálogo entre Sócrates y Steve Jobs sobre ética"
# Combina diferentes estilos narrativos
```

### 3. Análisis Técnico
```bash
./local-cros.sh "Explica las ventajas y desventajas de microservicios"
# Múltiples perspectivas técnicas combinadas
```

### 4. Resolución de Problemas
```bash
./local-cros.sh "Cómo debuggear un memory leak en C++"
# Diferentes enfoques de debugging
```

## Métricas y Análisis

### Historial Completo
El archivo `complete_history.txt` contiene:
```
#=== EXECUTION 2025-01-21 15:30:15 ===
MODEL: mistral1
QUESTION: ¿Qué es machine learning?
RESPONSE: Machine learning es una rama de la IA...

#=== EVALUATION 2025-01-21 15:30:45 ===
EVALUATOR: llama
EVALUATING: Machine learning es una rama...
RESULT: Respuesta precisa y bien estructurada...

#=== COMBINED RESPONSE 2025-01-21 15:31:00 ===
TYPE: texto_general
COMBINATION: Machine learning es una disciplina...
```

### Análisis de Tendencias
```bash
# Contar respuestas por modelo
grep -c "MODEL:" results/complete_history.txt

# Ver evolución temporal
grep "EXECUTION" results/complete_history.txt | tail -10
```

## Solución de Problemas

### Error: "llama-cli not found"
```bash
# Verificar instalación
which llama-cli

# Actualizar configuración
vim local-cros.conf
```

### Error: "Model execution failed"
```bash
# Verificar modelo
ls -la /path/to/your/model.gguf

# Probar manualmente
/path/to/llama-cli -m /path/to/model.gguf -p "test"
```

### Respuestas de Baja Calidad
```bash
# Ajustar parámetros en el script
--temp 0.5        # Menos creatividad, más precisión
-n 500            # Más tokens para respuestas completas
```

## Extensiones y Plugins

### Añadir Nuevo Modelo
1. Editar `local-cros.conf`
2. Añadir `MODEL_N_NAME` y `MODEL_N_PATH`
3. Reiniciar script

### Integración con APIs Externas
```bash
# Ejemplo: integrar con Claude API para evaluación externa
curl -X POST "https://api.anthropic.com/v1/messages" \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-3-sonnet", "messages": [...]}'
```

## Contribución

1. Fork del repositorio
2. Crear rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -am 'Añadir funcionalidad X'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Pull Request

## Licencia

MIT License

## Autor

**Gustavo Silva da Costa**

## Versión

**1.0.0** - Sistema de evaluación cruzada y síntesis inteligente

---

*Local-CROS: Donde múltiples mentes artificiales colaboran para generar respuestas superiores.*
