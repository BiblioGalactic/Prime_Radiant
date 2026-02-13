#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
MAIN - Punto de Entrada WikiRAG D4
========================================
Sistema inteligente de RAG portátil

Uso:
    python main.py                    # Modo interactivo
    python main.py --query "tu pregunta"
    python main.py --help             # Ver opciones
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Asegurar que core está en el path
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

# Importar core
from core import (
    CONFIG,
    initialize_core,
    SmartRouter,
    get_smart_router,
    IntentClassifier,
    get_intent_classifier,
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("wikirag.main")


class WikiRAGD4:
    """Interfaz principal de WikiRAG D4"""

    def __init__(self, verbose: bool = False):
        """
        Inicializar WikiRAG D4

        Args:
            verbose: Mostrar detalles de ejecución
        """
        self.verbose = verbose
        self.router = None
        self.classifier = None
        self.running = False

        logger.info("🚀 Inicializando WikiRAG D4...")
        self._initialize()

    def _initialize(self):
        """Inicializar componentes"""
        if self.verbose:
            print("\n📚 Inicializando componentes...")
            initialize_core(verbose=True)
            print()

        try:
            self.classifier = get_intent_classifier()
            logger.info("✅ IntentClassifier inicializado")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo inicializar IntentClassifier: {e}")

        try:
            self.router = get_smart_router(verbose=self.verbose)
            logger.info("✅ SmartRouter inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando SmartRouter: {e}")
            raise

        logger.info("✅ WikiRAG D4 iniciado correctamente")

    def query(self, query: str, context: str = "") -> str:
        """
        Procesar una consulta

        Args:
            query: La consulta del usuario
            context: Contexto adicional

        Returns:
            Respuesta del sistema
        """
        if not self.router:
            return "❌ Error: El router no está inicializado"

        try:
            result = self.router.route(query, context)
            return result.response
        except Exception as e:
            logger.error(f"Error procesando consulta: {e}")
            return f"❌ Error: {str(e)}"

    def interactive(self):
        """Modo interactivo"""
        print("\n" + "=" * 70)
        print("  🤖 WikiRAG D4 - Sistema Inteligente de RAG")
        print("=" * 70)
        print("  Escribe 'help' para ver comandos disponibles")
        print("  Escribe 'exit' para salir")
        print("=" * 70 + "\n")

        self.running = True

        try:
            while self.running:
                try:
                    query = input("📝 > ").strip()

                    if not query:
                        continue

                    if query.lower() == "exit":
                        print("👋 ¡Hasta luego!")
                        break

                    response = self.query(query)
                    print(f"\n📤 Respuesta:\n{response}\n")

                except KeyboardInterrupt:
                    print("\n\n👋 Interrupción del usuario. ¡Hasta luego!")
                    break
                except EOFError:
                    print("\n👋 Fin de entrada. ¡Hasta luego!")
                    break

        except Exception as e:
            logger.error(f"Error en modo interactivo: {e}")
            print(f"❌ Error: {e}")

    def batch(self, queries: list) -> list:
        """
        Procesar múltiples consultas

        Args:
            queries: Lista de consultas

        Returns:
            Lista de respuestas
        """
        results = []
        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] {query}")
            response = self.query(query)
            print(f"→ {response[:100]}...")
            results.append(response)
        return results

    def status(self) -> dict:
        """Obtener estado del sistema"""
        return {
            "initialized": self.router is not None,
            "verbose": self.verbose,
            "config_dir": CONFIG.VERSIOND4_DIR if CONFIG else None,
            "router_available": self.router is not None,
            "classifier_available": self.classifier is not None,
        }


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="WikiRAG D4 - Sistema Inteligente de RAG Portátil",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py                          # Modo interactivo
  python main.py --query "qué es Python?"
  python main.py -q "listar archivos" -c "contexto"
  python main.py --batch queries.txt      # Procesar archivo de queries
  python main.py --status                 # Ver estado del sistema
  python main.py --init-data              # Inicializar directorios de datos
        """
    )

    parser.add_argument(
        "-q", "--query",
        type=str,
        help="Procesar una consulta única y salir"
    )

    parser.add_argument(
        "-c", "--context",
        type=str,
        default="",
        help="Contexto adicional para la consulta"
    )

    parser.add_argument(
        "-b", "--batch",
        type=str,
        help="Procesar un archivo con múltiples consultas (una por línea)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Modo verboso"
    )

    parser.add_argument(
        "-s", "--status",
        action="store_true",
        help="Mostrar estado del sistema y salir"
    )

    parser.add_argument(
        "--init-data",
        action="store_true",
        help="Inicializar directorios de datos necesarios"
    )

    parser.add_argument(
        "--config",
        action="store_true",
        help="Mostrar configuración y salir"
    )

    args = parser.parse_args()

    # Mostrar configuración si se solicita
    if args.config:
        print("\n⚙️ CONFIGURACIÓN DE WIKIRAG D4")
        print("=" * 70)
        if CONFIG:
            config_dict = CONFIG.to_dict()
            for key, value in config_dict.items():
                if isinstance(value, dict):
                    print(f"\n{key}:")
                    for k, v in value.items():
                        print(f"  {k}: {v}")
                else:
                    print(f"{key}: {value}")
        else:
            print("❌ Configuración no disponible")
        print("=" * 70)
        return

    # Inicializar datos si se solicita
    if args.init_data:
        print("\n📁 Inicializando directorios de datos...")
        if CONFIG:
            CONFIG._ensure_directories()
            print("✅ Directorios inicializados correctamente")
            print(f"📂 Base: {CONFIG.VERSIOND4_DIR}")
        else:
            print("❌ No se pudo acceder a la configuración")
        return

    # Crear instancia de WikiRAG D4
    try:
        wikirag = WikiRAGD4(verbose=args.verbose)
    except Exception as e:
        print(f"❌ Error inicializando WikiRAG D4: {e}")
        sys.exit(1)

    # Mostrar estado si se solicita
    if args.status:
        print("\n📊 ESTADO DEL SISTEMA")
        print("=" * 70)
        status = wikirag.status()
        for key, value in status.items():
            icon = "✅" if isinstance(value, bool) and value else "❌" if isinstance(value, bool) else "📍"
            print(f"  {icon} {key}: {value}")
        print("=" * 70)
        return

    # Procesar archivo batch
    if args.batch:
        if not os.path.isfile(args.batch):
            print(f"❌ Archivo no encontrado: {args.batch}")
            sys.exit(1)

        print(f"\n📂 Procesando archivo: {args.batch}")
        try:
            with open(args.batch, 'r', encoding='utf-8') as f:
                queries = [line.strip() for line in f if line.strip()]

            if not queries:
                print("❌ El archivo está vacío")
                return

            print(f"📝 {len(queries)} consultas encontradas\n")
            wikirag.batch(queries)
            print(f"\n✅ Procesamiento completado")

        except Exception as e:
            print(f"❌ Error procesando batch: {e}")
            sys.exit(1)
        return

    # Procesar consulta única
    if args.query:
        if args.verbose:
            print()
        response = wikirag.query(args.query, args.context)
        print(f"\n📤 Respuesta:\n{response}\n")
        return

    # Modo interactivo por defecto
    wikirag.interactive()


if __name__ == "__main__":
    main()
