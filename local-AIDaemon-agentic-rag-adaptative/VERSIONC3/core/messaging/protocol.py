#!/usr/bin/env python3
# ============================================================
# 📨 WIKIRAG MESSAGING PROTOCOL v1.0
# ============================================================
# Define el protocolo de mensajes para comunicación multi-canal
# ============================================================

import json
import hashlib
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum


class MessageStatus(Enum):
    """Estados posibles de un mensaje"""
    PENDING = "pending"       # Pendiente de envío
    SENDING = "sending"       # En proceso de envío
    SENT = "sent"             # Enviado
    DELIVERED = "delivered"   # Entregado
    READ = "read"             # Leído
    FAILED = "failed"         # Error al enviar
    CANCELLED = "cancelled"   # Cancelado


class MessageDirection(Enum):
    """Dirección del mensaje"""
    INCOMING = "incoming"     # Mensaje recibido
    OUTGOING = "outgoing"     # Mensaje a enviar


class MessageType(Enum):
    """Tipos de mensajes"""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"
    COMMAND = "command"
    NOTIFICATION = "notification"


@dataclass
class Message:
    """
    Representa un mensaje en el sistema.
    Agnóstico del canal (WhatsApp, Telegram, Email, etc.)
    """
    id: str
    channel: str                          # telegram, whatsapp, email, webhook
    direction: MessageDirection
    sender: str                           # ID o nombre del remitente
    recipient: str                        # ID o nombre del destinatario
    content: str                          # Contenido del mensaje
    message_type: MessageType = MessageType.TEXT
    status: MessageStatus = MessageStatus.PENDING
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    attachments: List[str] = field(default_factory=list)
    reply_to: Optional[str] = None        # ID del mensaje al que responde
    thread_id: Optional[str] = None       # ID del hilo/conversación
    error: Optional[str] = None
    external_id: Optional[str] = None     # ID en el sistema externo

    @classmethod
    def create(
        cls,
        channel: str,
        direction: MessageDirection,
        sender: str,
        recipient: str,
        content: str,
        **kwargs
    ) -> 'Message':
        """Crear mensaje con ID único"""
        timestamp = datetime.now()
        content_hash = hashlib.md5(f"{content}{timestamp}".encode()).hexdigest()[:8]
        msg_id = f"{channel}_{timestamp.strftime('%Y%m%d%H%M%S')}_{content_hash}"

        return cls(
            id=msg_id,
            channel=channel,
            direction=direction,
            sender=sender,
            recipient=recipient,
            content=content,
            timestamp=timestamp,
            **kwargs
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializar a diccionario"""
        d = asdict(self)
        d['direction'] = self.direction.value
        d['status'] = self.status.value
        d['message_type'] = self.message_type.value
        d['timestamp'] = self.timestamp.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Message':
        """Deserializar desde diccionario"""
        d['direction'] = MessageDirection(d['direction'])
        d['status'] = MessageStatus(d['status'])
        d['message_type'] = MessageType(d.get('message_type', 'text'))
        d['timestamp'] = datetime.fromisoformat(d['timestamp'])
        return cls(**d)

    def to_json(self) -> str:
        """Serializar a JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Deserializar desde JSON"""
        return cls.from_dict(json.loads(json_str))

    def mark_sent(self, external_id: Optional[str] = None):
        """Marcar como enviado"""
        self.status = MessageStatus.SENT
        self.external_id = external_id

    def mark_failed(self, error: str):
        """Marcar como fallido"""
        self.status = MessageStatus.FAILED
        self.error = error

    def is_command(self) -> bool:
        """Verificar si es un comando"""
        return self.content.strip().startswith('/')

    def get_command(self) -> Optional[str]:
        """Extraer comando si existe"""
        if self.is_command():
            parts = self.content.strip().split()
            return parts[0][1:]  # Sin el /
        return None

    def get_command_args(self) -> List[str]:
        """Extraer argumentos del comando"""
        if self.is_command():
            parts = self.content.strip().split()
            return parts[1:] if len(parts) > 1 else []
        return []


@dataclass
class Conversation:
    """Representa una conversación/hilo"""
    id: str
    channel: str
    participants: List[str]
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

    def add_message(self, message: Message):
        """Añadir mensaje a la conversación"""
        message.thread_id = self.id
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_last_messages(self, n: int = 10) -> List[Message]:
        """Obtener últimos N mensajes"""
        return self.messages[-n:] if self.messages else []

    def get_context(self, max_messages: int = 5) -> str:
        """Obtener contexto de la conversación para el LLM"""
        recent = self.get_last_messages(max_messages)
        lines = []
        for msg in recent:
            direction = "→" if msg.direction == MessageDirection.OUTGOING else "←"
            lines.append(f"{direction} {msg.sender}: {msg.content[:200]}")
        return "\n".join(lines)


@dataclass
class ChannelConfig:
    """Configuración de un canal de mensajería"""
    name: str                             # telegram, whatsapp, etc.
    enabled: bool = True
    credentials: Dict[str, str] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    rate_limit: int = 30                  # Mensajes por minuto
    max_message_length: int = 4096
    supports_attachments: bool = True
    supports_replies: bool = True
    supports_threads: bool = False
    webhook_url: Optional[str] = None
    polling_interval: int = 1             # Segundos entre polls

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'ChannelConfig':
        return cls(**d)
