#!/usr/bin/env python3
# ============================================================
# 📨 WIKIRAG CHANNEL MANAGER v1.0
# ============================================================
# Gestor centralizado de canales de mensajería
# ============================================================

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from threading import Thread, Lock
import time

BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.messaging.protocol import (
    Message, MessageStatus, MessageDirection, MessageType,
    Conversation, ChannelConfig
)

logger = logging.getLogger(__name__)

# Singleton
_channel_manager_instance = None


class BaseAdapter:
    """Clase base para adaptadores de canal"""

    def __init__(self, config: ChannelConfig):
        self.config = config
        self.name = config.name
        self._connected = False
        self._message_handlers: List[Callable] = []

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> bool:
        """Conectar al servicio"""
        raise NotImplementedError

    def disconnect(self):
        """Desconectar del servicio"""
        raise NotImplementedError

    def send(self, message: Message) -> bool:
        """Enviar mensaje"""
        raise NotImplementedError

    def receive(self) -> List[Message]:
        """Recibir mensajes pendientes"""
        raise NotImplementedError

    def register_handler(self, handler: Callable[[Message], None]):
        """Registrar handler para mensajes entrantes"""
        self._message_handlers.append(handler)

    def _notify_handlers(self, message: Message):
        """Notificar a todos los handlers"""
        for handler in self._message_handlers:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error en handler: {e}")


