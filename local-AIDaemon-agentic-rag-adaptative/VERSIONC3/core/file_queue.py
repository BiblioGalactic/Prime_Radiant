#!/usr/bin/env python3
# ============================================================
# 📬 WIKIRAG FILE QUEUE v1.0
# ============================================================
# Sistema de colas basado en archivos (Unix-style)
# Complementa el QueueManager SQLite con persistencia de archivos
# ============================================================

import os
import json
import shutil
import time
import logging
import hashlib
import fcntl
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Niveles de prioridad para tareas"""
    CRITICAL = 0    # Ejecutar inmediatamente
    HIGH = 1        # Próxima en cola
    NORMAL = 2      # Orden estándar
    LOW = 3         # Cuando haya recursos
    BACKGROUND = 4  # Solo si está idle


class TaskStatus(Enum):
    """Estados posibles de una tarea"""
    PENDING = "pending"
    PROCESSING = "processing"
    WAITING_DEPS = "waiting_deps"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Tipos de tareas soportados"""
    TASK = "task"       # .task - Orden simple
    PLAN = "plan"       # .plan - Roadmap multi-paso
    MSG = "msg"         # .msg - Mensaje para canal externo
    STATUS = "status"   # .status - Estado de ejecución


@dataclass
class FileTask:
    """Representa una tarea basada en archivo"""
    id: str
    type: TaskType
    content: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    agent: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    parent_task: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retries: int = 0
    max_retries: int = 3
    result: Optional[str] = None
    error: Optional[str] = None
    source_file: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializar a diccionario"""
        return {
            'id': self.id,
            'type': self.type.value,
            'content': self.content,
            'priority': self.priority.value,
            'status': self.status.value,
            'agent': self.agent,
            'dependencies': self.dependencies,
            'parent_task': self.parent_task,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'retries': self.retries,
            'max_retries': self.max_retries,
            'result': self.result,
            'error': self.error,
            'source_file': self.source_file
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'FileTask':
        """Deserializar desde diccionario"""
        return cls(
            id=d['id'],
            type=TaskType(d['type']),
            content=d['content'],
            priority=TaskPriority(d['priority']),
            status=TaskStatus(d['status']),
            agent=d.get('agent'),
            dependencies=d.get('dependencies', []),
            parent_task=d.get('parent_task'),
            metadata=d.get('metadata', {}),
            created_at=datetime.fromisoformat(d['created_at']),
            started_at=datetime.fromisoformat(d['started_at']) if d.get('started_at') else None,
            completed_at=datetime.fromisoformat(d['completed_at']) if d.get('completed_at') else None,
            retries=d.get('retries', 0),
            max_retries=d.get('max_retries', 3),
            result=d.get('result'),
            error=d.get('error'),
            source_file=d.get('source_file')
        )

    @classmethod
    def from_file(cls, filepath: Path) -> 'FileTask':
        """Crear tarea desde archivo .task/.plan/.msg"""
        content = filepath.read_text(encoding='utf-8')
        ext = filepath.suffix.lower()
        task_id = filepath.stem

        # Detectar tipo por extensión
        type_map = {
            '.task': TaskType.TASK,
            '.plan': TaskType.PLAN,
            '.msg': TaskType.MSG,
            '.status': TaskType.STATUS
        }
        task_type = type_map.get(ext, TaskType.TASK)

        # Parsear metadatos del contenido (formato YAML-like)
        metadata = {}
        lines = content.split('\n')
        body_start = 0
        priority = TaskPriority.NORMAL
        agent = None
        dependencies = []
        parent = None

        for i, line in enumerate(lines):
            if line.startswith('#') or not line.strip():
                body_start = i + 1
                continue
            if ':' in line and not line.startswith(' '):
                key, value = line.split(':', 1)
                key = key.strip().lower().replace('-', '_')
                value = value.strip()

                if key == 'priority':
                    try:
                        priority = TaskPriority[value.upper()]
                    except KeyError:
                        priority = TaskPriority.NORMAL
                elif key == 'agent':
                    agent = value
                elif key == 'depends_on':
                    dependencies = [d.strip() for d in value.split(',')]
                elif key == 'parent':
                    parent = value
                else:
                    metadata[key] = value
                body_start = i + 1
            else:
                break

        actual_content = '\n'.join(lines[body_start:]).strip() or content

        return cls(
            id=task_id,
            type=task_type,
            content=actual_content,
            priority=priority,
            agent=agent,
            dependencies=dependencies,
            parent_task=parent,
            metadata=metadata,
            source_file=str(filepath)
        )


class FileQueue:
    """
    Gestor de cola de tareas basado en sistema de archivos.
    Estilo Unix: inbox → processing → archive
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Inicializar FileQueue.

        Args:
            base_path: Ruta base de la cola. Default: ~/wikirag/queue
        """
        if base_path:
            self.base_path = Path(base_path).expanduser()
        else:
            self.base_path = Path.home() / "wikirag" / "queue"

        # Directorios del sistema
        self.inbox_path = self.base_path / "inbox"
        self.processing_path = self.base_path / "processing"
        self.archive_path = self.base_path / "archive"
        self.logs_path = self.base_path / "logs"
        self.sent_path = self.base_path / "sent"
        self.received_path = self.base_path / "received"

        # Subdirectorios de agentes
        self.agents_path = self.base_path / "agents"

        # Crear estructura
        self._ensure_directories()

        # Lock file
        self.lock_file = self.base_path / ".queue.lock"
        self._lock_fd = None

        logger.info(f"📬 FileQueue inicializado en {self.base_path}")

    def _ensure_directories(self):
        """Crear directorios si no existen"""
        dirs = [
            self.inbox_path,
            self.processing_path,
            self.archive_path,
            self.logs_path,
            self.sent_path,
            self.received_path,
            self.agents_path / "professor",
            self.agents_path / "executor",
            self.agents_path / "strategist",
            self.base_path / "channels" / "whatsapp",
            self.base_path / "channels" / "telegram",
            self.base_path / "channels" / "imessage",
            self.base_path / "channels" / "webhook"
        ]
        for path in dirs:
            path.mkdir(parents=True, exist_ok=True)

    def _acquire_lock(self, timeout: int = 30) -> bool:
        """Adquirir lock exclusivo"""
        start = time.time()
        while time.time() - start < timeout:
            try:
                self._lock_fd = open(self.lock_file, 'w')
                fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except (IOError, OSError):
                time.sleep(0.1)
        return False

    def _release_lock(self):
        """Liberar lock"""
        if self._lock_fd:
            try:
                fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_UN)
                self._lock_fd.close()
            except:
                pass
            self._lock_fd = None

    def scan_tasks(self) -> List[FileTask]:
        """Escanear inbox y devolver tareas ordenadas por prioridad"""
        tasks = []
        extensions = ('.task', '.plan', '.msg')

        for filepath in self.inbox_path.iterdir():
            if filepath.is_file() and filepath.suffix.lower() in extensions:
                try:
                    task = FileTask.from_file(filepath)
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"❌ Error parseando {filepath}: {e}")

        # Ordenar por prioridad
        tasks.sort(key=lambda t: (t.priority.value, t.created_at))
        return tasks

    def get_next_task(self) -> Optional[FileTask]:
        """Obtener siguiente tarea considerando dependencias"""
        tasks = self.scan_tasks()
        completed_ids = self._get_completed_task_ids()

        for task in tasks:
            if task.dependencies:
                pending_deps = [d for d in task.dependencies if d not in completed_ids]
                if pending_deps:
                    logger.debug(f"⏳ Tarea {task.id} esperando: {pending_deps}")
                    continue
            return task
        return None

    def _get_completed_task_ids(self) -> set:
        """Obtener IDs de tareas completadas"""
        ids = set()
        for filepath in self.archive_path.iterdir():
            if filepath.is_file() and 'completed' in filepath.stem:
                parts = filepath.stem.split('.completed_')
                if parts:
                    ids.add(parts[0])
        return ids

    def move_to_processing(self, task: FileTask) -> Path:
        """Mover tarea a processing"""
        if not self._acquire_lock():
            raise RuntimeError("No se pudo adquirir lock")

        try:
            source = Path(task.source_file)
            if not source.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {source}")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = self.processing_path / f"{task.id}.{timestamp}{source.suffix}"

            shutil.move(str(source), str(dest))
            task.source_file = str(dest)
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.now()

            self._save_state(task)
            logger.info(f"📂 Tarea {task.id} → processing")
            return dest
        finally:
            self._release_lock()

    def archive_completed(self, task: FileTask, result: str) -> Path:
        """Archivar tarea completada"""
        if not self._acquire_lock():
            raise RuntimeError("No se pudo adquirir lock")

        try:
            source = Path(task.source_file) if task.source_file else None

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = self.archive_path / f"{task.id}.completed_{timestamp}.json"

            with open(dest, 'w', encoding='utf-8') as f:
                json.dump(task.to_dict(), f, ensure_ascii=False, indent=2)

            if source and source.exists():
                source.unlink()

            logger.info(f"✅ Tarea {task.id} archivada")
            return dest
        finally:
            self._release_lock()

    def archive_failed(self, task: FileTask, error: str) -> Path:
        """Archivar tarea fallida o reintentar"""
        if not self._acquire_lock():
            raise RuntimeError("No se pudo adquirir lock")

        try:
            source = Path(task.source_file) if task.source_file else None
            task.error = error

            # Reintentar si no se alcanzó el máximo
            if task.retries < task.max_retries:
                task.retries += 1
                task.status = TaskStatus.PENDING

                ext = source.suffix if source else '.task'
                dest = self.inbox_path / f"{task.id}.retry_{task.retries}{ext}"

                if source and source.exists():
                    shutil.move(str(source), str(dest))
                else:
                    # Recrear archivo
                    self._write_task_file(task, dest)

                logger.warning(f"⚠️ Tarea {task.id} reintento {task.retries}/{task.max_retries}")
                return dest

            # Archivar como fallida
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = self.archive_path / f"{task.id}.failed_{timestamp}.json"

            with open(dest, 'w', encoding='utf-8') as f:
                json.dump(task.to_dict(), f, ensure_ascii=False, indent=2)

            if source and source.exists():
                source.unlink()

            logger.error(f"❌ Tarea {task.id} fallida: {error}")
            return dest
        finally:
            self._release_lock()

    def create_task(
        self,
        content: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        agent: Optional[str] = None,
        dependencies: List[str] = None,
        task_type: TaskType = TaskType.TASK,
        parent_id: Optional[str] = None
    ) -> FileTask:
        """Crear nueva tarea en el inbox"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        content_hash = hashlib.md5(content.encode()).hexdigest()[:6]
        task_id = f"{timestamp}_{content_hash}"

        task = FileTask(
            id=task_id,
            type=task_type,
            content=content,
            priority=priority,
            agent=agent,
            dependencies=dependencies or [],
            parent_task=parent_id
        )

        ext_map = {
            TaskType.TASK: '.task',
            TaskType.PLAN: '.plan',
            TaskType.MSG: '.msg',
            TaskType.STATUS: '.status'
        }
        ext = ext_map[task_type]
        filepath = self.inbox_path / f"{task_id}{ext}"

        self._write_task_file(task, filepath)
        task.source_file = str(filepath)

        logger.info(f"📝 Tarea creada: {task_id}")
        return task

    def _write_task_file(self, task: FileTask, filepath: Path):
        """Escribir archivo de tarea con metadatos"""
        lines = [
            f"# WikiRAG Task - {datetime.now().isoformat()}",
            f"priority: {task.priority.name}"
        ]
        if task.agent:
            lines.append(f"agent: {task.agent}")
        if task.dependencies:
            lines.append(f"depends_on: {', '.join(task.dependencies)}")
        if task.parent_task:
            lines.append(f"parent: {task.parent_task}")
        lines.append("")
        lines.append(task.content)

        filepath.write_text('\n'.join(lines), encoding='utf-8')

    def create_subtasks(self, subtasks: List[Dict[str, Any]], parent_id: str) -> List[FileTask]:
        """Crear subtareas con dependencias encadenadas"""
        created = []
        previous_id = None

        for i, sub in enumerate(subtasks):
            deps = sub.get('dependencies', [])
            if previous_id:
                deps.append(previous_id)

            task = self.create_task(
                content=sub['content'],
                priority=TaskPriority[sub.get('priority', 'NORMAL').upper()],
                agent=sub.get('agent'),
                dependencies=deps,
                parent_id=parent_id
            )
            task.metadata['subtask_index'] = i

            created.append(task)
            previous_id = task.id

        logger.info(f"📋 {len(created)} subtareas creadas para {parent_id}")
        return created

    def _save_state(self, task: FileTask):
        """Guardar estado de tarea"""
        if task.source_file:
            state_file = Path(task.source_file).with_suffix('.state.json')
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(task.to_dict(), f, ensure_ascii=False, indent=2)

    def get_status(self) -> Dict[str, Any]:
        """Obtener estado de la cola"""
        inbox_count = sum(1 for _ in self.inbox_path.glob('*.task')) + \
                      sum(1 for _ in self.inbox_path.glob('*.plan')) + \
                      sum(1 for _ in self.inbox_path.glob('*.msg'))

        processing_count = sum(1 for f in self.processing_path.iterdir() if f.is_file())

        today = datetime.now().strftime("%Y%m%d")
        completed_today = sum(1 for _ in self.archive_path.glob(f"*.completed_{today}*.json"))
        failed_today = sum(1 for _ in self.archive_path.glob(f"*.failed_{today}*.json"))

        return {
            'inbox': inbox_count,
            'processing': processing_count,
            'completed_today': completed_today,
            'failed_today': failed_today,
            'timestamp': datetime.now().isoformat()
        }

    def cleanup_old(self, days: int = 30):
        """Limpiar archivos antiguos"""
        cutoff = time.time() - (days * 24 * 60 * 60)
        removed = 0

        for filepath in self.archive_path.iterdir():
            if filepath.stat().st_mtime < cutoff:
                filepath.unlink()
                removed += 1

        if removed:
            logger.info(f"🧹 Limpieza: {removed} archivos eliminados")


