"""
Streaming configuration for Ringover.
"""
import os


class StreamingConfig:
    """Ringover streaming configuration."""
    
    def __init__(self):
        self.streamer_auth_token = os.getenv("RINGOVER_STREAMER_AUTH_TOKEN", "")
        self.websocket_url = os.getenv("RINGOVER_WEBSOCKET_URL", "")
