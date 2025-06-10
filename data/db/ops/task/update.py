"""
Update operations for tasks.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from datetime import datetime, timezone

from data.db.models.task import Task, TaskStatus
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def update_task(
    session: AsyncSession,
    task_id: str,
    **kwargs
) -> Optional[Task]:
  """
  Update task information.

  Args:
      session: Database session
      task_id: Task ID
      **kwargs: Fields to update

  Returns:
      Updated Task object or None if failed
  """
  try:
    # Add updated timestamp
    kwargs["updated_at"] = datetime.now(timezone.utc)

    stmt = update(Task).where(Task.id == task_id).values(**kwargs)
    await session.execute(stmt)
    await session.commit()

    # Get updated task
    stmt = select(Task).where(Task.id == task_id)
    result = await session.execute(stmt)
    updated_task = result.scalar_one_or_none()

    if updated_task:
      logger.info(f"Updated task: {task_id}")
      return updated_task
    else:
      logger.warning(f"Task not found for update: {task_id}")
      return None

  except SQLAlchemyError as e:
    logger.error(f"Failed to update task {task_id}: {e}")
    await session.rollback()
    return None
  except Exception as e:
    logger.error(f"Unexpected error updating task {task_id}: {e}")
    await session.rollback()
    return None


async def complete_task(
    session: AsyncSession,
    task_id: str,
    **kwargs
) -> Optional[Task]:
  """
  Mark task as completed.

  Args:
      session: Database session
      task_id: Task ID
      **kwargs: Additional fields to update

  Returns:
      Updated Task object or None if failed
  """
  try:
    update_data = {
        "status": TaskStatus.COMPLETED,
        "completed_date": datetime.now(timezone.utc),
        "completion_percentage": "100",
        **kwargs
    }

    return await update_task(session, task_id, **update_data)

  except Exception as e:
    logger.error(f"Unexpected error completing task {task_id}: {e}")
    return None
