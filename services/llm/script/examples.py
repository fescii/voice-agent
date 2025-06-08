"""
Examples of JSON-based prompt scripts.
Backward compatibility wrapper for modularized script examples.
"""

# Import from modularized components
from .examples import (
    create_basic_script,
    create_customer_service_script,
    create_sales_script
)

# Re-export all functions for backward compatibility
__all__ = [
    'create_basic_script',
    'create_customer_service_script',
    'create_sales_script'
]
