"""
Example usage and demo scripts.
"""

from ..generators import generate_appointment_script_json, generate_customer_service_json
import json


def demo_appointment_script():
  """Demonstrate appointment script generation."""
  print("=== Appointment Script Demo ===")
  script_json = generate_appointment_script_json()
  script = json.loads(script_json)

  print(f"Script Name: {script['name']}")
  print(f"Description: {script['description']}")
  print(f"States: {len(script['states'])}")
  print(f"Transitions: {len(script['transitions'])}")
  print(f"Domain: {script['metadata']['domain']}")
  print()


def demo_customer_service_script():
  """Demonstrate customer service script generation."""
  print("=== Customer Service Script Demo ===")
  script_json = generate_customer_service_json()
  script = json.loads(script_json)

  print(f"Script Name: {script['name']}")
  print(f"Description: {script['description']}")
  print(f"States: {len(script['states'])}")
  print(f"Edges: {len(script['edges'])}")
  print(f"Domain: {script['metadata']['domain']}")
  print()


def demo_all_scripts():
  """Demonstrate all available scripts."""
  demo_appointment_script()
  demo_customer_service_script()


if __name__ == "__main__":
  demo_all_scripts()
