"""
Call supervisor service for managing active calls.
"""
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from ...data.db.ops.call import update_call_status, get_call_by_ringover_id
from ...data.db.ops.agent import update_agent_call_count
from ...data.redis.ops.session import get_call_session, update_call_session, delete_call_session
from ...models.external.ringover.webhook import RingoverWebhookEvent
from ...models.internal.callcontext import CallContext
from ...core.logging import get_logger

logger = get_logger(__name__)


class CallSupervisor:
    """
    Service for supervising and managing active calls.
    Handles call state transitions and coordination between services.
    """
    
    def __init__(self):
        self.logger = logger
        self._active_calls: Dict[str, CallContext] = {}
    
    async def handle_call_event(
        self,
        webhook_event: RingoverWebhookEvent,
        session
    ) -> bool:
        """
        Handle call events from Ringover webhooks.
        
        Args:
            webhook_event: Webhook event data
            session: Database session
            
        Returns:
            True if event was handled successfully
        """
        try:
            event_type = webhook_event.event_type
            ringover_call_id = webhook_event.call_id
            
            self.logger.info(f"Handling call event: {event_type} for {ringover_call_id}")
            
            # Get call context
            call_log = await get_call_by_ringover_id(session, ringover_call_id)
            if not call_log:
                self.logger.warning(f"No call log found for Ringover call {ringover_call_id}")
                return False
            
            call_context = await self._get_call_context(call_log.call_id)
            if not call_context:
                self.logger.warning(f"No call context found for {call_log.call_id}")
                return False
            
            # Handle specific events
            if event_type == "call_answered":
                return await self._handle_call_answered(call_context, session)
            elif event_type == "call_hangup":
                return await self._handle_call_hangup(call_context, session)
            elif event_type == "call_failed":
                return await self._handle_call_failed(call_context, session)
            else:
                self.logger.info(f"Unhandled event type: {event_type}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to handle call event: {e}")
            return False
    
    async def _handle_call_answered(
        self,
        call_context: CallContext,
        session
    ) -> bool:
        """Handle call answered event."""
        try:
            # Update call status
            success = await update_call_status(
                session=session,
                call_id=call_context.call_id,
                status="answered",
                answered_at=datetime.utcnow()
            )
            
            if success:
                # Update context
                call_context.status = "answered"
                call_context.answered_at = datetime.utcnow()
                
                # Store updated context
                await update_call_session(
                    call_id=call_context.call_id,
                    updates=call_context.dict()
                )
                
                # Register as active call
                self._active_calls[call_context.call_id] = call_context
                
                self.logger.info(f"Call {call_context.call_id} answered and active")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to handle call answered: {e}")
            return False
    
    async def _handle_call_hangup(
        self,
        call_context: CallContext,
        session
    ) -> bool:
        """Handle call hangup event."""
        try:
            # Calculate duration
            duration = None
            if call_context.answered_at:
                duration = (datetime.utcnow() - call_context.answered_at).total_seconds()
            
            # Update call status
            success = await update_call_status(
                session=session,
                call_id=call_context.call_id,
                status="completed",
                ended_at=datetime.utcnow(),
                duration_seconds=duration
            )
            
            if success:
                # Clean up
                await self._cleanup_call(call_context, session)
                self.logger.info(f"Call {call_context.call_id} completed")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to handle call hangup: {e}")
            return False
    
    async def _handle_call_failed(
        self,
        call_context: CallContext,
        session
    ) -> bool:
        """Handle call failed event."""
        try:
            # Update call status
            success = await update_call_status(
                session=session,
                call_id=call_context.call_id,
                status="failed",
                ended_at=datetime.utcnow()
            )
            
            if success:
                # Clean up
                await self._cleanup_call(call_context, session)
                self.logger.info(f"Call {call_context.call_id} failed")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to handle call failed: {e}")
            return False
    
    async def _cleanup_call(self, call_context: CallContext, session) -> None:
        """Clean up call resources."""
        try:
            # Remove from active calls
            self._active_calls.pop(call_context.call_id, None)
            
            # Delete session data
            await delete_call_session(call_context.call_id)
            
            # Update agent call count
            await update_agent_call_count(
                session, 
                call_context.agent_id, 
                increment=-1
            )
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup call {call_context.call_id}: {e}")
    
    async def _get_call_context(self, call_id: str) -> Optional[CallContext]:
        """Get call context from Redis or memory."""
        try:
            # Try memory first
            if call_id in self._active_calls:
                return self._active_calls[call_id]
            
            # Try Redis
            session_data = await get_call_session(call_id)
            if session_data:
                return CallContext(**session_data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get call context for {call_id}: {e}")
            return None
    
    def get_active_calls(self) -> List[CallContext]:
        """Get list of active calls."""
        return list(self._active_calls.values())
    
    def get_call_count(self) -> int:
        """Get total number of active calls."""
        return len(self._active_calls)
