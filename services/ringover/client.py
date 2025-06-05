"""
Ringover API client for call operations
"""
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

from core.config.providers.ringover import RingoverConfig
from models.external.ringover.apirequest import RingoverCallRequest
from core.logging.setup import get_logger

logger = get_logger(__name__)


class RingoverClient:
  """Client for interacting with Ringover API"""

  def __init__(self):
    self.config = RingoverConfig()
    self.base_url = self.config.api_base_url
    self.headers = {
        "Authorization": f"Bearer {self.config.api_key}",
        "Content-Type": "application/json"
    }

  async def initiate_call(self, request: RingoverCallRequest) -> Dict[str, Any]:
    """
    Initiate an outbound call through Ringover API

    Args:
        request: Call request parameters

    Returns:
        API response data
    """
    try:
      async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{self.base_url}/calls",
            json=request.dict(),
            headers=self.headers,
            timeout=30.0
        )

        if response.status_code == 200:
          logger.info(f"Call initiated successfully: {response.json()}")
          return response.json()
        else:
          logger.error(
              f"Failed to initiate call: {response.status_code} - {response.text}")
          return {"error": f"API call failed: {response.status_code}"}

    except Exception as e:
      logger.error(f"Error initiating call: {e}")
      return {"error": str(e)}

  async def terminate_call(self, call_id: str) -> Dict[str, Any]:
    """
    Terminate an ongoing call

    Args:
        call_id: The call identifier

    Returns:
        API response data
    """
    try:
      async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{self.base_url}/calls/{call_id}",
            headers=self.headers,
            timeout=30.0
        )

        if response.status_code == 200:
          logger.info(f"Call terminated successfully: {call_id}")
          return response.json()
        else:
          logger.error(
              f"Failed to terminate call {call_id}: {response.status_code}")
          return {"error": f"API call failed: {response.status_code}"}

    except Exception as e:
      logger.error(f"Error terminating call {call_id}: {e}")
      return {"error": str(e)}

  async def get_call_status(self, call_id: str) -> Dict[str, Any]:
    """
    Get status of a call

    Args:
        call_id: The call identifier

    Returns:
        Call status data
    """
    try:
      async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{self.base_url}/calls/{call_id}",
            headers=self.headers,
            timeout=30.0
        )

        if response.status_code == 200:
          return response.json()
        else:
          logger.error(
              f"Failed to get call status {call_id}: {response.status_code}")
          return {"error": f"API call failed: {response.status_code}"}

    except Exception as e:
      logger.error(f"Error getting call status {call_id}: {e}")
      return {"error": str(e)}

  async def transfer_call(self, call_id: str, target_number: str) -> Dict[str, Any]:
    """
    Transfer a call to another number

    Args:
        call_id: The call identifier
        target_number: Number to transfer to

    Returns:
        API response data
    """
    try:
      async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{self.base_url}/calls/{call_id}/transfer",
            json={"target": target_number},
            headers=self.headers,
            timeout=30.0
        )

        if response.status_code == 200:
          logger.info(f"Call {call_id} transferred to {target_number}")
          return response.json()
        else:
          logger.error(
              f"Failed to transfer call {call_id}: {response.status_code}")
          return {"error": f"API call failed: {response.status_code}"}

    except Exception as e:
      logger.error(f"Error transferring call {call_id}: {e}")
      return {"error": str(e)}
