"""
WebSocket endpoint for audio streaming
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Optional
import asyncio
import json
import uuid

from wss.connection import ConnectionManager, WebSocketConnection
from wss.handlers import WebSocketHandlers
from core.logging.setup import get_logger

logger = get_logger(__name__)

# Create WebSocket router
websocket_router = APIRouter()

# Global instances
connection_manager = ConnectionManager()
handlers = WebSocketHandlers()


class WebSocketManager:
  """Main WebSocket management class."""

  def __init__(self):
    self.connection_manager = connection_manager
    self.handlers = handlers

  async def handle_connection(self, websocket: WebSocket, call_id: str):
    """Handle a new WebSocket connection."""
    connection_id = str(uuid.uuid4())
    connection = WebSocketConnection(websocket, connection_id)

    try:
      await websocket.accept()
      await self.connection_manager.add_connection(connection_id, connection)
      logger.info(f"WebSocket connection established: {connection_id}")

      # Handle messages
      await self.handlers.handle_connection(connection)

    except WebSocketDisconnect:
      logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
      logger.error(f"WebSocket error: {e}")
    finally:
      await self.connection_manager.remove_connection(connection_id)


# Global manager instance
websocket_manager = WebSocketManager()


@websocket_router.websocket("/audio/{call_id}")
async def websocket_audio_endpoint(websocket: WebSocket, call_id: str):
  """WebSocket endpoint for audio streaming."""
  await websocket_manager.handle_connection(websocket, call_id)


@websocket_router.websocket("/agent/{agent_id}")
async def websocket_agent_endpoint(websocket: WebSocket, agent_id: str):
  """WebSocket endpoint for agent communication."""
  await websocket_manager.handle_connection(websocket, agent_id)
