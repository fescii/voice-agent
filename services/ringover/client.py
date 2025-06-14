"""
Ringover API client for call operations
"""
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from core.config.registry import config_registry
from models.external.ringover.apirequest import RingoverCallRequest
from core.logging.setup import get_logger

logger = get_logger(__name__)


class RingoverClient:
  """Client for interacting with Ringover API"""

  def __init__(self):
    self.config = config_registry.ringover
    self.base_url = self.config.api_base_url
    self.headers = {
        "Authorization": self.config.api_key,
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
            f"{self.base_url}/callback",
            json=request.model_dump(exclude_none=True),
            headers=self.headers,
            timeout=30.0
        )

        if response.status_code == 200:
          logger.info(f"Call initiated successfully: {response.json()}")
          return response.json()
        elif response.status_code == 401:
          error_msg = "Unauthorized - check API key and permissions"
          logger.error(error_msg)
          raise Exception(error_msg)
        elif response.status_code == 400:
          error_msg = f"Bad request - invalid call parameters: {response.text}"
          logger.error(error_msg)
          raise Exception(error_msg)
        else:
          error_msg = f"API call failed: {response.status_code} - {response.text}"
          logger.error(error_msg)
          raise Exception(error_msg)

    except httpx.RequestError as e:
      error_msg = f"Network error initiating call: {e}"
      logger.error(error_msg)
      raise Exception(error_msg)
    except Exception as e:
      if "API call failed" in str(e) or "Unauthorized" in str(e) or "Bad request" in str(e):
        raise  # Re-raise API errors as-is
      error_msg = f"Error initiating call: {e}"
      logger.error(error_msg)
      raise Exception(error_msg)

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
        elif response.status_code == 404:
          error_msg = f"Call not found: {call_id}"
          logger.error(error_msg)
          raise Exception(error_msg)
        elif response.status_code == 401:
          error_msg = "Unauthorized - check API key and permissions"
          logger.error(error_msg)
          raise Exception(error_msg)
        else:
          error_msg = f"API call failed: {response.status_code} - {response.text}"
          logger.error(error_msg)
          raise Exception(error_msg)

    except httpx.RequestError as e:
      error_msg = f"Network error terminating call: {e}"
      logger.error(error_msg)
      raise Exception(error_msg)
    except Exception as e:
      if "API call failed" in str(e) or "Unauthorized" in str(e) or "Call not found" in str(e):
        raise  # Re-raise API errors as-is
      error_msg = f"Error terminating call {call_id}: {e}"
      logger.error(error_msg)
      raise Exception(error_msg)

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
        elif response.status_code == 404:
          error_msg = f"Call not found: {call_id}"
          logger.error(error_msg)
          raise Exception(error_msg)
        elif response.status_code == 401:
          error_msg = "Unauthorized - check API key and permissions"
          logger.error(error_msg)
          raise Exception(error_msg)
        else:
          error_msg = f"API call failed: {response.status_code} - {response.text}"
          logger.error(error_msg)
          raise Exception(error_msg)

    except httpx.RequestError as e:
      error_msg = f"Network error getting call status: {e}"
      logger.error(error_msg)
      raise Exception(error_msg)
    except Exception as e:
      if "API call failed" in str(e) or "Unauthorized" in str(e) or "Call not found" in str(e):
        raise  # Re-raise API errors as-is
      error_msg = f"Error getting call status {call_id}: {e}"
      logger.error(error_msg)
      raise Exception(error_msg)

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
        elif response.status_code == 404:
          error_msg = f"Call not found: {call_id}"
          logger.error(error_msg)
          raise Exception(error_msg)
        elif response.status_code == 401:
          error_msg = "Unauthorized - check API key and permissions"
          logger.error(error_msg)
          raise Exception(error_msg)
        elif response.status_code == 400:
          error_msg = f"Bad request - invalid transfer parameters: {response.text}"
          logger.error(error_msg)
          raise Exception(error_msg)
        else:
          error_msg = f"API call failed: {response.status_code} - {response.text}"
          logger.error(error_msg)
          raise Exception(error_msg)

    except httpx.RequestError as e:
      error_msg = f"Network error transferring call: {e}"
      logger.error(error_msg)
      raise Exception(error_msg)
    except Exception as e:
      if "API call failed" in str(e) or "Unauthorized" in str(e) or "Call not found" in str(e) or "Bad request" in str(e):
        raise  # Re-raise API errors as-is
      error_msg = f"Error transferring call {call_id}: {e}"
      logger.error(error_msg)
      raise Exception(error_msg)

  async def list_calls(self, limit: int = 50, offset: int = 0,
                       start_date: Optional[str] = None, end_date: Optional[str] = None,
                       call_type: Optional[str] = None) -> Dict[str, Any]:
    """
    List calls from the Ringover API using GET method

    Args:
        limit: Maximum number of calls to retrieve (default 50, max 1000)
        offset: Number of calls to skip (default 0, max 9000)
        start_date: Filter start date (ISO format, e.g., "2020-06-27T00:00:00.53Z")
        end_date: Filter end date (ISO format, must be used with start_date)
        call_type: Filter by call type ("ANSWERED", "MISSED", "OUT", "VOICEMAIL")

    Returns:
        API response data with calls list

    Raises:
        Exception: If API call fails
    """
    try:
      # Build query parameters
      params: Dict[str, Any] = {"limit_count": min(
          limit, 1000), "limit_offset": min(offset, 9000)}

      if start_date and end_date:
        params["start_date"] = start_date
        params["end_date"] = end_date

      if call_type:
        params["call_type"] = call_type

      async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{self.base_url}/calls",
            headers=self.headers,
            params=params,
            timeout=30.0
        )

        if response.status_code == 200:
          logger.info("Calls retrieved successfully")
          return response.json()
        elif response.status_code == 204:
          logger.info("No calls found")
          return {"call_list": [], "call_list_count": 0}
        elif response.status_code == 401:
          error_msg = "Unauthorized - check API key and permissions"
          logger.error(error_msg)
          raise Exception(error_msg)
        elif response.status_code == 400:
          error_msg = f"Bad request - invalid parameters: {response.text}"
          logger.error(error_msg)
          raise Exception(error_msg)
        else:
          error_msg = f"API call failed: {response.status_code} - {response.text}"
          logger.error(error_msg)
          raise Exception(error_msg)

    except httpx.RequestError as e:
      error_msg = f"Network error listing calls: {e}"
      logger.error(error_msg)
      raise Exception(error_msg)
    except Exception as e:
      if "API call failed" in str(e) or "Unauthorized" in str(e) or "Bad request" in str(e):
        raise  # Re-raise API errors as-is
      error_msg = f"Error listing calls: {e}"
      logger.error(error_msg)
      raise Exception(error_msg)

  async def get_current_calls(self, status_filter: Optional[list] = None,
                              interface_filter: Optional[list] = None,
                              direction_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Get currently active calls using POST method with filters

    Args:
        status_filter: Filter by call status (e.g., ["ANSWERED", "RINGING"])
        interface_filter: Filter by interface (e.g., ["SIP", "MOBILE"])
        direction_filter: Filter by direction ("IN" or "OUT")

    Returns:
        API response data with current calls

    Raises:
        Exception: If API call fails
    """
    try:
      # Build the filter object according to OpenAPI spec
      filter_data = {}
      if status_filter:
        filter_data["status"] = status_filter
      if interface_filter:
        filter_data["interface"] = interface_filter
      if direction_filter:
        filter_data["direction"] = direction_filter

      async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{self.base_url}/calls/current",
            json=filter_data,
            headers=self.headers,
            timeout=30.0
        )

        if response.status_code == 200:
          logger.info("Current calls retrieved successfully")
          return response.json()
        elif response.status_code == 204:
          logger.info("No current calls found")
          return {"current_calls_list": [], "current_calls_list_count": 0}
        elif response.status_code == 401:
          error_msg = "Unauthorized - check API key and permissions"
          logger.error(error_msg)
          raise Exception(error_msg)
        elif response.status_code == 400:
          error_msg = f"Bad request - invalid filter parameters: {response.text}"
          logger.error(error_msg)
          raise Exception(error_msg)
        else:
          error_msg = f"API call failed: {response.status_code} - {response.text}"
          logger.error(error_msg)
          raise Exception(error_msg)

    except httpx.RequestError as e:
      error_msg = f"Network error getting current calls: {e}"
      logger.error(error_msg)
      raise Exception(error_msg)
    except Exception as e:
      if "API call failed" in str(e) or "Unauthorized" in str(e) or "Bad request" in str(e):
        raise  # Re-raise API errors as-is
      error_msg = f"Error getting current calls: {e}"
      logger.error(error_msg)
      raise Exception(error_msg)
