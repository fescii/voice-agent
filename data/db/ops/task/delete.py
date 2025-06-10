"""
Delete operations for tasks.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from data.db.models.task import Task
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def delete_task(
    session: AsyncSession,
    task_id: str
) -> bool:
  """
  Delete task by ID.

  Args:
      session: Database session
      task_id: Task ID

  Returns:
      True if deleted successfully, False otherwise
  """
  try:
    # Check if task exists first
    stmt = select(Task).where(Task.id == task_id)
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
      logger.warning(f"Task not found for deletion: {task_id}")
      return False

    # Delete the task
    stmt = delete(Task).where(Task.id == task_id)
    await session.execute(stmt)
    await session.commit()

    logger.info(f"Deleted task: {task_id}")
    return True

  except SQLAlchemyError as e:
    logger.error(f"Failed to delete task {task_id}: {e}")
    await session.rollback()
    return False
  except Exception as e:
    logger.error(f"Unexpected error deleting task {task_id}: {e}")
    await session.rollback()
    return False
