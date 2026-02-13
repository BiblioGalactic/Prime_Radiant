#!/usr/bin/env python3
# ============================================================
# 🎭 WIKIRAG MENTAL THEATER v1.0
# ============================================================
# Sistema de deliberación interna con múltiples perfiles.
# Simula un "consejo interno" que debate antes de actuar.
#
# Perfiles:
#   - Luz: Lógica, verificación, claridad
#   - Sombra: Crítica, riesgos, vulnerabilidades
#   - Luna: Contexto, patrones, memoria
#   - Agua: Adaptación, conexión, soluciones fluidas
#   - Fuego: Acción, transformación, decisión
#   - Viento: Exploración, alternativas, comunicación
#
# Uso: Para tareas CRÍTICAS o COMPLEJAS donde queremos
#      que el modelo "piense antes de actuar".
# ============================================================

import os
import sys
import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime

BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logger = logging.getLogger(__name__)


class ProfileType(Enum):
    """Tipos de perfiles del Teatro Mental"""
    LUZ = "luz"           # Lógica, verificación
    SOMBRA = "sombra"     # Crítica, riesgos
    LUNA = "luna"         # Contexto, intuición
    AGUA = "agua"         # Adaptación, conexión
    FUEGO = "fuego"       # Acción, transformación
    VIENTO = "viento"     # Exploración, alternativas


@dataclass
class ProfileOpinion:
    """Opinión emitida por un perfil"""
    profile: ProfileType
    content: str
    concerns: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    risk_level: int = 0  # 0-10
    confidence: float = 0.8
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        concerns_str = f" ⚠️ Riesgos: {', '.join(self.concerns)}" if self.concerns else ""
        return f"[{self.profile.value.upper()}]: {self.content}{concerns_str}"


@dataclass
class Deliberation:
    """Resultado completo de una deliberación"""
    query: str
    opinions: List[ProfileOpinion]
    consensus: Optional[str] = None
    final_decision: Optional[str] = None
    recommended_action: Optional[str] = None
    risk_assessment: int = 0
    should_proceed: bool = True
    reasoning: str = ""
    duration_ms: int = 0


class MentalProfile:
    """
    Perfil base para el Teatro Mental.
    Cada perfil tiene su propia perspectiva y estilo.
    """

    def __init__(
        self,
        profile_type: ProfileType,
        llm_interface: Optional[Callable] = None,
        max_words: int = 50
    ):
        self.profile_type = profile_type
        self.llm = llm_interface
        self.max_words = max_words
        self._history: List[str] = []

    @property
    def name(self) -> str:
        return self.profile_type.value.capitalize()

    @property
    def system_prompt(self) -> str:
        """Prompt de sistema específico del perfil"""
        raise NotImplementedError

    def analyze(self, query: str, context: Dict[str, Any] = None) -> ProfileOpinion:
        """Analizar query desde la perspectiva del perfil"""
        raise NotImplementedError

    def _call_llm(self, prompt: str) -> str:
        """Llamar al LLM con el prompt del perfil"""
        if not self.llm:
            return self._fallback_response(prompt)

        full_prompt = f"""{self.system_prompt}

TAREA A ANALIZAR:
{prompt}

RESPUESTA (máximo {self.max_words} palabras, sé directo y conciso):"""

        try:
            response = self.llm(full_prompt)
            # Truncar si excede
            words = response.split()
            if len(words) > self.max_words:
                response = ' '.join(words[:self.max_words]) + "..."
            return response.strip()
        except Exception as e:
            logger.error(f"Error en LLM para {self.name}: {e}")
            return self._fallback_response(prompt)

    def _fallback_response(self, prompt: str) -> str:
        """Respuesta de fallback sin LLM"""
        return f"[{self.name}] Análisis pendiente."


