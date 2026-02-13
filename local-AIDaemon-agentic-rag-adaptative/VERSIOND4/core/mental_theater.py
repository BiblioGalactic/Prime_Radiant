#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
🎭 MENTAL THEATER - Teatro Mental Deliberativo
========================================
Sistema de deliberación multi-perspectiva para mejorar respuestas.

Basado en:
- Chain-of-Thought (Wei et al., 2022)
- Self-Consistency (Wang et al., 2023)
- Debate Agents (Du et al., 2023)
- Constitutional AI (Anthropic)

Personajes:
- Luz 💡: Lógica, análisis riguroso, evidencia
- Sombra 🌑: Emociones, implicaciones humanas, ética
- Luna 🌙: Intuición, creatividad, conexiones no obvias
- (Opcional) Agua 💧: Adaptabilidad, alternativas
- (Opcional) Fuego 🔥: Acción, decisión, practicidad
- (Opcional) Viento 💨: Cambio, perspectiva externa

Uso:
    theater = MentalTheater(llm_cli)
    improved = theater.deliberate(query, initial_response, context)
"""

import os
import sys
import re
import subprocess
import tempfile
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import logging

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MentalTheater")


class Character(Enum):
    """Personajes del Teatro Mental"""
    LUZ = "Luz"       # 💡 Lógica
    SOMBRA = "Sombra" # 🌑 Emoción
    LUNA = "Luna"     # 🌙 Intuición
    AGUA = "Agua"     # 💧 Adaptabilidad (opcional)
    FUEGO = "Fuego"   # 🔥 Acción (opcional)
    VIENTO = "Viento" # 💨 Cambio (opcional)


@dataclass
class CharacterProfile:
    """Perfil de un personaje del teatro"""
    name: str
    emoji: str
    role: str
    style: str
    focus: str


# Perfiles predefinidos
PROFILES = {
    Character.LUZ: CharacterProfile(
        name="Luz",
        emoji="💡",
        role="Analista lógico",
        style="Preciso, basado en evidencia, estructurado",
        focus="¿Es lógicamente correcto? ¿Hay evidencia? ¿Falta algo?"
    ),
    Character.SOMBRA: CharacterProfile(
        name="Sombra",
        emoji="🌑",
        role="Consejero emocional",
        style="Empático, reflexivo, considera implicaciones humanas",
        focus="¿Cómo afecta a las personas? ¿Es ético? ¿Hay preocupaciones?"
    ),
    Character.LUNA: CharacterProfile(
        name="Luna",
        emoji="🌙",
        role="Visionario intuitivo",
        style="Creativo, usa metáforas, ve conexiones ocultas",
        focus="¿Qué se nos escapa? ¿Hay otra forma de verlo? ¿Qué intuyes?"
    ),
    Character.AGUA: CharacterProfile(
        name="Agua",
        emoji="💧",
        role="Adaptador flexible",
        style="Fluido, busca alternativas, se adapta",
        focus="¿Hay otras opciones? ¿Cómo podemos adaptar esto?"
    ),
    Character.FUEGO: CharacterProfile(
        name="Fuego",
        emoji="🔥",
        role="Ejecutor decisivo",
        style="Directo, orientado a la acción, práctico",
        focus="¿Qué hacemos ahora? ¿Cuál es el siguiente paso?"
    ),
    Character.VIENTO: CharacterProfile(
        name="Viento",
        emoji="💨",
        role="Observador externo",
        style="Desapegado, ve el panorama completo, cuestiona supuestos",
        focus="¿Desde afuera, qué se ve? ¿Qué asumimos sin cuestionar?"
    ),
}


@dataclass
class DeliberationRound:
    """Una ronda de deliberación"""
    character: Character
    content: str
    timestamp: float


@dataclass
class DeliberationResult:
    """Resultado de la deliberación"""
    original_response: str
    improved_response: str
    consensus: str
    rounds: List[DeliberationRound]
    total_time: float
    confidence_boost: float


class MentalTheater:
    """
    Teatro Mental para deliberación multi-perspectiva.

    Usa el modelo LLM en modo interactivo con reverse-prompt
    para simular un debate entre personajes que mejora la respuesta.
    """

    # Prompt base para el teatro
    THEATER_PROMPT = """Eres un simulador de Teatro Mental con múltiples perspectivas.

