"""
Ringover service startup manager.
Handles Ringover streamer initialization and management.
"""
from typing import Dict, Any, TYPE_CHECKING

from .base import BaseStartupService
from .ringover.streamer import RingoverStreamerStartup
from core.logging.setup import get_logger

if TYPE_CHECKING:
    from core.startup.manager import StartupContext

logger = get_logger(__name__)


class RingoverService(BaseStartupService):
    """Manages Ringover services including the streamer."""
    
    def __init__(self):
        """Initialize the Ringover service manager."""
        super().__init__("ringover", is_critical=False)
        self.streamer = RingoverStreamerStartup()
        
    async def initialize(self, context: "StartupContext") -> Dict[str, Any]:
        """
        Initialize the Ringover services.
        
        Args:
            context: Startup context containing configuration and other services
            
        Returns:
            Dict containing service metadata
        """
        try:
            logger.info("Initializing Ringover services...")
            
            # Initialize the streamer
            streamer_metadata = await self.streamer.initialize(context)
            
            metadata = {
                "components": {
                    "streamer": streamer_metadata
                }
            }
            
            logger.info("Ringover services initialized successfully")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to initialize Ringover services: {e}")
            await self.cleanup(context)
            raise
            
    async def cleanup(self, context: "StartupContext") -> None:
        """
        Cleanup Ringover service resources.
        
        Args:
            context: Startup context
        """
        try:
            logger.info("Cleaning up Ringover services...")
            await self.streamer.cleanup(context)
            logger.info("Ringover services cleanup completed")
        except Exception as e:
            logger.error(f"Error cleaning up Ringover services: {e}")
            
    def get_health_check(self) -> Dict[str, Any]:
        """
        Get health check information for this service.

        Returns:
            Dict containing health status
        """
        streamer_health = self.streamer.get_health_check()
        
        return {
            "service": self.name,
            "status": streamer_health["status"],
            "critical": self.is_critical,
            "components": {
                "streamer": streamer_health
            }
        }
