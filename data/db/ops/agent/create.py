"""
Create operations for agent configs.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional

from ...models.agentconfig import AgentConfig
from ....core.logging import get_logger

logger = get_logger(__name__)


async def create_agent_config(
    session: AsyncSession,
    agent_id: str,
    name: str,
    persona_prompt: str,
    **kwargs
) -> Optional[AgentConfig]:
    """
    Create a new agent configuration.
    
    Args:
        session: Database session
        agent_id: Unique agent identifier
        name: Agent display name
        persona_prompt: Agent persona description
        **kwargs: Additional configuration fields
        
    Returns:
        Created AgentConfig instance or None if failed
    """
    try:
        agent_config = AgentConfig(
            agent_id=agent_id,
            name=name,
            persona_prompt=persona_prompt,
            **kwargs
        )
        
        session.add(agent_config)
        await session.commit()
        await session.refresh(agent_config)
        
        logger.info(f"Created agent config: {agent_id}")
        return agent_config
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to create agent config {agent_id}: {e}")
        await session.rollback()
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating agent config {agent_id}: {e}")
        await session.rollback()
        return None
