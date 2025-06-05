"""
Agent script update and management functionality.
"""
from typing import Dict, Any, Optional
from core.logging.setup import get_logger

logger = get_logger(__name__)


class ScriptManager:
  """Manages script updates and reloading for agents."""

  def __init__(self, agent_core):
    """Initialize script manager with agent core reference."""
    self.agent_core = agent_core
    self.current_script_name: Optional[str] = None
    self.script_data: Optional[Dict[str, Any]] = None

  async def update_script(self, script_name: str, script_data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Update the agent's active script.

    Args:
        script_name: Name of the script to load
        script_data: Optional script data (if not loading from file)

    Returns:
        True if script was updated successfully
    """
    try:
      logger.info(
          f"Updating script for agent {self.agent_core.config.name} to: {script_name}")

      # Store previous script for rollback if needed
      previous_script = self.current_script_name
      previous_data = self.script_data

      # Update current script
      self.current_script_name = script_name
      self.script_data = script_data

      # Load script configuration if not provided
      if not script_data:
        script_data = await self._load_script_data(script_name)

      if script_data:
        # Update agent configuration with script data
        await self._apply_script_config(script_data)

        # Update conversation context
        await self._update_conversation_context(script_data)

        logger.info(f"Successfully updated script to: {script_name}")
        return True
      else:
        # Rollback on failure
        self.current_script_name = previous_script
        self.script_data = previous_data
        logger.error(f"Failed to load script data for: {script_name}")
        return False

    except Exception as e:
      logger.error(f"Error updating script to {script_name}: {e}")
      return False

  async def _load_script_data(self, script_name: str) -> Optional[Dict[str, Any]]:
    """Load script data from script manager."""
    try:
      # Import here to avoid circular imports
      from services.llm.script.manager import ScriptManager as LLMScriptManager
      from services.llm.prompt.manager import PromptManager

      prompt_manager = PromptManager()
      script_manager = LLMScriptManager(prompt_manager)
      script_schema = script_manager.get_script(script_name)
      
      # Convert script schema to dict if found
      if script_schema:
        # Extract relevant data from script schema
        script_data = {
          "name": script_schema.name,
          "description": script_schema.description,
          "version": script_schema.version,
          "general_prompt": script_schema.general_prompt,
          "sections": [{"title": section.title, "content": section.content, "weight": section.weight} 
                      for section in script_schema.sections],
          "states": [{"name": state.name, "type": state.type.value, "prompt": state.prompt, 
                     "tools": state.tools, "description": state.description, "metadata": state.metadata}
                    for state in script_schema.states],
          "tools": [{"name": tool.name, "description": tool.description, 
                    "parameters": tool.parameters, "required": tool.required}
                   for tool in script_schema.tools],
          "general_tools": script_schema.general_tools,
          "starting_state": script_schema.starting_state,
          "dynamic_variables": script_schema.dynamic_variables,
          "metadata": script_schema.metadata
        }
        return script_data

    except Exception as e:
      logger.error(f"Error loading script {script_name}: {e}")
      return None

  async def _apply_script_config(self, script_data: Dict[str, Any]) -> None:
    """Apply script configuration to agent."""
    try:
      # Update personality from script
      personality = script_data.get("personality", {})
      if personality:
        current_personality = self.agent_core.context_memory.get(
            "personality_traits", [])
        script_personality = personality.get("traits", [])

        # Merge personalities (script takes precedence)
        merged_traits = list(set(current_personality + script_personality))

        self.agent_core.context_memory.update({
            "personality_traits": merged_traits,
            "conversation_style": personality.get("style", "professional"),
            "agent_role": personality.get("role", "assistant")
        })

      # Update capabilities from script
      capabilities = script_data.get("capabilities", [])
      if capabilities:
        self.agent_core.context_memory["capabilities"] = capabilities

      # Update knowledge base from script
      knowledge_base = script_data.get("knowledge_base", [])
      if knowledge_base:
        current_kb = self.agent_core.context_memory.get("knowledge_base", [])
        merged_kb = list(set(current_kb + knowledge_base))
        self.agent_core.context_memory["knowledge_base"] = merged_kb

      logger.debug(
          f"Applied script configuration: {script_data.get('name', 'unknown')}")

    except Exception as e:
      logger.error(f"Error applying script config: {e}")
      raise

  async def _update_conversation_context(self, script_data: Dict[str, Any]) -> None:
    """Update conversation context with script information."""
    try:
      # Add script context to conversation memory
      self.agent_core.context_memory.update({
          "active_script": script_data.get("name", "unknown"),
          "script_version": script_data.get("version", "1.0"),
          "script_description": script_data.get("description", "")
      })

      # Update system instructions if provided
      instructions = script_data.get("instructions", "")
      if instructions:
        self.agent_core.context_memory["script_instructions"] = instructions

      logger.debug("Updated conversation context with script information")

    except Exception as e:
      logger.error(f"Error updating conversation context: {e}")
      raise

  def get_current_script(self) -> Optional[str]:
    """Get the name of the currently active script."""
    return self.current_script_name

  def get_script_data(self) -> Optional[Dict[str, Any]]:
    """Get the current script data."""
    return self.script_data

  async def reload_script(self) -> bool:
    """Reload the current script from source."""
    if self.current_script_name:
      return await self.update_script(self.current_script_name)
    return False
