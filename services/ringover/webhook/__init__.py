"""
Ringover webhook system.
"""
from .main import RingoverWebhookProcessor, CallEventProcessor
from .models import WebhookEventType, WebhookEvent, WebhookHandler
from .configuration import WebhookConfig

# Legacy import aliases for backward compatibility
RingoverWebhookConfig = WebhookConfig

__all__ = [
    'RingoverWebhookProcessor', 'CallEventProcessor',
    'WebhookEventType', 'WebhookEvent', 'WebhookHandler',
    'WebhookConfig', 'RingoverWebhookConfig'
]
