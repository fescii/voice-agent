"""
Base configuration model for Ringover settings.
"""
import os
from typing import Optional


class BaseRingoverConfig:
    """Base configuration for Ringover API settings."""
    
    def __init__(self):
        # Load from environment variables
        self.api_key = os.getenv("RINGOVER_API_KEY", "")
        api_base_url = os.getenv("RINGOVER_API_BASE_URL", "")
        
        # Ensure base URL has trailing slash for aiohttp
        self.api_base_url = api_base_url.rstrip('/') + '/' if api_base_url else ""
        
        self.api_secret = os.getenv("RINGOVER_API_SECRET", "")
        
        # Validate required fields
        if not self.api_base_url:
            raise ValueError("RINGOVER_API_BASE_URL is required")
        if not self.api_key:
            raise ValueError("RINGOVER_API_KEY is required")
