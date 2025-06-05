"""
Main WebSocket endpoint definition for FastAPI
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Optional
import asyncio
import json

from wss.connection.manager import ConnectionManager
from wss.connection.auth import authenticate_websocket
from wss.handlers.audio.receive import AudioReceiveHandler
from wss.handlers.audio.send import AudioSendHandler
from core.logging.setup import get_logger

logger = get_logger(__name__)

# Create WebSocket router
websocket_router = APIRouter()

# Connection manager instance
connection_manager = ConnectionManager()

@websocket_router.websocket("/audio/{call_id}")
async def websocket_audio_endpoint(
    websocket: WebSocket,
    call_id: str,
    token: Optional[str] = None
):
    """
    WebSocket endpoint for real-time audio streaming with Ringover
    
    Args:
        websocket: WebSocket connection
        call_id: Unique identifier for the call
        token: Optional authentication token
    """
    try:
        # Authenticate WebSocket connection
        auth_data = await authenticate_websocket(websocket, token)
        if not auth_data:
            await websocket.close(code=1008, reason="Authentication failed")
            return
        
        # Accept WebSocket connection
        await websocket.accept()
        logger.info(f"WebSocket connection established for call {call_id}")
        
        # Register connection
        connection_id = await connection_manager.connect(websocket, call_id, auth_data)
        
        # Initialize audio handlers
        receive_handler = AudioReceiveHandler(call_id, connection_id)
        send_handler = AudioSendHandler(call_id, connection_id, websocket)
        
        # Start audio send handler in background
        send_task = asyncio.create_task(send_handler.start())
        
        try:
            # Handle incoming audio data
            while True:
                # Receive data from WebSocket
                data = await websocket.receive()
                
                if data.get("type") == "websocket.receive":
                    if "bytes" in data:
                        # Handle binary audio data
                        await receive_handler.handle_audio_data(data["bytes"])
                    elif "text" in data:
                        # Handle control messages
                        message = json.loads(data["text"])
                        await receive_handler.handle_control_message(message)
                        
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for call {call_id}")
        except Exception as e:
            logger.error(f"Error in WebSocket handler for call {call_id}: {str(e)}")
            
    except Exception as e:
        logger.error(f"Failed to establish WebSocket connection for call {call_id}: {str(e)}")
        await websocket.close(code=1011, reason="Internal server error")
        
    finally:
        # Clean up connection
        if 'connection_id' in locals():
            await connection_manager.disconnect(connection_id)
            logger.info(f"WebSocket connection cleaned up for call {call_id}")
        
        # Cancel send task
        if 'send_task' in locals():
            send_task.cancel()
            try:
                await send_task
            except asyncio.CancelledError:
                pass


@websocket_router.websocket("/control/{call_id}")
async def websocket_control_endpoint(
    websocket: WebSocket,
    call_id: str,
    token: Optional[str] = None
):
    """
    WebSocket endpoint for call control messages
    
    Args:
        websocket: WebSocket connection
        call_id: Unique identifier for the call
        token: Optional authentication token
    """
    try:
        # Authenticate WebSocket connection
        auth_data = await authenticate_websocket(websocket, token)
        if not auth_data:
            await websocket.close(code=1008, reason="Authentication failed")
            return
        
        # Accept WebSocket connection
        await websocket.accept()
        logger.info(f"Control WebSocket connection established for call {call_id}")
        
        try:
            while True:
                # Receive control messages
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle control message
                await _handle_control_message(call_id, message, websocket)
                
        except WebSocketDisconnect:
            logger.info(f"Control WebSocket disconnected for call {call_id}")
        except Exception as e:
            logger.error(f"Error in control WebSocket for call {call_id}: {str(e)}")
            
    except Exception as e:
        logger.error(f"Failed to establish control WebSocket for call {call_id}: {str(e)}")
        await websocket.close(code=1011, reason="Internal server error")


async def _handle_control_message(call_id: str, message: Dict, websocket: WebSocket):
    """Handle control messages received over WebSocket"""
    message_type = message.get("type")
    
    if message_type == "ping":
        await websocket.send_json({"type": "pong", "timestamp": message.get("timestamp")})
    elif message_type == "mute":
        # Handle mute request
        logger.info(f"Mute request for call {call_id}: {message.get('muted')}")
        await websocket.send_json({"type": "mute_ack", "muted": message.get("muted")})
    elif message_type == "transfer":
        # Handle transfer request
        logger.info(f"Transfer request for call {call_id} to {message.get('target')}")
        await websocket.send_json({"type": "transfer_ack", "status": "initiated"})
    else:
        logger.warning(f"Unknown control message type: {message_type}")
        await websocket.send_json({"type": "error", "message": "Unknown message type"})
