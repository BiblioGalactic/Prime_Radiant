#!/usr/bin/env python3
# ============================================================
# 🔗 WIKIRAG WEBHOOK ADAPTER v1.0
# ============================================================
# Adaptador para recibir/enviar mensajes via Webhooks HTTP
# ============================================================

import os
import sys
import json
import logging
import hashlib
import hmac
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
from threading import Thread
import urllib.request
import urllib.parse

BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.messaging.protocol import (
    Message, MessageStatus, MessageDirection, MessageType, ChannelConfig
)
from core.messaging.channel_manager import BaseAdapter

logger = logging.getLogger(__name__)


class WebhookHandler(BaseHTTPRequestHandler):
    """Handler HTTP para webhooks entrantes"""

    adapter = None  # Se setea desde WebhookAdapter

    def log_message(self, format, *args):
        """Override para usar logger"""
        logger.debug(f"Webhook: {args[0]}")

    def do_GET(self):
        """Health check"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = {
            'status': 'ok',
            'service': 'WikiRAG Webhook',
            'timestamp': datetime.now().isoformat()
        }
        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        """Recibir webhook"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')

            # Verificar firma si está configurada
            if self.adapter and self.adapter.secret:
                signature = self.headers.get('X-Signature', '')
                if not self._verify_signature(body, signature):
                    self.send_error(403, "Invalid signature")
                    return

            # Parsear payload
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
                return

            # Procesar mensaje
            if self.adapter:
                message = self.adapter._parse_incoming(data)
                if message:
                    self.adapter._incoming_queue.append(message)
                    self.adapter._notify_handlers(message)

            # Responder OK
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "received"}')

        except Exception as e:
            logger.error(f"Error procesando webhook: {e}")
            self.send_error(500, str(e))

    def _verify_signature(self, body: str, signature: str) -> bool:
        """Verificar firma HMAC del payload"""
        if not self.adapter or not self.adapter.secret:
            return True

        expected = hmac.new(
            self.adapter.secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected)


