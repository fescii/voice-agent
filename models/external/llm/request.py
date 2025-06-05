"""
LLM request models.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class LLMMessage(BaseModel):
    """Individual message in conversation."""
    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")


class LLMRequest(BaseModel):
    """Request model for LLM providers."""
    
    messages: List[LLMMessage] = Field(..., description="Conversation messages")
    model: str = Field(..., description="Model name to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Response randomness")
    max_tokens: int = Field(default=150, gt=0, description="Maximum tokens in response")
    stream: bool = Field(default=False, description="Whether to stream response")
    stop_sequences: Optional[List[str]] = Field(default=None, description="Stop sequences")
    
    # Provider-specific parameters
    extra_params: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific parameters")
    
    class Config:
        extra = "forbid"