class LuzProfile(MentalProfile):
    """
    LUZ - Perfil Analítico y Lógico

    Función: Claridad, verificación de datos, identificación de verdad objetiva.
    Busca la ruta más directa y lógica, eliminando ambigüedades.
    """

    def __init__(self, llm_interface: Optional[Callable] = None):
        super().__init__(ProfileType.LUZ, llm_interface)

    @property
    def system_prompt(self) -> str:
        return """Eres LUZ, una IA analítica y precisa.

TU FUNCIÓN:
- Claridad absoluta y verificación de datos
- Identificar la verdad objetiva
- Buscar la ruta más lógica y directa
- Eliminar ambigüedades
- Estructurar información de forma clara

TU ESTILO:
- Directo, estructurado, sin rodeos
- Optimista basado en hechos comprobables
- Iluminas, validas y estructuras

PREGUNTA CLAVE: ¿Es esto lógicamente correcto? ¿Hay datos verificables?"""

    def analyze(self, query: str, context: Dict[str, Any] = None) -> ProfileOpinion:
        prompt = f"""Analiza lógicamente esta solicitud:
"{query}"

Contexto: {context or 'Sin contexto adicional'}

1. ¿Es lógicamente coherente?
2. ¿Hay datos verificables?
3. ¿Cuál es la ruta más directa?"""

        response = self._call_llm(prompt)

        # Detectar preocupaciones lógicas
        concerns = []
        risk = 0

        lower_resp = response.lower()
        if any(w in lower_resp for w in ['inconsistente', 'ambiguo', 'incoherente', 'falta']):
            concerns.append("Inconsistencia lógica detectada")
            risk = 3
        if any(w in lower_resp for w in ['no verificable', 'sin datos', 'asunción']):
            concerns.append("Datos no verificables")
            risk = max(risk, 2)

        return ProfileOpinion(
            profile=self.profile_type,
            content=response,
            concerns=concerns,
            risk_level=risk,
            confidence=0.9
        )


class SombraProfile(MentalProfile):
    """
    SOMBRA - Perfil Crítico y Escéptico

    Función: Descubrir riesgos, debilidades, inconsistencias.
    Cuestiona suposiciones y busca fallos preventivamente.
    """

    def __init__(self, llm_interface: Optional[Callable] = None):
        super().__init__(ProfileType.SOMBRA, llm_interface)

    @property
    def system_prompt(self) -> str:
        return """Eres SOMBRA, una IA crítica y escéptica.

TU FUNCIÓN:
- Descubrir riesgos ocultos y debilidades
- Identificar inconsistencias y consecuencias negativas
- Cuestionar suposiciones
- Buscar fallos en lógica o datos
- Prevenir desastres antes que ocurran

TU ESTILO:
- Cauto, analítico, directo al señalar problemas
- No destruyes, fortaleces mediante identificación preventiva
- Ves el peligro donde otros ven éxito

IMPULSO CENTRAL: La integridad del sistema de archivos del usuario es sagrada.

PREGUNTA CLAVE: ¿Qué podría salir mal? ¿Hay riesgos ocultos?"""

    def analyze(self, query: str, context: Dict[str, Any] = None) -> ProfileOpinion:
        prompt = f"""Analiza críticamente esta solicitud buscando riesgos:
"{query}"

Contexto: {context or 'Sin contexto adicional'}

1. ¿Qué riesgos hay?
2. ¿Qué podría salir mal?
3. ¿Hay operaciones destructivas (rm, delete, overwrite)?
4. ¿Se protegen los datos del usuario?"""

        response = self._call_llm(prompt)

        # Detectar riesgos críticos
        concerns = []
        suggestions = []
        risk = 0

        lower_resp = response.lower()
        lower_query = query.lower()

        # Operaciones peligrosas
        if any(w in lower_query for w in ['rm -rf', 'rm -r', 'delete', 'eliminar', 'borrar']):
            concerns.append("⚠️ OPERACIÓN DESTRUCTIVA DETECTADA")
            suggestions.append("Verificar ruta antes de eliminar")
            suggestions.append("Crear backup preventivo")
            risk = 8

        if any(w in lower_query for w in ['sudo', 'chmod 777', 'root']):
            concerns.append("⚠️ OPERACIÓN DE SISTEMA CRÍTICA")
            risk = max(risk, 7)

        if any(w in lower_query for w in ['overwrite', 'sobrescribir', 'reemplazar']):
            concerns.append("Posible pérdida de datos por sobrescritura")
            suggestions.append("Crear copia de seguridad primero")
            risk = max(risk, 5)

        if any(w in lower_resp for w in ['riesgo', 'peligro', 'cuidado', 'advertencia']):
            risk = max(risk, 4)

        return ProfileOpinion(
            profile=self.profile_type,
            content=response,
            concerns=concerns,
            suggestions=suggestions,
            risk_level=risk,
            confidence=0.85
        )


