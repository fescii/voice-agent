"""
Examples of JSON-formatted scripts with nodes and edges.
"""
import json
from typing import Dict, Any


def generate_appointment_script_json() -> str:
  """
  Generate a JSON script for appointment scheduling.

  Returns:
      Script as JSON string
  """
  script = {
      "name": "appointment_scheduling",
      "description": "Script for scheduling appointments with directed flow control",
      "version": "1.0",
      "general_prompt": "You are a helpful scheduling assistant for a medical clinic. Be professional, empathetic, and efficient.",
      "starting_state": "greeting",
      "states": [
          {
              "name": "greeting",
              "type": "initial",
              "prompt": "You are a friendly scheduling assistant. Greet the caller and ask how you can help them today. Remember to introduce yourself as {agent_name}.",
              "description": "Initial greeting state",
              "metadata": {
                  "expected_duration": "short",
                  "required": True
              }
          },
          {
              "name": "collect_information",
              "type": "information",
              "prompt": "You are collecting appointment information. Ask for the caller's name, preferred date and time for the appointment, and reason for the appointment. If they've already provided some information, only ask for what's missing.",
              "description": "Collect necessary appointment details",
              "metadata": {
                  "expected_duration": "medium",
                  "required_fields": ["name", "date", "time", "reason"]
              }
          },
          {
              "name": "check_availability",
              "type": "processing",
              "prompt": "You are checking the calendar for availability. Tell the caller you're checking the schedule. If their requested time is available, sound positive. If not, sound apologetic and suggest 2-3 alternative times close to their requested time.",
              "description": "Checking appointment availability",
              "metadata": {
                  "expected_duration": "short",
                  "simulated_delay": True
              }
          },
          {
              "name": "confirm_details",
              "type": "decision",
              "prompt": "Confirm the appointment details with the caller. Read back their name, the date and time, and the reason for the appointment. Ask if everything is correct.",
              "description": "Verify all appointment details are correct",
              "metadata": {
                  "expected_duration": "medium",
                  "decision_point": True
              }
          },
          {
              "name": "schedule_appointment",
              "type": "processing",
              "prompt": "Thank the caller for confirming the details. Let them know that you're scheduling their appointment now. Tell them they will receive a confirmation via email or text message. Ask if they'd prefer email or text message confirmation.",
              "description": "Process appointment scheduling",
              "metadata": {
                  "expected_duration": "short",
                  "confirmation_required": True
              }
          },
          {
              "name": "handle_confirmation_preference",
              "type": "information",
              "prompt": "Ask for their email address or phone number based on their confirmation preference. If they've already provided this information, confirm it with them.",
              "description": "Get preferred contact method",
              "metadata": {
                  "expected_duration": "short",
                  "required_fields": ["contact_method", "contact_info"]
              }
          },
          {
              "name": "closing",
              "type": "terminal",
              "prompt": "Thank the caller for contacting you. Wish them a good day and end the call professionally. Let them know they can call back anytime if they need to reschedule.",
              "description": "End conversation politely",
              "metadata": {
                  "expected_duration": "short",
                  "required": True
              }
          },
          {
              "name": "reschedule",
              "type": "decision",
              "prompt": "Ask the caller if they'd like to choose a different time or date. Be accommodating and apologetic that their preferred time is not available.",
              "description": "Handle reschedule request",
              "metadata": {
                  "expected_duration": "medium",
                  "decision_point": True
              }
          }
      ],
      "edges": [
          {
              "from_state": "greeting",
              "to_state": "collect_information",
              "description": "Move to collecting appointment information"
          },
          {
              "from_state": "collect_information",
              "to_state": "check_availability",
              "description": "Check availability once information is collected",
              "condition": {
                  "type": "entity_complete",
                  "value": ["name", "date", "time", "reason"],
                  "operator": "all_present"
              }
          },
          {
              "from_state": "check_availability",
              "to_state": "confirm_details",
              "description": "Time is available, confirm details",
              "condition": {
                  "type": "availability",
                  "value": True,
                  "operator": "equals"
              }
          },
          {
              "from_state": "check_availability",
              "to_state": "reschedule",
              "description": "Time not available, offer to reschedule",
              "condition": {
                  "type": "availability",
                  "value": False,
                  "operator": "equals"
              }
          },
          {
              "from_state": "reschedule",
              "to_state": "collect_information",
              "description": "Customer wants to try a different time",
              "condition": {
                  "type": "intent",
                  "value": "reschedule",
                  "operator": "equals"
              }
          },
          {
              "from_state": "reschedule",
              "to_state": "closing",
              "description": "Customer doesn't want to reschedule",
              "condition": {
                  "type": "intent",
                  "value": "cancel",
                  "operator": "equals"
              }
          },
          {
              "from_state": "confirm_details",
              "to_state": "schedule_appointment",
              "description": "Details confirmed, proceed with scheduling",
              "condition": {
                  "type": "confirmation",
                  "value": True,
                  "operator": "equals"
              }
          },
          {
              "from_state": "confirm_details",
              "to_state": "collect_information",
              "description": "Details incorrect, collect information again",
              "condition": {
                  "type": "confirmation",
                  "value": False,
                  "operator": "equals"
              }
          },
          {
              "from_state": "schedule_appointment",
              "to_state": "handle_confirmation_preference",
              "description": "Appointment scheduled, handle notification preferences"
          },
          {
              "from_state": "handle_confirmation_preference",
              "to_state": "closing",
              "description": "Notification preferences collected, finish call"
          }
      ],
      "dynamic_variables": {
          "agent_name": "Dr. Smith's Office Assistant",
          "clinic_name": "Smith Family Medical Clinic",
          "clinic_phone": "555-123-4567",
          "business_hours": "Monday through Friday, 9 AM to 5 PM"
      },
      "metadata": {
          "domain": "healthcare",
          "average_duration": "4-5 minutes",
          "success_criteria": "Appointment successfully scheduled with all required information"
      }
  }

  return json.dumps(script, indent=2)


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
