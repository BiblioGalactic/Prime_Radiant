# 📋 Guía de Migración - AIDaemon WikiRAG

**Fecha de Deprecación**: 16 de febrero de 2026
**Versión Activa**: VERSIONE5 (E5)

## 📌 Resumen Ejecutivo

Las versiones **A1, B2, C3 y D4 han sido deprecadas** y ya no reciben soporte. Se recomienda migrar a **VERSIONE5 (E5)** inmediatamente para beneficiarse de:

- ✅ Arquitectura simplificada y mantenible
- ✅ Mejor rendimiento de memoria
- ✅ API mejorada y consistente
- ✅ Mejor documentación y ejemplos
- ✅ Soporte a largo plazo

## 🔍 Versiones Deprecadas

| Versión | Fecha de Deprecación | Razón |
|---------|----------------------|-------|
| **A1** (Alpha 1) | 16-02-2026 | Consolidación arquitectónica |
| **B2** (Beta 2) | 16-02-2026 | Consolidación arquitectónica |
| **C3** (Candidate 3) | 16-02-2026 | Consolidación arquitectónica |
| **D4** (Development 4) | 16-02-2026 | Consolidación arquitectónica |

## 🆕 Versión Activa: E5

### ¿Qué es VERSIONE5?

VERSIONE5 es la evolución final del sistema WikiRAG, consolidando lo mejor de todas las versiones anteriores en una arquitectura simplificada, robusta y mantenible.

### Características de E5

```
✅ RAG Adaptativo mejorado
   - Estrategias broad/focused/balanced/iterative optimizadas
   - Selección automática de mejor estrategia

✅ Sistema multi-modelo potenciado
   - 12+ modelos GGUF con selección inteligente
   - Mejor distribución de carga

✅ Triaje inteligente
   - TINY → SMALL → MEDIUM → LARGE → GIANT
   - Puntuación más precisa

✅ Memoria a largo plazo
   - Episódica: interacciones del usuario
   - Semántica: conocimiento extraído
   - Procedural: planes exitosos
   - Persistencia mejorada en SQLite

✅ Agentes ReAct mejorados
   - Razonamiento: Thought → Action → Observation
   - Mejor integración con RAG

✅ Producción-ready
   - Error handling robusto
   - Logging completo
   - Métricas de rendimiento
```

## 🔄 Pasos de Migración

### Fase 1: Preparación (Día 1)

#### 1.1 Identifica todas las referencias a versiones deprecadas

```bash
# Busca imports en tu codebase
grep -r "from VERSION[ABCD]" . --include="*.py"
grep -r "import VERSION[ABCD]" . --include="*.py"
```

#### 1.2 Documenta dependencias

Crea un archivo temporal que liste:
- Módulos utilizados de versiones antiguas
- Parámetros de configuración específicos
- Integraciones externas

### Fase 2: Actualización (Día 1-2)

#### 2.1 Actualiza imports de Python

```python
# ❌ Antiguo (A1)
from VERSIONA1.core.orchestrator import Orchestrator
from VERSIONA1.agents.react_agent import ReActAgent

# ✅ Nuevo (E5)
from VERSIONE5.core.orchestrator import Orchestrator
from VERSIONE5.agents.react_agent import ReActAgent
```

#### 2.2 Actualiza rutas de configuración

```python
# ❌ Antiguo
config_path = "../VERSIONA1/core/config.py"

# ✅ Nuevo
config_path = "../VERSIONE5/core/config.py"
```

#### 2.3 Revisa y ajusta parámetros de configuración

Algunos parámetros pueden haber cambiado:

```python
# Antes verificar en VERSIONE5/core/config.py
MODELOS_BASE = os.path.expanduser("~/modelo/modelos_grandes")
LLAMA_CLI = os.path.expanduser("~/modelo/llama.cpp/build/bin/llama-cli")
```

### Fase 3: Pruebas (Día 2-3)

#### 3.1 Pruebas unitarias

```bash
cd VERSIONE5
python -m pytest tests/ -v
```

#### 3.2 Pruebas de integración

```bash
cd VERSIONE5/scripts
./start_orchestrator.sh -i

# Ejecuta consultas de prueba:
# > Hola, ¿cuál es tu nombre?
# > ¿Cuál es 2 + 2?
# > status
# > adaptive on
# > salir
```

#### 3.3 Validación de rendimiento

- Mide tiempos de respuesta
- Monitorea uso de memoria
- Verifica integridad de RAG

### Fase 4: Despliegue (Día 3-4)

#### 4.1 Reemplaza completamente

Una vez validado, reemplaza todas las referencias:

```bash
# Busca y reemplaza en bash scripts
sed -i 's/VERSIONA1/VERSIONE5/g' *.sh
sed -i 's/VERSIONB2/VERSIONE5/g' *.sh
sed -i 's/VERSIONC3/VERSIONE5/g' *.sh
sed -i 's/VERSIOND4/VERSIONE5/g' *.sh
```

