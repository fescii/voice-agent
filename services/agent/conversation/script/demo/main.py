"""
Main entry point for script demonstrations.
"""

import asyncio
from pathlib import Path

from .examples import advanced_script_flow_example, demonstrate_json_scripts
from .analysis import analyze_script_flow


async def main():
  """Run all demo examples."""
  await advanced_script_flow_example()
  await demonstrate_json_scripts()

  # Optionally analyze a specific script file
  script_path = Path.cwd() / "scripts" / "customer_service.json"
  if script_path.exists():
    await analyze_script_flow(script_path)


if __name__ == "__main__":
  asyncio.run(main())
