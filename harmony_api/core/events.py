"""
Event Bus and Event System for Scalable, Decoupled Architecture

This module provides:
- Event base class and types
- EventBus for pub/sub pattern
- Event handlers and subscriptions
- Async event processing
- Event filtering and routing

Example:
    Creating and publishing events:
    >>> class UserCreatedEvent(Event):
    ...     user_id: str
    ...     email: str
    
    >>> bus = EventBus()
    >>> await bus.subscribe(UserCreatedEvent, send_welcome_email_handler)
    >>> await bus.publish(UserCreatedEvent(user_id="123", email="user@example.com"))

    Listening to events:
    >>> async def send_welcome_email_handler(event: UserCreatedEvent):
    ...     await mail_service.send(event.email, "Welcome!")
"""

import asyncio
import logging
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type
from uuid import uuid4


logger = logging.getLogger(__name__)


# ======================= Event Types =======================

class EventPriority(str, Enum):
    """Event priority levels for processing order."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Event(ABC):
    """Base class for all domain events.
    
    Attributes:
        event_id: Unique identifier for this event instance
        timestamp: When the event was created (UTC)
        priority: Processing priority (LOW, NORMAL, HIGH, CRITICAL)
        source: Service/component that created the event
        metadata: Additional context data
    """
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: EventPriority = EventPriority.NORMAL
    source: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.event_id)


# ======================= Event Handlers =======================

class EventHandler:
    """Wrapper for event handler with metadata."""
    
    def __init__(
        self,
        handler: Callable,
        event_type: Type[Event],
        async_mode: bool = True,
        priority: int = 0,
    ):
        """Initialize handler.
        
        Args:
            handler: Callable that processes the event
            event_type: Type of event this handler processes
            async_mode: Whether handler should run async
            priority: Execution priority (higher = first)
        """
        self.handler = handler
        self.event_type = event_type
        self.async_mode = async_mode
        self.priority = priority
        self.execution_count = 0
        self.last_execution_time = None
        self.last_error = None

    async def execute(self, event: Event) -> bool:
        """Execute the handler.
        
        Args:
            event: Event to process
            
        Returns:
            True if successful, False if error
        """
        try:
            start = datetime.utcnow()
            
            if asyncio.iscoroutinefunction(self.handler):
                await self.handler(event)
            else:
                self.handler(event)
            
            self.execution_count += 1
            self.last_execution_time = (datetime.utcnow() - start).total_seconds()
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(
                f"Handler {self.handler.__name__} failed for {event.__class__.__name__}",
                exc_info=True
            )
            return False


# ======================= Event Bus =======================

class EventBus:
    """
    Asynchronous Event Bus for decoupled service communication.
    
    Implements pub/sub pattern with:
    - Multiple handlers per event
    - Async/sync handler support
    - Event priority handling
    - Error handling and resilience
    - Event filtering
    - Dead letter queue
    
    Example:
        >>> bus = EventBus()
        >>> await bus.subscribe(OrderCreated, process_order)
        >>> await bus.subscribe(OrderCreated, send_notification)
        >>> await bus.publish(OrderCreated(order_id="123"))
    """
    
    def __init__(self, max_retries: int = 3, error_callback: Optional[Callable] = None):
        """Initialize EventBus.
        
        Args:
            max_retries: Maximum retry attempts for failed handlers
            error_callback: Called when handler fails after retries
        """
        self._handlers: Dict[Type[Event], List[EventHandler]] = {}
        self._event_history: List[Event] = []
        self._dead_letter_queue: List[tuple[Event, Exception]] = []
        self._max_retries = max_retries
        self._error_callback = error_callback
        self._lock = asyncio.Lock()
        self._running = False
        self._logger = logging.getLogger(f"{__name__}.EventBus")

    async def subscribe(
        self,
        event_type: Type[Event],
        handler: Callable,
        async_mode: bool = True,
        priority: int = 0,
    ) -> None:
        """Subscribe to event type.
        
        Args:
            event_type: Event class to subscribe to
            handler: Callable(event) -> None
            async_mode: Whether to run async
            priority: Execution order (higher first)
        """
        async with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            
            event_handler = EventHandler(
                handler=handler,
                event_type=event_type,
                async_mode=async_mode,
                priority=priority,
            )
            
            self._handlers[event_type].append(event_handler)
            
            # Sort by priority (highest first)
            self._handlers[event_type].sort(
                key=lambda x: x.priority,
                reverse=True
            )
            
            self._logger.info(
                f"Subscribed {handler.__name__} to {event_type.__name__}"
            )

    async def unsubscribe(
        self,
        event_type: Type[Event],
        handler: Callable,
    ) -> bool:
        """Unsubscribe from event type.
        
        Args:
            event_type: Event class to unsubscribe from
            handler: Handler to remove
            
        Returns:
            True if handler was removed, False if not found
        """
        async with self._lock:
            if event_type not in self._handlers:
                return False
            
            original_length = len(self._handlers[event_type])
            self._handlers[event_type] = [
                h for h in self._handlers[event_type]
                if h.handler != handler
            ]
            
            removed = len(self._handlers[event_type]) < original_length
            if removed:
                self._logger.info(
                    f"Unsubscribed {handler.__name__} from {event_type.__name__}"
                )
            
            return removed

    async def publish(self, event: Event) -> None:
        """Publish event to all subscribers.
        
        Args:
            event: Event to publish
        """
        self._event_history.append(event)
        
        if event.__class__ not in self._handlers:
            self._logger.debug(f"No handlers for {event.__class__.__name__}")
            return

        handlers = self._handlers[event.__class__].copy()
        
        self._logger.info(
            f"Publishing {event.__class__.__name__} to {len(handlers)} handlers"
        )

        # Execute handlers in priority order
        tasks = []
        for handler in handlers:
            if handler.async_mode:
                tasks.append(self._execute_with_retry(event, handler))
            else:
                try:
                    success = await handler.execute(event)
                    if not success:
                        await self._handle_error(event, handler)
                except Exception as e:
                    self._dead_letter_queue.append((event, e))
                    self._logger.error(f"Handler execution failed: {e}")

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    self._logger.error(f"Task failed: {result}")

    async def _execute_with_retry(
        self,
        event: Event,
        handler: EventHandler,
    ) -> None:
        """Execute handler with retry logic.
        
        Args:
            event: Event to process
            handler: Handler to execute
        """
        for attempt in range(self._max_retries):
            try:
                success = await handler.execute(event)
                if success:
                    return
            except Exception as e:
                if attempt == self._max_retries - 1:
                    self._dead_letter_queue.append((event, e))
                    await self._handle_error(event, handler)
                    return
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)

    async def _handle_error(
        self,
        event: Event,
        handler: EventHandler,
    ) -> None:
        """Handle handler error."""
        if self._error_callback:
            try:
                if asyncio.iscoroutinefunction(self._error_callback):
                    await self._error_callback(event, handler)
                else:
                    self._error_callback(event, handler)
            except Exception as e:
                self._logger.error(f"Error callback failed: {e}")

    def get_subscribers(self, event_type: Type[Event]) -> List[str]:
        """Get list of handler names for event type.
        
        Args:
            event_type: Event class
            
        Returns:
            List of handler names
        """
        if event_type not in self._handlers:
            return []
        
        return [h.handler.__name__ for h in self._handlers[event_type]]

    def get_event_history(
        self,
        event_type: Optional[Type[Event]] = None,
        limit: int = 100,
    ) -> List[Event]:
        """Get event history.
        
        Args:
            event_type: Filter by event type (optional)
            limit: Maximum events to return
            
        Returns:
            List of events
        """
        history = self._event_history
        
        if event_type:
            history = [e for e in history if isinstance(e, event_type)]
        
        return history[-limit:]

    def get_dead_letter_queue(self) -> List[tuple[Event, str]]:
        """Get failed events.
        
        Returns:
            List of (event, error_message) tuples
        """
        return [(e, str(ex)) for e, ex in self._dead_letter_queue]

    def clear_dead_letter_queue(self) -> None:
        """Clear failed events queue."""
        count = len(self._dead_letter_queue)
        self._dead_letter_queue.clear()
        self._logger.info(f"Cleared {count} events from dead letter queue")

    def get_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics.
        
        Returns:
            Dictionary with stats about event processing
        """
        total_handlers = sum(len(h) for h in self._handlers.values())
        
        handler_stats = {}
        for event_type, handlers in self._handlers.items():
            handler_stats[event_type.__name__] = {
                "handler_count": len(handlers),
                "handlers": [
                    {
                        "name": h.handler.__name__,
                        "executions": h.execution_count,
                        "last_duration": h.last_execution_time,
                        "last_error": h.last_error,
                    }
                    for h in handlers
                ]
            }

        return {
            "total_handlers": total_handlers,
            "event_types": len(self._handlers),
            "event_history_size": len(self._event_history),
            "dead_letter_queue_size": len(self._dead_letter_queue),
            "handler_details": handler_stats,
        }


# ======================= Utility Functions =======================

def create_event(
    event_class: Type[Event],
    source: str,
    priority: EventPriority = EventPriority.NORMAL,
    **data,
) -> Event:
    """Factory function to create events with defaults.
    
    Args:
        event_class: Event class to instantiate
        source: Service creating the event
        priority: Event priority
        **data: Event data
        
    Returns:
        Event instance
    """
    return event_class(
        source=source,
        priority=priority,
        **data,
    )


# Singleton instance (optional, can create per service)
_default_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create default event bus singleton.
    
    Returns:
        EventBus instance
    """
    global _default_bus
    if _default_bus is None:
        _default_bus = EventBus()
    return _default_bus


def set_event_bus(bus: EventBus) -> None:
    """Set the default event bus instance.
    
    Args:
        bus: EventBus to use
    """
    global _default_bus
    _default_bus = bus
