"""
Conversation analysis and summarization.
"""
import time
from typing import Dict, Any, List
from core.logging.setup import get_logger

logger = get_logger(__name__)


class ConversationAnalyzer:
  """Analyzes conversation patterns and generates summaries."""

  def __init__(self, agent_core):
    """Initialize analyzer with agent core reference."""
    self.agent_core = agent_core

  async def get_conversation_summary(self) -> Dict[str, Any]:
    """
    Get summary of current conversation.

    Returns:
        Conversation summary
    """
    try:
      total_exchanges = len(self.agent_core.conversation_history) // 2
      call_duration = time.time() - \
          self.agent_core.context_memory.get("call_start_time", time.time())

      user_messages = [
          msg for msg in self.agent_core.conversation_history if msg["role"] == "user"]
      agent_messages = [
          msg for msg in self.agent_core.conversation_history if msg["role"] == "assistant"]

      summary = {
          "call_id": self.agent_core.current_call_context.call_id if self.agent_core.current_call_context else None,
          "agent_name": self.agent_core.config.name,
          "total_exchanges": total_exchanges,
          "call_duration": call_duration,
          "user_message_count": len(user_messages),
          "agent_message_count": len(agent_messages),
          "current_state": self.agent_core.state.value,
          "avg_response_time": sum(
              msg.get("metadata", {}).get("thinking_time", 0)
              for msg in agent_messages
          ) / max(len(agent_messages), 1),
          "conversation_topics": await self._extract_topics()
      }

      return summary

    except Exception as e:
      logger.error(f"Error generating conversation summary: {str(e)}")
      return {"error": str(e)}

  async def _extract_topics(self) -> List[str]:
    """Extract main topics from conversation."""
    # Simple keyword extraction - could be enhanced with NLP
    try:
      all_text = " ".join([
          msg["content"]
          for msg in self.agent_core.conversation_history
          if msg["role"] == "user"
      ]).lower()

      # Basic topic keywords
      topic_keywords = {
          "support": ["help", "problem", "issue", "trouble"],
          "sales": ["buy", "purchase", "price", "cost", "product"],
          "billing": ["bill", "payment", "charge", "invoice"],
          "account": ["account", "profile", "settings", "login"],
          "technical": ["not working", "error", "bug", "technical"]
      }

      detected_topics = []
      for topic, keywords in topic_keywords.items():
        if any(keyword in all_text for keyword in keywords):
          detected_topics.append(topic)

      return detected_topics or ["general"]

    except Exception as e:
      logger.warning(f"Error extracting topics: {str(e)}")
      return ["general"]
