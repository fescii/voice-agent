"""
Converter for transforming JSON scripts into prompt templates.
"""
from typing import Optional

from core.logging.setup import get_logger
from services.llm.prompt.manager import (
    PromptManager,
    PromptTemplate,
    PromptStructureType,
    PromptSection,
    State as PromptState,
    Edge as PromptEdge
)
from services.llm.script.schema import ScriptSchema

logger = get_logger(__name__)


class ScriptConverter:
  """Converts JSON scripts to prompt templates."""

  @staticmethod
  async def convert_to_template(script: ScriptSchema) -> PromptTemplate:
    """
    Convert a JSON script to a prompt template.

    Args:
        script: The script to convert

    Returns:
        A prompt template based on the script
    """
    # Determine structure type based on script content
    structure_type = PromptStructureType.SINGLE
    if script.states:
      structure_type = PromptStructureType.MULTI_PROMPT

    # Convert script sections to prompt sections
    sections = [
        PromptSection(
            title=section.title,
            content=section.content,
            weight=section.weight
        )
        for section in script.sections
    ]

    # Convert script states to prompt states
    states = [
        PromptState(
            name=state.name,
            prompt=state.prompt,
            tools=state.tools,
            description=state.description
        )
        for state in script.states
    ]

    # Convert script edges to prompt edges
    edges = [
        PromptEdge(
            from_state=edge.from_state,
            to_state=edge.to_state,
            condition=edge.condition.value if edge.condition else "",
            description=edge.description
        )
        for edge in script.edges
    ]

    # Create the prompt template
    template = PromptTemplate(
        name=script.name,
        structure_type=structure_type,
        sections=sections,
        states=states,
        edges=edges,
        general_prompt=script.general_prompt,
        general_tools=script.general_tools,
        starting_state=script.starting_state,
        dynamic_variables=script.dynamic_variables
    )

    return template

  @staticmethod
  async def register_script(
      script: ScriptSchema,
      prompt_manager: PromptManager,
      make_default: bool = False
  ) -> bool:
    """
    Convert and register a script as a prompt template.

    Args:
        script: The script to register
        prompt_manager: The prompt manager to register with
        make_default: Whether to make this the default template

    Returns:
        True if successful, False otherwise
    """
    try:
      template = await ScriptConverter.convert_to_template(script)
      prompt_manager.register_template(template, make_default)
      logger.info(f"Registered script '{script.name}' as a prompt template")
      return True
    except Exception as e:
      logger.error(f"Failed to register script as template: {e}")
      return False
