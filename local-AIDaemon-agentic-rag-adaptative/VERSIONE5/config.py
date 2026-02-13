"""
VERSIONE5: Configuración mínima y automática
Detecta rutas, modelo GGUF e índice FAISS automáticamente
"""

import os
from pathlib import Path


def get_base_path():
    """Detecta automáticamente el directorio base del proyecto"""
    return Path(__file__).parent.parent.parent


def get_model_path():
    """Retorna ruta del modelo GGUF"""
    base = get_base_path()
    models_dir = base / "models"

    # Buscar el primer .gguf disponible
    if models_dir.exists():
        gguf_files = list(models_dir.glob("*.gguf"))
        if gguf_files:
            return str(gguf_files[0])

    raise FileNotFoundError(
        f"No se encontró modelo GGUF en {models_dir}. "
        "Por favor, coloca un archivo .gguf en models/"
    )


def get_index_path():
    """Retorna ruta del índice FAISS"""
    base = get_base_path()
    index_dir = base / "data" / "faiss_index"
    index_file = index_dir / "index.faiss"

    if not index_file.exists():
        raise FileNotFoundError(
            f"No se encontró índice en {index_file}. "
            "Por favor, genera el índice primero con: python scripts/build_index.py"
        )

    return str(index_file)


def get_embeddings_model():
    """Modelo de embeddings (sentence-transformers)"""
    return "sentence-transformers/all-MiniLM-L6-v2"


def get_context_window():
    """Número de fragmentos de contexto a recuperar"""
    return 5


def get_max_tokens():
    """Máximo de tokens a generar"""
    return 512


def get_temperature():
    """Temperatura para generación de texto"""
    return 0.7


# Validación de directorios en importación
BASE_PATH = get_base_path()
MODEL_PATH = get_model_path()
INDEX_PATH = get_index_path()
EMBEDDINGS_MODEL = get_embeddings_model()
CONTEXT_WINDOW = get_context_window()
MAX_TOKENS = get_max_tokens()
TEMPERATURE = get_temperature()

print(f"✓ Configuración cargada desde: {BASE_PATH}")
print(f"✓ Modelo GGUF: {os.path.basename(MODEL_PATH)}")
print(f"✓ Índice FAISS: {os.path.basename(INDEX_PATH)}")
