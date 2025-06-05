#!/usr/bin/env python3
"""
Example usage of the Gemini LLM provider.

This script demonstrates how to use the GeminiProvider class for both
single response generation and streaming responses.

Make sure to set the GEMINI_API_KEY environment variable or update
the config dictionary with your API key.
"""
from models.external.llm.request import LLMRequest, LLMMessage
from services.llm.providers.gemini import GeminiProvider
import asyncio
import os
from typing import List, Dict

# Add the project root to the path for imports
import sys
sys.path.append('/home/femar/A03/voice')


async def test_gemini_provider():
  """Test the Gemini provider with various scenarios."""

  # Initialize the provider
  config = {
      "api_key": os.getenv("GEMINI_API_KEY", ""),
      "model": "gemini-pro",
      "temperature": 0.7,
      "max_tokens": 150
  }

  provider = GeminiProvider(config)

  # Test configuration validation
  print("Testing configuration validation...")
  is_valid = await provider.validate_config()
  print(f"Configuration valid: {is_valid}")

  if not is_valid:
    print("❌ Provider configuration is invalid. Please check your API key.")
    return

  print("✅ Provider configuration is valid!")

  # Test single response generation
  print("\n" + "="*50)
  print("Testing single response generation...")
  print("="*50)

  messages = [
      LLMMessage(
          role="system", content="You are a helpful AI assistant for a voice agent system."),
      LLMMessage(
          role="user", content="Hello! Can you briefly explain what you are?")
  ]

  request = LLMRequest(
      messages=messages,
      model="gemini-pro",
      temperature=0.7,
      max_tokens=150
  )

  try:
    response = await provider.generate_response(request)
    print(f"Response ID: {response.id}")
    print(f"Provider: {response.provider}")
    print(f"Model: {response.model}")
    print(f"Content: {response.get_content()}")
    if response.usage:
      print(f"Token usage: {response.usage.total_tokens} total tokens")
  except Exception as e:
    print(f"❌ Error generating response: {e}")
    return

  # Test streaming response
  print("\n" + "="*50)
  print("Testing streaming response...")
  print("="*50)

  stream_messages = [
      LLMMessage(
          role="system", content="You are a helpful voice assistant. Keep responses conversational and concise."),
      LLMMessage(
          role="user", content="Tell me a short story about an AI helping people.")
  ]

  stream_request = LLMRequest(
      messages=stream_messages,
      model="gemini-pro",
      temperature=0.8,
      max_tokens=200,
      stream=True
  )

  try:
    print("Streaming response:")
    print("-" * 30)
    async for chunk in provider.stream_response(stream_request):
      print(chunk, end="", flush=True)
    print("\n" + "-" * 30)
    print("✅ Streaming completed successfully!")
  except Exception as e:
    print(f"❌ Error streaming response: {e}")
    return

  # Test conversation with multiple turns
  print("\n" + "="*50)
  print("Testing multi-turn conversation...")
  print("="*50)

  conversation = [
      LLMMessage(
          role="system", content="You are a customer service voice agent. Be helpful and professional."),
      LLMMessage(
          role="user", content="I'm having trouble with my account login."),
      LLMMessage(role="assistant", content="I'd be happy to help you with your account login issue. Can you tell me what specific problem you're experiencing?"),
      LLMMessage(
          role="user", content="I forgot my password and the reset email isn't coming through.")
  ]

  conversation_request = LLMRequest(
      messages=conversation,
      model="gemini-pro",
      temperature=0.6,
      max_tokens=100
  )

  try:
    conv_response = await provider.generate_response(conversation_request)
    print("Multi-turn conversation response:")
    print(f"Assistant: {conv_response.get_content()}")
    print("✅ Multi-turn conversation test completed!")
  except Exception as e:
    print(f"❌ Error in conversation: {e}")


async def main():
  """Main function to run the tests."""
  print("🚀 Starting Gemini Provider Tests")
  print("="*60)

  # Check if API key is available
  api_key = os.getenv("GEMINI_API_KEY")
  if not api_key:
    print("⚠️  Warning: GEMINI_API_KEY environment variable not set.")
    print("Please set it with your Google AI Studio API key to test the provider.")
    print("\nExample:")
    print("export GEMINI_API_KEY='your-api-key-here'")
    print("python examples/test_gemini_provider.py")
    return

  await test_gemini_provider()
  print("\n" + "="*60)
  print("🏁 Tests completed!")


if __name__ == "__main__":
  asyncio.run(main())
