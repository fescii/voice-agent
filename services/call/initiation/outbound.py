"""
Handles outbound call initiation sequence
"""
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from models.internal.callcontext import CallContext, CallResult, CallStatus, CallDirection
from models.external.ringover.apirequest import RingoverCallRequest
from services.ringover.client import RingoverClient
from services.call.state.updater import CallStateUpdater
from data.db.ops.call.create import create_call_log
from data.db.models.calllog import CallDirection as DBCallDirection
from data.db.connection import get_db_session
from core.config.registry import config_registry
from core.logging.setup import get_logger

logger = get_logger(__name__)


class OutboundCallService:
  """Service for handling outbound call initiation"""

  def __init__(self):
    self.ringover_client = RingoverClient()
    self.state_updater = CallStateUpdater()
    self.ringover_config = config_registry.ringover

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
      session_id = str(uuid.uuid4())

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
      async with get_db_session() as session:
        await create_call_log(
            session=session,
            call_id=call_id,
            agent_id=agent_id,
            caller_number=caller_id or self.ringover_config.default_caller_id,
            callee_number=phone_number,
            direction=DBCallDirection.OUTBOUND,
            metadata=context or {}
        )

      # Initialize call context
      call_context = CallContext(
          call_id=call_id,
          session_id=session_id,
          phone_number=phone_number,
          agent_id=agent_id,
          direction=CallDirection.OUTBOUND,
          status=CallStatus.INITIATED,
          start_time=datetime.now(timezone.utc),
          end_time=None,
          duration=None,
          ringover_call_id=None,
          websocket_id=None,
          metadata=context or {}
      )

      # Store call context in Redis
      await self.state_updater.create_call_session(call_context)

      # Initiate call through Ringover API
      ringover_response = await self.ringover_client.initiate_call(call_request)

      if "error" in ringover_response:
        logger.error(
            f"Ringover call initiation failed: {ringover_response.get('error')}")
        await self.state_updater.update_call_status(call_id, CallStatus.FAILED)
        raise Exception(
            f"Call initiation failed: {ringover_response.get('error')}")

      # Update call status with Ringover call ID if provided
      ringover_call_id = ringover_response.get(
          "call_id") or ringover_response.get("id")
      if ringover_call_id:
        # Update call context with Ringover call ID
        call_context.ringover_call_id = ringover_call_id
        await self.state_updater.create_call_session(call_context)

      logger.info(
          f"Successfully initiated call {call_id} via Ringover (ID: {ringover_call_id})")

      return CallResult(
          call_id=call_id,
          status=CallStatus.INITIATED,
          ringover_call_id=ringover_call_id,
          error_message=None
      )

    except Exception as e:
      logger.error(f"Failed to initiate outbound call: {str(e)}")
      if 'call_id' in locals():
        await self.state_updater.update_call_status(call_id, CallStatus.FAILED)
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
    async with get_db_session() as session:
      await create_call_log(
          session=session,
          call_id=call_id,
          agent_id=agent_id,
          caller_number=caller_id or self.ringover_config.default_caller_id,
          callee_number=phone_number,
          direction=DBCallDirection.OUTBOUND,
          scheduled_time=scheduled_time,
          metadata=context or {}
      )

    # TODO: Add to task queue for execution at scheduled time
    logger.info(f"Call {call_id} scheduled for {scheduled_time}")

    return call_id
