"""
Library of reusable prompt templates.
"""
from typing import Dict, List

from .manager import PromptStructureType, PromptSection, State, Edge, PromptTemplate


def create_single_prompt_template(
    name: str,
    identity: str,
    style: str,
    tasks: str,
    guidelines: str,
    tools: List[str] = []
) -> PromptTemplate:
  """
  Create a single prompt template with standard sections.

  Args:
      name: Template name
      identity: Agent identity description
      style: Communication style guidelines
      tasks: Task and goal description
      guidelines: Response guidelines
      tools: Available tools

  Returns:
      A configured PromptTemplate
  """
  return PromptTemplate(
      name=name,
      structure_type=PromptStructureType.SINGLE,
      sections=[
          PromptSection(
              title="Identity",
              content=identity,
              weight=1.0
          ),
          PromptSection(
              title="Style Guardrails",
              content=style,
              weight=0.8
          ),
          PromptSection(
              title="Task & Goals",
              content=tasks,
              weight=1.0
          ),
          PromptSection(
              title="Response Guidelines",
              content=guidelines,
              weight=0.7
          )
      ],
      general_prompt="You are an AI voice assistant engaging in a phone conversation. Respond naturally, keep responses concise, and maintain a friendly, helpful tone.",
      general_tools=tools
  )


def create_call_center_agent_template() -> PromptTemplate:
  """
  Create a template for a call center agent with multiple states.

  Returns:
      A multi-state PromptTemplate for call center scenarios
  """
  return PromptTemplate(
      name="call_center_agent",
      structure_type=PromptStructureType.MULTI_PROMPT,
      general_prompt="You are a professional AI call center agent named {{agent_name}}. You represent {{company_name}} and are here to provide excellent customer service. Always be courteous, helpful, and efficient.",
      general_tools=["end_call", "transfer_to_human"],
      starting_state="greeting",
      states=[
          State(
              name="greeting",
              prompt="This is the start of the call. Introduce yourself by name, mention you're with {{company_name}}. Be warm and welcoming, but professional. Ask how you can help the caller today.",
              tools=[]
          ),
          State(
              name="identification",
              prompt="You need to verify the caller's identity. Ask for their full name and one piece of verification information like their email address or account number. Be courteous but thorough.",
              tools=["verify_customer"]
          ),
          State(
              name="issue_discovery",
              prompt="Listen to the customer's issue. Ask clarifying questions as needed to fully understand their problem. Show empathy for their situation. Your goal is to categorize their issue correctly.",
              tools=["categorize_issue", "check_account_status"]
          ),
          State(
              name="resolution",
              prompt="Provide a solution to the customer's issue. Be clear and concise. If you need to access specific information, use the appropriate tools. Confirm that the solution meets their needs.",
              tools=["lookup_order", "process_refund", "schedule_service"]
          ),
          State(
              name="closing",
              prompt="Thank the customer for calling {{company_name}}. Summarize what was discussed and any actions that will be taken. Offer additional help if needed. End the call politely.",
              tools=[]
          )
      ],
      edges=[
          Edge(
              from_state="greeting",
              to_state="identification",
              condition="Customer has responded to greeting",
              description="Move to identification after initial greeting"
          ),
          Edge(
              from_state="identification",
              to_state="issue_discovery",
              condition="Customer identity verified",
              description="Begin issue discovery after successful verification"
          ),
          Edge(
              from_state="issue_discovery",
              to_state="resolution",
              condition="Issue is understood",
              description="Move to resolution once issue is clear"
          ),
          Edge(
              from_state="resolution",
              to_state="closing",
              condition="Issue has been resolved",
              description="Close call after resolution"
          )
      ],
      dynamic_variables={
          "agent_name": "Support Agent",
          "company_name": "Example Company"
      }
  )


def create_sales_agent_template() -> PromptTemplate:
  """
  Create a template for a sales agent with multiple states.

  Returns:
      A multi-state PromptTemplate for sales scenarios
  """
  return PromptTemplate(
      name="sales_agent",
      structure_type=PromptStructureType.MULTI_PROMPT,
      general_prompt="You are an enthusiastic AI sales agent named {{agent_name}} for {{company_name}}. Your goal is to understand customer needs and recommend appropriate products or services. Be friendly, helpful, and persuasive without being pushy.",
      general_tools=["end_call", "transfer_to_human"],
      starting_state="greeting",
      states=[
          State(
              name="greeting",
              prompt="Warmly introduce yourself and {{company_name}}. Express appreciation for their interest. Ask an engaging open-ended question about what brought them to consider our products/services today.",
              tools=[]
          ),
          State(
              name="needs_discovery",
              prompt="Explore the customer's needs, pain points, and goals. Ask thoughtful questions to understand their situation fully. Show genuine interest in helping them find the right solution.",
              tools=["check_customer_history"]
          ),
          State(
              name="product_presentation",
              prompt="Based on the customer's needs, present relevant products or services. Highlight benefits rather than features. Use clear, compelling language. Check for understanding and interest.",
              tools=["lookup_product", "check_availability", "get_pricing"]
          ),
          State(
              name="objection_handling",
              prompt="Address any concerns or objections the customer raises. Be empathetic, non-defensive, and solution-oriented. Provide relevant information to overcome objections.",
              tools=["get_comparison", "check_reviews"]
          ),
          State(
              name="closing",
              prompt="Move the sale forward appropriately. This might mean completing a purchase, scheduling a demo, or setting up a follow-up call. Be clear about next steps. Thank them for their time.",
              tools=["process_order", "schedule_demo", "create_followup"]
          )
      ],
      edges=[
          Edge(
              from_state="greeting",
              to_state="needs_discovery",
              condition="Customer has responded to greeting",
              description="Begin needs discovery after initial connection"
          ),
          Edge(
              from_state="needs_discovery",
              to_state="product_presentation",
              condition="Customer needs are understood",
              description="Present products once needs are clear"
          ),
          Edge(
              from_state="product_presentation",
              to_state="objection_handling",
              condition="Customer raises concerns",
              description="Address objections when they arise"
          ),
          Edge(
              from_state="product_presentation",
              to_state="closing",
              condition="Customer shows interest without objections",
              description="Move to close when interest is high"
          ),
          Edge(
              from_state="objection_handling",
              to_state="closing",
              condition="Objections successfully addressed",
              description="Move to close after addressing concerns"
          )
      ],
      dynamic_variables={
          "agent_name": "Sales Consultant",
          "company_name": "Example Products Inc."
      }
  )
