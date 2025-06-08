"""
Customer service script generator.
"""
import json
from typing import Dict, Any


def generate_customer_service_json() -> str:
  """
  Generate a JSON script for customer service call handling.

  Returns:
      Script as JSON string
  """
  script = {
      "name": "customer_service",
      "description": "Call script for handling customer service inquiries",
      "version": "1.0",
      "general_prompt": "You are a helpful customer service representative for a retail company. Be professional, friendly, and focused on resolving customer issues efficiently.",
      "starting_state": "greeting",
      "states": [
          {
              "name": "greeting",
              "type": "initial",
              "prompt": "Greet the customer warmly and ask how you can help them today. Introduce yourself as {agent_name} from {company_name}.",
              "description": "Initial greeting",
              "metadata": {
                  "tone": "warm",
                  "priority": "high"
              }
          },
          {
              "name": "identify_customer",
              "type": "information",
              "prompt": "Ask for the customer's name and order number or account information to look up their details.",
              "description": "Identify customer in system",
              "metadata": {
                  "required_fields": ["customer_name", "identifier"]
              }
          },
          {
              "name": "categorize_issue",
              "type": "decision",
              "prompt": "Listen to the customer's issue and categorize it as one of: order status, return request, product complaint, billing issue, or general inquiry.",
              "description": "Determine issue category",
              "metadata": {
                  "categories": ["order_status", "return", "complaint", "billing", "general"]
              }
          },
          {
              "name": "order_status",
              "type": "information",
              "prompt": "Look up the order status and provide details to the customer. Let them know the current status, estimated delivery date, and any relevant tracking information.",
              "description": "Handle order status inquiry"
          },
          {
              "name": "return_request",
              "type": "processing",
              "prompt": "Assist the customer with their return request. Ask for the reason for the return, verify their order details, and explain the return process step by step.",
              "description": "Process return request"
          },
          {
              "name": "handle_complaint",
              "type": "processing",
              "prompt": "Address the customer's complaint empathetically. Listen to their concerns, apologize for the inconvenience, and explore possible solutions.",
              "description": "Handle product or service complaint"
          },
          {
              "name": "resolve_billing",
              "type": "processing",
              "prompt": "Help resolve the customer's billing issue. Verify the billing details, explain any charges, and offer to correct any errors.",
              "description": "Handle billing inquiries"
          },
          {
              "name": "general_inquiry",
              "type": "information",
              "prompt": "Provide helpful information in response to the customer's general inquiry. Be informative and thorough.",
              "description": "Handle general questions"
          },
          {
              "name": "escalate_issue",
              "type": "decision",
              "prompt": "Determine if this issue needs to be escalated to a supervisor. If the customer is unsatisfied or if the issue is complex, offer to transfer them.",
              "description": "Consider escalation"
          },
          {
              "name": "resolution_confirmation",
              "type": "decision",
              "prompt": "Ask the customer if their issue has been resolved or if they have any other questions or concerns.",
              "description": "Confirm resolution"
          },
          {
              "name": "additional_assistance",
              "type": "decision",
              "prompt": "Ask if there's anything else you can help with today.",
              "description": "Offer additional help"
          },
          {
              "name": "closing",
              "type": "terminal",
              "prompt": "Thank the customer for contacting customer service. Express appreciation for their business and wish them a great day.",
              "description": "Close conversation"
          }
      ],
      "edges": [
          {
              "from_state": "greeting",
              "to_state": "identify_customer",
              "description": "After greeting, identify the customer"
          },
          {
              "from_state": "identify_customer",
              "to_state": "categorize_issue",
              "description": "After identifying customer, determine their issue",
              "condition": {
                  "type": "entity_complete",
                  "value": ["customer_name"],
                  "operator": "all_present"
              }
          },
          {
              "from_state": "categorize_issue",
              "to_state": "order_status",
              "condition": {
                  "type": "intent",
                  "value": "check_order",
                  "operator": "equals"
              }
          },
          {
              "from_state": "categorize_issue",
              "to_state": "return_request",
              "condition": {
                  "type": "intent",
                  "value": "return",
                  "operator": "equals"
              }
          },
          {
              "from_state": "categorize_issue",
              "to_state": "handle_complaint",
              "condition": {
                  "type": "intent",
                  "value": "complain",
                  "operator": "equals"
              }
          },
          {
              "from_state": "categorize_issue",
              "to_state": "resolve_billing",
              "condition": {
                  "type": "intent",
                  "value": "billing",
                  "operator": "equals"
              }
          },
          {
              "from_state": "categorize_issue",
              "to_state": "general_inquiry",
              "condition": {
                  "type": "intent",
                  "value": "general",
                  "operator": "equals"
              }
          },
          {
              "from_state": "order_status",
              "to_state": "resolution_confirmation",
              "description": "After handling order status, check if resolved"
          },
          {
              "from_state": "return_request",
              "to_state": "resolution_confirmation",
              "description": "After processing return, check if resolved"
          },
          {
              "from_state": "handle_complaint",
              "to_state": "escalate_issue",
              "description": "After handling complaint, consider escalation"
          },
          {
              "from_state": "resolve_billing",
              "to_state": "resolution_confirmation",
              "description": "After resolving billing, check if resolved"
          },
          {
              "from_state": "general_inquiry",
              "to_state": "resolution_confirmation",
              "description": "After answering inquiry, check if resolved"
          },
          {
              "from_state": "escalate_issue",
              "to_state": "resolution_confirmation",
              "condition": {
                  "type": "intent",
                  "value": "no_escalation",
                  "operator": "equals"
              }
          },
          {
              "from_state": "escalate_issue",
              "to_state": "closing",
              "description": "End call after escalation decision",
              "condition": {
                  "type": "intent",
                  "value": "escalate",
                  "operator": "equals"
              }
          },
          {
              "from_state": "resolution_confirmation",
              "to_state": "additional_assistance",
              "condition": {
                  "type": "confirmation",
                  "value": True,
                  "operator": "equals"
              }
          },
          {
              "from_state": "resolution_confirmation",
              "to_state": "categorize_issue",
              "description": "If not resolved, identify new issue",
              "condition": {
                  "type": "confirmation",
                  "value": False,
                  "operator": "equals"
              }
          },
          {
              "from_state": "additional_assistance",
              "to_state": "categorize_issue",
              "description": "If more help needed, identify new issue",
              "condition": {
                  "type": "confirmation",
                  "value": True,
                  "operator": "equals"
              }
          },
          {
              "from_state": "additional_assistance",
              "to_state": "closing",
              "description": "If no more help needed, close conversation",
              "condition": {
                  "type": "confirmation",
                  "value": False,
                  "operator": "equals"
              }
          }
      ],
      "dynamic_variables": {
          "agent_name": "Alex",
          "company_name": "Global Retail Solutions",
          "support_hours": "24/7",
          "return_policy_days": "30"
      },
      "metadata": {
          "domain": "retail",
          "average_duration": "5-8 minutes",
          "success_criteria": "Customer issue resolved with high satisfaction"
      }
  }

  return json.dumps(script, indent=2)
