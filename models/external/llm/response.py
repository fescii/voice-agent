"""
LLM response models.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class LLMUsage(BaseModel):
    """Token usage information."""
    prompt_tokens: int = Field(..., description="Tokens in prompt")
    completion_tokens: int = Field(..., description="Tokens in completion")
    total_tokens: int = Field(..., description="Total tokens used")


class LLMChoice(BaseModel):
    """Single response choice."""
    message: Dict[str, str] = Field(..., description="Response message")
    finish_reason: str = Field(..., description="Reason for completion")
    index: int = Field(..., description="Choice index")


class LLMResponse(BaseModel):
    """Response model for LLM providers."""
    
    id: str = Field(..., description="Response ID")
    provider: str = Field(..., description="Provider name")
    model: str = Field(..., description="Model used")
    choices: List[LLMChoice] = Field(..., description="Response choices")
    usage: Optional[LLMUsage] = Field(default=None, description="Token usage")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    # Raw provider response for debugging
    raw_response: Optional[Dict[str, Any]] = Field(default=None, description="Raw provider response")
    
    def get_content(self) -> str:
        """Get the content of the first choice."""
        if self.choices:
            return self.choices[0].message.get("content", "")
        return ""
    
    def get_finish_reason(self) -> str:
        """Get the finish reason of the first choice."""
        if self.choices:
            return self.choices[0].finish_reason
        return "unknown"
    
    class Config:
        extra = "forbid"
