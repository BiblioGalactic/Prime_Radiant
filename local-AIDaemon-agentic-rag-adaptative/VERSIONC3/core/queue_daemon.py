#!/usr/bin/env python3
# ============================================================
# 🤖 WIKIRAG QUEUE DAEMON v1.0
# ============================================================
# Daemon headless que procesa la cola de tareas automáticamente
# Monitorea inbox/, procesa tareas, y archiva resultados
# ============================================================

import os
import sys
import time
import signal
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import threading
import json

# Setup paths
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.file_queue import FileQueue, FileTask, TaskStatus, TaskPriority, TaskType
from core.strategic_agent import StrategicAgent

# Importar orchestrator de forma lazy para evitar carga pesada al inicio
orchestrator_instance = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("QueueDaemon")


def get_orchestrator():
    """Obtener instancia del orchestrator (lazy load)"""
    global orchestrator_instance
    if orchestrator_instance is None:
        from core.orchestrator import Orchestrator
        orchestrator_instance = Orchestrator()
        logger.info("🧠 Orchestrator inicializado")
    return orchestrator_instance


class QueueDaemon:
    """
    Daemon que procesa la cola de tareas de forma autónoma.

    Características:
    - Monitorea inbox/ por nuevas tareas
    - Procesa tareas según prioridad
    - Maneja dependencias entre tareas
    - Auto-genera subtareas cuando es necesario
    - Archiva resultados
    - Envía notificaciones (opcional)
    """

    def __init__(
        self,
        check_interval: int = 5,
        max_concurrent: int = 1,
        auto_decompose: bool = True,
        notify_channel: Optional[str] = None
    ):
        """
        Inicializar Queue Daemon.

        Args:
            check_interval: Segundos entre chequeos de inbox
            max_concurrent: Máximo de tareas simultáneas (para futuro)
            auto_decompose: Descomponer tareas complejas automáticamente
            notify_channel: Canal para notificaciones (whatsapp, telegram, etc.)
        """
        self.file_queue = FileQueue()
        self.strategic_agent = StrategicAgent(self.file_queue)
        self.check_interval = check_interval
        self.max_concurrent = max_concurrent
        self.auto_decompose = auto_decompose
        self.notify_channel = notify_channel

        # Estado
        self._running = False
        self._current_task: Optional[FileTask] = None
        self._processed_count = 0
        self._failed_count = 0
        self._start_time = None

        # Configuración de agentes por tipo
        self.agent_handlers = {
            'researcher': self._handle_research_task,
            'writer': self._handle_writing_task,
            'executor': self._handle_execution_task,
            'reviewer': self._handle_review_task,
            'message_handler': self._handle_message_task,
        }

        logger.info(f"📬 Queue Daemon inicializado")
        logger.info(f"   Check interval: {check_interval}s")
        logger.info(f"   Auto-decompose: {auto_decompose}")
        logger.info(f"   Notify channel: {notify_channel or 'none'}")

    def start(self):
        """Iniciar daemon"""
        if self._running:
            logger.warning("Daemon ya está corriendo")
            return

        self._running = True
        self._start_time = datetime.now()

        logger.info("🚀 Queue Daemon iniciado")
        logger.info(f"   📂 Monitoreando: {self.file_queue.inbox_path}")

        # Registrar handlers de señales
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Loop principal
        self._main_loop()

    def stop(self):
        """Detener daemon"""
        logger.info("🛑 Deteniendo Queue Daemon...")
        self._running = False

        # Estadísticas finales
        if self._start_time:
            uptime = datetime.now() - self._start_time
            logger.info(f"📊 Estadísticas finales:")
            logger.info(f"   Uptime: {uptime}")
            logger.info(f"   Procesadas: {self._processed_count}")
            logger.info(f"   Fallidas: {self._failed_count}")

    def _signal_handler(self, signum, frame):
        """Manejar señales de sistema"""
        logger.info(f"Recibida señal {signum}")
        self.stop()
        sys.exit(0)

    def _main_loop(self):
        """Loop principal del daemon"""
        while self._running:
            try:
                # Obtener siguiente tarea
                task = self.file_queue.get_next_task()

                if task:
                    self._process_task(task)
                else:
                    # No hay tareas, esperar
                    time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"❌ Error en loop principal: {e}")
                time.sleep(self.check_interval)

    def _process_task(self, task: FileTask):
        """Procesar una tarea"""
        self._current_task = task
        start_time = time.time()

        logger.info(f"📝 Procesando tarea: {task.id}")
        logger.info(f"   Tipo: {task.type.value}")
        logger.info(f"   Prioridad: {task.priority.name}")
        logger.info(f"   Agente: {task.agent or 'auto'}")

        try:
            # Mover a processing
            self.file_queue.move_to_processing(task)

            # Analizar complejidad si auto_decompose está activo
            if self.auto_decompose and not task.parent_task:
                complexity = self.strategic_agent.analyze_complexity(task.content)

                if complexity['needs_planning'] and complexity['score'] >= 3:
                    logger.info(f"   📋 Tarea compleja detectada, descomponiendo...")
                    plan = self.strategic_agent.decompose_task(task.content)
                    subtasks = self.strategic_agent.execute_plan(plan)

                    # Archivar tarea padre como "plan generado"
                    result = f"Plan generado: {len(subtasks)} subtareas"
                    self.file_queue.archive_completed(task, result)
                    self._processed_count += 1

                    # Notificar
                    self._notify(f"📋 Plan creado para: {task.content[:50]}...\n{len(subtasks)} subtareas encoladas")
                    return

            # Procesar según agente asignado
            if task.agent and task.agent in self.agent_handlers:
                handler = self.agent_handlers[task.agent]
                result = handler(task)
            else:
                # Handler genérico
                result = self._handle_generic_task(task)

            # Archivar éxito
            elapsed = time.time() - start_time
            full_result = f"{result}\n\n[Procesado en {elapsed:.1f}s]"
            self.file_queue.archive_completed(task, full_result)
            self._processed_count += 1

            logger.info(f"✅ Tarea completada: {task.id} ({elapsed:.1f}s)")

            # Notificar si es tarea de alto nivel
            if not task.parent_task:
                self._notify(f"✅ Completada: {task.content[:50]}...")

            # Verificar si generó subtareas (en el resultado)
            if result and "NEXT_STEPS:" in result:
                self._generate_follow_up_tasks(task, result)

        except Exception as e:
            logger.error(f"❌ Error procesando tarea: {e}")
            self.file_queue.archive_failed(task, str(e))
            self._failed_count += 1

            # Notificar fallo
            self._notify(f"❌ Falló: {task.content[:30]}...\nError: {str(e)[:100]}")

        finally:
            self._current_task = None

    def _handle_generic_task(self, task: FileTask) -> str:
        """Handler genérico usando el Orchestrator"""
        orchestrator = get_orchestrator()

        # Procesar con el sistema RAG/Agentes
        result = orchestrator.process_query(task.content)

        return result.response

    def _handle_research_task(self, task: FileTask) -> str:
        """Handler para tareas de investigación"""
        orchestrator = get_orchestrator()

        # Usar modo adaptativo para investigación
        result = orchestrator.process_query_adaptive(task.content)

        # Guardar output si se especificó
        if task.metadata.get('expected_output'):
            output_path = Path(task.metadata['expected_output']).expanduser()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result.response, encoding='utf-8')
            logger.info(f"   📄 Output guardado: {output_path}")

        return result.response

    def _handle_writing_task(self, task: FileTask) -> str:
        """Handler para tareas de escritura"""
        orchestrator = get_orchestrator()

        # Prompt especializado para escritura
        writing_prompt = f"""Escribe el siguiente contenido de forma completa y detallada:

{task.content}

INSTRUCCIONES:
- Escribe contenido extenso y bien estructurado
- Usa formato Markdown
- Incluye ejemplos y explicaciones
- Mínimo 1000 palabras si el tema lo permite
"""

        result = orchestrator.process_query(writing_prompt)

        # Guardar output
        if task.metadata.get('expected_output'):
            output_path = Path(task.metadata['expected_output']).expanduser()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result.response, encoding='utf-8')

        return result.response

    def _handle_execution_task(self, task: FileTask) -> str:
        """Handler para tareas de ejecución"""
        orchestrator = get_orchestrator()

        # Si tiene modo agentic, usarlo para ejecución
        if orchestrator.agentic_mode and orchestrator.agent_runtime:
            result = orchestrator.process_with_agent(task.content)
        else:
            result = orchestrator.process_query(task.content)

        return result.response

    def _handle_review_task(self, task: FileTask) -> str:
        """Handler para tareas de revisión"""
        orchestrator = get_orchestrator()

        # Prompt especializado para revisión
        review_prompt = f"""Revisa críticamente el siguiente contenido:

{task.content}

INSTRUCCIONES:
- Identifica errores, inconsistencias o problemas
- Sugiere mejoras específicas
- Evalúa la calidad general (1-10)
- Proporciona feedback constructivo
"""

        result = orchestrator.process_query(review_prompt)
        return result.response

    def _handle_message_task(self, task: FileTask) -> str:
        """Handler para procesar mensajes entrantes"""
        orchestrator = get_orchestrator()

        # Procesar mensaje y generar respuesta
        result = orchestrator.process_query(task.content)

        # TODO: Enviar respuesta por el canal correspondiente
        # Por ahora solo devolver la respuesta
        return result.response

    def _generate_follow_up_tasks(self, parent_task: FileTask, result: str):
        """Generar tareas de seguimiento desde el resultado"""
        try:
            # Extraer NEXT_STEPS del resultado
            if "NEXT_STEPS:" not in result:
                return

            steps_text = result.split("NEXT_STEPS:")[1].strip()
            steps = [s.strip() for s in steps_text.split("\n") if s.strip()]

            subtasks = []
            for step in steps[:5]:  # Máximo 5 subtareas
                if step.startswith("-") or step.startswith("*"):
                    step = step[1:].strip()
                if step:
                    subtasks.append({
                        'content': step,
                        'priority': 'NORMAL'
                    })

            if subtasks:
                self.file_queue.create_subtasks(subtasks, parent_task.id)
                logger.info(f"   📋 {len(subtasks)} subtareas auto-generadas")

        except Exception as e:
            logger.warning(f"Error generando subtareas: {e}")

    def _notify(self, message: str):
        """Enviar notificación por el canal configurado"""
        if not self.notify_channel:
            return

        try:
            from core.file_queue import ChannelMessage, MessageChannel

            msg = ChannelMessage(
                id=f"notify_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                channel=self.notify_channel,
                direction="outgoing",
                sender="WikiRAG Daemon",
                recipient="user",
                content=message
            )

            channel = MessageChannel(self.file_queue)
            channel.send(msg)
            logger.info(f"📤 Notificación enviada a {self.notify_channel}")

        except Exception as e:
            logger.warning(f"Error enviando notificación: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del daemon"""
        queue_status = self.file_queue.get_status()

        return {
            'running': self._running,
            'current_task': self._current_task.id if self._current_task else None,
            'processed': self._processed_count,
            'failed': self._failed_count,
            'uptime': str(datetime.now() - self._start_time) if self._start_time else None,
            'queue': queue_status
        }

    def process_single(self):
        """Procesar una única tarea y salir (modo one-shot)"""
        task = self.file_queue.get_next_task()

        if task:
            self._process_task(task)
            return True
        else:
            logger.info("📭 No hay tareas pendientes")
            return False

    def process_all(self):
        """Procesar todas las tareas pendientes y salir"""
        processed = 0

        while True:
            task = self.file_queue.get_next_task()
            if not task:
                break

            self._process_task(task)
            processed += 1

        logger.info(f"✅ Procesadas {processed} tareas")
        return processed


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="WikiRAG Queue Daemon - Procesador de tareas autónomo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Iniciar daemon en modo continuo
  python -m core.queue_daemon --daemon

  # Procesar todas las tareas y salir
  python -m core.queue_daemon --process-all

  # Procesar una sola tarea
  python -m core.queue_daemon --process-one

  # Ver estado de la cola
  python -m core.queue_daemon --status

  # Crear una tarea de prueba
  python -m core.queue_daemon --test "Escribe un poema sobre Python"
"""
    )

    parser.add_argument('--daemon', '-d', action='store_true',
                        help='Ejecutar como daemon continuo')
    parser.add_argument('--process-all', '-a', action='store_true',
                        help='Procesar todas las tareas y salir')
    parser.add_argument('--process-one', '-1', action='store_true',
                        help='Procesar una tarea y salir')
    parser.add_argument('--status', '-s', action='store_true',
                        help='Mostrar estado de la cola')
    parser.add_argument('--test', '-t', type=str,
                        help='Crear tarea de prueba')
    parser.add_argument('--interval', '-i', type=int, default=5,
                        help='Intervalo de chequeo en segundos (default: 5)')
    parser.add_argument('--no-decompose', action='store_true',
                        help='Deshabilitar auto-descomposición de tareas')
    parser.add_argument('--notify', '-n', type=str,
                        help='Canal de notificaciones (telegram, whatsapp)')

    args = parser.parse_args()

    # Crear daemon
    daemon = QueueDaemon(
        check_interval=args.interval,
        auto_decompose=not args.no_decompose,
        notify_channel=args.notify
    )

    if args.status:
        status = daemon.file_queue.get_status()
        print("\n📊 Estado de la Cola WikiRAG")
        print("=" * 40)
        print(f"📥 Inbox:          {status['inbox']} tareas")
        print(f"⚙️  Processing:     {status['processing']} tareas")
        print(f"✅ Completadas hoy: {status['completed_today']}")
        print(f"❌ Fallidas hoy:    {status['failed_today']}")
        print(f"🕐 Timestamp:       {status['timestamp']}")

    elif args.test:
        task = daemon.file_queue.create_task(
            args.test,
            priority=TaskPriority.NORMAL
        )
        print(f"✅ Tarea de prueba creada: {task.id}")
        print(f"   Archivo: {task.source_file}")

    elif args.process_one:
        print("🔄 Procesando una tarea...")
        daemon.process_single()

    elif args.process_all:
        print("🔄 Procesando todas las tareas...")
        daemon.process_all()

    elif args.daemon:
        print("🚀 Iniciando Queue Daemon en modo continuo...")
        print("   Presiona Ctrl+C para detener\n")
        daemon.start()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