class WebhookAdapter(BaseAdapter):
    """
    Adaptador para comunicación via Webhooks HTTP.

    Soporta:
    - Recibir mensajes via POST
    - Enviar mensajes a URLs configuradas
    - Verificación de firma HMAC

    Configuración:
    {
        "channels": {
            "webhook": {
                "name": "webhook",
                "enabled": true,
                "credentials": {
                    "secret": "your_hmac_secret"
                },
                "settings": {
                    "listen_port": 8080,
                    "outgoing_url": "https://your-service.com/webhook"
                }
            }
        }
    }
    """

    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        self.secret = config.credentials.get('secret', '')
        self.listen_port = config.settings.get('listen_port', 8080)
        self.outgoing_url = config.settings.get('outgoing_url', '')
        self._server: Optional[HTTPServer] = None
        self._server_thread: Optional[Thread] = None
        self._incoming_queue: List[Message] = []

    def connect(self) -> bool:
        """Iniciar servidor webhook"""
        if self._server:
            return True

        try:
            # Configurar handler
            WebhookHandler.adapter = self

            # Crear servidor
            self._server = HTTPServer(('0.0.0.0', self.listen_port), WebhookHandler)

            # Iniciar en thread separado
            self._server_thread = Thread(target=self._server.serve_forever)
            self._server_thread.daemon = True
            self._server_thread.start()

            self._connected = True
            logger.info(f"✅ Webhook server escuchando en puerto {self.listen_port}")
            return True

        except Exception as e:
            logger.error(f"Error iniciando webhook server: {e}")
            return False

    def disconnect(self):
        """Detener servidor webhook"""
        if self._server:
            self._server.shutdown()
            self._server = None
            self._server_thread = None
            self._connected = False
            logger.info("🛑 Webhook server detenido")

    def send(self, message: Message) -> bool:
        """Enviar mensaje via webhook saliente"""
        if not self.outgoing_url:
            logger.warning("No hay URL de webhook saliente configurada")
            message.mark_failed("No outgoing URL")
            return False

        try:
            payload = {
                'id': message.id,
                'sender': message.sender,
                'recipient': message.recipient,
                'content': message.content,
                'type': message.message_type.value,
                'timestamp': message.timestamp.isoformat(),
                'metadata': message.metadata
            }

            data = json.dumps(payload).encode('utf-8')

            req = urllib.request.Request(
                self.outgoing_url,
                data=data,
                method='POST'
            )
            req.add_header('Content-Type', 'application/json')

            # Añadir firma si hay secret
            if self.secret:
                signature = hmac.new(
                    self.secret.encode(),
                    data,
                    hashlib.sha256
                ).hexdigest()
                req.add_header('X-Signature', signature)

            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    message.status = MessageStatus.SENT
                    logger.info(f"📤 Webhook: Mensaje enviado")
                    return True
                else:
                    message.mark_failed(f"HTTP {response.status}")
                    return False

        except Exception as e:
            message.mark_failed(str(e))
            logger.error(f"Error enviando webhook: {e}")
            return False

    def receive(self) -> List[Message]:
        """Obtener mensajes recibidos"""
        messages = self._incoming_queue.copy()
        self._incoming_queue.clear()
        return messages

    def _parse_incoming(self, data: Dict[str, Any]) -> Optional[Message]:
        """Parsear payload de webhook entrante"""
        try:
            # Intentar diferentes formatos comunes

            # Formato estándar WikiRAG
            if 'content' in data and 'sender' in data:
                return Message(
                    id=data.get('id', f"wh_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                    channel='webhook',
                    direction=MessageDirection.INCOMING,
                    sender=data['sender'],
                    recipient=data.get('recipient', 'wikirag'),
                    content=data['content'],
                    status=MessageStatus.DELIVERED,
                    metadata=data.get('metadata', {})
                )

            # Formato Slack-like
            if 'text' in data and 'user' in data:
                return Message(
                    id=data.get('ts', f"wh_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                    channel='webhook',
                    direction=MessageDirection.INCOMING,
                    sender=data['user'],
                    recipient=data.get('channel', 'wikirag'),
                    content=data['text'],
                    status=MessageStatus.DELIVERED,
                    metadata={'channel': data.get('channel')}
                )

            # Formato Discord-like
            if 'content' in data and 'author' in data:
                author = data['author']
                return Message(
                    id=data.get('id', f"wh_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                    channel='webhook',
                    direction=MessageDirection.INCOMING,
                    sender=author.get('username', author.get('id', 'unknown')),
                    recipient=data.get('channel_id', 'wikirag'),
                    content=data['content'],
                    status=MessageStatus.DELIVERED,
                    metadata={'guild': data.get('guild_id')}
                )

            logger.warning(f"Formato de webhook no reconocido: {list(data.keys())}")
            return None

        except Exception as e:
            logger.error(f"Error parseando webhook: {e}")
            return None


# ============================================================
# CLI para testing
# ============================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Webhook Adapter CLI")
    parser.add_argument('--listen', '-l', type=int, help="Puerto para escuchar")
    parser.add_argument('--send', '-s', help="URL para enviar mensaje")
    parser.add_argument('--message', '-m', help="Mensaje a enviar")
    parser.add_argument('--secret', help="Secret para HMAC")

    args = parser.parse_args()

    if args.listen:
        config = ChannelConfig(
            name='webhook',
            settings={'listen_port': args.listen},
            credentials={'secret': args.secret or ''}
        )

        adapter = WebhookAdapter(config)

        if adapter.connect():
            print(f"✅ Servidor webhook escuchando en puerto {args.listen}")
            print("   Presiona Ctrl+C para detener")
            try:
                while True:
                    messages = adapter.receive()
                    for msg in messages:
                        print(f"📥 [{msg.sender}]: {msg.content}")
                    __import__('time').sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Deteniendo...")
                adapter.disconnect()
        else:
            print("❌ Error iniciando servidor")

    elif args.send and args.message:
        config = ChannelConfig(
            name='webhook',
            settings={'outgoing_url': args.send},
            credentials={'secret': args.secret or ''}
        )

        adapter = WebhookAdapter(config)

        msg = Message.create(
            channel='webhook',
            direction=MessageDirection.OUTGOING,
            sender='CLI',
            recipient='test',
            content=args.message
        )

        if adapter.send(msg):
            print(f"✅ Mensaje enviado a {args.send}")
        else:
            print(f"❌ Error: {msg.error}")

    else:
        parser.print_help()
