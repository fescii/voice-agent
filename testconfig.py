#!/usr/bin/env python3
"""
Quick test to verify centralized configuration is working.
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_config_registry():
  """Test that the config registry initializes properly."""
  try:
    # Import and initialize the registry
    from core.config.registry import config_registry

    print("✓ Config registry imported successfully")

    # Initialize the registry
    config_registry.initialize()
    print("✓ Config registry initialized successfully")

    # Test accessing different configs
    print(f"✓ Database config: {config_registry.database}")
    print(f"✓ Redis config: {config_registry.redis}")
    print(f"✓ Ringover config: {config_registry.ringover}")
    print(f"✓ LLM config: {config_registry.llm}")
    print(f"✓ STT config: {config_registry.stt}")
    print(f"✓ TTS config: {config_registry.tts}")
    print(f"✓ WebSocket config: {config_registry.websocket}")

    print("\n🎉 All configuration tests passed!")
    return True

  except Exception as e:
    print(f"❌ Configuration test failed: {e}")
    import traceback
    traceback.print_exc()
    return False


if __name__ == "__main__":
  success = test_config_registry()
  sys.exit(0 if success else 1)
