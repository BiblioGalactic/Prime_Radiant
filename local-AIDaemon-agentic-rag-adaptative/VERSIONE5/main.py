"""
VERSIONE5: Loop interactivo simple
Flujo: pregunta -> RAG -> LLM -> respuesta
"""

import sys
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

from llm import SimpleLLM
from rag import SimpleRAG


class WikiRAGE5:
    """Sistema RAG mínimo y funcional"""

    def __init__(self):
        print("\n=== WikiRAG VERSIONE5 ===\n")

        print("Cargando componentes...")
        try:
            self.llm = SimpleLLM()
            print("✓ LLM listo")

            self.rag = SimpleRAG()
            print("✓ RAG listo")
        except Exception as e:
            print(f"✗ Error al inicializar: {e}")
            raise

        print("\nSistema listo. Escribe 'exit' para salir.\n")

    def answer(self, question: str) -> tuple:
        """
        Procesa una pregunta:
        1. Recupera contexto con RAG
        2. Genera respuesta con LLM

        Returns:
            (respuesta, contexto_usado)
        """
        print("\n[Buscando contexto...]")
        try:
            context = self.rag.search(question)
        except Exception as e:
            return f"Error en RAG: {e}", ""

        # Construir prompt
        prompt = f"""Basado en el siguiente contexto, responde la pregunta de forma concisa.

CONTEXTO:
{context}

PREGUNTA: {question}

RESPUESTA:"""

        print("[Generando respuesta...]")
        try:
            response = self.llm.query(prompt)
            return response, context
        except Exception as e:
            return f"Error en LLM: {e}", context

    def interactive_loop(self):
        """Loop interactivo simple"""
        while True:
            try:
                question = input("\n> Pregunta: ").strip()

                if not question:
                    continue

                if question.lower() in ["exit", "quit", "salir"]:
                    print("\nHasta luego!")
                    break

                response, context = self.answer(question)

                print(f"\n[RESPUESTA]\n{response}")

                # Mostrar contexto si el usuario lo solicita
                if input("\n¿Ver contexto? (s/n): ").lower() == "s":
                    print(f"\n[CONTEXTO UTILIZADO]\n{context[:500]}...")

            except KeyboardInterrupt:
                print("\n\nInterrumpido por usuario.")
                break
            except Exception as e:
                print(f"Error inesperado: {e}")


def main():
    """Punto de entrada"""
    try:
        wiki_rag = WikiRAGE5()
        wiki_rag.interactive_loop()
    except Exception as e:
        print(f"Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
