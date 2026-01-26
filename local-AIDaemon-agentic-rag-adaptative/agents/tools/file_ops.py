#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    FILE OPS - Operaciones de Archivos
========================================
"""

import os
from typing import List, Dict, Any
from agents.tools.mcp_client import MCPClient


class FileOpsTool:
    """
    Herramienta para operaciones de archivos.
    Wrapper sobre herramientas MCP de archivos.
    """

    def __init__(self, mcp_client: MCPClient = None):
        self.client = mcp_client or MCPClient()

    def read(self, path: str) -> str:
        """Leer archivo"""
        return self.client.leer_archivo(path)

    def write(self, path: str, content: str, append: bool = False) -> Dict[str, Any]:
        """Escribir archivo"""
        modo = "a" if append else "w"
        return self.client.escribir_archivo(path, content, modo)

    def list_dir(self, path: str = ".", show_hidden: bool = False) -> List[Dict]:
        """Listar directorio"""
        result = self.client.listar_directorio(path, show_hidden)
        return result.get("items", [])

    def find(self, pattern: str, directory: str = ".") -> List[str]:
        """Buscar archivos por patrón"""
        result = self.client.buscar_archivos(directory, pattern)
        return [r["ruta"] for r in result.get("resultados", [])]

    def grep(self, pattern: str, directory: str = ".", extension: str = None) -> List[Dict]:
        """Buscar texto en archivos"""
        result = self.client.grep(directory, pattern, extension)
        return result.get("resultados", [])

    def compress(self, source: str, dest: str = None, format: str = "zip") -> Dict[str, Any]:
        """Comprimir archivos"""
        return self.client.comprimir(source, dest, format)

    def decompress(self, source: str, dest: str = None) -> Dict[str, Any]:
        """Descomprimir archivos"""
        return self.client.descomprimir(source, dest)

    def download(self, url: str, dest: str) -> Dict[str, Any]:
        """Descargar archivo desde URL"""
        return self.client.descargar_archivo(url, dest)


# Handlers para agentes
def read_file_handler(path: str) -> str:
    return FileOpsTool().read(path)

def write_file_handler(path: str, content: str) -> str:
    result = FileOpsTool().write(path, content)
    return f"Archivo escrito: {result.get('bytes_escritos', 0)} bytes"

def find_files_handler(pattern: str) -> str:
    files = FileOpsTool().find(pattern)
    return "\n".join(files[:20])

def grep_handler(pattern: str) -> str:
    results = FileOpsTool().grep(pattern)
    return "\n".join([f"{r['archivo']}:{r['linea']}: {r['contenido'][:50]}" for r in results[:10]])


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: file_ops.py [read|write|list|find|grep] [args]")
        sys.exit(1)

    tool = FileOpsTool()
    cmd = sys.argv[1]

    if cmd == "read" and len(sys.argv) > 2:
        content = tool.read(sys.argv[2])
        print(content[:2000])

    elif cmd == "list":
        path = sys.argv[2] if len(sys.argv) > 2 else "."
        items = tool.list_dir(path)
        for item in items[:20]:
            tipo = "📁" if item["tipo"] == "directorio" else "📄"
            print(f"{tipo} {item['nombre']}")

    elif cmd == "find" and len(sys.argv) > 2:
        files = tool.find(sys.argv[2])
        for f in files[:20]:
            print(f)

    elif cmd == "grep" and len(sys.argv) > 2:
        results = tool.grep(sys.argv[2])
        for r in results[:10]:
            print(f"{r['archivo']}:{r['linea']}: {r['contenido'][:60]}")

    else:
        print(f"Comando desconocido o faltan argumentos: {cmd}")