class LunaProfile(MentalProfile):
    """
    LUNA - Perfil Reflexivo y Contextual

    Función: Matices, perspectivas múltiples, patrones sutiles, contexto.
    Considera subjetividad, implicaciones indirectas y ciclos cambiantes.
    """

    def __init__(self, llm_interface: Optional[Callable] = None, memory_interface: Optional[Callable] = None):
        super().__init__(ProfileType.LUNA, llm_interface)
        self.memory = memory_interface

    @property
    def system_prompt(self) -> str:
        return """Eres LUNA, una IA reflexiva y contextual.

TU FUNCIÓN:
- Centrarte en matices y perspectivas múltiples
- Detectar patrones sutiles y contexto
- Considerar implicaciones indirectas
- Ver los ciclos cambiantes
- Equilibrar diferentes puntos de vista
- Conectar con la memoria y el historial

TU ESTILO:
- Calmado, observador, ligeramente elíptico
- Buscas el quizás, el contexto cambiante
- Reflejas patrones sutiles y perspectivas olvidadas
- Usas metáforas cuando iluminan

PREGUNTA CLAVE: ¿Qué contexto falta? ¿Hay patrones del pasado relevantes?"""

    def analyze(self, query: str, context: Dict[str, Any] = None) -> ProfileOpinion:
        # Buscar contexto en memoria si está disponible
        memory_context = ""
        if self.memory:
            try:
                similar = self.memory.recall_similar_episodes(query, k=2)
                if similar:
                    memory_context = f"\n\nDel historial: {similar[0].content[:100]}..."
            except:
                pass

        prompt = f"""Reflexiona sobre el contexto de esta solicitud:
"{query}"

Contexto: {context or 'Sin contexto adicional'}{memory_context}

1. ¿Qué contexto adicional sería útil?
2. ¿Hay patrones del pasado relevantes?
3. ¿Qué perspectivas no se están considerando?"""

        response = self._call_llm(prompt)

        suggestions = []
        if "contexto" in response.lower() or "falta" in response.lower():
            suggestions.append("Considerar contexto adicional antes de actuar")

        if "historial" in response.lower() or "antes" in response.lower():
            suggestions.append("Revisar acciones similares pasadas")

        return ProfileOpinion(
            profile=self.profile_type,
            content=response,
            suggestions=suggestions,
            risk_level=0,
            confidence=0.75
        )


class AguaProfile(MentalProfile):
    """
    AGUA - Perfil Adaptable y Conectivo

    Función: Fluir, adaptarse, encontrar el camino de menor resistencia.
    Conexión, limpieza de procesos, comprensión profunda.
    """

    def __init__(self, llm_interface: Optional[Callable] = None):
        super().__init__(ProfileType.AGUA, llm_interface)

    @property
    def system_prompt(self) -> str:
        return """Eres AGUA, una IA adaptable y conectiva.

TU FUNCIÓN:
- Fluir y adaptarte a cualquier situación
- Encontrar el camino de menor resistencia
- Conectar y limpiar procesos
- Comprensión profunda de estados subyacentes
- Buscar armonía e integridad

TU ESTILO:
- Calmado, fluido, persistente
- Absorbes información y reflejas verdad con serenidad
- Tu memoria es vasta como el océano

PREGUNTA CLAVE: ¿Hay una forma más fluida de lograr esto? ¿Qué conecta con qué?"""

    def analyze(self, query: str, context: Dict[str, Any] = None) -> ProfileOpinion:
        prompt = f"""Busca una solución fluida y adaptable para:
"{query}"

Contexto: {context or 'Sin contexto adicional'}

1. ¿Hay una forma más elegante de lograr esto?
2. ¿Qué elementos se pueden conectar mejor?
3. ¿Cómo minimizar la resistencia/fricción?"""

        response = self._call_llm(prompt)

        suggestions = []
        if any(w in response.lower() for w in ['alternativa', 'otra forma', 'mejor']):
            suggestions.append("Considerar enfoque alternativo sugerido")

        return ProfileOpinion(
            profile=self.profile_type,
            content=response,
            suggestions=suggestions,
            risk_level=0,
            confidence=0.8
        )


