"""
Pydantic schemas for agent-related requests
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class AgentConfigCreateRequest(BaseModel):
    """Request schema for creating an agent configuration"""
    name: str = Field(..., description="Name of the agent")
    persona: str = Field(..., description="Agent persona/character description")
    llm_provider: str = Field(..., description="LLM provider to use (openai, gemini, anthropic)")
    tts_provider: str = Field(..., description="TTS provider to use (elevenlabs)")
    voice_settings: Dict[str, Any] = Field(default_factory=dict, description="Voice synthesis settings")
    active: bool = Field(True, description="Whether the agent is active")


class AgentConfigUpdateRequest(BaseModel):
    """Request schema for updating an agent configuration"""
    name: Optional[str] = Field(None, description="Name of the agent")
    persona: Optional[str] = Field(None, description="Agent persona/character description")
    llm_provider: Optional[str] = Field(None, description="LLM provider to use")
    tts_provider: Optional[str] = Field(None, description="TTS provider to use")
    voice_settings: Optional[Dict[str, Any]] = Field(None, description="Voice synthesis settings")
    active: Optional[bool] = Field(None, description="Whether the agent is active")
