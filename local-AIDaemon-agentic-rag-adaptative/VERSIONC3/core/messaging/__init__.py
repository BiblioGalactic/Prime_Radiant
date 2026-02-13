#!/usr/bin/env python3
"""
📨 WikiRAG Messaging System
Sistema multi-canal para comunicación externa.
"""

from .protocol import Message, MessageStatus, MessageDirection
from .channel_manager import ChannelManager, get_channel_manager
from .telegram_adapter import TelegramAdapter
from .webhook_adapter import WebhookAdapter

__all__ = [
    'Message',
    'MessageStatus',
    'MessageDirection',
    'ChannelManager',
    'get_channel_manager',
    'TelegramAdapter',
    'WebhookAdapter'
]