## PERSONAJES ACTIVOS:
{characters}

## REGLAS ESTRICTAS:
1. Orden cíclico: {order} -> SÍNTESIS
2. Formato: Cada línea empieza con "Nombre:" (ej: "Luz:", "Sombra:")
3. Límite: Máximo 50 palabras por intervención
4. Tras la última perspectiva, genera "SÍNTESIS:" con la respuesta mejorada
5. Mantén el estilo de cada personaje

## CONTEXTO:
Consulta original: {query}

Respuesta inicial a evaluar:
{response}

## TAREA:
Los personajes deben deliberar sobre la respuesta inicial:
- ¿Es correcta y completa?
- ¿Qué falta o qué mejorar?
- ¿Hay otra perspectiva importante?

Al final, genera una SÍNTESIS con la respuesta mejorada.

## INICIO DE DELIBERACIÓN:
Luz:"""

    # Prompt simplificado para modelos pequeños
    SIMPLE_PROMPT = """La respuesta actual NO es correcta. Genera una NUEVA respuesta correcta.

PREGUNTA DEL USUARIO: {query}

RESPUESTA INCORRECTA (NO USAR): {response}

INSTRUCCIONES:
- La respuesta anterior es incorrecta o genérica, IGNÓRALA completamente
- Genera una respuesta NUEVA y CORRECTA directamente a la pregunta del usuario
- Sé conciso pero completo
- NO te presentes ni digas qué puedes hacer

RESPUESTA CORRECTA:"""

    def __init__(
        self,
        llm_cli=None,
        llama_cli_path: str = None,
        model_path: str = None,
        characters: List[Character] = None,
        max_rounds: int = 1,
        use_reverse_prompt: bool = True,
        verbose: bool = True
    ):
        """
        Inicializar Teatro Mental.

        Args:
            llm_cli: Interfaz DaemonCLI existente (preferido)
            llama_cli_path: Ruta a llama-cli (si no hay llm_cli)
            model_path: Ruta al modelo GGUF
            characters: Lista de personajes a usar (default: Luz, Sombra, Luna)
            max_rounds: Número de rondas de deliberación
            use_reverse_prompt: Si usar modo interactivo con reverse-prompt
            verbose: Si mostrar progreso
        """
        self.llm_cli = llm_cli
        self.llama_cli = llama_cli_path or os.path.expanduser(
            "~/modelo/llama.cpp/build/bin/llama-cli"
        )
        self.model_path = model_path
        self.characters = characters or [Character.LUZ, Character.SOMBRA, Character.LUNA]
        self.max_rounds = max_rounds
        self.use_reverse_prompt = use_reverse_prompt
        self.verbose = verbose

        # Cargar config si existe
        self._load_config()

    def _load_config(self):
        """Cargar configuración del sistema"""
        try:
            from core.config import config
            if not self.model_path:
                # Usar modelo del daemon o alternativo
                if hasattr(config, 'MODEL_THEATER'):
                    self.model_path = config.MODEL_THEATER.path
                elif hasattr(config, 'MODEL_DAEMON'):
                    self.model_path = config.MODEL_DAEMON.path
        except ImportError:
            pass

        # Fallback a modelo por defecto
        if not self.model_path:
            self.model_path = os.path.expanduser(
                "~/modelo/modelos_grandes/M5/Qwen3-8B-Q4_K_M.gguf"
            )

    def _format_characters(self) -> Tuple[str, str]:
        """Formatear lista de personajes para el prompt"""
        char_lines = []
        order_parts = []

        for char in self.characters:
            profile = PROFILES[char]
            char_lines.append(
                f"- {profile.emoji} {profile.name}: {profile.role}. "
                f"Estilo: {profile.style}. "
                f"Enfoque: {profile.focus}"
            )
            order_parts.append(profile.name)

        return "\n".join(char_lines), " -> ".join(order_parts)

    def deliberate(
        self,
        query: str,
        initial_response: str,
        context: str = "",
        use_simple: bool = False
    ) -> DeliberationResult:
        """
        Ejecutar deliberación del Teatro Mental.

        Args:
            query: Consulta original del usuario
            initial_response: Respuesta inicial a mejorar
            context: Contexto adicional (opcional)
            use_simple: Usar prompt simplificado (más rápido)

        Returns:
            DeliberationResult con respuesta mejorada
        """
        start_time = time.time()
        rounds = []

        if self.verbose:
            print("\n" + "="*60)
            print("   🎭 TEATRO MENTAL - Deliberación")
            print("="*60)
            chars = " → ".join([PROFILES[c].emoji + PROFILES[c].name for c in self.characters])
            print(f"   Personajes: {chars}")
            print("="*60 + "\n")

        # Elegir método según configuración
        if use_simple or not self.use_reverse_prompt:
            result = self._deliberate_simple(query, initial_response, context)
        elif self.llm_cli:
            result = self._deliberate_with_cli(query, initial_response, context)
        else:
            result = self._deliberate_with_subprocess(query, initial_response, context)

        total_time = time.time() - start_time

        # Extraer síntesis
        improved, consensus = self._extract_synthesis(result)

        if self.verbose:
            print("\n" + "-"*60)
            print("   📋 SÍNTESIS")
            print("-"*60)
            print(f"   {improved[:200]}..." if len(improved) > 200 else f"   {improved}")
            print(f"\n   ⏱️ Tiempo: {total_time:.1f}s")
            print("="*60 + "\n")

        return DeliberationResult(
            original_response=initial_response,
            improved_response=improved if improved else initial_response,
            consensus=consensus,
            rounds=rounds,
            total_time=total_time,
            confidence_boost=0.15 if improved else 0.0
        )

    def _deliberate_simple(self, query: str, response: str, context: str) -> str:
        """Deliberación simplificada usando prompt directo"""
        # Construir prompt con contexto prominente
        if context:
            prompt = f"""INFORMACIÓN RELEVANTE:
{context[:800]}

