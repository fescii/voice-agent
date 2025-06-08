"""
Information extraction from user input.
"""

import re
from typing import Dict, Any
from core.logging.setup import get_logger

logger = get_logger(__name__)


class InformationExtractor:
  """Extracts structured information from user input."""

  def __init__(self):
    """Initialize information extractor."""
    # Define extraction patterns
    self.patterns = {
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'account': r'\b(?:account|acct)\s*(?:number|#)?\s*:?\s*([A-Za-z0-9]+)\b'
    }

  async def extract_information(self, user_input: str) -> Dict[str, Any]:
    """Extract structured information from user input."""
    try:
      extracted = {}

      # Extract phone numbers
      phones = re.findall(self.patterns['phone'], user_input)
      if phones:
        extracted["phone"] = phones[0]

      # Extract email addresses
      emails = re.findall(self.patterns['email'], user_input)
      if emails:
        extracted["email"] = emails[0]

      # Extract account numbers
      accounts = re.findall(
          self.patterns['account'], user_input, re.IGNORECASE)
      if accounts:
        extracted["account_number"] = accounts[0]

      return extracted

    except Exception as e:
      logger.error(f"Error extracting information: {str(e)}")
      return {}

  async def has_sufficient_information(self, context: Dict[str, Any]) -> bool:
    """Check if we have sufficient information to proceed."""
    # Define required information based on conversation context
    required_fields = ["contact_reason"]  # Basic requirement

    # Check if we have enough context
    return len(context) >= len(required_fields)

  async def identify_missing_information(self, context: Dict[str, Any]) -> str:
    """Identify what information is still needed."""
    # Simple implementation - could be more sophisticated
    if "contact_reason" not in context:
      return "what you're calling about"
    elif "account_number" not in context:
      return "your account number"
    else:
      return "more details"
