"""
Test database service imports and basic functionality.
"""
import asyncio
from core.startup.services.database import DatabaseService


async def test_database_service():
  """Test the database service initialization."""
  try:
    print("Creating DatabaseService instance...")
    db_service = DatabaseService()
    print("Instance created successfully!")

    print(f"Service name: {db_service.name}")
    print(f"Is critical: {db_service.is_critical}")

    print("Test completed successfully!")
  except Exception as e:
    print(f"Test failed: {e}")

if __name__ == "__main__":
  print("Starting database service test...")
  asyncio.run(test_database_service())
