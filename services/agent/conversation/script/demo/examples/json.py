"""
JSON script demonstration and testing.
"""

import os
from pathlib import Path

from services.llm.script.json.example import (
    generate_appointment_script_json,
    generate_customer_service_json
)
from services.agent.conversation.script.advanced import (
    create_appointment_script_with_edges,
    load_script_from_json,
    save_script_to_json,
    validate_script_structure
)


async def demonstrate_json_scripts() -> None:
  """
  Demonstrate loading and using JSON scripts.
  """
  print("\n===== JSON SCRIPT DEMONSTRATION =====\n")

  # Create scripts directory if it doesn't exist
  script_dir = Path.cwd() / "scripts"
  os.makedirs(script_dir, exist_ok=True)

  # Generate JSON examples
  appointment_json = generate_appointment_script_json()
  customer_service_json = generate_customer_service_json()

  # Save to files
  appointment_path = script_dir / "appointment.json"
  with open(appointment_path, "w") as f:
    f.write(appointment_json)

  customer_service_path = script_dir / "customer_service.json"
  with open(customer_service_path, "w") as f:
    f.write(customer_service_json)

  print(f"Generated example scripts in {script_dir}")

  # Also save the programmatic example
  programmatic_script = create_appointment_script_with_edges()
  programmatic_path = script_dir / "appointment_programmatic.json"
  await save_script_to_json(programmatic_script, programmatic_path)

  # Validate the scripts
  for script_path in [appointment_path, customer_service_path, programmatic_path]:
    print(f"\nValidating script: {script_path.name}")
    validation = await validate_script_structure(script_path)

    if validation.get("valid"):
      script = await load_script_from_json(script_path)
      if script:
        print(f"✅ Successfully loaded and validated {script.name}")
        print(f"   Number of states: {len(script.states)}")
        print(f"   Number of edges: {len(script.edges)}")
        print(f"   Starting state: {script.starting_state}")
    else:
      print(f"❌ Validation failed:")
      for error in validation.get("errors", []):
        print(f"   - {error}")

  print("\nJSON script demonstration complete!")
