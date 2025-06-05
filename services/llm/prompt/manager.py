"""
Prompt manager for constructing and managing LLM prompts.
"""
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel

from core.logging.setup import get_logger

logger = get_logger(__name__)


class PromptStructureType(Enum):
  """Types of prompt structures supported."""
  SINGLE = "single"
  MULTI_PROMPT = "multi_prompt"
  CONVERSATION_FLOW = "conversation_flow"


class PromptSection(BaseModel):
  """Section of a prompt with specific purpose."""
  title: str
  content: str
  weight: float = 1.0  # For potential prioritization in token limited contexts


class State(BaseModel):
  """State in a multi-prompt or conversation flow structure."""
  name: str
  prompt: str
  tools: List[str] = []
  description: Optional[str] = None


class Edge(BaseModel):
  """Edge connecting two states in a conversation flow."""
  from_state: str
  to_state: str
  condition: str
  description: Optional[str] = None


class PromptTemplate(BaseModel):
  """Template for constructing prompts."""
  name: str
  structure_type: PromptStructureType
  sections: List[PromptSection] = []
  states: List[State] = []
  edges: List[Edge] = []
  general_prompt: Optional[str] = None
  general_tools: List[str] = []
  starting_state: Optional[str] = None
  dynamic_variables: Dict[str, str] = {}


class PromptManager:
  """Manages prompt templates and construction."""

  def __init__(self):
    self.templates: Dict[str, PromptTemplate] = {}
    self.default_template = None

  def register_template(self, template: PromptTemplate, make_default: bool = False):
    """
    Register a prompt template.

    Args:
        template: The prompt template to register
        make_default: Whether to make this the default template
    """
    self.templates[template.name] = template
    logger.info(f"Registered prompt template: {template.name}")

    if make_default or not self.default_template:
      self.default_template = template.name
      logger.info(f"Set default prompt template to: {template.name}")

  def get_template(self, template_name: Optional[str] = None) -> PromptTemplate:
    """
    Get a prompt template by name.

    Args:
        template_name: Name of template to retrieve, or None for default

    Returns:
        The prompt template
    """
    name = template_name or self.default_template
    if not name or name not in self.templates:
      raise ValueError(f"Prompt template not found: {name}")

    return self.templates[name]

  def build_prompt(
      self,
      template_name: Optional[str] = None,
      state: Optional[str] = None,
      variables: Optional[Dict[str, str]] = None
  ) -> str:
    """
    Build a prompt from a template.

    Args:
        template_name: Name of template to use, or None for default
        state: Specific state to build prompt for, if applicable
        variables: Dynamic variables to inject into the prompt

    Returns:
        The constructed prompt
    """
    template = self.get_template(template_name)
    variables = variables or {}

    # Combine template dynamic variables with passed variables
    all_variables = {**template.dynamic_variables, **variables}

    if template.structure_type == PromptStructureType.SINGLE:
      return self._build_single_prompt(template, all_variables)

    if state:
      return self._build_state_prompt(template, state, all_variables)

    # If multi-prompt or conversation flow and no state specified, use starting state
    if template.starting_state:
      return self._build_state_prompt(template, template.starting_state, all_variables)

    raise ValueError("No state specified for multi-prompt template")

  def _build_single_prompt(self, template: PromptTemplate, variables: Dict[str, str]) -> str:
    """Build a single prompt from sections."""
    prompt_parts = []

    # Add general prompt if available
    if template.general_prompt:
      prompt_parts.append(self._apply_variables(
          template.general_prompt, variables))

    # Add sections
    for section in template.sections:
      section_text = f"## {section.title}\n{section.content}\n"
      prompt_parts.append(self._apply_variables(section_text, variables))

    return "\n".join(prompt_parts)

  def _build_state_prompt(
      self,
      template: PromptTemplate,
      state_name: str,
      variables: Dict[str, str]
  ) -> str:
    """Build a prompt for a specific state."""
    prompt_parts = []

    # Add general prompt if available
    if template.general_prompt:
      prompt_parts.append(self._apply_variables(
          template.general_prompt, variables))

    # Find the specific state
    state = None
    for s in template.states:
      if s.name == state_name:
        state = s
        break

    if not state:
      raise ValueError(f"State not found in template: {state_name}")

    # Add state-specific prompt
    prompt_parts.append(self._apply_variables(state.prompt, variables))

    # List available tools for this state
    if state.tools or template.general_tools:
      tools_list = []
      if template.general_tools:
        tools_list.extend(template.general_tools)
      if state.tools:
        tools_list.extend(state.tools)

      unique_tools = list(set(tools_list))  # Remove duplicates
      tools_section = "## Available Tools\n" + \
          "\n".join([f"- {tool}" for tool in unique_tools])
      prompt_parts.append(tools_section)

    return "\n".join(prompt_parts)

  def _apply_variables(self, text: str, variables: Dict[str, str]) -> str:
    """Apply variable substitution to text."""
    result = text
    for key, value in variables.items():
      placeholder = f"{{{{{key}}}}}"
      result = result.replace(placeholder, value)
    return result
