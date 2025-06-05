"""
Handles outbound call initiation sequence
"""
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from models.internal.callcontext import CallContext, CallResult
from models.external.ringover.apirequest import RingoverCallRequest
from services.ringover.client import RingoverClient
from services.call.state.updater import CallStateUpdater
from data.db.ops.call.create import create_call_record
from core.config.providers.ringover import RingoverConfig
from core.logging.setup import get_logger

logger = get_logger(__name__)


class OutboundCallService:
  """Service for handling outbound call initiation"""

  def __init__(self):
    self.ringover_client = RingoverClient()
    self.state_updater = CallStateUpdater()
    self.ringover_config = RingoverConfig()

  async def initiate_call(
      self,
      phone_number: str,
      agent_id: str,
      caller_id: Optional[str] = None,
      context: Optional[Dict[str, Any]] = None
  ) -> CallResult:
    """
    Initiate an outbound call through Ringover

    Args:
        phone_number: Target phone number to call
        agent_id: ID of the agent to handle the call
        caller_id: Optional caller ID to display
        context: Additional context for the call

    Returns:
        CallResult with call ID and initial status

    Raises:
        Exception: If call initiation fails
    """
    try:
      # Generate unique call ID
      call_id = str(uuid.uuid4())

      logger.info(
          f"Initiating outbound call {call_id} to {phone_number} with agent {agent_id}")

      # Prepare call request
      call_request = RingoverCallRequest(
          call_id=call_id,
          from_number=caller_id or self.ringover_config.default_caller_id,
          to_number=phone_number,
          agent_id=agent_id,
          context=context or {}
      )

      # Create initial call record in database
      await create_call_record(
          call_id=call_id,
          phone_number=phone_number,
          agent_id=agent_id,
          direction="outbound",
          status="initiated",
          metadata=context or {}
      )

      # Initialize call state in Redis
      call_context = CallContext(
          call_id=call_id,
          phone_number=phone_number,
          agent_id=agent_id,
          direction="outbound",
          status="initiated",
          start_time=datetime.utcnow(),
          metadata=context or {}
      )

      await self.state_updater.store_call_context(call_context)

      # Initiate call through Ringover API
      ringover_response = await self.ringover_client.initiate_call(call_request)

      if not ringover_response.success:
        logger.error(
            f"Ringover call initiation failed: {ringover_response.error}")
        await self.state_updater.update_call_status(call_id, "failed")
        raise Exception(f"Call initiation failed: {ringover_response.error}")

      # Update call state with Ringover call ID
      await self.state_updater.update_call_metadata(
          call_id,
          {"ringover_call_id": ringover_response.ringover_call_id}
      )

      logger.info(
          f"Successfully initiated call {call_id} via Ringover (ID: {ringover_response.ringover_call_id})")

      return CallResult(
          call_id=call_id,
          status="initiated",
          ringover_call_id=ringover_response.ringover_call_id
      )

    except Exception as e:
      logger.error(f"Failed to initiate outbound call: {str(e)}")
      if 'call_id' in locals():
        await self.state_updater.update_call_status(call_id, "failed")
      raise

  async def schedule_call(
      self,
      phone_number: str,
      agent_id: str,
      scheduled_time: datetime,
      caller_id: Optional[str] = None,
      context: Optional[Dict[str, Any]] = None
  ) -> str:
    """
    Schedule an outbound call for later execution

    Args:
        phone_number: Target phone number to call
        agent_id: ID of the agent to handle the call
        scheduled_time: When to make the call
        caller_id: Optional caller ID to display
        context: Additional context for the call

    Returns:
        Scheduled call ID
    """
    # Generate unique call ID for scheduling
    call_id = str(uuid.uuid4())

    logger.info(
        f"Scheduling outbound call {call_id} to {phone_number} for {scheduled_time}")

    # Store scheduled call in database
    await create_call_record(
        call_id=call_id,
        phone_number=phone_number,
        agent_id=agent_id,
        direction="outbound",
        status="scheduled",
        scheduled_time=scheduled_time,
        metadata=context or {}
    )

    # TODO: Add to task queue for execution at scheduled time
    logger.info(f"Call {call_id} scheduled for {scheduled_time}")

    return call_id
