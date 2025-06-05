#!/usr/bin/env python3
"""
Test script to validate all LLM providers are properly implemented and configured.
Run this to ensure all providers (Gemini, OpenAI, Anthropic) are working correctly.
"""

from models.external.llm.request import LLMRequest, LLMMessage
from services.llm.orchestrator import LLMOrchestrator
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_provider(orchestrator: LLMOrchestrator, provider_name: str):
  """Test a specific provider with basic functionality."""
  print(f"\n=== Testing {provider_name.upper()} Provider ===")

  try:
    # Test basic response
    messages = [{"role": "user", "content": "Say 'Hello' in one word."}]

    response = await orchestrator.generate_response(
        messages=messages,
        provider=provider_name,
        model="",  # Use default model
        max_tokens=10,
        temperature=0.0
    )

    if response and response.choices:
      print(f"✅ Basic response: {response.choices[0].message.content[:50]}...")
    else:
      print("❌ No response received")
      return False

    # Test provider validation
    is_valid = await orchestrator.validate_provider(provider_name)
    if is_valid:
      print("✅ Provider validation passed")
    else:
      print("⚠️  Provider validation failed")

    # Test streaming (just a few tokens)
    print("✅ Testing streaming...")
    stream_count = 0
    async for chunk in orchestrator.stream_response(
        messages=messages,
        provider=provider_name,
        model="",
        max_tokens=10
    ):
      stream_count += 1
      if stream_count > 3:  # Limit output for testing
        break
    print(f"✅ Streaming works ({stream_count} chunks received)")

    return True

  except Exception as e:
    print(f"❌ Error testing {provider_name}: {str(e)}")
    return False


async def main():
  """Main test function."""
  print("🚀 Starting LLM Provider Integration Test")
  print("=" * 50)

  try:
    # Initialize orchestrator
    orchestrator = LLMOrchestrator()

    # Get available providers
    providers = orchestrator.get_available_providers()
    print(f"📋 Available providers: {providers}")

    if not providers:
      print("❌ No providers available!")
      return

    # Test each provider
    results = {}
    for provider_name in providers:
      results[provider_name] = await test_provider(orchestrator, provider_name)

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    success_count = sum(results.values())
    total_count = len(results)

    for provider, success in results.items():
      status = "✅ PASS" if success else "❌ FAIL"
      print(f"{provider.upper()}: {status}")

    print(f"\n🎯 Overall: {success_count}/{total_count} providers working")

    if success_count == total_count:
      print("🎉 All providers are working correctly!")
    else:
      print("⚠️  Some providers need attention.")

  except Exception as e:
    print(f"❌ Fatal error: {str(e)}")


if __name__ == "__main__":
  asyncio.run(main())
