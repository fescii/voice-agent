"""
Webhook security and signature verification for Ringover.
"""
import hmac
import hashlib
from typing import Optional

from core.logging.setup import get_logger
from core.config.registry import config_registry

logger = get_logger(__name__)


class WebhookSecurity:
  """
  Handles HMAC signature verification for Ringover webhooks.

  As mentioned in the documentation, HMAC signature verification
  is critical to ensure webhook authenticity and prevent spoofing attacks.
  """

  def __init__(self):
    """Initialize webhook security with secret from config."""
    self.webhook_secret = config_registry.ringover.webhook_secret

  def verify_signature(self, payload: bytes, signature: Optional[str]) -> bool:
    """
    Verify HMAC signature of webhook payload.

    Args:
        payload: Raw webhook payload as bytes
        signature: Signature from X-Ringover-Signature header

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature:
      logger.warning("No signature provided in webhook request")
      return False

    if not self.webhook_secret:
      logger.warning("No webhook secret configured - cannot verify signature")
      return False

    try:
      # Remove 'sha256=' prefix if present
      if signature.startswith('sha256='):
        signature = signature[7:]

      # Compute expected signature
      expected_signature = hmac.new(
          self.webhook_secret.encode('utf-8'),
          payload,
          hashlib.sha256
      ).hexdigest()

      # Compare signatures using secure comparison
      is_valid = hmac.compare_digest(expected_signature, signature)

      if not is_valid:
        logger.warning("Webhook signature verification failed")

      return is_valid

    except Exception as e:
      logger.error(f"Error verifying webhook signature: {e}")
      return False

  def is_webhook_secure(self) -> bool:
    """Check if webhook security is properly configured."""
    return bool(self.webhook_secret)

  def get_signature_header_name(self) -> str:
    """Get the expected signature header name."""
    return "X-Ringover-Signature"
