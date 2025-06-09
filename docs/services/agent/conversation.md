# Conversation Management System

This module provides a comprehensive system for managing voice agent conversations, with both standard conversation flows and script-driven conversations.

## Directory Structure

- **flow.py**: Defines conversation flow states as an enum
- **turn.py**: Defines the conversation turn data structure
- **manager.py**: Core conversation manager implementation
- **handler.py**: Individual handlers for each conversation flow state
- **processor.py**: Processing logic for applying flow-specific behavior
- **scriptflow.py**: Script-driven conversation flow manager
- **examples.py**: Usage examples for script-driven flows
- **test.py**: Integration tests

## Components

- **ConversationFlow**: Defines the possible states of a conversation
- **ConversationTurn**: Data structure for a single turn in a conversation
- **ConversationManager**: Main class for managing conversation state and flow
- **ScriptConversationFlow**: Extension for script-driven conversations
- **ScriptFlowState**: Tracks the state of active script flows for calls

## Usage

### Standard Conversations

Use the `ConversationManager` class to process conversation turns with flow-based handling.

### Script-Driven Conversations

1. Create and load a conversation script using the `ScriptManager`
2. Activate the script for a call using `ScriptConversationFlow.activate_script_flow()`
3. Process user input with `process_script_turn()`
4. Transition between states with `transition_script_state()`
5. When done, deactivate with `deactivate_script_flow()`

### Examples

See `examples.py` for complete working examples of script-driven conversation flows.

## Integration

This module integrates with:

- Voice agent system via `AgentCore`
- LLM prompt system via `PromptManager` and `PromptLLMAdapter`
- Script management via `VoiceAgentScriptManager`

Scripts can define multiple states with different prompt templates and transitions between states to create complex, stateful conversation flows.
