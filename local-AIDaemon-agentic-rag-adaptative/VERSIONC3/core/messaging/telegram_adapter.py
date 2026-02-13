#!/usr/bin/env python3
# ============================================================
# 📱 WIKIRAG TELEGRAM ADAPTER v1.0
# ============================================================
# Adaptador para comunicación via Telegram Bot API
# ============================================================

import os
import sys
import json
import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
import urllib.request
import urllib.parse
import urllib.error

BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.messaging.protocol import (
    Message, MessageStatus, MessageDirection, MessageType, ChannelConfig
)
from core.messaging.channel_manager import BaseAdapter

logger = logging.getLogger(__name__)


class TelegramAdapter(BaseAdapter):
    """
    Adaptador para Telegram usando Bot API.

    Requisitos:
    - Token de bot (obtener de @BotFather)
    - Chat ID del usuario/grupo

    Configuración en messaging.json:
    {
        "channels": {
            "telegram": {
                "name": "telegram",
                "enabled": true,
                "credentials": {
                    "bot_token": "YOUR_BOT_TOKEN"
                },
                "settings": {
                    "default_recipient": "YOUR_CHAT_ID",
                    "parse_mode": "Markdown"
                }
            }
        }
    }
    """

    BASE_URL = "https://api.telegram.org/bot{token}/{method}"

    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        self.bot_token = config.credentials.get('bot_token', '')
        self.default_chat_id = config.settings.get('default_recipient', '')
        self.parse_mode = config.settings.get('parse_mode', 'Markdown')
        self._last_update_id = 0
        self._connected = False

    def _make_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Optional[Dict[str, Any]]:
        """Hacer request a la API de Telegram"""
        if not self.bot_token:
            logger.error("Bot token no configurado")
            return None

        url = self.BASE_URL.format(token=self.bot_token, method=method)

        try:
            if params:
                # Codificar parámetros
                data = urllib.parse.urlencode(params).encode('utf-8')
                req = urllib.request.Request(url, data=data, method='POST')
            else:
                req = urllib.request.Request(url)

            req.add_header('Content-Type', 'application/x-www-form-urlencoded')

            with urllib.request.urlopen(req, timeout=timeout) as response:
                result = json.loads(response.read().decode('utf-8'))

                if result.get('ok'):
                    return result.get('result')
                else:
                    logger.error(f"API error: {result.get('description')}")
                    return None

        except urllib.error.HTTPError as e:
            logger.error(f"HTTP error: {e.code} - {e.reason}")
            return None
        except urllib.error.URLError as e:
            logger.error(f"URL error: {e.reason}")
            return None
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None

    def connect(self) -> bool:
        """Verificar conexión con bot"""
        if not self.bot_token:
            logger.error("❌ Telegram: bot_token no configurado")
            return False

        # Verificar bot con getMe
        result = self._make_request('getMe')

        if result:
            bot_name = result.get('username', 'Unknown')
            logger.info(f"✅ Telegram: Conectado como @{bot_name}")
            self._connected = True
            return True

        self._connected = False
        return False

    def disconnect(self):
        """Desconectar (no-op para Telegram)"""
        self._connected = False

    def send(self, message: Message) -> bool:
        """Enviar mensaje por Telegram"""
        if not self._connected:
            if not self.connect():
                return False

        chat_id = message.recipient or self.default_chat_id

        if not chat_id:
            logger.error("No se especificó chat_id")
            message.mark_failed("No chat_id")
            return False

        # Preparar parámetros
        params = {
            'chat_id': chat_id,
            'text': message.content
        }

        # Añadir parse_mode si hay formato
        if self.parse_mode:
            params['parse_mode'] = self.parse_mode

        # Añadir reply_to si es respuesta
        if message.reply_to:
            params['reply_to_message_id'] = message.reply_to

        # Enviar
        result = self._make_request('sendMessage', params)

        if result:
            message.external_id = str(result.get('message_id'))
            message.status = MessageStatus.SENT
            logger.info(f"📤 Telegram: Mensaje enviado a {chat_id}")
            return True
        else:
            message.mark_failed("Error de API")
            return False

    def receive(self) -> List[Message]:
        """Recibir mensajes nuevos via getUpdates"""
        if not self._connected:
            return []

        params = {
            'offset': self._last_update_id + 1,
            'timeout': 0,  # Non-blocking
            'allowed_updates': json.dumps(['message'])
        }

        result = self._make_request('getUpdates', params, timeout=10)

        if not result:
            return []

        messages = []

        for update in result:
            self._last_update_id = update.get('update_id', self._last_update_id)

            msg_data = update.get('message', {})
            if not msg_data:
                continue

            # Crear Message
            chat = msg_data.get('chat', {})
            from_user = msg_data.get('from', {})
            text = msg_data.get('text', '')

            if not text:
                continue

            message = Message(
                id=f"tg_{msg_data.get('message_id')}",
                channel='telegram',
                direction=MessageDirection.INCOMING,
                sender=str(from_user.get('id', '')),
                recipient=str(chat.get('id', '')),
                content=text,
                status=MessageStatus.DELIVERED,
                external_id=str(msg_data.get('message_id')),
                metadata={
                    'from_username': from_user.get('username'),
                    'from_name': from_user.get('first_name', ''),
                    'chat_type': chat.get('type'),
                    'chat_title': chat.get('title', chat.get('first_name', ''))
                }
            )

            messages.append(message)
            logger.info(f"📥 Telegram: Mensaje de {from_user.get('username', 'unknown')}")

        return messages

    def send_typing(self, chat_id: str):
        """Enviar indicador de 'escribiendo...'"""
        params = {
            'chat_id': chat_id,
            'action': 'typing'
        }
        self._make_request('sendChatAction', params)

    def send_photo(
        self,
        chat_id: str,
        photo_url: str,
        caption: Optional[str] = None
    ) -> bool:
        """Enviar foto"""
        params = {
            'chat_id': chat_id,
            'photo': photo_url
        }
        if caption:
            params['caption'] = caption
            params['parse_mode'] = self.parse_mode

        result = self._make_request('sendPhoto', params)
        return result is not None

    def send_document(
        self,
        chat_id: str,
        document_url: str,
        caption: Optional[str] = None
    ) -> bool:
        """Enviar documento"""
        params = {
            'chat_id': chat_id,
            'document': document_url
        }
        if caption:
            params['caption'] = caption

        result = self._make_request('sendDocument', params)
        return result is not None

    def get_chat_info(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Obtener información de un chat"""
        params = {'chat_id': chat_id}
        return self._make_request('getChat', params)

    def set_webhook(self, url: str) -> bool:
        """Configurar webhook para recibir updates"""
        params = {'url': url}
        result = self._make_request('setWebhook', params)
        return result is not None

    def delete_webhook(self) -> bool:
        """Eliminar webhook"""
        result = self._make_request('deleteWebhook')
        return result is not None


# ============================================================
# CLI para testing
# ============================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Telegram Adapter CLI")
    parser.add_argument('--token', '-t', help="Bot token")
    parser.add_argument('--chat', '-c', help="Chat ID")
    parser.add_argument('--send', '-s', help="Mensaje a enviar")
    parser.add_argument('--receive', '-r', action='store_true', help="Recibir mensajes")
    parser.add_argument('--info', '-i', action='store_true', help="Info del bot")

    args = parser.parse_args()

    # Cargar token de env si no se proporciona
    token = args.token or os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = args.chat or os.getenv('TELEGRAM_CHAT_ID')

    if not token:
        print("❌ Se requiere token. Usa --token o TELEGRAM_BOT_TOKEN env")
        sys.exit(1)

    config = ChannelConfig(
        name='telegram',
        credentials={'bot_token': token},
        settings={'default_recipient': chat_id or ''}
    )

    adapter = TelegramAdapter(config)

    if args.info:
        if adapter.connect():
            print("✅ Bot conectado correctamente")
        else:
            print("❌ Error conectando")

    elif args.send:
        if not chat_id:
            print("❌ Se requiere chat ID. Usa --chat o TELEGRAM_CHAT_ID env")
            sys.exit(1)

        msg = Message.create(
            channel='telegram',
            direction=MessageDirection.OUTGOING,
            sender='CLI',
            recipient=chat_id,
            content=args.send
        )

        if adapter.connect() and adapter.send(msg):
            print(f"✅ Mensaje enviado: {msg.id}")
        else:
            print(f"❌ Error: {msg.error}")

    elif args.receive:
        if adapter.connect():
            print("📥 Esperando mensajes (Ctrl+C para salir)...")
            try:
                while True:
                    messages = adapter.receive()
                    for msg in messages:
                        print(f"  [{msg.metadata.get('from_username')}]: {msg.content}")
                    time.sleep(2)
            except KeyboardInterrupt:
                print("\n👋 Adiós")
        else:
            print("❌ Error conectando")

    else:
        parser.print_help()
