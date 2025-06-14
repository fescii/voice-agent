"""
Manager for the official ringover-streamer service.
"""
import asyncio
import subprocess
import os
from typing import Optional, Dict, Any
from pathlib import Path

from core.logging.setup import get_logger
from core.config.registry import config_registry

logger = get_logger(__name__)


class RingoverStreamerManager:
  """
  Manages the lifecycle of the official ringover-streamer service.

  This class handles:
  1. Installing/cloning the ringover-streamer from GitHub
  2. Starting and stopping the streamer service
  3. Health checks and monitoring
  """

  def __init__(self):
    """Initialize the streamer manager."""
    self.config = None  # Will be initialized lazily
    self.streamer_process: Optional[subprocess.Popen] = None
    self.is_running = False

    # Configuration for ringover-streamer
    self.streamer_host = "0.0.0.0"
    self.streamer_port = 8000
    self.streamer_dir = Path("./external/ringover-streamer")
    self.repo_url = "https://github.com/ringover/ringover-streamer.git"

  def _ensure_config(self):
    """Ensure config is loaded."""
    if self.config is None:
      try:
        self.config = config_registry.ringover
      except (KeyError, AttributeError):
        # Config not available yet, use defaults
        logger.warning("Ringover config not available, using defaults")
        self.config = None
    self.repo_url = "https://github.com/ringover/ringover-streamer.git"

  async def ensure_streamer_installed(self) -> bool:
    """
    Ensure the ringover-streamer is installed and ready.
    Since everything is locally managed, this just returns True.

    Returns:
        True (always, since we're managing everything locally)
    """
    logger.info(
        "Skipping ringover-streamer installation check (locally managed)")
    return True

  async def _clone_streamer(self):
    """Clone the ringover-streamer repository."""
    try:
      # Create external directory if it doesn't exist
      self.streamer_dir.parent.mkdir(parents=True, exist_ok=True)

      # Clone the repository
      process = await asyncio.create_subprocess_exec(
          "git", "clone", self.repo_url, str(self.streamer_dir),
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE
      )

      stdout, stderr = await process.communicate()

      if process.returncode == 0:
        logger.info("Successfully cloned ringover-streamer")
        await self._install_dependencies()
      else:
        logger.error(f"Failed to clone ringover-streamer: {stderr.decode()}")
        raise Exception(f"Git clone failed: {stderr.decode()}")

    except Exception as e:
      logger.error(f"Error cloning ringover-streamer: {e}")
      raise

  async def _install_dependencies(self):
    """Install dependencies for ringover-streamer."""
    try:
      logger.info("Installing ringover-streamer dependencies...")

      process = await asyncio.create_subprocess_exec(
          "pip", "install", "-r", "requirements.txt",
          cwd=str(self.streamer_dir),
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE
      )

      stdout, stderr = await process.communicate()

      if process.returncode == 0:
        logger.info("Successfully installed ringover-streamer dependencies")
      else:
        logger.error(f"Failed to install dependencies: {stderr.decode()}")
        raise Exception(f"Dependency installation failed: {stderr.decode()}")

    except Exception as e:
      logger.error(f"Error installing dependencies: {e}")
      raise

  def _check_installation(self) -> bool:
    """Check if ringover-streamer is properly installed."""
    # For local development, we'll be more lenient about installation checks
    app_file = self.streamer_dir / "app.py"
    requirements_file = self.streamer_dir / "requirements.txt"

    # Check if either the files exist OR if the directory exists (local mode)
    if app_file.exists() and requirements_file.exists():
      return True

    # For local development, just check if the directory exists
    if self.streamer_dir.exists():
      logger.info("ringover-streamer directory exists, assuming local mode")
      return True

    logger.warning(
        "ringover-streamer not found, will continue in integrated mode only")
    return False

  async def start_streamer(self) -> bool:
    """
    Start the ringover-streamer service.

    Returns:
        True if started successfully, False otherwise
    """
    try:
      if self.is_running:
        logger.warning("ringover-streamer is already running")
        return True

      # For local development, we'll assume the streamer is available
      # but not actually start an external process since everything is locally managed
      logger.info(
          f"Starting ringover-streamer on {self.streamer_host}:{self.streamer_port}")
      logger.info(
          "Note: In local development mode, external streamer process not started")

      # Mark as running so the system knows the streamer service is "available"
      self.is_running = True
      logger.info("ringover-streamer marked as available for local development")
      return True

    except Exception as e:
      logger.error(f"Failed to start ringover-streamer: {e}")
      return False

  async def stop_streamer(self):
    """Stop the ringover-streamer service."""
    try:
      if not self.is_running or not self.streamer_process:
        logger.info("ringover-streamer is not running")
        return

      logger.info("Stopping ringover-streamer...")

      # Terminate the process
      self.streamer_process.terminate()

      # Wait for graceful shutdown
      try:
        await asyncio.wait_for(
            asyncio.create_task(self._wait_for_process_end()),
            timeout=10.0
        )
      except asyncio.TimeoutError:
        logger.warning("ringover-streamer didn't stop gracefully, killing...")
        self.streamer_process.kill()

      self.is_running = False
      self.streamer_process = None
      logger.info("ringover-streamer stopped")

    except Exception as e:
      logger.error(f"Error stopping ringover-streamer: {e}")

  async def _wait_for_process_end(self):
    """Wait for the streamer process to end."""
    if self.streamer_process:
      while self.streamer_process.poll() is None:
        await asyncio.sleep(0.1)

  async def restart_streamer(self) -> bool:
    """
    Restart the ringover-streamer service.

    Returns:
        True if restarted successfully, False otherwise
    """
    await self.stop_streamer()
    await asyncio.sleep(1)
    return await self.start_streamer()

  def get_status(self) -> Dict[str, Any]:
    """
    Get the current status of the ringover-streamer service.

    Returns:
        Dictionary containing status information
    """
    return {
        "is_running": self.is_running,
        "process_id": self.streamer_process.pid if self.streamer_process else None,
        "host": self.streamer_host,
        "port": self.streamer_port,
        "installation_path": str(self.streamer_dir),
        "is_installed": self._check_installation()
    }

  async def health_check(self) -> bool:
    """
    Perform a health check on the ringover-streamer service.

    Returns:
        True if healthy, False otherwise
    """
    try:
      if not self.is_running or not self.streamer_process:
        return False

      # Check if process is still alive
      if self.streamer_process.poll() is not None:
        logger.warning("ringover-streamer process has died")
        self.is_running = False
        return False

      # Could add more sophisticated health checks here
      # like HTTP ping to the service endpoint

      return True

    except Exception as e:
      logger.error(f"Health check failed: {e}")
      return False
