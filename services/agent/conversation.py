"""
Backward compatibility module for conversation management.
This file maintains the original API while using the new modular structure.
"""

# Import from the new modular structure
from .conversation.manager import ConversationManager
from .conversation.flow.definitions import ConversationFlow, ConversationTurn

# Re-export for backward compatibility
__all__ = ['ConversationManager', 'ConversationFlow', 'ConversationTurn']
