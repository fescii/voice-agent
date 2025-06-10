"""
Create operations for tasks.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional

from data.db.models.task import Task, TaskType, TaskPriority, TaskStatus
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def create_task(
    session: AsyncSession,
    subject: str,
    owner_id: str,
    task_type: TaskType = TaskType.FOLLOW_UP,
    priority: TaskPriority = TaskPriority.NORMAL,
    **kwargs
) -> Optional[Task]:
  """
  Create a new task record.

  Args:
      session: Database session
      subject: Task subject (required)
      owner_id: Task owner/assignee ID (required)
      task_type: Type of task
      priority: Task priority
      **kwargs: Additional task fields

  Returns:
      Created Task object or None if failed
  """
  try:
    task = Task(
        subject=subject,
        owner_id=owner_id,
        task_type=task_type,
        priority=priority,
        **kwargs
    )

    session.add(task)
    await session.commit()
    await session.refresh(task)

    logger.info(f"Created task: {task.id} - {subject}")
    return task

  except SQLAlchemyError as e:
    logger.error(f"Failed to create task {subject}: {e}")
    await session.rollback()
    return None
  except Exception as e:
    logger.error(f"Unexpected error creating task {subject}: {e}")
    await session.rollback()
    return None
