"""
PAMHoYA - Event Bus Infrastructure

Asynchronous communication infrastructure for microservices.
Enables loose coupling and event-driven workflows between services.

Copyright (c) 2025 PAMHoYA Team
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence
Lead Developer: Augustine Khumalo
"""

from datetime import datetime
from typing import List, Optional, Callable, Dict, Any
from enum import Enum
import uuid
import asyncio
from dataclasses import dataclass
import json


# ============================================================================
# MODELS
# ============================================================================

class EventType(str, Enum):
    """Event types for system workflows"""
    # Item Harmonisation events
    ITEM_HARMONISED = "item_harmonised"
    HARMONISATION_COMPLETED = "harmonisation_completed"
    
    # Data Discovery events
    DATASET_SUBMITTED = "dataset_submitted"
    DATASET_APPROVED = "dataset_approved"
    DATASET_INDEXED = "dataset_indexed"
    
    # Data Harmonisation events
    DATA_HARMONISATION_STARTED = "data_harmonisation_started"
    DATA_HARMONISATION_COMPLETED = "data_harmonisation_completed"
    
    # Summarisation events
    SUMMARY_GENERATED = "summary_generated"
    SUMMARY_APPROVED = "summary_approved"
    SUMMARY_PUBLISHED = "summary_published"
    
    # Analytics events
    ANALYTICS_UPDATED = "analytics_updated"
    REPORT_GENERATED = "report_generated"


class EventStatus(str, Enum):
    """Event processing status"""
    PUBLISHED = "published"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Event:
    """Event message"""
    id: str
    event_type: str
    source_service: str
    target_services: List[str]
    payload: Dict[str, Any]
    timestamp: datetime
    status: str = EventStatus.PUBLISHED.value
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary"""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "source_service": self.source_service,
            "target_services": self.target_services,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "retry_count": self.retry_count
        }
    
    def to_json(self) -> str:
        """Convert event to JSON"""
        return json.dumps(self.to_dict())


# ============================================================================
# EVENT BUS - CORE
# ============================================================================

class EventHandler:
    """Base event handler"""
    
    def __init__(self, event_types: List[str]):
        self.event_types = event_types
        self.id = str(uuid.uuid4())
    
    async def handle(self, event: Event) -> bool:
        """Handle event - override in subclasses"""
        raise NotImplementedError()


class EventBus:
    """
    Central Event Bus for asynchronous communication.
    Implements publish-subscribe pattern with async support.
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[EventHandler]] = {}
        self.event_queue: List[Event] = []
        self.event_history: Dict[str, Event] = {}
        self.dead_letter_queue: List[Event] = []
        self._running = False
    
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe handler to event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
        print(f"Handler {handler.id} subscribed to {event_type}")
    
    def unsubscribe(self, event_type: str, handler_id: str) -> None:
        """Unsubscribe handler from event type"""
        if event_type in self.subscribers:
            self.subscribers[event_type] = [
                h for h in self.subscribers[event_type] if h.id != handler_id
            ]
    
    async def publish(self, event: Event) -> None:
        """Publish event to bus"""
        event.id = str(uuid.uuid4())
        event.timestamp = datetime.now()
        
        self.event_queue.append(event)
        self.event_history[event.id] = event
        
        print(f"Event published: {event.event_type} ({event.id})")
        
        # Process immediately
        await self._process_event(event)
    
    async def _process_event(self, event: Event) -> None:
        """Process event through subscribers"""
        event.status = EventStatus.PROCESSING.value
        
        # Get handlers for this event type
        handlers = self.subscribers.get(event.event_type, [])
        
        if not handlers:
            print(f"WARNING: No handlers for event type {event.event_type}")
            event.status = EventStatus.COMPLETED.value
            return
        
        # Execute handlers
        results = []
        for handler in handlers:
            try:
                result = await handler.handle(event)
                results.append(result)
            except Exception as e:
                print(f"ERROR in handler {handler.id}: {str(e)}")
                event.retry_count += 1
                
                if event.retry_count >= event.max_retries:
                    self.dead_letter_queue.append(event)
                    event.status = EventStatus.FAILED.value
                else:
                    # Re-queue for retry
                    await asyncio.sleep(2 ** event.retry_count)  # Exponential backoff
                    await self._process_event(event)
                    return
        
        event.status = EventStatus.COMPLETED.value
        print(f"Event processed: {event.event_type} ({event.id})")
    
    async def start(self) -> None:
        """Start event bus processing"""
        self._running = True
        print("Event Bus started")
        
        while self._running:
            await asyncio.sleep(1)
    
    def stop(self) -> None:
        """Stop event bus"""
        self._running = False
        print("Event Bus stopped")
    
    def get_event_history(self, limit: int = 100) -> List[Dict]:
        """Get event history"""
        events = list(self.event_history.values())[-limit:]
        return [e.to_dict() for e in events]
    
    def get_dead_letter_queue(self) -> List[Dict]:
        """Get failed events"""
        return [e.to_dict() for e in self.dead_letter_queue]


