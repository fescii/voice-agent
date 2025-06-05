"""
Example usage of the script system.
"""
import asyncio
import json
from pathlib import Path

from services.llm.prompt.manager import PromptManager
from services.llm.script.manager import ScriptManager
from services.llm.script.api import ScriptAPI
from services.llm.script.examples import create_customer_service_script


async def main():
  """Example of using the script system."""

  # Create a prompt manager
  prompt_manager = PromptManager()

  # Create a script manager with the prompt manager
  script_manager = ScriptManager(prompt_manager)

  # Create an API interface for the script manager
  script_api = ScriptAPI(script_manager)

  # Get an example script
  example_script = await script_api.get_example_script("customer_service")

  # Load the script through the API
  result = await script_api.load_script_from_json(example_script, make_default=True)
  print(f"Load script result: {result}")

  # List all loaded scripts
  scripts = await script_api.list_loaded_scripts()
  print(f"Loaded scripts: {scripts}")

  # Create the script directory if it doesn't exist
  script_dir = Path("./scripts")
  script_dir.mkdir(exist_ok=True)

  # Save the example script to a file
  script_path = script_dir / "customer_service.json"
  with open(script_path, "w") as f:
    json.dump(example_script, f, indent=2)
  print(f"Saved example script to: {script_path}")

  # Load all scripts from the directory
  loaded_scripts = await script_manager.load_scripts_from_directory(script_dir)
  print(f"Loaded {len(loaded_scripts)} scripts from directory")

  # Show the available templates in the prompt manager
  templates = prompt_manager.templates
  print(f"Available templates: {list(templates.keys())}")

  # Get the default template
  default_template = prompt_manager.get_template()
  print(f"Default template: {default_template.name}")

  # Build a prompt from the template
  prompt = prompt_manager.build_prompt(
      state="greeting",
      variables={"agent_name": "Custom Agent", "company_name": "My Company"}
  )
  print(f"Built prompt: {prompt[:200]}...")  # Show just the first part


if __name__ == "__main__":
  asyncio.run(main())
