# 🚀 Guía de Inicio Rápido - WikiRAG D4

## En 5 Minutos

### 1. Descargar y Entrar

```bash
cd VERSIOND4
```

### 2. Crear Entorno Virtual

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar

```bash
python main.py
```

### 5. Usar

```
📝 > help
📝 > ¿Qué es machine learning?
📝 > exit
```

---

## Comandos Comunes

### Consulta Única

```bash
python main.py -q "tu pregunta aquí"
```

### Ver Estado

```bash
python main.py --status
```

### Inicializar Directorios

```bash
python main.py --init-data
```

### Ver Configuración

```bash
python main.py --config
```

### Procesamiento por Lotes

```bash
# Crear archivo queries.txt
echo "Consulta 1" > queries.txt
echo "Consulta 2" >> queries.txt

# Procesar
python main.py --batch queries.txt
```

---

## Ejemplos de Uso

### Búsqueda Informativa

```
📝 > ¿Cuál es la capital de Francia?
📤 La capital de Francia es París...
```

### Operación de Filesystem

```
📝 > lista los archivos de /home/usuario
📤 📁 Contenido de `/home/usuario`:
   drwxr-xr-x  Documents/
   drwxr-xr-x  Downloads/
   ...
```

### Búsqueda + Acción

```
📝 > busca info sobre Python y guarda en archivo
📤 📚 Información: Python es...
   ⚡ Acción: Archivo guardado en /tmp/python.txt
```

---

## Solución Rápida de Problemas

### "Módulo no encontrado"

```bash
# Asegurar que estás en el directorio correcto
cd /path/to/VERSIOND4

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### "llama-cpp-python no se instala"

```bash
# Linux/Mac
pip install llama-cpp-python --no-cache-dir --force-reinstall

# Windows (con Visual Studio instalado)
set CMAKE_ARGS=-DLLAMA_OPENBLAS=ON
pip install llama-cpp-python --no-cache-dir
```

### "Las rutas están mal"

```bash
# Inicializar directorios
python main.py --init-data

# Verificar
python main.py --config
```

---

## Próximos Pasos

1. **Leer README.md** - Documentación completa
2. **Agregar Modelos** - Copiar modelos GGUF a `data/models/`
3. **Construir Índices** - Indexar tus documentos para RAG
4. **Personalizar** - Crear handlers y prompts personalizados

---

## Ayuda

```bash
# Ver todas las opciones
python main.py --help

# Ver estado del sistema
python main.py --status

# Ver configuración
python main.py --config
```

---

**¡Listo!** Ahora puedes empezar a usar WikiRAG D4.

Para documentación completa, ver `README.md`.
