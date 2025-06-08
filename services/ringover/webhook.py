"""
Ringover webhook event handler - thin wrapper for backward compatibility.
"""
from .webhook.main import (
    RingoverWebhookProcessor, CallEventProcessor,
    WebhookEventType, WebhookEvent, WebhookHandler,
    WebhookConfig as RingoverWebhookConfig
)

__all__ = [
    'RingoverWebhookProcessor', 'CallEventProcessor',
    'WebhookEventType', 'WebhookEvent', 'WebhookHandler',
    'RingoverWebhookConfig'
]
