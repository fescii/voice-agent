#!/usr/bin/env python3
"""
Generate webhook endpoints for Ringover dashboard configuration
"""

from core.config.registry import config_registry
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def get_webhook_endpoints():
  """Generate the webhook endpoints to add to Ringover dashboard"""

  # Get configuration from centralized registry
  config = config_registry.ringover

  # Get values from config
  webhook_secret = config.webhook_secret
  base_url = config.webhook_url

  # Main webhook endpoint
  main_endpoint = f"{base_url}/api/v1/webhooks/ringover/event"

  # Test endpoint (optional)
  test_endpoint = f"{base_url}/api/v1/webhooks/ringover/test"

  print("=" * 60)
  print("RINGOVER WEBHOOK DASHBOARD CONFIGURATION")
  print("=" * 60)
  print()
  print("🔗 WEBHOOK ENDPOINTS TO ADD:")
  print("-" * 40)
  print(f"Main Endpoint: {main_endpoint}")
  print(f"Test Endpoint: {test_endpoint}")
  print()
  print("🔑 WEBHOOK KEY:")
  print("-" * 40)
  print(f"Key: {webhook_secret}")
  print()
  print("📋 COPY/PASTE FOR RINGOVER DASHBOARD:")
  print("-" * 40)
  print("Add these URLs (one per line) in your webhook settings:")
  print()
  print(main_endpoint)
  print(test_endpoint)
  print()
  print("✅ EVENTS TO ENABLE:")
  print("-" * 40)
  events = [
      "POST Calls ringing",
      "POST Calls answered",
      "POST Calls ended",
      "POST Missed calls",
      "POST Voicemail",
      "POST SMS messages received",
      "POST SMS messages sent",
      "POST After-Call Work",
      "POST Faxes received"
  ]

  for event in events:
    print(f"☑️  {event}")

  print()
  print("⚠️  IMPORTANT NOTES:")
  print("-" * 40)
  print("1. Set your actual domain in RINGOVER_WEBHOOK_URL environment variable")
  print("2. Make sure your server is accessible from the internet")
  print("3. Test with the /test endpoint first")
  print("4. All events should use POST method")
  print()


if __name__ == "__main__":
  get_webhook_endpoints()
