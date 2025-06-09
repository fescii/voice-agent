"""
Lifespan event management for FastAPI.
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.startup.manager import StartupManager
from core.startup.shutdown import ShutdownHandler
from core.logging.setup import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan_manager(app: FastAPI):
  """
  Manage application lifespan with proper startup and shutdown.
  """
  startup_manager = StartupManager()
  shutdown_handler = ShutdownHandler()

  try:
    # Setup signal handlers
    shutdown_handler.setup_signal_handlers()

    # Startup
    logger.info("🚀 Application lifespan starting...")

    async with startup_manager.startup_context() as context:
      # Store context in app state for access during requests
      app.state.startup_context = context
      app.state.shutdown_handler = shutdown_handler

      logger.info("✅ Application lifespan startup completed")

      # Yield control to FastAPI
      yield

  except asyncio.CancelledError:
    # Handle cancellation gracefully
    logger.info("📝 Application lifespan cancelled - initiating cleanup")
    raise
  except Exception as e:
    logger.error(f"❌ Application lifespan error: {e}")
    raise
  finally:
    logger.info("🧹 Application lifespan cleanup completed")
