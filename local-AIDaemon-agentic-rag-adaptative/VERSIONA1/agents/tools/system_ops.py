#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    SYSTEM OPS - Operaciones del Sistema
========================================
"""

from typing import Dict, Any, List
from agents.tools.mcp_client import MCPClient


class SystemOpsTool:
    """
    Herramienta para operaciones del sistema.
    """

    # Comandos bloqueados
    BLOCKED_COMMANDS = [
        'rm', 'dd', 'mkfs', 'format', 'sudo', 'su',
        'chmod 777', 'chown', '>', '>>', '|', '&',
        'wget', 'curl', 'nc', 'netcat'
    ]

    def __init__(self, mcp_client: MCPClient = None):
        self.client = mcp_client or MCPClient()

    def is_safe_command(self, command: str) -> bool:
        """Verificar si el comando es seguro"""
        cmd_lower = command.lower()
        for blocked in self.BLOCKED_COMMANDS:
            if blocked in cmd_lower:
                return False
        return True

    def run_command(self, command: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Ejecutar comando del sistema.

        Args:
            command: Comando a ejecutar
            timeout: Timeout en segundos

        Returns:
            Dict con stdout, stderr, return_code
        """
        if not self.is_safe_command(command):
            return {
                "stdout": "",
                "stderr": f"Comando bloqueado por seguridad: {command}",
                "returncode": -1
            }

        return self.client.ejecutar_comando(command, timeout)

    def get_system_info(self) -> Dict[str, Any]:
        """Obtener información del sistema"""
        return self.client.consultar_memoria()

    def git_status(self, repo_path: str = ".") -> str:
        """Git status"""
        return self.client.git_status(repo_path)

    def git_log(self, repo_path: str = ".") -> str:
        """Git log"""
        return self.client.git_log(repo_path)

    def git_diff(self, repo_path: str = ".") -> str:
        """Git diff"""
        return self.client.git_diff(repo_path)

    def which(self, program: str) -> str:
        """Buscar ubicación de programa"""
        result = self.run_command(f"which {program}")
        return result.get("stdout", "").strip()

    def env(self, var: str = None) -> str:
        """Obtener variable de entorno"""
        if var:
            result = self.run_command(f"echo ${var}")
        else:
            result = self.run_command("env")
        return result.get("stdout", "").strip()

    def date(self) -> str:
        """Obtener fecha actual"""
        result = self.run_command("date")
        return result.get("stdout", "").strip()

    def uptime(self) -> str:
        """Obtener uptime del sistema"""
        result = self.run_command("uptime")
        return result.get("stdout", "").strip()


# Handlers para agentes
def run_command_handler(command: str) -> str:
    """Handler para comandos"""
    result = SystemOpsTool().run_command(command)
    if result.get("returncode", 0) == 0:
        return result.get("stdout", "")
    return f"Error: {result.get('stderr', 'Unknown error')}"

def system_info_handler() -> str:
    """Handler para info del sistema"""
    info = SystemOpsTool().get_system_info()
    lines = [f"{k}: {v}" for k, v in info.items()]
    return "\n".join(lines)

def git_status_handler(path: str = ".") -> str:
    """Handler para git status"""
    return SystemOpsTool().git_status(path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: system_ops.py [info|run|git] [args]")
        sys.exit(1)

    tool = SystemOpsTool()
    cmd = sys.argv[1]

    if cmd == "info":
        print("💻 Información del sistema:")
        for k, v in tool.get_system_info().items():
            print(f"  {k}: {v}")

    elif cmd == "run" and len(sys.argv) > 2:
        command = " ".join(sys.argv[2:])
        print(f"▶️ Ejecutando: {command}")
        result = tool.run_command(command)
        print(result.get("stdout", ""))
        if result.get("stderr"):
            print(f"⚠️ {result['stderr']}")

    elif cmd == "git":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else "status"
        if subcmd == "status":
            print(tool.git_status())
        elif subcmd == "log":
            print(tool.git_log())
        elif subcmd == "diff":
            print(tool.git_diff())

    else:
        print(f"Comando desconocido: {cmd}")
