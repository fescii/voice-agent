"""
Agent status endpoint
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, List

from api.v1.schemas.response.agent import AgentStatusResponse
from services.agent.assignment.router import AgentRouter
from api.dependencies.auth import get_current_user
from core.logging.setup import get_logger
from core.config.response import GenericResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get("/{agent_id}/status", response_model=GenericResponse[AgentStatusResponse])
async def get_agent_status(
    agent_id: str,
    current_user: Any = Depends(get_current_user)
) -> GenericResponse[AgentStatusResponse]:
  """
  Get the current status of an agent

  Args:
      agent_id: The unique identifier of the agent
      current_user: Authenticated user

  Returns:
      Agent status information

  Raises:
      HTTPException: If agent not found
  """
  try:
    logger.info(f"Getting status for agent {agent_id} for user {current_user}")

    agent_router = AgentRouter()
    agent_status = await agent_router.get_agent_status(agent_id)

    if not agent_status:
      return GenericResponse.error(f"Agent {agent_id} not found", status.HTTP_404_NOT_FOUND)

    logger.info(
        f"Retrieved status for agent {agent_id}: {agent_status['status']}")

    agent_status_response = AgentStatusResponse(
        agent_id=agent_id,
        name=agent_status["name"],
        active=agent_status["active"],
        current_calls=agent_status["current_calls"],
        max_calls=agent_status["max_calls"],
        status=agent_status["status"],
        last_activity=agent_status["last_activity"]
    )

    return GenericResponse.ok(agent_status_response)

  except Exception as e:
    logger.error(f"Failed to get status for agent {agent_id}: {str(e)}")
    return GenericResponse.error(f"Failed to get agent status: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/", response_model=GenericResponse[List[AgentStatusResponse]])
async def list_agent_statuses(
    current_user: Any = Depends(get_current_user)
) -> GenericResponse[List[AgentStatusResponse]]:
  """
  List all agent statuses

  Args:
      current_user: Authenticated user

  Returns:
      List of agent statuses
  """
  try:
    logger.info(f"Listing all agent statuses for user {current_user}")

    agent_router = AgentRouter()
    agents = await agent_router.get_all_agent_statuses()

    result = []
    for agent in agents:
      result.append(AgentStatusResponse(
          agent_id=agent["agent_id"],
          name=agent["name"],
          active=agent["active"],
          current_calls=agent["current_calls"],
          max_calls=agent["max_calls"],
          status=agent["status"],
          last_activity=agent["last_activity"]
      ))

    logger.info(f"Retrieved {len(result)} agent statuses")
    return GenericResponse.ok(result)

  except Exception as e:
    logger.error(f"Failed to list agent statuses: {str(e)}")
    return GenericResponse.error(f"Failed to list agent statuses: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)
