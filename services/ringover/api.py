"""
Ringover API client implementation.
"""
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
import json
from dataclasses import dataclass
from enum import Enum

from core.logging.setup import get_logger
from core.config.registry import config_registry

logger = get_logger(__name__)


class CallDirection(Enum):
  """Call direction enumeration."""
  INBOUND = "inbound"
  OUTBOUND = "outbound"


class CallStatus(Enum):
  """Call status enumeration."""
  RINGING = "ringing"
  ANSWERED = "answered"
  ENDED = "ended"
  BUSY = "busy"
  NO_ANSWER = "no_answer"
  FAILED = "failed"


@dataclass
class CallInfo:
  """Call information data structure."""
  call_id: str
  phone_number: str
  direction: CallDirection
  status: CallStatus
  agent_number: Optional[str] = None
  start_time: Optional[str] = None
  duration: Optional[int] = None
  metadata: Optional[Dict[str, Any]] = None


class RingoverAPIClient:
  """
  Ringover API client for call management and control.

  Handles authentication, call initiation, call control,
  and webhook event processing.
  """

  def __init__(self):
    """
    Initialize Ringover API client.
    Uses the centralized config registry for configuration.
    """
    self.config = config_registry.ringover
    self.session: Optional[aiohttp.ClientSession] = None
    self.headers = {
        "Authorization": f"Bearer {self.config.api_key}",
        "Content-Type": "application/json"
    }

  async def __aenter__(self):
    """Async context manager entry."""
    self.session = aiohttp.ClientSession(
        base_url=self.config.api_base_url,
        headers=self.headers,
        timeout=aiohttp.ClientTimeout(total=30)
    )
    return self

  async def __aexit__(self, exc_type, exc_val, exc_tb):
    """Async context manager exit."""
    if self.session:
      await self.session.close()

  async def initiate_outbound_call(self,
                                   to_number: str,
                                   from_number: str,
                                   agent_id: str,
                                   metadata: Optional[Dict[str, Any]] = None) -> Optional[CallInfo]:
    """
    Initiate an outbound call.

    Args:
        to_number: Target phone number
        from_number: Ringover number to use as caller ID
        agent_id: ID of the agent making the call
        metadata: Additional call metadata

    Returns:
        Call information if successful, None otherwise
    """
    if not self.session:
      logger.error("API client session not initialized")
      return None

    payload = {
        "to": to_number,
        "from": from_number,
        "agent_id": agent_id,
        "webhook_url": f"{self.config.api_base_url}/webhooks/ringover",
        "metadata": metadata or {}
    }

    try:
      async with self.session.post("/v1/calls", json=payload) as response:
        if response.status == 201:
          data = await response.json()
          return CallInfo(
              call_id=data.get("call_id"),
              phone_number=to_number,
              direction=CallDirection.OUTBOUND,
              status=CallStatus.RINGING,
              agent_number=from_number,
              metadata=metadata
          )
        else:
          error_text = await response.text()
          logger.error(
              f"Failed to initiate call: {response.status} - {error_text}")
          return None

    except Exception as e:
      logger.error(f"Exception during call initiation: {e}")
      return None

  async def answer_call(self, call_id: str, agent_id: str) -> bool:
    """
    Answer an incoming call.

    Args:
        call_id: ID of the call to answer
        agent_id: ID of the agent answering

    Returns:
        True if successful, False otherwise
    """
    if not self.session:
      logger.error("API client session not initialized")
      return False

    payload = {
        "agent_id": agent_id,
        "action": "answer"
    }

    try:
      async with self.session.post(f"/v1/calls/{call_id}/control", json=payload) as response:
        return response.status == 200
    except Exception as e:
      logger.error(f"Exception during call answer: {e}")
      return False

  async def hang_up_call(self, call_id: str) -> bool:
    """
    Hang up a call.

    Args:
        call_id: ID of the call to hang up

    Returns:
        True if successful, False otherwise
    """
    if not self.session:
      logger.error("API client session not initialized")
      return False

    payload = {"action": "hangup"}

    try:
      async with self.session.post(f"/v1/calls/{call_id}/control", json=payload) as response:
        return response.status == 200
    except Exception as e:
      logger.error(f"Exception during call hangup: {e}")
      return False

  async def get_call_info(self, call_id: str) -> Optional[CallInfo]:
    """
    Get information about a call.

    Args:
        call_id: ID of the call

    Returns:
        Call information if found, None otherwise
    """
    if not self.session:
      logger.error("API client session not initialized")
      return None

    try:
      async with self.session.get(f"/v1/calls/{call_id}") as response:
        if response.status == 200:
          data = await response.json()
          return CallInfo(
              call_id=data.get("call_id"),
              phone_number=data.get("phone_number"),
              direction=CallDirection(data.get("direction", "inbound")),
              status=CallStatus(data.get("status", "ringing")),
              agent_number=data.get("agent_number"),
              start_time=data.get("start_time"),
              duration=data.get("duration"),
              metadata=data.get("metadata", {})
          )
        else:
          logger.warning(f"Call not found: {call_id}")
          return None
    except Exception as e:
      logger.error(f"Exception during call info retrieval: {e}")
      return None

  async def list_active_calls(self, agent_id: Optional[str] = None) -> List[CallInfo]:
    """
    List active calls for an agent or all agents.

    Args:
        agent_id: Optional agent ID filter

    Returns:
        List of active calls
    """
    if not self.session:
      logger.error("API client session not initialized")
      return []

    params = {"status": "active"}
    if agent_id:
      params["agent_id"] = agent_id

    try:
      async with self.session.get("/v1/calls", params=params) as response:
        if response.status == 200:
          data = await response.json()
          return [
              CallInfo(
                  call_id=call.get("call_id"),
                  phone_number=call.get("phone_number"),
                  direction=CallDirection(call.get("direction", "inbound")),
                  status=CallStatus(call.get("status", "ringing")),
                  agent_number=call.get("agent_number"),
                  start_time=call.get("start_time"),
                  duration=call.get("duration"),
                  metadata=call.get("metadata", {})
              )
              for call in data.get("calls", [])
          ]
        else:
          logger.warning(f"Failed to list calls: {response.status}")
          return []
    except Exception as e:
      logger.error(f"Exception during call listing: {e}")
      return []
