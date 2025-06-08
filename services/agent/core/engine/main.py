"""
Main agent engine - modularized version.
"""
from typing import Dict, Any, Optional

from core.logging.setup import get_logger
from models.internal.callcontext import CallContext
from services.llm.orchestrator import LLMOrchestrator
from ..state import AgentState
from ..response import AgentResponse

from .initialization import InitializationManager
from .processing import InputProcessor, ResponseProcessor
from .context import ContextManager
from .state import StateManager
from .actions import ActionDelegator

logger = get_logger(__name__)


class AgentCore:
  """Core agent logic and conversation engine."""

  def __init__(
      self,
      agent_config: Any,  # Accept any agent config object with required properties
      llm_orchestrator: LLMOrchestrator
  ):
    """Initialize agent core."""
    self.config = agent_config
    self.llm_orchestrator = llm_orchestrator
    self.state = AgentState.IDLE
    self.conversation_history = []
    self.context_memory = {}
    self.current_call_context: Optional[CallContext] = None

    # Initialize modular components first
    self._initialize_engine_components()
    # Then initialize external components
    self._initialize_components()

  def _initialize_engine_components(self):
    """Initialize modular engine components."""
    self.initialization_manager = InitializationManager(
        self.config, self.context_memory)
    self.input_processor = InputProcessor(self)
    self.response_processor = ResponseProcessor(self)
    self.context_manager = ContextManager(self)
    self.state_manager = StateManager(self)
    self.action_delegator = ActionDelegator(self)

  def _initialize_components(self):
    """Initialize external modular components."""
    # Import here to avoid circular imports
    from ...actions.handler import ActionHandler
    from ...analysis.conversation import ConversationAnalyzer
    from ...script.manager import ScriptManager

    self.action_handler = ActionHandler(self)
    self.conversation_analyzer = ConversationAnalyzer(self)
    self.script_manager = ScriptManager(self)

  async def initialize(self, call_context: CallContext):
    """
    Initialize agent for a new call.

    Args:
        call_context: Call context information
    """
    try:
      self.current_call_context = call_context
      self.state = AgentState.IDLE
      self.conversation_history = []
      self.context_memory = {}

      await self.initialization_manager.initialize_agent(call_context)
      logger.info("Agent initialized successfully")

    except Exception as e:
      logger.error(f"Error initializing agent: {str(e)}")
      self.state = AgentState.ERROR
      raise

  async def process_user_input(
      self,
      user_text: str,
      audio_data: Optional[bytes] = None,
      metadata: Optional[Dict[str, Any]] = None
  ) -> AgentResponse:
    """
    Process user input and generate agent response.
    """
    return await self.input_processor.process_user_input(user_text, audio_data, metadata)

  async def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
    """
    Process a message from a user.
    """
    return await self.input_processor.process_message(message, context)

  def get_current_state(self) -> AgentState:
    """Get current agent state."""
    return self.state_manager.get_current_state()

  def set_state(self, state: AgentState):
    """Set agent state."""
    self.state_manager.set_state(state)

  async def handle_call_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> AgentResponse:
    """Handle call-specific actions."""
    return await self.action_delegator.handle_call_action(action, params)

  async def get_conversation_summary(self) -> Dict[str, Any]:
    """Get conversation summary."""
    return await self.action_delegator.get_conversation_summary()

  async def update_script(self, script_name: str, script_data: Optional[Dict[str, Any]] = None) -> bool:
    """Update agent script."""
    return await self.action_delegator.update_script(script_name, script_data)

  def get_current_script(self) -> Optional[str]:
    """Get current script name."""
    return self.action_delegator.get_current_script()
