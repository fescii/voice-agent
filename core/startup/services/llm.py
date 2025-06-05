"""
LLM startup service.
"""
from typing import Dict, Any, TYPE_CHECKING

from .base import BaseStartupService
from services.llm.orchestrator import LLMOrchestrator
from core.logging.setup import get_logger

if TYPE_CHECKING:
  from core.startup.manager import StartupContext

logger = get_logger(__name__)


class LLMService(BaseStartupService):
  """LLM orchestrator initialization service."""

  def __init__(self):
    super().__init__("llm", is_critical=False)
    self._orchestrator = None

  async def initialize(self, context: "StartupContext") -> Dict[str, Any]:
    """Initialize LLM orchestrator and providers."""
    try:
      # Initialize LLM orchestrator
      self._orchestrator = LLMOrchestrator()

      # Test a simple generation to verify providers work
      test_messages = [{"role": "user", "content": "Hello, this is a test."}]

      # Try to get a response from the default provider
      response = await self._orchestrator.generate_response(
          messages=test_messages,
          provider="openai",
          max_tokens=10
      )

      # Get available providers
      available_providers = list(self._orchestrator._providers.keys())

      logger.info(
          f"LLM orchestrator initialized with {len(available_providers)} providers")

      return {
          "available_providers": available_providers,
          "default_provider": "openai",
          "test_response": response.choices[0].message.content if response else "No response",
          "status": "initialized"
      }

    except Exception as e:
      logger.error(f"LLM service initialization failed: {e}")
      # Non-critical service, don't raise
      return {
          "available_providers": [],
          "status": "error",
          "error": str(e)
      }

  async def cleanup(self, context: "StartupContext") -> None:
    """Cleanup LLM resources."""
    try:
      if self._orchestrator:
        # Cleanup any provider connections if needed
        pass
      logger.info("LLM service cleaned up")
    except Exception as e:
      logger.error(f"Error cleaning up LLM service: {e}")

  def get_health_check(self) -> Dict[str, Any]:
    """Get LLM service health information."""
    if self._orchestrator:
      return {
          "service": self.name,
          "status": "healthy",
          "critical": self.is_critical,
          "providers": len(self._orchestrator._providers)
      }
    else:
      return {
          "service": self.name,
          "status": "not_initialized",
          "critical": self.is_critical
      }
