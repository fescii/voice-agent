"""
Adapter for integrating prompt management with LLM orchestration.
"""
from typing import Dict, Any, Optional, List, AsyncGenerator
from dataclasses import dataclass

from core.logging.setup import get_logger
from services.llm.orchestrator import LLMOrchestrator
from services.llm.prompt.manager import PromptManager
from services.llm.prompt.builder import PromptBuilder, ConversationContext
from models.external.llm.request import LLMRequest, LLMMessage
from models.external.llm.response import LLMResponse, LLMMessage, LLMChoice

logger = get_logger(__name__)


@dataclass
class PromptedLLMResponse:
  """Response from the LLM with prompt details."""
  response: LLMResponse
  prompt_used: str
  template_name: Optional[str] = None
  state: Optional[str] = None


class PromptLLMAdapter:
  """
  Adapter that connects prompt management with LLM orchestration.

  This class is responsible for integrating the prompt system with
  the existing LLM orchestrator, handling the conversion of
  structured prompts into LLM requests and processing responses.
  """

  def __init__(self,
               llm_orchestrator: LLMOrchestrator,
               prompt_manager: PromptManager):
    """
    Initialize the adapter.

    Args:
        llm_orchestrator: The LLM orchestrator for sending requests
        prompt_manager: The prompt manager for template handling
    """
    self.llm_orchestrator = llm_orchestrator
    self.prompt_manager = prompt_manager
    self.prompt_builder = PromptBuilder(prompt_manager)

  async def generate_response_with_prompt(
      self,
      context: ConversationContext,
      template_name: Optional[str] = None,
      provider: str = "openai",
      model: Optional[str] = None,
      temperature: float = 0.7,
      additional_variables: Optional[Dict[str, str]] = None
  ) -> PromptedLLMResponse:
    """
    Generate a response using a prompt template.

    Args:
        context: Conversation context
        template_name: Name of template to use, or None for default
        provider: LLM provider to use
        model: Specific model to use, or None for provider default
        temperature: Temperature for response generation
        additional_variables: Additional variables for the prompt

    Returns:
        LLM response with prompt details
    """
    # Build the prompt
    prompt = self.prompt_builder.build_prompt_with_context(
        context=context,
        template_name=template_name,
        additional_variables=additional_variables
    )

    # Create the LLM request
    messages = [
        {"role": "system", "content": prompt}
    ]

    # Add the latest user input from context if available
    if context.conversation_history:
      last_turn = context.conversation_history[-1]
      if "user" in last_turn:
        messages.append({
            "role": "user",
            "content": last_turn["user"]
        })

    # Generate the response
    response = await self.llm_orchestrator.generate_response(
        messages=messages,
        provider=provider,
        model=model or "gpt-3.5-turbo",
        temperature=temperature
    )

    if not response:
      logger.error("Failed to generate response from LLM")
      # Return a default response instead of None
      empty_message = LLMMessage(role="assistant", content="")
      empty_choice = LLMChoice(message=empty_message,
                               index=0, finish_reason="error")
      empty_response = LLMResponse(
          id="error",
          provider=provider,
          model=model or "unknown",
          choices=[empty_choice]
      )
      return PromptedLLMResponse(
          response=empty_response,
          prompt_used=prompt,
          template_name=template_name,
          state=context.current_state
      )

    return PromptedLLMResponse(
        response=response,
        prompt_used=prompt,
        template_name=template_name,
        state=context.current_state
    )

  # Note: This method is commented out until streaming is implemented in the orchestrator
  """
    async def generate_streaming_response(
        self,
        context: ConversationContext,
        template_name: Optional[str] = None,
        provider: str = "openai",
        model: Optional[str] = None,
        temperature: float = 0.7,
        additional_variables: Optional[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        # Build the prompt
        prompt = self.prompt_builder.build_prompt_with_context(
            context=context,
            template_name=template_name,
            additional_variables=additional_variables
        )
        
        # Create the LLM request
        messages = [
            {"role": "system", "content": prompt}
        ]
        
        # Add the latest user input from context if available
        if context.conversation_history:
            last_turn = context.conversation_history[-1]
            if "user" in last_turn:
                messages.append({
                    "role": "user", 
                    "content": last_turn["user"]
                })
        
        # Note: This requires implementing generate_streaming_response in LLMOrchestrator
        # For now, this is a placeholder
        response = await self.llm_orchestrator.generate_response(
            messages=messages,
            provider=provider,
            model=model,
            temperature=temperature
        )
        
        if response:
            yield response.get_content()
    """

  def update_conversation_context(
      self,
      context: ConversationContext,
      user_input: str,
      agent_response: str
  ) -> ConversationContext:
    """
    Update the conversation context with a new turn.

    Args:
        context: The existing conversation context
        user_input: The user's input
        agent_response: The agent's response

    Returns:
        The updated conversation context
    """
    # Add the new turn to the history
    context.conversation_history.append({
        "user": user_input,
        "agent": agent_response
    })

    # Limit history size if needed
    if len(context.conversation_history) > self.prompt_builder.max_history_turns:
      context.conversation_history = context.conversation_history[-self.prompt_builder.max_history_turns:]

    return context

  def transition_state(
      self,
      context: ConversationContext,
      new_state: str
  ) -> ConversationContext:
    """
    Transition to a new state in the conversation.

    Args:
        context: The existing conversation context
        new_state: The new state to transition to

    Returns:
        The updated conversation context
    """
    logger.info(
        f"Transitioning from state {context.current_state} to {new_state}")
    context.current_state = new_state

    # Could add state transition logic here

    return context
