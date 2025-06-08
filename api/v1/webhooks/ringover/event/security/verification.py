"""
Webhook signature verification utilities.
"""
import hmac
import hashlib
from typing import Optional

from core.logging.setup import get_logger

logger = get_logger(__name__)


def verify_webhook_signature(body: bytes, signature: Optional[str], secret: str) -> bool:
  """
  Verify HMAC signature of webhook payload

  Args:
      body: Raw webhook payload
      signature: Received signature
      secret: Webhook secret for verification

  Returns:
      True if signature is valid, False otherwise
  """
  if not signature or not secret:
    return False

  try:
    # Remove 'sha256=' prefix if present
    if signature.startswith('sha256='):
      signature = signature[7:]

    # Calculate expected signature
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()

    # Compare signatures
    return hmac.compare_digest(signature, expected_signature)

  except Exception as e:
    logger.error(f"Error verifying webhook signature: {str(e)}")
    return False
