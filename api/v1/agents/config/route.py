"""
Agent configuration management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, List, Dict
from datetime import datetime, timezone

from api.v1.schemas.request.agent import AgentConfigUpdateRequest, AgentConfigCreateRequest
from api.v1.schemas.response.agent import AgentConfigResponse
from services.agent.profile.loader import AgentProfileLoader
from data.db.models.agentconfig import AgentConfig
from api.dependencies.auth import get_current_user
from core.logging.setup import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/{agent_id}", response_model=AgentConfigResponse)
async def get_agent_config(
    agent_id: str,
    current_user: Any = Depends(get_current_user)
) -> AgentConfigResponse:
  """
  Get configuration for a specific agent

  Args:
      agent_id: The unique identifier of the agent
      current_user: Authenticated user

  Returns:
      Agent configuration data

  Raises:
      HTTPException: If agent not found
  """
  try:
    logger.info(f"Getting config for agent {agent_id} for user {current_user}")

    loader = AgentProfileLoader()
    agent_config = await loader.get_agent_config(agent_id)

    if not agent_config:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"Agent {agent_id} not found"
      )

    logger.info(f"Retrieved config for agent {agent_id}")

    return _agent_config_to_response(agent_config)

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Failed to get config for agent {agent_id}: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to get agent config: {str(e)}"
    )


@router.get("/", response_model=List[AgentConfigResponse])
async def list_agent_configs(
    current_user: Any = Depends(get_current_user)
) -> List[AgentConfigResponse]:
  """
  List all agent configurations

  Args:
      current_user: Authenticated user

  Returns:
      List of agent configurations
  """
  try:
    logger.info(f"Listing all agent configs for user {current_user}")

    loader = AgentProfileLoader()
    agents = await loader.get_all_agent_configs()

    result = []
    for agent in agents:
      result.append(_agent_config_to_response(agent))

    logger.info(f"Retrieved {len(result)} agent configs")
    return result

  except Exception as e:
    logger.error(f"Failed to list agent configs: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to list agent configs: {str(e)}"
    )


@router.put("/{agent_id}", response_model=AgentConfigResponse)
async def update_agent_config(
    agent_id: str,
    request: AgentConfigUpdateRequest,
    current_user: Any = Depends(get_current_user)
) -> AgentConfigResponse:
  """
  Update configuration for a specific agent

  Args:
      agent_id: The unique identifier of the agent
      request: Agent configuration update data
      current_user: Authenticated user

  Returns:
      Updated agent configuration

  Raises:
      HTTPException: If agent not found or update fails
  """
  try:
    logger.info(
        f"Updating config for agent {agent_id} for user {current_user}")

    loader = AgentProfileLoader()
    updated_config = await loader.update_agent_config(agent_id, request.dict(exclude_unset=True))

    if not updated_config:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"Agent {agent_id} not found"
      )

    logger.info(f"Updated config for agent {agent_id}")

    return _agent_config_to_response(updated_config)

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Failed to update config for agent {agent_id}: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to update agent config: {str(e)}"
    )


def _agent_config_to_response(agent_config: AgentConfig) -> AgentConfigResponse:
  """
  Convert AgentConfig model to AgentConfigResponse.

  Args:
      agent_config: The AgentConfig database model

  Returns:
      AgentConfigResponse with properly typed fields
  """
  # Use getattr with defaults to safely extract values
  return AgentConfigResponse(
      agent_id=getattr(agent_config, 'agent_id', ''),
      name=getattr(agent_config, 'name', ''),
      persona=getattr(agent_config, 'persona_prompt', ''),
      llm_provider=getattr(agent_config, 'llm_provider', 'openai'),
      tts_provider=getattr(agent_config, 'tts_provider', 'elevenlabs'),
      voice_settings=getattr(agent_config, 'custom_config', None) or {},
      active=getattr(agent_config, 'is_active', True),
      created_at=getattr(agent_config, 'created_at',
                         datetime.now(timezone.utc)),
      updated_at=getattr(agent_config, 'updated_at',
                         datetime.now(timezone.utc))
  )
