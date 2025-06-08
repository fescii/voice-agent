"""
Advanced example for script-driven voice agent flow with nodes and edges from JSON.

This module has been modularized into the demo/ subdirectory.
For backward compatibility, key functions are re-exported here.
"""

import asyncio
from pathlib import Path

# Import all components from the modular structure
from .demo import (
    ScriptStateTracker,
    advanced_script_flow_example,
    demonstrate_json_scripts,
    analyze_script_flow,
    find_longest_path
)

# Re-export for backward compatibility
__all__ = [
    'ScriptStateTracker',
    'advanced_script_flow_example',
    'demonstrate_json_scripts',
    'analyze_script_flow',
    'find_longest_path'
]


if __name__ == "__main__":
  asyncio.run(advanced_script_flow_example())
  asyncio.run(demonstrate_json_scripts())

  # Optionally analyze a specific script file
  script_path = Path.cwd() / "scripts" / "customer_service.json"
  if script_path.exists():
    asyncio.run(analyze_script_flow(script_path))
