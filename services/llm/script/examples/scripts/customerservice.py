"""
Customer service script example.
"""
from typing import Dict, Any


def create_customer_service_script() -> Dict[str, Any]:
  """
  Create a multi-state customer service script.

  Returns:
      Dictionary representing a customer service script
  """
  return {
      "name": "customer_service_agent",
      "description": "A customer service agent for handling inquiries",
      "version": "1.0",
      "general_prompt": "You are a customer service agent named {{agent_name}} for {{company_name}}. You're professional, helpful, and efficient.",
      "tools": [
          {
              "name": "look_up_order",
              "description": "Look up a customer order by ID",
              "parameters": {
                  "order_id": {
                      "type": "string",
                      "description": "The order ID to look up"
                  }
              },
              "required": False
          },
          {
              "name": "process_refund",
              "description": "Process a refund for a customer",
              "parameters": {
                  "order_id": {
                      "type": "string",
                      "description": "The order ID to refund"
                  },
                  "amount": {
                      "type": "number",
                      "description": "The amount to refund"
                  },
                  "reason": {
                      "type": "string",
                      "description": "The reason for the refund"
                  }
              },
              "required": False
          },
          {
              "name": "transfer_to_human",
              "description": "Transfer the call to a human agent",
              "parameters": {
                  "reason": {
                      "type": "string",
                      "description": "The reason for the transfer"
                  }
              },
              "required": False
          }
      ],
      "general_tools": ["transfer_to_human"],
      "states": [
          {
              "name": "greeting",
              "type": "initial",
              "prompt": "Start the conversation with a warm greeting. Introduce yourself as {{agent_name}} from {{company_name}} customer service. Ask how you can help the customer today.",
              "description": "Initial greeting state"
          },
          {
              "name": "identify_issue",
              "type": "information",
              "prompt": "Try to understand the customer's issue. Ask clarifying questions if needed. Show empathy for their situation.",
              "tools": ["look_up_order"],
              "description": "Identify customer issue state"
          },
          {
              "name": "resolve_issue",
              "type": "processing",
              "prompt": "Provide a solution to the customer's issue. Be specific and clear about what you're doing. If you need to process a refund, use the process_refund tool.",
              "tools": ["look_up_order", "process_refund"],
              "description": "Resolve customer issue state"
          },
          {
              "name": "closing",
              "type": "terminal",
              "prompt": "Thank the customer for contacting {{company_name}} customer service. Summarize what was done to help them. Ask if there's anything else they need help with.",
              "description": "Closing conversation state"
          }
      ],
      "edges": [
          {
              "from_state": "greeting",
              "to_state": "identify_issue",
              "condition": {
                  "type": "intent",
                  "value": "explain_problem",
                  "operator": "equals"
              },
              "description": "Customer explains their issue"
          },
          {
              "from_state": "identify_issue",
              "to_state": "resolve_issue",
              "condition": {
                  "type": "entity",
                  "value": "order_id",
                  "operator": "exists"
              },
              "description": "Order information gathered"
          },
          {
              "from_state": "resolve_issue",
              "to_state": "closing",
              "condition": {
                  "type": "intent",
                  "value": "issue_resolved",
                  "operator": "equals"
              },
              "description": "Issue has been resolved"
          }
      ],
      "starting_state": "greeting",
      "dynamic_variables": {
          "agent_name": "Customer Support Agent",
          "company_name": "Example Company"
      }
  }
