"""Redis data access package."""

from data.redis import connection
from data.redis import ops

__all__ = ["connection", "ops"]
