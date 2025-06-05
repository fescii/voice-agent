"""
Slack notification configuration settings
"""
import os
from pydantic import BaseModel


class SlackConfig(BaseModel):
  """Slack notification configuration"""

  # API settings
  bot_token: str = ""
  webhook_url: str = ""
  api_base_url: str = "https://slack.com/api"

  # Channel settings
  default_channel: str = "#general"

  class Config:
    env_file = ".env"
    env_prefix = "SLACK_"

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    # Load from environment variables
    self.bot_token = os.getenv("SLACK_BOT_TOKEN", self.bot_token)
    self.webhook_url = os.getenv("SLACK_WEBHOOK_URL", self.webhook_url)
    self.api_base_url = os.getenv("SLACK_API_BASE_URL", self.api_base_url)
    self.default_channel = os.getenv(
        "SLACK_DEFAULT_CHANNEL", self.default_channel)
