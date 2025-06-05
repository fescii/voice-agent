"""
Test the startup context integration.
"""
import asyncio
import sys
from core.startup.manager import StartupManager
from core.logging.setup import setup_logging


async def test_startup_context():
  """Test the startup context system."""
  # Configure logging
  setup_logging()

  # Create startup manager
  manager = StartupManager()

  try:
    # Use context manager to handle startup/shutdown
    async with manager.startup_context() as context:
      print(f"\n{'=' * 50}")
      print(f"Application started at: {context.startup_time}")
      print(f"{'=' * 50}")

      # Display service status
      for name, service in context.services.items():
        status_emoji = "✅" if service.status == "running" else "❌"
        print(f"{status_emoji} {name}: {service.status}")

        if service.metadata:
          for key, value in service.metadata.items():
            print(f"   - {key}: {value}")

      # Check healthy services
      print(f"\nHealthy services: {context.get_healthy_services()}")
      print(f"Failed services: {context.get_failed_services()}")
      print(
          f"Overall health: {'✅ Healthy' if context.is_healthy() else '❌ Unhealthy'}")

      print(f"\n{'=' * 50}")
      input("Press Enter to continue and cleanup services...")

  except Exception as e:
    print(f"Error during startup context test: {e}")
    return 1

  return 0


if __name__ == "__main__":
  exit_code = asyncio.run(test_startup_context())
  sys.exit(exit_code)
