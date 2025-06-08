"""
JSON script templates and constants.
"""

# Common script structure template
SCRIPT_TEMPLATE = {
    "name": "",
    "description": "",
    "version": "1.0",
    "general_prompt": "",
    "starting_state": "greeting",
    "states": [],
    "transitions": [],
    "dynamic_variables": {},
    "metadata": {}
}

# Common state types
STATE_TYPES = {
    "INITIAL": "initial",
    "INFORMATION": "information",
    "PROCESSING": "processing",
    "DECISION": "decision",
    "CONFIRMATION": "confirmation",
    "ESCALATION": "escalation",
    "TERMINAL": "terminal",
    "FINAL": "final"
}

# Common condition operators
CONDITION_OPERATORS = {
    "EQUALS": "equals",
    "NOT_EQUALS": "not_equals",
    "GREATER_THAN": "greater_than",
    "LESS_THAN": "less_than",
    "CONTAINS": "contains",
    "ALL_PRESENT": "all_present"
}

# Common condition types
CONDITION_TYPES = {
    "INTENT": "intent",
    "ENTITY_COMPLETE": "entity_complete",
    "CONFIRMATION": "confirmation",
    "AVAILABILITY": "availability",
    "INFORMATION_COMPLETE": "information_complete",
    "ATTEMPTS": "attempts"
}