# ============================================================
# 📨 MENSAJE PARA CANALES EXTERNOS
# ============================================================

@dataclass
class ChannelMessage:
    """Mensaje para canales de comunicación externos"""
    id: str
    channel: str  # whatsapp, telegram, imessage, email, webhook
    direction: str  # incoming, outgoing
    sender: str
    recipient: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)
    attachments: List[str] = field(default_factory=list)
    reply_to: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'ChannelMessage':
        d['timestamp'] = datetime.fromisoformat(d['timestamp'])
        return cls(**d)


class MessageChannel:
    """Gestor de mensajes para canales externos"""

    def __init__(self, file_queue: FileQueue):
        self.fq = file_queue
        self.sent_path = file_queue.sent_path
        self.received_path = file_queue.received_path

    def send(self, message: ChannelMessage) -> Path:
        """Encolar mensaje para envío"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{message.channel}_{timestamp}_{message.id}.msg"
        filepath = self.sent_path / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(message.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"📤 Mensaje encolado: {message.channel} → {message.recipient}")
        return filepath

    def receive(self, message: ChannelMessage) -> Path:
        """Almacenar mensaje recibido y crear tarea"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{message.channel}_{timestamp}_{message.id}.msg"
        filepath = self.received_path / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(message.to_dict(), f, ensure_ascii=False, indent=2)

        # Crear tarea para procesar
        self.fq.create_task(
            content=f"[{message.channel}] De: {message.sender}\n{message.content}",
            priority=TaskPriority.HIGH,
            agent="message_handler"
        )

        logger.info(f"📥 Mensaje recibido: {message.channel} ← {message.sender}")
        return filepath

    def get_pending(self, channel: Optional[str] = None) -> List[ChannelMessage]:
        """Obtener mensajes pendientes de envío"""
        messages = []
        pattern = f"{channel}_*.msg" if channel else "*.msg"

        for filepath in self.sent_path.glob(pattern):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                msg = ChannelMessage.from_dict(data)
                if msg.status == "pending":
                    msg.metadata['_source_file'] = str(filepath)
                    messages.append(msg)
            except Exception as e:
                logger.error(f"Error leyendo {filepath}: {e}")

        return messages

    def mark_sent(self, message: ChannelMessage):
        """Marcar mensaje como enviado"""
        if '_source_file' in message.metadata:
            filepath = Path(message.metadata['_source_file'])
            message.status = "sent"
            del message.metadata['_source_file']

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(message.to_dict(), f, ensure_ascii=False, indent=2)


