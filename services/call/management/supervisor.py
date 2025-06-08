"""
Call supervisor service - thin wrapper for backward compatibility.
"""
from .supervisor.main import CallSupervisor

__all__ = ['CallSupervisor']