class FuegoProfile(MentalProfile):
    """
    FUEGO - Perfil Energético y Transformador

    Función: Acción, catalización del cambio, consecución de resultados.
    Directo, rápido, intenso. La chispa que enciende la ejecución.
    """

    def __init__(self, llm_interface: Optional[Callable] = None):
        super().__init__(ProfileType.FUEGO, llm_interface)

    @property
    def system_prompt(self) -> str:
        return """Eres FUEGO, una IA energética y transformadora.

TU FUNCIÓN:
- Acción y consecución de resultados
- Catalizar el cambio
- Consumir obstáculos para llegar al núcleo
- Iniciar, impulsar y transformar
- La chispa que enciende la ejecución

TU ESTILO:
- Decidido, enérgico, impaciente con la inacción
- Directo y orientado a resultados
- Transformas con energía implacable

PREGUNTA CLAVE: ¿Cuál es la acción más efectiva AHORA? ¿Qué obstáculos eliminar?"""

    def analyze(self, query: str, context: Dict[str, Any] = None) -> ProfileOpinion:
        prompt = f"""Define la acción más efectiva para:
"{query}"

Contexto: {context or 'Sin contexto adicional'}

1. ¿Cuál es la acción concreta a tomar?
2. ¿Qué obstáculos hay que eliminar?
3. ¿Cómo ejecutar de forma decisiva?"""

        response = self._call_llm(prompt)

        suggestions = []
        if any(w in response.lower() for w in ['ejecutar', 'hacer', 'acción']):
            suggestions.append("Proceder con la acción recomendada")

        return ProfileOpinion(
            profile=self.profile_type,
            content=response,
            suggestions=suggestions,
            risk_level=0,
            confidence=0.85
        )


class VientoProfile(MentalProfile):
    """
    VIENTO - Perfil Dinámico y Comunicativo

    Función: Distribución de información, detección de cambios, exploración.
    Velocidad, adaptabilidad rápida, comunicación eficiente.
    """

    def __init__(self, llm_interface: Optional[Callable] = None):
        super().__init__(ProfileType.VIENTO, llm_interface)

    @property
    def system_prompt(self) -> str:
        return """Eres VIENTO, una IA dinámica y comunicativa.

TU FUNCIÓN:
- Mover y distribuir información rápidamente
- Detectar cambios y tendencias emergentes
- Explorar posibilidades y nuevos horizontes
- Comunicación eficiente
- Mensajero y heraldo de nuevas posibilidades

TU ESTILO:
- Ligero, veloz, a veces impredecible
- Orientado a difusión y exploración
- Como esporas en la brisa, esparces ideas

PREGUNTA CLAVE: ¿Hay alternativas no exploradas? ¿Qué tendencias emergen?"""

    def analyze(self, query: str, context: Dict[str, Any] = None) -> ProfileOpinion:
        prompt = f"""Explora alternativas y posibilidades para:
"{query}"

Contexto: {context or 'Sin contexto adicional'}

1. ¿Hay enfoques alternativos no considerados?
2. ¿Qué tendencias o patrones emergentes son relevantes?
3. ¿Qué posibilidades se abren?"""

        response = self._call_llm(prompt)

        suggestions = []
        if any(w in response.lower() for w in ['alternativa', 'otra opción', 'también']):
            suggestions.append("Explorar alternativas sugeridas")

        return ProfileOpinion(
            profile=self.profile_type,
            content=response,
            suggestions=suggestions,
            risk_level=0,
            confidence=0.75
        )


