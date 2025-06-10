"""
Read operations for tasks.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List

from data.db.models.task import Task
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def get_task(
    session: AsyncSession,
    task_id: str
) -> Optional[Task]:
  """
  Get task by ID.

  Args:
      session: Database session
      task_id: Task ID

  Returns:
      Task object or None if not found
  """
  try:
    stmt = select(Task).where(Task.id == task_id)
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()

    if task:
      logger.debug(f"Found task: {task_id}")
    else:
      logger.debug(f"Task not found: {task_id}")

    return task

  except SQLAlchemyError as e:
    logger.error(f"Failed to get task {task_id}: {e}")
    return None


async def get_tasks_by_contact(
    session: AsyncSession,
    contact_id: str
) -> List[Task]:
  """
  Get tasks by contact ID.

  Args:
      session: Database session
      contact_id: Contact ID

  Returns:
      List of Task objects
  """
  try:
    stmt = select(Task).where(Task.contact_id == contact_id)
    result = await session.execute(stmt)
    tasks = result.scalars().all()

    logger.debug(f"Found {len(tasks)} tasks for contact: {contact_id}")
    return list(tasks)

  except SQLAlchemyError as e:
    logger.error(f"Failed to get tasks by contact {contact_id}: {e}")
    return []


async def get_tasks_by_owner(
    session: AsyncSession,
    owner_id: str
) -> List[Task]:
  """
  Get tasks by owner/assignee ID.

  Args:
      session: Database session
      owner_id: Owner ID

  Returns:
      List of Task objects
  """
  try:
    stmt = select(Task).where(Task.owner_id == owner_id)
    result = await session.execute(stmt)
    tasks = result.scalars().all()

    logger.debug(f"Found {len(tasks)} tasks for owner: {owner_id}")
    return list(tasks)

  except SQLAlchemyError as e:
    logger.error(f"Failed to get tasks by owner {owner_id}: {e}")
    return []