# ============================================================================
# CONCRETE EVENT HANDLERS
# ============================================================================

class DatasetApprovedHandler(EventHandler):
    """Handler for when dataset is approved"""
    
    def __init__(self):
        super().__init__([EventType.DATASET_APPROVED.value])
    
    async def handle(self, event: Event) -> bool:
        """Index approved dataset"""
        dataset_id = event.payload.get("dataset_id")
        print(f"Indexing dataset {dataset_id}")
        return True


class HarmonisationCompletedHandler(EventHandler):
    """Handler for when harmonisation is completed"""
    
    def __init__(self):
        super().__init__([EventType.HARMONISATION_COMPLETED.value])
    
    async def handle(self, event: Event) -> bool:
        """Update analytics with harmonisation result"""
        result = event.payload.get("result")
        print(f"Updating analytics with harmonisation result")
        return True


class SummaryPublishedHandler(EventHandler):
    """Handler for when summary is published"""
    
    def __init__(self):
        super().__init__([EventType.SUMMARY_PUBLISHED.value])
    
    async def handle(self, event: Event) -> bool:
        """Notify stakeholders of published summary"""
        summary_id = event.payload.get("summary_id")
        print(f"Notifying stakeholders about published summary {summary_id}")
        return True


class DataHarmonisationCompletedHandler(EventHandler):
    """Handler for data harmonisation completion"""
    
    def __init__(self):
        super().__init__([EventType.DATA_HARMONISATION_COMPLETED.value])
    
    async def handle(self, event: Event) -> bool:
        """Update analytics with harmonisation completion"""
        job_id = event.payload.get("job_id")
        print(f"Recording data harmonisation job {job_id} completion")
        return True


# ============================================================================
# EVENT BUS SINGLETON
# ============================================================================

_event_bus_instance: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create event bus singleton"""
    global _event_bus_instance
    
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
        
        # Register default handlers
        _event_bus_instance.subscribe(
            EventType.DATASET_APPROVED.value,
            DatasetApprovedHandler()
        )
        _event_bus_instance.subscribe(
            EventType.HARMONISATION_COMPLETED.value,
            HarmonisationCompletedHandler()
        )
        _event_bus_instance.subscribe(
            EventType.SUMMARY_PUBLISHED.value,
            SummaryPublishedHandler()
        )
        _event_bus_instance.subscribe(
            EventType.DATA_HARMONISATION_COMPLETED.value,
            DataHarmonisationCompletedHandler()
        )
    
    return _event_bus_instance


async def publish_event(event_type: str, source_service: str, 
                       target_services: List[str], payload: Dict[str, Any]) -> Event:
    """Helper function to publish event"""
    event = Event(
        id=str(uuid.uuid4()),
        event_type=event_type,
        source_service=source_service,
        target_services=target_services,
        payload=payload,
        timestamp=datetime.now()
    )
    
    bus = get_event_bus()
    await bus.publish(event)
    return event