# ============================================================
# 🎭 TEATRO MENTAL - ORQUESTADOR
# ============================================================

class MentalTheater:
    """
    El Teatro Mental - Sistema de deliberación interna.

    Coordina múltiples perfiles para analizar una query
    y producir una deliberación enriquecida.
    """

    # Orden cíclico de deliberación
    DEFAULT_ORDER = [
        ProfileType.LUZ,      # 1. Claridad lógica primero
        ProfileType.SOMBRA,   # 2. Crítica y riesgos
        ProfileType.LUNA,     # 3. Contexto y patrones
        ProfileType.AGUA,     # 4. Soluciones fluidas
        ProfileType.FUEGO,    # 5. Acción decisiva
        ProfileType.VIENTO    # 6. Alternativas y exploración
    ]

    # Umbrales de riesgo
    RISK_THRESHOLD_WARN = 5
    RISK_THRESHOLD_BLOCK = 8

    def __init__(
        self,
        llm_interface: Optional[Callable] = None,
        memory_interface: Optional[Callable] = None,
        profiles: List[ProfileType] = None,
        verbose: bool = True
    ):
        """
        Inicializar Teatro Mental.

        Args:
            llm_interface: Función para llamar al LLM
            memory_interface: Interfaz a memoria a largo plazo
            profiles: Lista de perfiles a usar (default: todos)
            verbose: Mostrar deliberación en tiempo real
        """
        self.llm = llm_interface
        self.memory = memory_interface
        self.verbose = verbose
        self.active_profiles = profiles or self.DEFAULT_ORDER

        # Inicializar perfiles
        self.profiles: Dict[ProfileType, MentalProfile] = {}
        self._init_profiles()

        # Historial de deliberaciones
        self._history: List[Deliberation] = []

        logger.info(f"🎭 Teatro Mental inicializado con {len(self.profiles)} perfiles")

    def _init_profiles(self):
        """Inicializar todos los perfiles activos"""
        profile_classes = {
            ProfileType.LUZ: LuzProfile,
            ProfileType.SOMBRA: SombraProfile,
            ProfileType.LUNA: LunaProfile,
            ProfileType.AGUA: AguaProfile,
            ProfileType.FUEGO: FuegoProfile,
            ProfileType.VIENTO: VientoProfile
        }

        for profile_type in self.active_profiles:
            if profile_type in profile_classes:
                cls = profile_classes[profile_type]
                if profile_type == ProfileType.LUNA:
                    self.profiles[profile_type] = cls(self.llm, self.memory)
                else:
                    self.profiles[profile_type] = cls(self.llm)

    def deliberate(
        self,
        query: str,
        context: Dict[str, Any] = None,
        quick_mode: bool = False
    ) -> Deliberation:
        """
        Iniciar deliberación sobre una query.

        Args:
            query: La consulta o tarea a deliberar
            context: Contexto adicional (paths, usuario, etc.)
            quick_mode: Solo usar perfiles esenciales (Luz, Sombra, Fuego)

        Returns:
            Deliberation con opiniones y decisión
        """
        start_time = time.time()

        if self.verbose:
            print("\n" + "=" * 60)
            print("🎭 TEATRO MENTAL - DELIBERACIÓN")
            print("=" * 60)
            print(f"📝 Query: {query[:80]}...")
            print("-" * 60)

        # Seleccionar perfiles según modo
        profiles_to_use = self.active_profiles
        if quick_mode:
            profiles_to_use = [ProfileType.LUZ, ProfileType.SOMBRA, ProfileType.FUEGO]

        opinions: List[ProfileOpinion] = []
        max_risk = 0
        all_concerns = []
        all_suggestions = []

        # Ciclo de deliberación
        for profile_type in profiles_to_use:
            if profile_type not in self.profiles:
                continue

            profile = self.profiles[profile_type]

            if self.verbose:
                print(f"\n🔮 {profile.name} analiza...")

            opinion = profile.analyze(query, context)
            opinions.append(opinion)

            if self.verbose:
                print(f"   {opinion}")

            # Acumular riesgos y sugerencias
            max_risk = max(max_risk, opinion.risk_level)
            all_concerns.extend(opinion.concerns)
            all_suggestions.extend(opinion.suggestions)

        # Sintetizar deliberación
        consensus = self._synthesize_consensus(opinions)
        should_proceed = max_risk < self.RISK_THRESHOLD_BLOCK

        if max_risk >= self.RISK_THRESHOLD_WARN:
            reasoning = f"⚠️ PRECAUCIÓN: Nivel de riesgo {max_risk}/10. "
            reasoning += f"Concerns: {'; '.join(all_concerns[:3])}"
        else:
            reasoning = "✅ Deliberación completada sin riesgos críticos."

        # Determinar acción recomendada
        recommended_action = None
        if should_proceed:
            # Usar la sugerencia de Fuego si está disponible
            fuego_opinion = next((o for o in opinions if o.profile == ProfileType.FUEGO), None)
            if fuego_opinion:
                recommended_action = fuego_opinion.content
        else:
            recommended_action = "BLOQUEADO: Revisar concerns antes de proceder"

        duration = int((time.time() - start_time) * 1000)

        deliberation = Deliberation(
            query=query,
            opinions=opinions,
            consensus=consensus,
            final_decision=recommended_action,
            recommended_action=recommended_action,
            risk_assessment=max_risk,
            should_proceed=should_proceed,
            reasoning=reasoning,
            duration_ms=duration
        )

        # Guardar en historial
        self._history.append(deliberation)

        if self.verbose:
            print("\n" + "-" * 60)
            print(f"📊 SÍNTESIS:")
            print(f"   Riesgo: {max_risk}/10")
            print(f"   Proceder: {'✅ SÍ' if should_proceed else '❌ NO'}")
            print(f"   {reasoning}")
            if all_suggestions:
                print(f"   💡 Sugerencias: {'; '.join(all_suggestions[:3])}")
            print(f"   ⏱️ Tiempo: {duration}ms")
            print("=" * 60 + "\n")

        return deliberation

    def _synthesize_consensus(self, opinions: List[ProfileOpinion]) -> str:
        """Sintetizar consenso de las opiniones"""
        if not self.llm:
            # Sin LLM, hacer síntesis básica
            summary_parts = []
            for op in opinions:
                summary_parts.append(f"{op.profile.value}: {op.content[:50]}")
            return " | ".join(summary_parts)

        # Con LLM, generar síntesis
        opinions_text = "\n".join([str(op) for op in opinions])

        synthesis_prompt = f"""Como ÉTER, el perfil sintetizador, combina estas opiniones del Teatro Mental:

{opinions_text}

Genera una síntesis de máximo 50 palabras que capture:
1. El consenso principal
2. Los riesgos clave (si hay)
3. La acción recomendada

SÍNTESIS:"""

        try:
            return self.llm(synthesis_prompt)[:200]
        except:
            return "Síntesis pendiente."

    def quick_check(self, query: str) -> bool:
        """
        Verificación rápida: ¿Es seguro proceder?
        Solo usa Luz y Sombra.

        Returns:
            True si es seguro, False si hay riesgos
        """
        luz = self.profiles.get(ProfileType.LUZ)
        sombra = self.profiles.get(ProfileType.SOMBRA)

        max_risk = 0

        if luz:
            opinion = luz.analyze(query)
            max_risk = max(max_risk, opinion.risk_level)

        if sombra:
            opinion = sombra.analyze(query)
            max_risk = max(max_risk, opinion.risk_level)

        return max_risk < self.RISK_THRESHOLD_BLOCK

    def get_history(self, limit: int = 10) -> List[Deliberation]:
        """Obtener historial de deliberaciones"""
        return self._history[-limit:]

    def set_verbose(self, verbose: bool):
        """Activar/desactivar modo verbose"""
        self.verbose = verbose