{self.SIMPLE_PROMPT.format(query=query, response=response[:200])}"""
        else:
            prompt = self.SIMPLE_PROMPT.format(query=query, response=response[:200])

        if self.llm_cli:
            result = self.llm_cli.query(prompt, max_tokens=400, timeout=45)
            # Limpiar resultado
            return self._clean_simple_output(result)
        else:
            result = self._run_llama_cli(prompt, max_tokens=400)
            return self._clean_simple_output(result)

    def _clean_simple_output(self, output: str) -> str:
        """Limpiar output del modo simple"""
        if not output:
            return ""
        # Eliminar tags de thinking
        output = re.sub(r'<think>.*?</think>', '', output, flags=re.DOTALL | re.IGNORECASE)
        # Eliminar prefijo assistant/user
        output = re.sub(r'^(assistant|user)\s*', '', output, flags=re.IGNORECASE)
        # Eliminar marcadores de respuesta
        output = re.sub(r'^RESPUESTA CORRECTA[:\s]*', '', output, flags=re.IGNORECASE)
        output = re.sub(r'^SÍNTESIS[:\s]*', '', output, flags=re.IGNORECASE)
        # Limpiar artifacts
        output = re.sub(r'<\|.*?\|>', '', output)
        output = re.sub(r'\[end of text\]', '', output, flags=re.IGNORECASE)
        return output.strip()

    def _deliberate_with_cli(self, query: str, response: str, context: str) -> str:
        """Deliberación usando DaemonCLI existente"""
        characters_text, order = self._format_characters()

        prompt = self.THEATER_PROMPT.format(
            characters=characters_text,
            order=order,
            query=query,
            response=response
        )

        if context:
            prompt = prompt.replace(
                "## CONTEXTO:",
                f"## CONTEXTO ADICIONAL:\n{context[:500]}\n\n## CONTEXTO:"
            )

        # Usar DaemonCLI
        result = self.llm_cli.query(
            prompt,
            max_tokens=800,
            temperature=0.7,
            timeout=90
        )

        return result

    def _deliberate_with_subprocess(self, query: str, response: str, context: str) -> str:
        """Deliberación usando subprocess con reverse-prompt"""
        if not os.path.exists(self.llama_cli) or not os.path.exists(self.model_path):
            logger.error("llama-cli o modelo no encontrado")
            return response

        characters_text, order = self._format_characters()

        prompt = self.THEATER_PROMPT.format(
            characters=characters_text,
            order=order,
            query=query,
            response=response
        )

        # Escribir prompt a archivo temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(prompt)
            prompt_file = f.name

        try:
            # Construir comando con reverse-prompt para ciclo
            cmd = [
                self.llama_cli,
                "-m", self.model_path,
                "--file", prompt_file,
                "--ctx-size", "4096",
                "--n-predict", "800",
                "--temp", "0.7",
                "--top-p", "0.9",
                "--repeat-penalty", "1.1",
                "--threads", "4",
            ]

            if self.verbose:
                logger.info(f"🎭 Ejecutando teatro mental...")

            # Ejecutar
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                stdin=subprocess.DEVNULL
            )

            Path(prompt_file).unlink(missing_ok=True)

            if result.returncode == 0:
                return self._clean_output(result.stdout)
            else:
                logger.error(f"Error en teatro mental: {result.stderr[:200]}")
                return response

        except subprocess.TimeoutExpired:
            logger.error("Timeout en teatro mental")
            Path(prompt_file).unlink(missing_ok=True)
            return response
        except Exception as e:
            logger.error(f"Error: {e}")
            Path(prompt_file).unlink(missing_ok=True)
            return response

    def _run_llama_cli(self, prompt: str, max_tokens: int = 500) -> str:
        """Ejecutar llama-cli directamente"""
        if not os.path.exists(self.llama_cli) or not os.path.exists(self.model_path):
            return ""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(prompt)
            prompt_file = f.name

        try:
            cmd = [
                self.llama_cli,
                "-m", self.model_path,
                "--file", prompt_file,
                "--n-predict", str(max_tokens),
                "--ctx-size", "4096",
                "--temp", "0.7",
                "--threads", "4",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=90,
                stdin=subprocess.DEVNULL
            )

            Path(prompt_file).unlink(missing_ok=True)
            return self._clean_output(result.stdout) if result.returncode == 0 else ""

        except Exception as e:
            Path(prompt_file).unlink(missing_ok=True)
            return ""

    def _clean_output(self, output: str) -> str:
        """Limpiar output del LLM"""
        # Eliminar logs de llama.cpp
        lines = []
        for line in output.split('\n'):
            line_lower = line.lower()
            if any(p in line_lower for p in [
                'ggml_', 'llama_', 'llm_load', 'metal', 'gpu',
                'sampling', 'sampler', 'generate:', 'system_info',
                'loaded', 'ctx_size', 'n_predict', 'warning'
            ]):
                continue
            lines.append(line)

        # Eliminar tags de thinking
        result = '\n'.join(lines)
        result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL | re.IGNORECASE)

        return result.strip()

    def _extract_synthesis(self, deliberation: str) -> Tuple[str, str]:
        """Extraer síntesis/consenso de la deliberación"""
        # Primero limpiar tags de thinking y artifacts
        clean = re.sub(r'<think>.*?</think>', '', deliberation, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r'<\|.*?\|>', '', clean)
        clean = re.sub(r'\[end of text\]', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'^.*?assistant\s*', '', clean, flags=re.DOTALL)  # Remover prefijo assistant
        clean = clean.strip()

        # Buscar marcador de síntesis explícita
        synthesis_patterns = [
            r'SÍNTESIS[:\s]*\(respuesta mejorada\)[:\s]*(.+?)(?:$)',
            r'SÍNTESIS[:\s]*(.+?)(?:$|\n\n\n)',
            r'Síntesis[:\s]*(.+?)(?:$|\n\n\n)',
            r'RESPUESTA MEJORADA[:\s]*(.+?)(?:$|\n\n\n)',
            r'CONSENSO[:\s]*(.+?)(?:$|\n\n\n)',
            r'(?:En conclusión|Por lo tanto|Finalmente)[,:\s]+(.+?)(?:$|\n\n)',
        ]

        for pattern in synthesis_patterns:
            match = re.search(pattern, clean, re.DOTALL | re.IGNORECASE)
            if match:
                synthesis = match.group(1).strip()
                if len(synthesis) > 30:  # Solo si es sustancial
                    return synthesis, "Consenso alcanzado"

        # Buscar análisis de Luz (el más lógico/útil)
        luz_patterns = [
            r'Luz\s*\(lógica\)[:\s]*(.+?)(?=Sombra|Luna|$)',
            r'\*\*Luz\s*\(lógica\)\*\*[:\s]*(.+?)(?=Sombra|\*\*Sombra|Luna|\*\*Luna|$)',
            r'Luz[:\s]+(.+?)(?=Sombra|Luna|$)',
        ]

        for pattern in luz_patterns:
            match = re.search(pattern, clean, re.DOTALL | re.IGNORECASE)
            if match:
                luz_content = match.group(1).strip()
                # Limpiar y truncar si es muy largo
                luz_content = re.sub(r'\*\*', '', luz_content)
                if len(luz_content) > 50:
                    return luz_content[:500], "Análisis de Luz"

        # Fallback: extraer líneas significativas (no patrones de prompt)
        lines = []
        for line in clean.split('\n'):
            line = line.strip()
            # Ignorar líneas de prompt/instrucciones
            if any(skip in line.lower() for skip in [
                'evalúa', 'mejora', 'perspectiva', 'consulta:',
                'respuesta a evaluar', 'síntesis', '[analiza', '[considera', '[busca'
            ]):
                continue
            if len(line) > 30 and not line.startswith('[') and not line.startswith('##'):
                lines.append(line)

        if lines:
            # Combinar las mejores líneas
            best_content = ' '.join(lines[:3])
            return best_content[:500], "Contenido extraído"

        return "", "Sin síntesis"

    def quick_improve(self, query: str, response: str) -> str:
        """
        Mejora rápida de respuesta (sin deliberación completa).

        Útil para mejorar respuestas PARCIAL rápidamente.
        """
        prompt = f"""Mejora esta respuesta haciéndola más completa y precisa:

