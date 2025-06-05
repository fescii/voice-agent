"""
Dynamic prompt builder for real-time context integration.
"""
from typing import Dict, Any, List, Optional
import time
from dataclasses import dataclass

from core.logging.setup import get_logger
from .manager import PromptManager, PromptTemplate, PromptStructureType

logger = get_logger(__name__)


@dataclass
class ConversationContext:
  """Context information for the current conversation."""
  call_id: str
  caller_info: Dict[str, Any]
  conversation_history: List[Dict[str, str]]
  current_state: Optional[str] = None
  metadata: Optional[Dict[str, Any]] = None


class PromptBuilder:
  """Builds prompts dynamically with real-time context."""

  def __init__(self, prompt_manager: PromptManager):
    """
    Initialize prompt builder.

    Args:
        prompt_manager: The prompt manager to use for templates
    """
    self.prompt_manager = prompt_manager
    self.max_history_turns = 10  # Default maximum conversation turns to include
    self.token_limit = 4000  # Default token limit for context window

  def build_prompt_with_context(
      self,
      context: ConversationContext,
      template_name: Optional[str] = None,
      additional_variables: Optional[Dict[str, str]] = None
  ) -> str:
    """
    Build a prompt with conversation context.

    Args:
        context: The conversation context
        template_name: Name of template to use, or None for default
        additional_variables: Additional variables to inject

    Returns:
        The complete prompt with context
    """
    # Get the appropriate template
    template = self.prompt_manager.get_template(template_name)

    # Prepare variables
    variables = self._prepare_variables(context, additional_variables)

    # Build the base prompt
    if template.structure_type != PromptStructureType.SINGLE and context.current_state:
      base_prompt = self.prompt_manager.build_prompt(
          template_name=template_name,
          state=context.current_state,
          variables=variables
      )
    else:
      base_prompt = self.prompt_manager.build_prompt(
          template_name=template_name,
          variables=variables
      )

    # Add conversation history
    history_text = self._format_conversation_history(
        context.conversation_history)

    # Combine everything
    full_prompt = f"{base_prompt}\n\n## Conversation History\n{history_text}\n\n## Current Response"

    return full_prompt

  def _prepare_variables(
      self,
      context: ConversationContext,
      additional_vars: Optional[Dict[str, str]] = None
  ) -> Dict[str, str]:
    """Prepare variables from context and additional sources."""
    variables = {}

    # Add caller info
    for key, value in context.caller_info.items():
      if isinstance(value, str):
        variables[f"caller_{key}"] = value

    # Add metadata
    if context.metadata:
      for key, value in context.metadata.items():
        if isinstance(value, str):
          variables[key] = value

    # Add time-related info
    current_time = time.strftime("%H:%M:%S")
    current_date = time.strftime("%Y-%m-%d")
    variables["current_time"] = current_time
    variables["current_date"] = current_date

    # Add additional variables
    if additional_vars:
      variables.update(additional_vars)

    return variables

  def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
    """Format conversation history for the prompt."""
    # Limit history to the most recent turns
    limited_history = history[-self.max_history_turns:] if len(
        history) > self.max_history_turns else history

    formatted_turns = []
    for turn in limited_history:
      user_msg = turn.get("user", "")
      agent_msg = turn.get("agent", "")

      if user_msg:
        formatted_turns.append(f"User: {user_msg}")
      if agent_msg:
        formatted_turns.append(f"Agent: {agent_msg}")

    return "\n\n".join(formatted_turns)

  def update_with_streaming_transcription(
      self,
      base_prompt: str,
      transcription_segment: str
  ) -> str:
    """
    Update a prompt with new streaming transcription segment.

    Args:
        base_prompt: The current prompt
        transcription_segment: New transcription segment

    Returns:
        Updated prompt
    """
    # Split the base prompt to find where to insert the new transcription
    if "## Current Response" in base_prompt:
      parts = base_prompt.split("## Current Response", 1)
      main_part = parts[0]

      # Check if there's already a "Current User Input" section
      if "## Current User Input\n" in main_part:
        # Update the existing section
        sections = main_part.split("## Current User Input\n", 1)
        new_main_part = sections[0] + \
            f"## Current User Input\n{transcription_segment}\n\n"
      else:
        # Add a new section
        new_main_part = main_part + \
            f"## Current User Input\n{transcription_segment}\n\n"

      # Reassemble the prompt
      updated_prompt = new_main_part + "## Current Response"
      return updated_prompt

    # Fallback if structure not as expected
    return base_prompt + f"\n\nUser's current input: {transcription_segment}"
