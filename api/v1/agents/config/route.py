"""
Agent configuration management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, List

from api.v1.schemas.request.agent import AgentConfigUpdateRequest, AgentConfigCreateRequest
from api.v1.schemas.response.agent import AgentConfigResponse
from services.agent.profile.loader import AgentProfileLoader
from core.security.auth.token import get_current_user
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
        agent_config = await loader.load_agent_profile(agent_id)
        
        if not agent_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        logger.info(f"Retrieved config for agent {agent_id}")
        
        return AgentConfigResponse(
            agent_id=agent_id,
            name=agent_config.name,
            persona=agent_config.persona,
            llm_provider=agent_config.llm_provider,
            tts_provider=agent_config.tts_provider,
            voice_settings=agent_config.voice_settings,
            active=agent_config.active,
            created_at=agent_config.created_at,
            updated_at=agent_config.updated_at
        )
        
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
        agents = await loader.list_all_agents()
        
        result = []
        for agent in agents:
            result.append(AgentConfigResponse(
                agent_id=agent.agent_id,
                name=agent.name,
                persona=agent.persona,
                llm_provider=agent.llm_provider,
                tts_provider=agent.tts_provider,
                voice_settings=agent.voice_settings,
                active=agent.active,
                created_at=agent.created_at,
                updated_at=agent.updated_at
            ))
        
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
        logger.info(f"Updating config for agent {agent_id} for user {current_user}")
        
        loader = AgentProfileLoader()
        updated_config = await loader.update_agent_profile(agent_id, request.dict(exclude_unset=True))
        
        if not updated_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        logger.info(f"Updated config for agent {agent_id}")
        
        return AgentConfigResponse(
            agent_id=agent_id,
            name=updated_config.name,
            persona=updated_config.persona,
            llm_provider=updated_config.llm_provider,
            tts_provider=updated_config.tts_provider,
            voice_settings=updated_config.voice_settings,
            active=updated_config.active,
            created_at=updated_config.created_at,
            updated_at=updated_config.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update config for agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent config: {str(e)}"
        )
