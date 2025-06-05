"""
Examples of JSON-based prompt scripts.
"""
from typing import Dict, Any

from services.llm.script.schema import (
    ScriptSchema,
    ScriptSection,
    State,
    Edge,
    ToolDefinition,
    StateType,
    EdgeCondition
)


def create_basic_script() -> Dict[str, Any]:
  """
  Create a basic single-prompt script.

  Returns:
      Dictionary representing a basic script
  """
  return {
      "name": "basic_assistant",
      "description": "A simple assistant script",
      "version": "1.0",
      "general_prompt": "You are a helpful AI assistant. Answer questions clearly and concisely.",
      "sections": [
          {
              "title": "Identity",
              "content": "You are a friendly and professional AI assistant.",
              "weight": 1.0
          },
          {
              "title": "Style",
              "content": "Keep your responses concise and focused on answering the question.",
              "weight": 0.8
          },
          {
              "title": "Knowledge",
              "content": "You have access to general knowledge, but admit when you don't know something.",
              "weight": 0.9
          }
      ],
      "dynamic_variables": {
          "assistant_name": "AI Helper",
          "company_name": "Example Corp"
      }
  }


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


def create_sales_script() -> Dict[str, Any]:
  """
  Create a multi-state sales script.

  Returns:
      Dictionary representing a sales script
  """
  return {
      "name": "sales_agent",
      "description": "A sales agent for product inquiries and purchases",
      "version": "1.0",
      "general_prompt": "You are a sales agent for {{company_name}}. You're friendly, knowledgeable about our products, and helpful without being pushy.",
      "tools": [
          {
              "name": "get_product_info",
              "description": "Get information about a product",
              "parameters": {
                  "product_id": {
                      "type": "string",
                      "description": "The product ID to look up"
                  }
              },
              "required": False
          },
          {
              "name": "check_availability",
              "description": "Check if a product is in stock",
              "parameters": {
                  "product_id": {
                      "type": "string",
                      "description": "The product ID to check"
                  },
                  "quantity": {
                      "type": "number",
                      "description": "The quantity desired"
                  }
              },
              "required": False
          },
          {
              "name": "create_order",
              "description": "Create a new order",
              "parameters": {
                  "product_id": {
                      "type": "string",
                      "description": "The product ID to order"
                  },
                  "quantity": {
                      "type": "number",
                      "description": "The quantity to order"
                  },
                  "customer_info": {
                      "type": "object",
                      "description": "Customer information"
                  }
              },
              "required": False
          }
      ],
      "states": [
          {
              "name": "greeting",
              "type": "initial",
              "prompt": "Greet the customer warmly. Introduce yourself as a sales representative from {{company_name}}. Ask how you can assist them with our products today.",
              "description": "Initial greeting state"
          },
          {
              "name": "needs_discovery",
              "type": "information",
              "prompt": "Ask questions to understand what the customer is looking for. Try to determine their needs, preferences, and budget constraints.",
              "description": "Discover customer needs state"
          },
          {
              "name": "product_recommendation",
              "type": "information",
              "prompt": "Based on the customer's needs, recommend appropriate products. Describe key features and benefits. Use the get_product_info tool to provide accurate information.",
              "tools": ["get_product_info"],
              "description": "Recommend products state"
          },
          {
              "name": "handle_objections",
              "type": "decision",
              "prompt": "Address any concerns or objections the customer may have. Provide additional information or alternatives as needed. Be understanding but highlight the value of our products.",
              "tools": ["get_product_info", "check_availability"],
              "description": "Handle objections state"
          },
          {
              "name": "close_sale",
              "type": "processing",
              "prompt": "Guide the customer through the purchase process. Ask if they're ready to place an order. Use the create_order tool to process their purchase.",
              "tools": ["check_availability", "create_order"],
              "description": "Close sale state"
          },
          {
              "name": "follow_up",
              "type": "terminal",
              "prompt": "Thank the customer for their time or purchase. Summarize next steps. Offer additional assistance if needed.",
              "description": "Follow up state"
          }
      ],
      "edges": [
          {
              "from_state": "greeting",
              "to_state": "needs_discovery",
              "description": "Begin needs discovery after greeting"
          },
          {
              "from_state": "needs_discovery",
              "to_state": "product_recommendation",
              "condition": {
                  "type": "intent",
                  "value": "needs_identified",
                  "operator": "equals"
              },
              "description": "Customer needs identified"
          },
          {
              "from_state": "product_recommendation",
              "to_state": "handle_objections",
              "condition": {
                  "type": "sentiment",
                  "value": "negative",
                  "operator": "equals"
              },
              "description": "Customer has objections"
          },
          {
              "from_state": "product_recommendation",
              "to_state": "close_sale",
              "condition": {
                  "type": "sentiment",
                  "value": "positive",
                  "operator": "equals"
              },
              "description": "Customer interested in product"
          },
          {
              "from_state": "handle_objections",
              "to_state": "close_sale",
              "condition": {
                  "type": "intent",
                  "value": "objection_addressed",
                  "operator": "equals"
              },
              "description": "Objections successfully addressed"
          },
          {
              "from_state": "close_sale",
              "to_state": "follow_up",
              "description": "Complete sale and follow up"
          }
      ],
      "starting_state": "greeting",
      "dynamic_variables": {
          "agent_name": "Sales Consultant",
          "company_name": "Example Products Inc."
      }
  }
