"""
Backward compatibility module for conversation management.
This file maintains the original API while using the new modular structure.
"""

# Import from the new modular structure
from .manager import ConversationManager
from .flow.definitions import ConversationFlow, ConversationTurn

# Re-export for backward compatibility
__all__ = ['ConversationManager', 'ConversationFlow', 'ConversationTurn']
