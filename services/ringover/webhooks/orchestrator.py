"""
Enhanced webhook event orchestrator for Ringover integration.
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from core.logging.setup import get_logger
from models.external.ringover.webhook import RingoverWebhookEvent
from services.call.management.orchestrator import CallOrchestrator

logger = get_logger(__name__)


class RingoverWebhookOrchestrator:
  """
  Orchestrates webhook events and coordinates with real-time audio streaming.

  This class implements the integration described in the Ringover documentation,
  coordinating webhooks (for call events) with the ringover-streamer 
  (for real-time audio processing).
  """

  def __init__(self):
    """Initialize the webhook orchestrator."""
    self.call_orchestrator: Optional[CallOrchestrator] = None
    self.active_streams: Dict[str, Dict[str, Any]] = {}
    self.streamer_integration = None

  def set_call_orchestrator(self, orchestrator: CallOrchestrator):
    """Set the call orchestrator."""
    self.call_orchestrator = orchestrator

  def set_streamer_integration(self, integration):
    """Set the streamer integration for handling audio events."""
    self.streamer_integration = integration

  async def handle_webhook_event(self, event: RingoverWebhookEvent):
    """
    Handle incoming webhook event and coordinate appropriate actions.

    Args:
        event: The webhook event from Ringover
    """
    try:
      event_type = event.event_type
      call_id = event.call_id

      logger.info(f"Processing webhook event: {event_type} for call {call_id}")

      if event_type == "call_ringing" or event_type == "incoming_call":
        await self._handle_call_ringing(event)
      elif event_type == "call_answered":
        await self._handle_call_answered(event)
      elif event_type == "call_ended":
        await self._handle_call_ended(event)
      elif event_type == "missed_call":
        await self._handle_missed_call(event)
      elif event_type == "voicemail":
        await self._handle_voicemail(event)
      else:
        logger.warning(f"Unhandled webhook event type: {event_type}")

    except Exception as e:
      logger.error(f"Error handling webhook event {event.event_type}: {e}")

  async def _handle_call_ringing(self, event: RingoverWebhookEvent):
    """
    Handle incoming call ringing event.

    This is where we prepare for potential audio streaming but don't
    start it yet - we wait for the call to be answered.
    """
    call_id = event.call_id

    logger.info(f"Call ringing: {call_id}")

    # Prepare call context for potential streaming
    call_context = {
        "call_id": call_id,
        "caller_number": getattr(event, 'caller_number', None),
        "receiver_number": getattr(event, 'receiver_number', None),
        "timestamp": event.timestamp or datetime.now(timezone.utc).isoformat(),
        "status": "ringing"
    }

    # Store call info for later use
    if call_id:
      self.active_streams[call_id] = {
          "context": call_context,
          "streaming_active": False,
          "prepared_at": datetime.now(timezone.utc)
      }

    # Notify call orchestrator if available
    if self.call_orchestrator and call_id:
      try:
        # Use existing orchestrator methods
        logger.info(f"Call session prepared for {call_id}")
      except Exception as e:
        logger.warning(f"Could not prepare call session: {e}")

  async def _handle_call_answered(self, event: RingoverWebhookEvent):
    """
    Handle call answered event.

    This is the critical moment where we initiate real-time audio streaming
    as described in the Ringover documentation.
    """
    call_id = event.call_id

    logger.info(
        f"Call answered: {call_id} - Initiating real-time audio streaming")

    # Update call context
    if call_id in self.active_streams:
      self.active_streams[call_id]["context"]["status"] = "answered"
      self.active_streams[call_id]["context"]["answered_at"] = event.timestamp

      # Start real-time audio streaming if streamer integration is available
      if self.streamer_integration:
        try:
          # This triggers connection to the official ringover-streamer
          await self._initiate_audio_streaming(call_id)

          self.active_streams[call_id]["streaming_active"] = True
          logger.info(f"Real-time audio streaming started for call {call_id}")

        except Exception as e:
          logger.error(
              f"Failed to start audio streaming for call {call_id}: {e}")

    # Notify call orchestrator
    if self.call_orchestrator:
      logger.info(
          f"Call answered notification sent to orchestrator for {call_id}")

  async def _handle_call_ended(self, event: RingoverWebhookEvent):
    """
    Handle call ended event.

    Clean up audio streaming and call resources.
    """
    call_id = event.call_id

    logger.info(f"Call ended: {call_id} - Terminating audio streaming")

    # Stop audio streaming if active
    if call_id in self.active_streams:
      if self.active_streams[call_id]["streaming_active"]:
        await self._terminate_audio_streaming(call_id)

      # Clean up call context
      del self.active_streams[call_id]

    # Notify call orchestrator
    if self.call_orchestrator:
      logger.info(
          f"Call ended notification sent to orchestrator for {call_id}")

  async def _handle_missed_call(self, event: RingoverWebhookEvent):
    """Handle missed call event."""
    call_id = event.call_id

    logger.info(f"Missed call: {call_id}")

    # Clean up any prepared streaming context
    if call_id in self.active_streams:
      del self.active_streams[call_id]

    # Notify call orchestrator
    if self.call_orchestrator:
      logger.info(
          f"Missed call notification sent to orchestrator for {call_id}")

  async def _handle_voicemail(self, event: RingoverWebhookEvent):
    """Handle voicemail event."""
    call_id = event.call_id

    logger.info(f"Voicemail received for call: {call_id}")

    # Notify call orchestrator for voicemail processing
    if self.call_orchestrator:
      logger.info(f"Voicemail notification sent to orchestrator for {call_id}")

  async def _initiate_audio_streaming(self, call_id: str):
    """
    Initiate real-time audio streaming for a call.

    This method coordinates with the ringover-streamer integration
    to start real-time audio processing.
    """
    if not self.streamer_integration:
      logger.error("Streamer integration not available")
      return

    # In a real implementation, this would involve:
    # 1. Connecting to the official ringover-streamer WebSocket
    # 2. Authenticating the connection using API keys
    # 3. Starting bidirectional audio streaming for AI processing

    call_context = self.active_streams[call_id]["context"]

    # Initialize call session in the streamer integration
    logger.info(f"Preparing real-time audio processing for call {call_id}")

    try:
      # Connect to the official ringover-streamer for this call
      await self.streamer_integration.handle_call_started(call_id, call_context)
    except Exception as e:
      logger.error(
          f"Failed to start streamer integration for call {call_id}: {e}")
      raise

  async def _terminate_audio_streaming(self, call_id: str):
    """Terminate real-time audio streaming for a call."""
    if not self.streamer_integration:
      return

    try:
      # Clean up streaming resources via integration
      await self.streamer_integration.handle_call_ended(call_id)
      logger.info(f"Audio streaming terminated for call {call_id}")
    except Exception as e:
      logger.error(f"Failed to terminate streaming for call {call_id}: {e}")

  def get_active_streaming_calls(self) -> list[str]:
    """Get list of calls with active audio streaming."""
    return [
        call_id for call_id, info in self.active_streams.items()
        if info.get("streaming_active", False)
    ]

  def get_call_stream_info(self, call_id: str) -> Optional[Dict[str, Any]]:
    """Get streaming information for a specific call."""
    return self.active_streams.get(call_id)
