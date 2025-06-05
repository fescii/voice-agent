"""
PostgreSQL database startup service wrapper.

For implementation details, see the database subpackage.
"""
# Re-export DatabaseService from the database subpackage
from core.startup.services.database.service import DatabaseService

__all__ = ['DatabaseService']
