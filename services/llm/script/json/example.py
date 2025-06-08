"""
Modular script example that aggregates different script types.
This module provides a unified interface to various script generators.
"""

from .generators.appointment import generate_appointment_script_json
from .generators.customerservice import generate_customer_service_json


def get_appointment_script():
  """Get appointment booking script configuration."""
  return generate_appointment_script_json()


def get_customer_service_script():
  """Get customer service script configuration."""
  return generate_customer_service_json()


def get_all_script_examples():
  """Get all available script examples."""
  return {
      "appointment": get_appointment_script(),
      "customer_service": get_customer_service_script()
  }


# For backward compatibility
def generate_script_example(script_type="appointment"):
  """Generate script example based on type."""
  if script_type == "appointment":
    return generate_appointment_script_json()
  elif script_type == "customer_service":
    return generate_customer_service_json()
  else:
    raise ValueError(f"Unknown script type: {script_type}")