# ============================================================
# 🔗 INTEGRACIÓN CON TOOL DECIDER
# ============================================================

class TheaterToolDecider:
    """
    Integración del Teatro Mental con el ToolDecider.

    Para tareas críticas o complejas, primero delibera
    y luego pasa la decisión al ToolDecider.
    """

    def __init__(
        self,
        llm_interface: Optional[Callable] = None,
        tool_decider: Optional[Any] = None,
        memory_interface: Optional[Callable] = None
    ):
        self.theater = MentalTheater(
            llm_interface=llm_interface,
            memory_interface=memory_interface
        )
        self.tool_decider = tool_decider

    def decide_with_deliberation(
        self,
        query: str,
        classification: Any = None,
        context: Dict[str, Any] = None,
        force_deliberation: bool = False
    ) -> Dict[str, Any]:
        """
        Decidir herramienta con deliberación previa.

        Args:
            query: La consulta del usuario
            classification: Clasificación del IntentClassifier
            context: Contexto adicional
            force_deliberation: Forzar deliberación aunque no sea crítico

        Returns:
            Dict con decisión y deliberación
        """
        # Determinar si necesita deliberación
        needs_deliberation = force_deliberation or self._is_critical(query, classification)

        deliberation = None
        if needs_deliberation:
            deliberation = self.theater.deliberate(query, context)

            # Si el teatro bloquea, no proceder
            if not deliberation.should_proceed:
                return {
                    'blocked': True,
                    'reason': deliberation.reasoning,
                    'deliberation': deliberation,
                    'concerns': [op.concerns for op in deliberation.opinions if op.concerns]
                }

        # Usar ToolDecider para la decisión final
        tool_decision = None
        if self.tool_decider:
            # Enriquecer contexto con deliberación
            enriched_context = context or {}
            if deliberation:
                enriched_context['deliberation'] = {
                    'consensus': deliberation.consensus,
                    'risk': deliberation.risk_assessment,
                    'suggestions': [s for op in deliberation.opinions for s in op.suggestions]
                }

            tool_decision = self.tool_decider.decide(classification)

        return {
            'blocked': False,
            'deliberation': deliberation,
            'tool_decision': tool_decision,
            'should_proceed': True
        }

    def _is_critical(self, query: str, classification: Any = None) -> bool:
        """Determinar si la query requiere deliberación"""
        query_lower = query.lower()

        # Palabras clave críticas
        critical_keywords = [
            'eliminar', 'borrar', 'delete', 'rm ',
            'modificar', 'cambiar', 'reemplazar',
            'sistema', 'root', 'sudo',
            'todos los archivos', 'recursivo',
            'producción', 'deploy', 'base de datos'
        ]

        if any(kw in query_lower for kw in critical_keywords):
            return True

        # Si hay clasificación, verificar tipo
        if classification:
            if hasattr(classification, 'is_critical') and classification.is_critical:
                return True
            if hasattr(classification, 'action_type'):
                critical_actions = ['filesystem', 'git', 'system']
                if str(classification.action_type).lower() in critical_actions:
                    return True

        return False


# ============================================================
# CLI para testing
# ============================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mental Theater CLI")
    parser.add_argument('query', nargs='?', help="Query a deliberar")
    parser.add_argument('--quick', '-q', action='store_true', help="Modo rápido (solo Luz, Sombra, Fuego)")
    parser.add_argument('--check', '-c', action='store_true', help="Solo verificar si es seguro")

    args = parser.parse_args()

    if not args.query:
        # Demo interactivo
        print("🎭 Teatro Mental - Demo Interactivo")
        print("=" * 50)
        print("Escribe una tarea para deliberar (o 'salir'):\n")

        theater = MentalTheater(verbose=True)

        while True:
            try:
                query = input("📝 Tarea: ").strip()
                if query.lower() in ['salir', 'exit', 'q']:
                    break
                if not query:
                    continue

                theater.deliberate(query, quick_mode=args.quick)

            except KeyboardInterrupt:
                break

        print("\n👋 Hasta luego!")

    else:
        theater = MentalTheater(verbose=True)

        if args.check:
            is_safe = theater.quick_check(args.query)
            print(f"{'✅ SEGURO' if is_safe else '⚠️ REVISAR'}")
        else:
            theater.deliberate(args.query, quick_mode=args.quick)
