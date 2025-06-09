"""
Ringover streamer startup service manager.
Handles the lifecycle of the ringover-streamer alongside the main application.
"""
import os
import asyncio
import subprocess
import signal
from typing import Optional, Dict, Any, TYPE_CHECKING
from pathlib import Path

from core.logging.setup import get_logger
from core.config.registry import config_registry
from core.startup.services.base import BaseStartupService

if TYPE_CHECKING:
  from core.startup.manager import StartupContext

logger = get_logger(__name__)


class RingoverStreamerStartup(BaseStartupService):
  """
  Manages the ringover-streamer service lifecycle during application startup.

  This service ensures the ringover-streamer is running alongside the main app
  and handles proper cleanup on shutdown.
  """

  def __init__(self):
    """Initialize the streamer startup manager."""
    super().__init__("ringover_streamer", is_critical=False)
    self.process: Optional[subprocess.Popen] = None
    self.is_running = False

    # Configuration
    self.streamer_dir = Path("./external/ringover-streamer")
    self.streamer_host = "0.0.0.0"
    self.streamer_port = 8000
    self.python_executable = self._get_python_executable()

  def _get_python_executable(self) -> str:
    """Get the Python executable path, preferring virtual environment."""
    venv_python = Path(".venv/bin/python")
    if venv_python.exists():
      return str(venv_python.absolute())
    return "python"

  async def initialize(self, context: "StartupContext") -> Dict[str, Any]:
    """
    Initialize and start the ringover-streamer service.

    Args:
        context: Startup context containing configuration and other services

    Returns:
        Dict containing service metadata
    """
    try:
      logger.info("Initializing Ringover streamer service...")

      # Check if streamer directory exists
      if not self.streamer_dir.exists():
        raise Exception(f"Ringover streamer not found at {self.streamer_dir}")

      # Check if app.py exists
      app_path = self.streamer_dir / "app.py"
      if not app_path.exists():
        raise Exception(f"Ringover streamer app.py not found at {app_path}")

      # Start the streamer process
      await self._start_streamer()

      # Wait a moment for the process to initialize
      await asyncio.sleep(2)

      # Verify the process is still running
      if not self._is_process_healthy():
        raise Exception("Ringover streamer failed to start properly")

      self.is_running = True

      metadata = {
          "host": self.streamer_host,
          "port": self.streamer_port,
          "pid": self.process.pid if self.process else None,
          "streamer_dir": str(self.streamer_dir),
          "python_executable": self.python_executable
      }

      logger.info(
          f"Ringover streamer started successfully on {self.streamer_host}:{self.streamer_port}")
      return metadata

    except Exception as e:
      logger.error(f"Failed to initialize Ringover streamer: {e}")
      await self.cleanup(context)
      raise

  async def _start_streamer(self):
    """Start the ringover-streamer process."""
    try:
      cmd = [
          self.python_executable,
          "app.py"
      ]

      # Set environment variables
      env = {
          **dict(os.environ),
          "RINGOVER_STREAMER_HOST": self.streamer_host,
          "RINGOVER_STREAMER_PORT": str(self.streamer_port)
      }

      self.process = subprocess.Popen(
          cmd,
          cwd=self.streamer_dir,
          env=env,
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE,
          preexec_fn=os.setsid if hasattr(os, 'setsid') else None
      )

      logger.info(
          f"Started ringover-streamer process with PID {self.process.pid}")

    except Exception as e:
      logger.error(f"Failed to start ringover-streamer process: {e}")
      raise

  def _is_process_healthy(self) -> bool:
    """Check if the streamer process is healthy."""
    if not self.process:
      return False

    # Check if process is still running
    return self.process.poll() is None

  async def health_check(self) -> bool:
    """
    Perform a health check on the ringover-streamer service.

    Returns:
        True if healthy, False otherwise
    """
    if not self.is_running or not self._is_process_healthy():
      return False

    try:
      # Try to connect to the health endpoint
      import aiohttp
      async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://{self.streamer_host}:{self.streamer_port}/health",
            timeout=aiohttp.ClientTimeout(total=5)
        ) as response:
          return response.status == 200

    except Exception as e:
      logger.warning(f"Ringover streamer health check failed: {e}")
      return False

  async def cleanup(self, context: "StartupContext"):
    """Clean up the ringover-streamer service."""
    if self.process:
      try:
        logger.info("Stopping ringover-streamer...")

        # Try graceful shutdown first
        if hasattr(os, 'killpg'):
          os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
        else:
          self.process.terminate()

        # Wait for graceful shutdown
        try:
          await asyncio.wait_for(
              asyncio.create_task(self._wait_for_process_end()),
              timeout=10.0
          )
        except asyncio.TimeoutError:
          logger.warning(
              "Ringover streamer didn't stop gracefully, forcing...")

          # Force kill if graceful shutdown failed
          if hasattr(os, 'killpg'):
            os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
          else:
            self.process.kill()

          await self._wait_for_process_end()

        logger.info("Ringover streamer stopped")

      except Exception as e:
        logger.error(f"Error stopping ringover-streamer: {e}")
      finally:
        self.process = None
        self.is_running = False

    async def _wait_for_process_end(self):
        """Wait for the process to end."""
        while self.process and self.process.poll() is None:
            await asyncio.sleep(0.1)
            
    def get_health_check(self) -> Dict[str, Any]:
        """
        Get health check information for this service.

        Returns:
            Dict containing health status
        """
        return {
            "service": self.name,
            "status": "running" if self.is_running and self._is_process_healthy() else "error",
            "critical": self.is_critical,
            "metadata": self.get_status()
        }
            
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the service."""
        return {
            "is_running": self.is_running,
            "process_healthy": self._is_process_healthy(),
            "pid": self.process.pid if self.process else None,
            "host": self.streamer_host,
            "port": self.streamer_port
        }