class ChannelManager:
    """
    Gestor centralizado de canales de mensajería.

    Maneja múltiples canales (Telegram, WhatsApp, Email, etc.)
    y enruta mensajes apropiadamente.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializar ChannelManager.

        Args:
            config_path: Ruta al archivo de configuración
        """
        self.config_path = config_path or os.path.expanduser(
            "~/wikirag/config/messaging.json"
        )
        self.adapters: Dict[str, BaseAdapter] = {}
        self.conversations: Dict[str, Conversation] = {}
        self.pending_messages: List[Message] = []
        self._lock = Lock()
        self._running = False
        self._poll_thread: Optional[Thread] = None

        # Directorio para mensajes
        self.messages_dir = Path.home() / "wikirag" / "queue"
        self.sent_dir = self.messages_dir / "sent"
        self.received_dir = self.messages_dir / "received"

        # Crear directorios
        self.sent_dir.mkdir(parents=True, exist_ok=True)
        self.received_dir.mkdir(parents=True, exist_ok=True)

        # Cargar configuración
        self._load_config()

        logger.info(f"📨 ChannelManager inicializado")

    def _load_config(self):
        """Cargar configuración de canales"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)

                for name, cfg in config.get('channels', {}).items():
                    channel_config = ChannelConfig.from_dict(cfg)
                    self._init_adapter(channel_config)

            except Exception as e:
                logger.warning(f"Error cargando config: {e}")

    def _init_adapter(self, config: ChannelConfig):
        """Inicializar adaptador para un canal"""
        try:
            if config.name == 'telegram':
                from core.messaging.telegram_adapter import TelegramAdapter
                self.adapters['telegram'] = TelegramAdapter(config)

            elif config.name == 'webhook':
                from core.messaging.webhook_adapter import WebhookAdapter
                self.adapters['webhook'] = WebhookAdapter(config)

            # Añadir más adaptadores aquí...

            logger.info(f"   ✅ Adaptador {config.name} inicializado")

        except ImportError as e:
            logger.warning(f"   ⚠️ Adaptador {config.name} no disponible: {e}")
        except Exception as e:
            logger.error(f"   ❌ Error inicializando {config.name}: {e}")

    def register_adapter(self, name: str, adapter: BaseAdapter):
        """Registrar adaptador manualmente"""
        self.adapters[name] = adapter
        logger.info(f"📨 Adaptador {name} registrado")

    def send(self, message: Message) -> bool:
        """
        Enviar mensaje por el canal apropiado.

        Args:
            message: Mensaje a enviar

        Returns:
            True si se envió correctamente
        """
        channel = message.channel

        if channel not in self.adapters:
            logger.error(f"Canal no disponible: {channel}")
            message.mark_failed(f"Canal {channel} no configurado")
            return False

        adapter = self.adapters[channel]

        if not adapter.is_connected:
            if not adapter.connect():
                message.mark_failed("No se pudo conectar al canal")
                return False

        try:
            success = adapter.send(message)

            if success:
                message.status = MessageStatus.SENT
                self._save_message(message, self.sent_dir)
                logger.info(f"📤 Mensaje enviado vía {channel}: {message.id}")
            else:
                message.mark_failed("Error de envío")

            return success

        except Exception as e:
            message.mark_failed(str(e))
            logger.error(f"Error enviando mensaje: {e}")
            return False

    def receive_all(self) -> List[Message]:
        """Recibir mensajes de todos los canales"""
        all_messages = []

        for name, adapter in self.adapters.items():
            if adapter.is_connected:
                try:
                    messages = adapter.receive()
                    for msg in messages:
                        self._save_message(msg, self.received_dir)
                        all_messages.append(msg)
                except Exception as e:
                    logger.error(f"Error recibiendo de {name}: {e}")

        return all_messages

    def _save_message(self, message: Message, directory: Path):
        """Guardar mensaje en disco"""
        filename = f"{message.id}.json"
        filepath = directory / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(message.to_json())

    def start_polling(self, interval: int = 2):
        """Iniciar polling de mensajes"""
        if self._running:
            return

        self._running = True
        self._poll_thread = Thread(target=self._poll_loop, args=(interval,))
        self._poll_thread.daemon = True
        self._poll_thread.start()
        logger.info(f"🔄 Polling iniciado (cada {interval}s)")

    def stop_polling(self):
        """Detener polling"""
        self._running = False
        if self._poll_thread:
            self._poll_thread.join(timeout=5)
        logger.info("🛑 Polling detenido")

    def _poll_loop(self, interval: int):
        """Loop de polling"""
        while self._running:
            try:
                messages = self.receive_all()

                for msg in messages:
                    self._process_incoming(msg)

            except Exception as e:
                logger.error(f"Error en poll: {e}")

            time.sleep(interval)

    def _process_incoming(self, message: Message):
        """Procesar mensaje entrante"""
        # Añadir a conversación
        thread_id = message.thread_id or message.sender
        if thread_id not in self.conversations:
            self.conversations[thread_id] = Conversation(
                id=thread_id,
                channel=message.channel,
                participants=[message.sender]
            )

        self.conversations[thread_id].add_message(message)

        # Crear tarea si es comando
        if message.is_command():
            self._create_task_from_command(message)
        else:
            self._create_task_from_message(message)

    def _create_task_from_command(self, message: Message):
        """Crear tarea desde comando"""
        from core.file_queue import FileQueue, TaskPriority

        fq = FileQueue()
        cmd = message.get_command()
        args = message.get_command_args()

        content = f"[COMANDO] /{cmd} {' '.join(args)}\n"
        content += f"De: {message.sender} vía {message.channel}"

        fq.create_task(
            content=content,
            priority=TaskPriority.HIGH,
            agent="executor"
        )

        logger.info(f"📝 Tarea creada desde comando: /{cmd}")

    def _create_task_from_message(self, message: Message):
        """Crear tarea desde mensaje normal"""
        from core.file_queue import FileQueue, TaskPriority

        fq = FileQueue()

        content = f"[{message.channel.upper()}] De: {message.sender}\n"
        content += f"Mensaje: {message.content}\n"
        content += f"Responder a: {message.id}"

        fq.create_task(
            content=content,
            priority=TaskPriority.NORMAL,
            agent="message_handler"
        )

    def send_notification(
        self,
        content: str,
        channel: str = "telegram",
        recipient: Optional[str] = None
    ) -> bool:
        """
        Enviar notificación rápida.

        Args:
            content: Contenido del mensaje
            channel: Canal a usar
            recipient: Destinatario (usa default si no se especifica)
        """
        if channel not in self.adapters:
            logger.warning(f"Canal {channel} no disponible")
            return False

        # Usar recipient default del config si no se especifica
        if not recipient:
            adapter = self.adapters[channel]
            recipient = adapter.config.settings.get('default_recipient', 'user')

        message = Message.create(
            channel=channel,
            direction=MessageDirection.OUTGOING,
            sender="WikiRAG",
            recipient=recipient,
            content=content,
            message_type=MessageType.NOTIFICATION
        )

        return self.send(message)

    def get_conversation(self, thread_id: str) -> Optional[Conversation]:
        """Obtener conversación por ID"""
        return self.conversations.get(thread_id)

    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema de mensajería"""
        return {
            'channels': {
                name: {
                    'connected': adapter.is_connected,
                    'enabled': adapter.config.enabled
                }
                for name, adapter in self.adapters.items()
            },
            'conversations': len(self.conversations),
            'pending': len(self.pending_messages),
            'polling': self._running
        }

    def connect_all(self):
        """Conectar todos los adaptadores"""
        for name, adapter in self.adapters.items():
            if adapter.config.enabled:
                try:
                    if adapter.connect():
                        logger.info(f"✅ {name} conectado")
                    else:
                        logger.warning(f"⚠️ {name} no se pudo conectar")
                except Exception as e:
                    logger.error(f"❌ Error conectando {name}: {e}")

    def disconnect_all(self):
        """Desconectar todos los adaptadores"""
        for name, adapter in self.adapters.items():
            try:
                adapter.disconnect()
            except Exception as e:
                logger.warning(f"Error desconectando {name}: {e}")


def get_channel_manager() -> ChannelManager:
    """Obtener instancia singleton del ChannelManager"""
    global _channel_manager_instance
    if _channel_manager_instance is None:
        _channel_manager_instance = ChannelManager()
    return _channel_manager_instance
