#!/usr/bin/env python3
"""
Test script to verify STT/TTS/LLM services are accessible from startup context.
"""
from core.logging.setup import get_logger
from core.startup.services.access import get_stt_service, get_tts_service, get_llm_service
from core.startup.manager import StartupManager
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


logger = get_logger(__name__)


async def test_service_access():
  """Test accessing services from startup context."""
  try:
    # Initialize startup manager
    startup_manager = StartupManager()

    async with startup_manager.startup_context() as context:
      logger.info("✅ Startup context initialized")

      # Test service access
      stt_service = await get_stt_service(context)
      if stt_service:
        logger.info("✅ STT service retrieved successfully")
      else:
        logger.error("❌ Failed to retrieve STT service")

      tts_service = await get_tts_service(context)
      if tts_service:
        logger.info("✅ TTS service retrieved successfully")
      else:
        logger.error("❌ Failed to retrieve TTS service")

      llm_service = await get_llm_service(context)
      if llm_service:
        logger.info("✅ LLM service retrieved successfully")
      else:
        logger.error("❌ Failed to retrieve LLM service")

      logger.info("🎉 Service access test completed")

  except Exception as e:
    logger.error(f"❌ Service access test failed: {e}")
    raise

if __name__ == "__main__":
  asyncio.run(test_service_access())