PREGUNTA: {query}

RESPUESTA ACTUAL: {response}

RESPUESTA MEJORADA (más completa y precisa):"""

        if self.llm_cli:
            improved = self.llm_cli.query(prompt, max_tokens=300, timeout=30)
            return improved if improved and not improved.startswith("Error") else response
        else:
            return response


# === INTEGRACIÓN CON ORCHESTRATOR ===

def should_use_theater(verdict: str, confidence: float) -> bool:
    """Determinar si usar el Teatro Mental para mejorar respuesta"""
    # Usar teatro si:
    # - Respuesta es PARCIAL o FALLA
    # - Confianza es baja (<0.5)
    # - Es una pregunta compleja (podría detectarse por longitud o keywords)

    if verdict == "FALLA":
        return True
    if verdict == "PARCIAL" and confidence < 0.6:
        return True
    return False


def create_theater(llm_cli=None, mode: str = "balanced") -> MentalTheater:
    """
    Factory para crear Teatro Mental con diferentes configuraciones.

    Args:
        llm_cli: Interfaz LLM
        mode: "minimal" (2 chars), "balanced" (3 chars), "full" (6 chars)
    """
    if mode == "minimal":
        characters = [Character.LUZ, Character.LUNA]
    elif mode == "full":
        characters = list(Character)
    else:  # balanced
        characters = [Character.LUZ, Character.SOMBRA, Character.LUNA]

    return MentalTheater(
        llm_cli=llm_cli,
        characters=characters,
        verbose=True
    )


# === SINGLETON ===
_theater_instance = None

def get_theater(llm_cli=None) -> MentalTheater:
    """Obtener instancia singleton del Teatro Mental"""
    global _theater_instance
    if _theater_instance is None:
        _theater_instance = create_theater(llm_cli, mode="balanced")
    return _theater_instance


# === TEST ===
if __name__ == "__main__":
    print("🎭 Test de Teatro Mental")
    print("="*50)

    # Crear teatro
    theater = MentalTheater(verbose=True)

    # Test con respuesta a mejorar
    query = "¿Cómo puedo mejorar mi productividad?"
    initial_response = "Hacer listas de tareas."

    print(f"\n📝 Consulta: {query}")
    print(f"📤 Respuesta inicial: {initial_response}")

    # Deliberar
    result = theater.deliberate(query, initial_response, use_simple=True)

    print(f"\n✨ Respuesta mejorada:")
    print(result.improved_response)
    print(f"\n📊 Consenso: {result.consensus}")
    print(f"⏱️ Tiempo: {result.total_time:.1f}s")
    print(f"📈 Boost confianza: +{result.confidence_boost:.0%}")
