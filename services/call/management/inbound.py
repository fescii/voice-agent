"""
Inbound call handling service.
"""
from typing import Dict, Any, Optional
from datetime import datetime

from ...data.db.ops.call import create_call_log, update_call_status
from ...data.db.ops.agent import get_active_agents, update_agent_call_count
from ...data.redis.ops.session import store_call_session
from ...models.external.ringover.webhook import RingoverWebhookEvent
from ...models.internal.callcontext import CallContext
from ...core.logging import get_logger

logger = get_logger(__name__)


class InboundCallService:
  """Service for handling inbound call logic."""

  def __init__(self):
    self.logger = logger

  async def handle_incoming_call(
      self,
      webhook_event: RingoverWebhookEvent,
      session
  ) -> Optional[CallContext]:
    """
    Handle incoming call webhook from Ringover.

    Args:
        webhook_event: Ringover webhook event
        session: Database session

    Returns:
        CallContext if call accepted, None otherwise
    """
    try:
      # Extract call details
      caller_number = webhook_event.caller_number
      callee_number = webhook_event.callee_number
      ringover_call_id = webhook_event.call_id

      # Find available agent
      agent = await self._find_available_agent(session)
      if not agent:
        self.logger.warning(
            f"No available agent for incoming call {ringover_call_id}")
        return None

      # Generate internal call ID
      call_id = f"inbound_{ringover_call_id}_{int(datetime.utcnow().timestamp())}"

      # Create call log
      call_log = await create_call_log(
          session=session,
          call_id=call_id,
          agent_id=agent.agent_id,
          caller_number=caller_number,
          callee_number=callee_number,
          direction="inbound",
          ringover_call_id=ringover_call_id
      )

      if not call_log:
        self.logger.error(f"Failed to create call log for {call_id}")
        return None

      # Create call context
      call_context = CallContext(
          call_id=call_id,
          ringover_call_id=ringover_call_id,
          agent_id=agent.agent_id,
          caller_number=caller_number,
          callee_number=callee_number,
          direction="inbound",
          status="initiated",
          agent_config=agent
      )

      # Store session in Redis
      await store_call_session(
          call_id=call_id,
          session_data=call_context.dict()
      )

      # Update agent call count
      await update_agent_call_count(session, agent.agent_id, increment=1)

      self.logger.info(f"Initiated inbound call handling: {call_id}")
      return call_context

    except Exception as e:
      self.logger.error(f"Failed to handle incoming call: {e}")
      return None

  async def _find_available_agent(self, session) -> Optional[Any]:
    """
    Find an available agent for the call.

    Args:
        session: Database session

    Returns:
        Available agent config or None
    """
    try:
      active_agents = await get_active_agents(session)

      for agent in active_agents:
        if agent.current_call_count < agent.max_concurrent_calls:
          return agent

      return None

    except Exception as e:
      self.logger.error(f"Failed to find available agent: {e}")
      return None
