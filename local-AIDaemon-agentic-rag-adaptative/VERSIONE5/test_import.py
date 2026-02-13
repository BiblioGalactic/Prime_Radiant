"""
Script de verificación: Prueba que todos los módulos se importan correctamente
Útil para detectar problemas antes de ejecutar main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("\n=== Verificación de Módulos WikiRAG E5 ===\n")

# Test 1: Config
print("[1/4] Importando config...")
try:
    from config import (
        BASE_PATH,
        MODEL_PATH,
        INDEX_PATH,
        EMBEDDINGS_MODEL,
        CONTEXT_WINDOW,
        MAX_TOKENS,
        TEMPERATURE,
    )
    print("  ✓ config.py cargado")
    print(f"    - Base path: {BASE_PATH}")
    print(f"    - Modelo: {Path(MODEL_PATH).name}")
    print(f"    - Índice: {Path(INDEX_PATH).name}")
    print(f"    - Embeddings: {EMBEDDINGS_MODEL}")
    print(f"    - Context window: {CONTEXT_WINDOW}")
except Exception as e:
    print(f"  ✗ Error en config: {e}")
    sys.exit(1)

# Test 2: LLM
print("\n[2/4] Importando llm...")
try:
    from llm import SimpleLLM
    print("  ✓ llm.py cargado")
    print("  - Verificando llama-cli...")
    try:
        llm = SimpleLLM()
        print("    ✓ llama-cli disponible")
    except RuntimeError as e:
        print(f"    ⚠ Advertencia: {e}")
except Exception as e:
    print(f"  ✗ Error en llm: {e}")
    sys.exit(1)

# Test 3: RAG
print("\n[3/4] Importando rag...")
try:
    from rag import SimpleRAG
    print("  ✓ rag.py cargado")
    print("  - Cargando FAISS e índice...")
    try:
        rag = SimpleRAG()
        print(f"    ✓ Índice FAISS cargado ({rag.index.ntotal} vectores)")
    except FileNotFoundError as e:
        print(f"    ⚠ Advertencia: {e}")
except Exception as e:
    print(f"  ✗ Error en rag: {e}")
    sys.exit(1)

# Test 4: Main
print("\n[4/4] Importando main...")
try:
    from main import WikiRAGE5
    print("  ✓ main.py cargado")
except Exception as e:
    print(f"  ✗ Error en main: {e}")
    sys.exit(1)

print("\n=== Verificación Completada ===\n")
print("✓ Todos los módulos importan correctamente")
print("\nPróximo paso: python main.py\n")
