"""
Integrated Ringover streamer service.
Provides WebSocket endpoints and streaming functionality within the main FastAPI app.
Also manages the external ringover-streamer process.
"""
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from core.logging.setup import get_logger
from .manager import RingoverStreamerManager

logger = get_logger(__name__)


class RingoverStreamerService:
  """
  Integrated Ringover streamer service that runs within the main FastAPI app.
  Provides WebSocket endpoints for Ringover media server connections.
  """

  def __init__(self):
    """Initialize the streamer service."""
    self.active_connections: Dict[str, WebSocket] = {}
    self.is_running = False
    self.streamer_manager: Optional[RingoverStreamerManager] = None

  def _ensure_streamer_manager(self) -> RingoverStreamerManager:
    """Ensure the streamer manager is initialized."""
    if self.streamer_manager is None:
      self.streamer_manager = RingoverStreamerManager()
    return self.streamer_manager

  async def initialize(self) -> Dict[str, Any]:
    """
    Initialize the streamer service.

    Returns:
        Dict containing service metadata
    """
    logger.info("Initializing integrated Ringover streamer service...")

    # Initialize the streamer manager
    streamer_manager = self._ensure_streamer_manager()

    # Start the external ringover-streamer process
    logger.info("🚀 Starting external ringover-streamer process...")
    streamer_started = await streamer_manager.start_streamer()

    if streamer_started:
      logger.info("✅ External ringover-streamer started successfully!")
    else:
      logger.warning(
          "⚠️  Failed to start external ringover-streamer, but continuing...")

    self.is_running = True

    metadata = {
        "service_type": "integrated_streamer",
        "active_connections": 0,
        "external_streamer_running": streamer_started,
        "external_streamer_host": streamer_manager.streamer_host,
        "external_streamer_port": streamer_manager.streamer_port,
        "status": "ready"
    }

    logger.info(
        "✅ Integrated Ringover streamer service initialized successfully")
    logger.info(
        f"🔗 External streamer available at: ws://{streamer_manager.streamer_host}:{streamer_manager.streamer_port}/ws")
    return metadata

  async def cleanup(self) -> None:
    """Clean up the streamer service."""
    logger.info("Cleaning up Ringover streamer service...")

    # Stop the external ringover-streamer process
    if self.streamer_manager and self.streamer_manager.is_running:
      logger.info("🛑 Stopping external ringover-streamer process...")
      await self.streamer_manager.stop_streamer()

    # Close all active connections
    for connection_id, websocket in list(self.active_connections.items()):
      try:
        await websocket.close()
      except Exception as e:
        logger.warning(f"Error closing connection {connection_id}: {e}")

    self.active_connections.clear()
    self.is_running = False
    logger.info("✅ Ringover streamer service cleanup completed")

  def get_health_status(self) -> Dict[str, Any]:
    """Get the current health status of the service."""
    status = {
        "status": "healthy" if self.is_running else "stopped",
        "active_connections": len(self.active_connections),
        "external_streamer_running": False,
        "external_streamer_port": 8000,  # default
        "timestamp": datetime.now().isoformat()
    }

    # Add streamer manager info if available
    if self.streamer_manager:
      status["external_streamer_running"] = self.streamer_manager.is_running
      status["external_streamer_port"] = self.streamer_manager.streamer_port

    return status

  async def handle_websocket_connection(self, websocket: WebSocket) -> None:
    """
    Handle a new WebSocket connection for Ringover media server.

    Args:
        websocket: The WebSocket connection
    """
    await websocket.accept()
    connection_id = f"conn_{len(self.active_connections)}_{datetime.now().timestamp()}"
    self.active_connections[connection_id] = websocket

    logger.info(
        f"New Ringover WebSocket connection established: {connection_id}")

    try:
      # Send welcome message
      await websocket.send_json({
          "event": "connected",
          "connection_id": connection_id,
          "timestamp": datetime.now().isoformat()
      })

      while True:
        # Receive messages from client
        data = await websocket.receive_text()

        try:
          message = json.loads(data)
          logger.debug(f"Received message on {connection_id}: {message}")

          # Handle different event types
          await self._handle_websocket_message(websocket, message)

        except json.JSONDecodeError:
          logger.warning(f"Invalid JSON received on {connection_id}: {data}")
          await websocket.send_json({
              "event": "error",
              "message": "Invalid JSON format"
          })

    except WebSocketDisconnect:
      logger.info(f"WebSocket connection closed normally: {connection_id}")
    except Exception as e:
      logger.error(f"WebSocket error on {connection_id}: {e}")
    finally:
      if connection_id in self.active_connections:
        del self.active_connections[connection_id]
      logger.info(f"WebSocket connection cleaned up: {connection_id}")

  async def _handle_websocket_message(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle incoming WebSocket messages."""
    event_type = message.get("event")

    if event_type == "call_start":
      await self._handle_call_start(websocket, message)
    elif event_type == "audio_data":
      await self._handle_audio_data(websocket, message)
    elif event_type == "play":
      await self._handle_play_audio(websocket, message)
    elif event_type == "call_end":
      await self._handle_call_end(websocket, message)
    else:
      logger.warning(f"Unknown event type: {event_type}")
      await websocket.send_json({
          "event": "error",
          "message": f"Unknown event type: {event_type}"
      })

  async def _handle_call_start(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle call start event."""
    call_id = message.get("call_id")
    logger.info(f"Starting call session: {call_id}")

    await websocket.send_json({
        "event": "call_started",
        "call_id": call_id,
        "status": "ready_for_audio"
    })

  async def _handle_audio_data(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle incoming audio data."""
    call_id = message.get("call_id")
    audio_data = message.get("data")  # Base64 encoded audio

    logger.debug(f"Received audio data for call {call_id}")

    # Simulate processing delay
    await asyncio.sleep(0.1)

    # Send acknowledgment
    await websocket.send_json({
        "event": "audio_received",
        "call_id": call_id,
        "timestamp": datetime.now().isoformat()
    })

  async def _handle_play_audio(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle play audio response."""
    file_url = message.get("file")
    call_id = message.get("call_id")

    logger.info(f"Playing audio file for call {call_id}: {file_url}")

    await websocket.send_json({
        "event": "audio_playing",
        "call_id": call_id,
        "file": file_url
    })

  async def _handle_call_end(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle call end event."""
    call_id = message.get("call_id")
    logger.info(f"Ending call session: {call_id}")

    await websocket.send_json({
        "event": "call_ended",
        "call_id": call_id
    })


# Global instance
ringover_streamer_service = RingoverStreamerService()
