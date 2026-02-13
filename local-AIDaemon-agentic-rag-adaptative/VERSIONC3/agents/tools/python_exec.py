#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    PYTHON EXEC - Ejecución de Python
========================================
Ejecuta código Python de forma segura.
"""

import os
import sys
import tempfile
import subprocess
from typing import Dict, Any


class PythonExecTool:
    """
    Herramienta para ejecutar código Python de forma segura.
    """

    # Módulos bloqueados por seguridad
    BLOCKED_MODULES = [
        'subprocess', 'os.system', 'eval', 'exec',
        'shutil.rmtree', '__import__', 'importlib'
    ]

    # Imports permitidos
    ALLOWED_IMPORTS = [
        'math', 'json', 'datetime', 're', 'collections',
        'itertools', 'functools', 'statistics', 'random',
        'string', 'textwrap', 'csv', 'io'
    ]

    def __init__(self, timeout: int = 30, max_output: int = 10000):
        self.timeout = timeout
        self.max_output = max_output

    def is_safe(self, code: str) -> bool:
        """Verificar si el código es seguro"""
        code_lower = code.lower()

        # Verificar módulos bloqueados
        for blocked in self.BLOCKED_MODULES:
            if blocked in code_lower:
                return False

        # Verificar patrones peligrosos
        dangerous_patterns = [
            'open(',  # Acceso a archivos
            'file(',
            '__',     # Dunder methods
            'system(',
            'popen(',
            'spawn',
        ]

        for pattern in dangerous_patterns:
            if pattern in code_lower:
                return False

        return True

    def execute(self, code: str) -> Dict[str, Any]:
        """
        Ejecutar código Python.

        Args:
            code: Código Python a ejecutar

        Returns:
            Dict con stdout, stderr, return_code
        """
        # Verificar seguridad
        if not self.is_safe(code):
            return {
                "success": False,
                "stdout": "",
                "stderr": "Código bloqueado por razones de seguridad",
                "return_code": -1
            }

        try:
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False
            ) as f:
                # Wrapper para capturar output
                wrapped_code = f"""
import sys
from io import StringIO

# Capturar stdout
_stdout = StringIO()
_old_stdout = sys.stdout
sys.stdout = _stdout

try:
{self._indent_code(code)}
except Exception as e:
    print(f"Error: {{type(e).__name__}}: {{e}}")

sys.stdout = _old_stdout
print(_stdout.getvalue())
"""
                f.write(wrapped_code)
                temp_file = f.name

            # Ejecutar
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # Limpiar
            os.unlink(temp_file)

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:self.max_output],
                "stderr": result.stderr[:1000],
                "return_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Timeout: ejecución excedió {self.timeout}s",
                "return_code": -2
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -3
            }

    def _indent_code(self, code: str, spaces: int = 4) -> str:
        """Indentar código"""
        indent = " " * spaces
        lines = code.split('\n')
        return '\n'.join(indent + line for line in lines)

    def evaluate(self, expression: str) -> str:
        """
        Evaluar una expresión simple.

        Args:
            expression: Expresión matemática o simple

        Returns:
            Resultado como string
        """
        # Solo permitir expresiones matemáticas simples
        allowed_chars = set('0123456789+-*/().%** ')
        allowed_funcs = ['abs', 'round', 'min', 'max', 'sum', 'len', 'int', 'float']

        expr_clean = expression.strip()

        # Verificar caracteres
        if not all(c in allowed_chars or c.isalpha() for c in expr_clean):
            return "Expresión no permitida"

        # Verificar funciones
        import re
        funcs_used = re.findall(r'([a-z]+)\s*\(', expr_clean)
        for func in funcs_used:
            if func not in allowed_funcs:
                return f"Función no permitida: {func}"

        try:
            # Evaluar en contexto restringido
            result = eval(expr_clean, {"__builtins__": {}}, {
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "len": len, "int": int, "float": float
            })
            return str(result)
        except Exception as e:
            return f"Error: {e}"


# Handler para agentes
def python_exec_handler(code: str) -> str:
    """Handler para usar en agentes"""
    tool = PythonExecTool()
    result = tool.execute(code)
    if result["success"]:
        return result["stdout"]
    return f"Error: {result['stderr']}"


def python_eval_handler(expression: str) -> str:
    """Handler para evaluación simple"""
    return PythonExecTool().evaluate(expression)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python_exec.py [exec|eval] <código>")
        sys.exit(1)

    tool = PythonExecTool()
    cmd = sys.argv[1]

    if cmd == "exec":
        code = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "print('Hello')"
        print(f"🐍 Ejecutando: {code[:50]}...")
        result = tool.execute(code)
        print(f"\n📤 Output:")
        print(result["stdout"])
        if result["stderr"]:
            print(f"⚠️ Stderr: {result['stderr']}")

    elif cmd == "eval":
        expr = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "2 + 2"
        print(f"🔢 Evaluando: {expr}")
        result = tool.evaluate(expr)
        print(f"= {result}")

    else:
        print(f"Comando desconocido: {cmd}")