#### 4.2 Actualiza documentación

Cambia cualquier referencia a versiones antiguas en:
- README.md
- Guías de implementación
- Ejemplos de código
- Scripts de inicio

#### 4.3 Limpieza (opcional)

Una vez completamente migrado y validado:

```bash
# ⚠️ Solo si estás 100% seguro
# rm -rf VERSIONA1 VERSIONB2 VERSIONC3 VERSIOND4
```

## 🔀 Diferencias Clave entre Versiones

### A1 → E5

| Aspecto | A1 | E5 |
|---------|----|----|
| **Orquestador** | Básico | Mejorado con caché |
| **RAG** | Adaptativo manual | Selección automática |
| **Triaje** | Simple | Puntuación sofisticada |
| **Memoria** | Episódica | Episódica + Semántica + Procedural |
| **Documentación** | Básica | Completa |

### B2 → E5

| Aspecto | B2 | E5 |
|---------|----|----|
| **Modelos** | 12 modelos | 12+ modelos optimizados |
| **Query Refiner** | Manual | Automático mejorado |
| **Critic** | Básico | Sistema de evaluación avanzado |
| **Terminal Fix** | Parcial | Completo |

### C3 → E5

| Aspecto | C3 | E5 |
|---------|----|----|
| **Agentes** | ReAct básico | ReAct mejorado |
| **Plan Cache** | Simple | Caché inteligente |
| **Planner** | Lineal | Planificación jerárquica |
| **Integración** | Suelta | Fuerte |

### D4 → E5

| Aspecto | D4 | E5 |
|---------|----|----|
| **Estabilidad** | Beta | Production-ready |
| **Error Handling** | Básico | Robusto |
| **Logging** | Parcial | Completo |
| **Métricas** | Limitadas | Extensas |

## 📁 Estructura de Directorios Comparada

### Antigua (A1-D4)
```
VERSIONA1/
├── core/
│   ├── orchestrator.py
│   ├── daemon_interface.py
│   ├── rag_manager.py
│   ├── model_router.py
│   └── ...
├── agents/
└── scripts/
```

### Nueva (E5)
```
VERSIONE5/
├── core/
│   ├── orchestrator.py (mejorado)
│   ├── daemon_interface.py (mejorado)
│   ├── rag_manager.py (optimizado)
│   ├── model_router.py (inteligente)
│   └── ...
├── agents/
├── scripts/
└── tests/  # NUEVO
```

## 🛠️ Troubleshooting

### Error: "Module not found"

```python
# Verifica que hayas actualizado los imports
from VERSIONE5.core import orchestrator  # ✅ Correcto
from VERSIONA1.core import orchestrator  # ❌ Deprecado
```

### Error: "Config file not found"

```bash
# Verifica la ruta de config
cd VERSIONE5
cat core/config.py | grep -E "MODELOS|LLAMA"
```

### Error: "Memory issues"

E5 tiene mejor manejo de memoria. Si persisten los problemas:

```python
# En VERSIONE5/core/config.py
THROTTLE_LARGE = 50  # Aumenta si es necesario
THROTTLE_GIANT = 200  # Aumenta si es necesario
```

### Rendimiento lento

Verifica que no estés usando versiones antiguas en memoria:

```bash
ps aux | grep VERSIONA1  # Debería estar vacío
ps aux | grep VERSIONE5  # Debería estar activo
```

## 📞 Soporte

### Recursos

- **README.md** - Documentación general
- **VERSIONE5/DEPRECATED.md** - Detalles de deprecación
- **VERSIONE5/scripts/** - Scripts de inicio

### Pasos Siguientes

1. Leer esta guía completamente
2. Identificar todas las referencias
3. Crear rama de desarrollo para cambios
4. Actualizar código
5. Ejecutar pruebas
6. Validar en staging
7. Desplegar a producción

## ✅ Checklist de Migración

- [ ] He leído esta guía completamente
- [ ] He identificado todas las referencias a versiones antiguas
- [ ] He actualizado todos los imports de Python
- [ ] He actualizado todas las rutas de configuración
- [ ] He ejecutado pruebas unitarias
- [ ] He ejecutado pruebas de integración
- [ ] He validado el rendimiento
- [ ] He actualizado la documentación
- [ ] He eliminado versiones antiguas (opcional)
- [ ] He informado al equipo sobre la migración

## 📝 Notas Finales

- La migración típicamente tarda **2-4 días**
- No hay cambios incompatibles críticos
- E5 es completamente compatible con el flujo de trabajo anterior
- Se recomienda hacer pruebas extensas antes de desplegar a producción

**¡Bienvenido a VERSIONE5!** 🎉
