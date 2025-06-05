"""
Models for JSON-based prompt script schemas.
"""
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
  """Definition of a tool available to the LLM."""
  name: str = Field(..., description="Name of the tool")
  description: str = Field(...,
                           description="Description of what the tool does")
  parameters: Dict[str, Any] = Field(
      default_factory=dict, description="Parameters for the tool")
  required: bool = Field(
      default=False, description="Whether this tool is required")


class StateType(str, Enum):
  """Types of states in a conversation flow."""
  INITIAL = "initial"
  INFORMATION = "information"
  PROCESSING = "processing"
  DECISION = "decision"
  TERMINAL = "terminal"


class EdgeCondition(BaseModel):
  """Condition for transitioning between states."""
  type: str = Field(...,
                    description="Type of condition (e.g., 'intent', 'entity', 'sentiment')")
  value: Any = Field(..., description="Value to compare against")
  operator: str = Field(default="equals", description="Comparison operator")


class Edge(BaseModel):
  """Edge connecting two states in a conversation flow."""
  from_state: str = Field(..., description="Source state name")
  to_state: str = Field(..., description="Target state name")
  condition: Optional[EdgeCondition] = Field(
      None, description="Condition for this transition")
  description: Optional[str] = Field(
      None, description="Human-readable description")


class State(BaseModel):
  """State in a conversation flow."""
  name: str = Field(..., description="Unique identifier for the state")
  type: StateType = Field(..., description="Type of state")
  prompt: str = Field(..., description="Prompt template for this state")
  tools: List[str] = Field(
      default_factory=list, description="Tools available in this state")
  description: Optional[str] = Field(
      None, description="Human-readable description")
  metadata: Dict[str, Any] = Field(
      default_factory=dict, description="Additional state metadata")


class ScriptSection(BaseModel):
  """Section of a script with specific purpose."""
  title: str = Field(..., description="Section title")
  content: str = Field(..., description="Section content")
  weight: float = Field(
      default=1.0, description="Importance weight for token prioritization")


class ScriptSchema(BaseModel):
  """Schema for JSON-based prompt script."""
  name: str = Field(..., description="Name of the script")
  description: Optional[str] = Field(
      None, description="Description of the script's purpose")
  version: str = Field(default="1.0", description="Script version")
  general_prompt: Optional[str] = Field(
      None, description="General system prompt")
  sections: List[ScriptSection] = Field(
      default_factory=list, description="Script sections")
  states: List[State] = Field(
      default_factory=list, description="Conversation states")
  edges: List[Edge] = Field(
      default_factory=list, description="State transitions")
  tools: List[ToolDefinition] = Field(
      default_factory=list, description="Available tools")
  general_tools: List[str] = Field(
      default_factory=list, description="Tools available in all states")
  starting_state: Optional[str] = Field(None, description="Initial state name")
  dynamic_variables: Dict[str, str] = Field(
      default_factory=dict, description="Default variable values")
  metadata: Dict[str, Any] = Field(
      default_factory=dict, description="Additional script metadata")
