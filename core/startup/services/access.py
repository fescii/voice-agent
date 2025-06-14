"""
Service accessor utilities for getting initialized services from startup context.
"""
from typing import Any, Optional
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def get_stt_service(context: Any) -> Optional[Any]:
  """
  Get the STT service from the startup context.

  Args:
      context: Startup context

  Returns:
      STT service instance or None
  """
  try:
    stt_status = context.get_service_status("stt")
    if stt_status and stt_status.status == "running":
      return stt_status.metadata.get("service")
    else:
      logger.error("STT service not available or not running")
      return None
  except Exception as e:
    logger.error(f"Error getting STT service: {e}")
    return None


async def get_tts_service(context: Any) -> Optional[Any]:
  """
  Get the TTS service from the startup context.

  Args:
      context: Startup context

  Returns:
      TTS service instance or None
  """
  try:
    tts_status = context.get_service_status("tts")
    if tts_status and tts_status.status == "running":
      return tts_status.metadata.get("service")
    else:
      logger.error("TTS service not available or not running")
      return None
  except Exception as e:
    logger.error(f"Error getting TTS service: {e}")
    return None


async def get_llm_service(context: Any) -> Optional[Any]:
  """
  Get the LLM service from the startup context.

  Args:
      context: Startup context

  Returns:
      LLM orchestrator instance or None
  """
  try:
    llm_status = context.get_service_status("llm")
    if llm_status and llm_status.status == "running":
      return llm_status.metadata.get("service")
    else:
      logger.error("LLM service not available or not running")
      return None
  except Exception as e:
    logger.error(f"Error getting LLM service: {e}")
    return None