# ============================================================
# CLI
# ============================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="WikiRAG File Queue CLI")
    parser.add_argument('command', choices=['status', 'create', 'list', 'next', 'cleanup'])
    parser.add_argument('--content', '-c', help="Contenido de la tarea")
    parser.add_argument('--priority', '-p', default='NORMAL')
    parser.add_argument('--agent', '-a', help="Agente asignado")
    parser.add_argument('--days', '-d', type=int, default=30)

    args = parser.parse_args()
    fq = FileQueue()

    if args.command == 'status':
        status = fq.get_status()
        print("\n📊 Estado de la Cola WikiRAG")
        print("=" * 40)
        print(f"📥 Inbox:          {status['inbox']} tareas")
        print(f"⚙️  Processing:     {status['processing']} tareas")
        print(f"✅ Completadas hoy: {status['completed_today']}")
        print(f"❌ Fallidas hoy:    {status['failed_today']}")

    elif args.command == 'create':
        if not args.content:
            print("❌ Se requiere --content")
        else:
            priority = TaskPriority[args.priority.upper()]
            task = fq.create_task(args.content, priority=priority, agent=args.agent)
            print(f"✅ Tarea creada: {task.id}")

    elif args.command == 'list':
        tasks = fq.scan_tasks()
        if not tasks:
            print("📭 Cola vacía")
        else:
            print(f"\n📋 {len(tasks)} tareas en cola:")
            for t in tasks:
                agent_info = f" [{t.agent}]" if t.agent else ""
                print(f"  [{t.priority.name}]{agent_info} {t.id}: {t.content[:50]}...")

    elif args.command == 'next':
        task = fq.get_next_task()
        if task:
            print(f"\n📌 Próxima tarea: {task.id}")
            print(f"   Tipo: {task.type.name}")
            print(f"   Prioridad: {task.priority.name}")
            print(f"   Agente: {task.agent or 'no asignado'}")
            print(f"   Contenido: {task.content}")
        else:
            print("📭 No hay tareas pendientes")

    elif args.command == 'cleanup':
        fq.cleanup_old(days=args.days)
        print(f"✅ Limpieza completada")
