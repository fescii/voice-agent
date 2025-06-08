#!/usr/bin/env python3
"""
Generate complete list of webhook URLs configured in the system for Ringover dashboard setup
"""

from core.config.registry import config_registry
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def get_actual_webhook_urls():
  """Generate actual implemented webhook URLs for Ringover dashboard"""

  # Get configuration from centralized registry
  config = config_registry.ringover

  # Get base URL from config
  base_url = config.webhook_url
  webhook_secret = config.webhook_secret

  # Define the actual webhook endpoints implemented in the system
  endpoints = [
      "/api/v1/webhooks/ringover/calls/ringing",
      "/api/v1/webhooks/ringover/calls/answered",
      "/api/v1/webhooks/ringover/calls/ended",
      "/api/v1/webhooks/ringover/calls/missed",
      "/api/v1/webhooks/ringover/voicemail",
      "/api/v1/webhooks/ringover/sms/received",
      "/api/v1/webhooks/ringover/sms/sent",
      "/api/v1/webhooks/ringover/aftercall/work",
      "/api/v1/webhooks/ringover/fax/received"
  ]

  # Generate full URLs
  full_urls = []
  if base_url:
    full_urls = [f"{base_url.rstrip('/')}{endpoint}" for endpoint in endpoints]

  return {
      'base_url': base_url,
      'webhook_secret': webhook_secret,
      'endpoints': endpoints,
      'full_urls': full_urls
  }


def main():
  """Main function to display webhook configuration"""
  urls_data = get_actual_webhook_urls()

  print("🔗 ACTUAL IMPLEMENTED WEBHOOK URLS:")
  print("=" * 80)
  print("Copy these URLs into your Ringover dashboard (one per line):")
  print()

  if urls_data['full_urls']:
    for url in urls_data['full_urls']:
      print(url)
  else:
    for endpoint in urls_data['endpoints']:
      print(endpoint)

  print()
  print("🔑 WEBHOOK KEY:")
  print(urls_data['webhook_secret'])
  print()
  print()
  print("📋 URL MAPPING:")
  print("-" * 50)
  print("POST Calls ringing     → /calls/ringing")
  print("POST Calls answered    → /calls/answered")
  print("POST Calls ended       → /calls/ended")
  print("POST Missed calls      → /calls/missed")
  print("POST Voicemail         → /voicemail")
  print("POST SMS received      → /sms/received")
  print("POST SMS sent          → /sms/sent")
  print("POST After-Call Work   → /aftercall/work")
  print("POST Faxes received    → /fax/received")
  print()
  print("⚠️  REMEMBER:")
  print("Set RINGOVER_WEBHOOK_URL and RINGOVER_WEBHOOK_SECRET in .env file!")


if __name__ == "__main__":
  main()
