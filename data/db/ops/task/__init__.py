"""Task operations package."""

from data.db.ops.task.create import create_task
from data.db.ops.task.read import get_task, get_tasks_by_contact, get_tasks_by_owner
from data.db.ops.task.update import update_task, complete_task
from data.db.ops.task.delete import delete_task

__all__ = [
    "create_task",
    "get_task",
    "get_tasks_by_contact",
    "get_tasks_by_owner",
    "update_task",
    "complete_task",
    "delete_task"
]
