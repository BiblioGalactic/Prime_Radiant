#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    WEB SEARCH - Herramienta de Búsqueda Web
========================================
"""

import re
import urllib.parse
from typing import List, Dict, Any
from agents.tools.mcp_client import MCPClient


class WebSearchTool:
    """
    Herramienta de búsqueda web usando la API de DuckDuckGo.
    """

    def __init__(self, mcp_client: MCPClient = None):
        self.client = mcp_client or MCPClient()

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Buscar en la web.

        Args:
            query: Términos de búsqueda
            max_results: Máximo resultados

        Returns:
            Lista de resultados {title, url, snippet}
        """
        # Usar DuckDuckGo HTML API (no requiere key)
        encoded_query = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        result = self.client.consultar_api(url, metodo="GET", timeout=15)

        if "error" in result:
            return [{"error": result["error"]}]

        # Parsear HTML básico
        content = result.get("content", "")
        if isinstance(content, dict):
            content = str(content)

        results = []

        # Extraer resultados (parsing muy básico)
        link_pattern = r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        snippet_pattern = r'<a[^>]+class="result__snippet"[^>]*>([^<]+)</a>'

        links = re.findall(link_pattern, content)
        snippets = re.findall(snippet_pattern, content)

        for i, (url, title) in enumerate(links[:max_results]):
            snippet = snippets[i] if i < len(snippets) else ""
            results.append({
                "title": title.strip(),
                "url": url,
                "snippet": snippet.strip()
            })

        return results or [{"error": "No se encontraron resultados"}]

    def get_page_content(self, url: str, max_chars: int = 5000) -> str:
        """
        Obtener contenido de una página web.

        Args:
            url: URL de la página
            max_chars: Máximo caracteres a retornar

        Returns:
            Contenido de texto de la página
        """
        result = self.client.consultar_api(url, metodo="GET", timeout=15)

        if "error" in result:
            return f"Error: {result['error']}"

        content = result.get("content", "")
        if isinstance(content, dict):
            content = str(content)

        # Limpiar HTML básico
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
        content = re.sub(r'<[^>]+>', ' ', content)
        content = re.sub(r'\s+', ' ', content)

        return content[:max_chars].strip()


# Handler para agentes
def web_search_handler(query: str) -> str:
    """Handler para usar en agentes"""
    tool = WebSearchTool()
    results = tool.search(query)
    return str(results)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: web_search.py <query>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    tool = WebSearchTool()

    print(f"🔍 Buscando: {query}")
    results = tool.search(query)

    for i, r in enumerate(results, 1):
        if "error" in r:
            print(f"❌ {r['error']}")
        else:
            print(f"\n{i}. {r['title']}")
            print(f"   {r['url']}")
            print(f"   {r['snippet'][:100]}...")
