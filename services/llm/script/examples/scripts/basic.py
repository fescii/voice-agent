"""
Basic assistant script example.
"""
from typing import Dict, Any


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
