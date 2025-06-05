"""
Pydantic schemas for agent-related responses
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class AgentConfigResponse(BaseModel):
    """Response schema for agent configuration"""
    agent_id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Name of the agent")
    persona: str = Field(..., description="Agent persona/character description")
    llm_provider: str = Field(..., description="LLM provider being used")
    tts_provider: str = Field(..., description="TTS provider being used")
    voice_settings: Dict[str, Any] = Field(..., description="Voice synthesis settings")
    active: bool = Field(..., description="Whether the agent is active")
    created_at: datetime = Field(..., description="When the agent was created")
    updated_at: datetime = Field(..., description="When the agent was last updated")


class AgentStatusResponse(BaseModel):
    """Response schema for agent status"""
    agent_id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Name of the agent")
    active: bool = Field(..., description="Whether the agent is active")
    current_calls: int = Field(..., description="Number of current active calls")
    max_calls: int = Field(..., description="Maximum number of concurrent calls")
    status: str = Field(..., description="Current agent status (available, busy, offline)")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
