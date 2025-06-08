"""
Sales script example.
"""
from typing import Dict, Any


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
