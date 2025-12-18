"""
Event-Driven Service Architecture using Event Bus

This module demonstrates:
- Decoupled services using events
- Service separation for scalability
- Event-driven communication
- Service isolation and independence

Architecture:
    [Service A] --publish--> [EventBus] <--subscribe-- [Service B]
                                           <--subscribe-- [Service C]
    
    Services don't know about each other, only about events.
    Each service can scale independently.
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from harmony_api.core.base import BaseService, Result
from harmony_api.core.events import Event, EventBus, EventPriority, get_event_bus


logger = logging.getLogger(__name__)


# ======================= Domain Events =======================

@dataclass
class InstrumentCreatedEvent(Event):
    """Emitted when instrument is created."""
    instrument_id: str
    name: str
    category: str
    provider: str


@dataclass
class InstrumentEmbeddingRequestedEvent(Event):
    """Emitted when embedding is requested for instrument."""
    instrument_id: str
    instrument_data: Dict
    provider: str


@dataclass
class InstrumentEmbeddingCompletedEvent(Event):
    """Emitted when embedding is completed."""
    instrument_id: str
    embedding_vector: List[float]
    provider: str
    duration_ms: float


@dataclass
class InstrumentIndexedEvent(Event):
    """Emitted when instrument is indexed."""
    instrument_id: str
    index_name: str
    timestamp: str


@dataclass
class InstrumentSearchRequestedEvent(Event):
    """Emitted when search is requested."""
    query: str
    limit: int
    instrument_type: Optional[str] = None


@dataclass
class InstrumentSearchCompletedEvent(Event):
    """Emitted when search completes."""
    query: str
    results_count: int
    duration_ms: float


# ======================= Core Services (Separated) =======================

class InstrumentService(BaseService):
    """Service: Manages instrument CRUD operations.
    
    Responsibilities:
    - Create instruments
    - Update instruments
    - Delete instruments
    - Retrieve instrument metadata
    
    Does NOT:
    - Handle embeddings
    - Handle search
    - Handle indexing
    
    Publishes:
    - InstrumentCreatedEvent
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        super().__init__("InstrumentService")
        self.event_bus = event_bus or get_event_bus()
        self.instruments_db: Dict = {}

    async def create_instrument(
        self,
        instrument_id: str,
        name: str,
        category: str,
        provider: str,
        data: Dict,
    ) -> Result[Dict]:
        """Create a new instrument."""
        try:
            self._log_operation("create_instrument", "started", {
                "instrument_id": instrument_id
            })
            
            # Store in "database"
            self.instruments_db[instrument_id] = {
                "id": instrument_id,
                "name": name,
                "category": category,
                "provider": provider,
                "data": data,
            }
            
            # Publish event - other services will handle embeddings/indexing
            event = InstrumentCreatedEvent(
                instrument_id=instrument_id,
                name=name,
                category=category,
                provider=provider,
                source="InstrumentService",
                priority=EventPriority.HIGH,
            )
            await self.event_bus.publish(event)
            
            self._log_operation("create_instrument", "success", {
                "instrument_id": instrument_id
            })
            
            return Result(data={"id": instrument_id, "status": "created"})
            
        except Exception as e:
            self._log_operation("create_instrument", "failed", {"error": str(e)})
            return Result(error=e)

    async def get_instrument(self, instrument_id: str) -> Result[Dict]:
        """Retrieve instrument by ID."""
        try:
            if instrument_id not in self.instruments_db:
                return Result(error=ValueError(f"Instrument {instrument_id} not found"))
            
            return Result(data=self.instruments_db[instrument_id])
            
        except Exception as e:
            return Result(error=e)

    async def list_instruments(self) -> Result[List[Dict]]:
        """List all instruments."""
        try:
            return Result(data=list(self.instruments_db.values()))
        except Exception as e:
            return Result(error=e)


class EmbeddingService(BaseService):
    """Service: Handles embedding generation.
    
    Responsibilities:
    - Generate embeddings
    - Manage embedding providers
    - Cache embeddings
    
    Does NOT:
    - Manage instruments
    - Handle search
    - Handle indexing
    
    Subscribes to:
    - InstrumentCreatedEvent
    - InstrumentEmbeddingRequestedEvent
    
    Publishes:
    - InstrumentEmbeddingCompletedEvent
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        super().__init__("EmbeddingService")
        self.event_bus = event_bus or get_event_bus()
        self.embeddings_cache: Dict[str, List[float]] = {}

    async def initialize(self) -> None:
        """Initialize event subscriptions."""
        await self.event_bus.subscribe(
            InstrumentCreatedEvent,
            self._handle_instrument_created,
        )
        await self.event_bus.subscribe(
            InstrumentEmbeddingRequestedEvent,
            self._handle_embedding_requested,
        )
        logger.info("EmbeddingService initialized and subscribed to events")

    async def _handle_instrument_created(self, event: InstrumentCreatedEvent) -> None:
        """Handle instrument creation - request embedding."""
        self._log_operation("_handle_instrument_created", "processing", {
            "instrument_id": event.instrument_id
        })
        
        # Request embedding for newly created instrument
        embedding_event = InstrumentEmbeddingRequestedEvent(
            instrument_id=event.instrument_id,
            instrument_data={"name": event.name, "category": event.category},
            provider=event.provider,
            source="EmbeddingService",
            priority=EventPriority.HIGH,
        )
        await self.event_bus.publish(embedding_event)

    async def _handle_embedding_requested(
        self,
        event: InstrumentEmbeddingRequestedEvent,
    ) -> None:
        """Generate embedding for instrument."""
        self._log_operation("_handle_embedding_requested", "processing", {
            "instrument_id": event.instrument_id
        })
        
        # Simulate embedding generation (in reality, call OpenAI/HuggingFace/etc)
        embedding_vector = await self._generate_embedding(
            event.instrument_data,
            event.provider,
        )
        
        # Cache embedding
        self.embeddings_cache[event.instrument_id] = embedding_vector
        
        # Publish completion event
        completion_event = InstrumentEmbeddingCompletedEvent(
            instrument_id=event.instrument_id,
            embedding_vector=embedding_vector,
            provider=event.provider,
            duration_ms=150.0,
            source="EmbeddingService",
            priority=EventPriority.NORMAL,
        )
        await self.event_bus.publish(completion_event)

    async def _generate_embedding(
        self,
        data: Dict,
        provider: str,
    ) -> List[float]:
        """Generate embedding vector (simulated)."""
        # In production: call actual embedding provider
        await asyncio.sleep(0.15)  # Simulate API call
        # Return mock embedding (usually 1536 or 384 dimensions)
        return [0.1 * i for i in range(10)]

    async def get_embedding(self, instrument_id: str) -> Result[List[float]]:
        """Retrieve cached embedding."""
        try:
            if instrument_id not in self.embeddings_cache:
                return Result(error=ValueError("Embedding not found"))
            
            return Result(data=self.embeddings_cache[instrument_id])
            
        except Exception as e:
            return Result(error=e)


class IndexingService(BaseService):
    """Service: Handles indexing and persistence.
    
    Responsibilities:
    - Index embeddings
    - Persist to vector DB
    - Manage indexes
    
    Does NOT:
    - Generate embeddings
    - Manage instruments
    - Handle search
    
    Subscribes to:
    - InstrumentEmbeddingCompletedEvent
    
    Publishes:
    - InstrumentIndexedEvent
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        super().__init__("IndexingService")
        self.event_bus = event_bus or get_event_bus()
        self.indexed_items: Dict[str, str] = {}

    async def initialize(self) -> None:
        """Initialize event subscriptions."""
        await self.event_bus.subscribe(
            InstrumentEmbeddingCompletedEvent,
            self._handle_embedding_completed,
        )
        logger.info("IndexingService initialized and subscribed to events")

    async def _handle_embedding_completed(
        self,
        event: InstrumentEmbeddingCompletedEvent,
    ) -> None:
        """Index embedding when ready."""
        self._log_operation("_handle_embedding_completed", "processing", {
            "instrument_id": event.instrument_id
        })
        
        # Simulate indexing to vector DB
        await self._index_to_db(
            event.instrument_id,
            event.embedding_vector,
            event.provider,
        )
        
        # Publish indexing completion
        indexed_event = InstrumentIndexedEvent(
            instrument_id=event.instrument_id,
            index_name=f"instruments_{event.provider}",
            timestamp="2025-12-15T10:30:00Z",
            source="IndexingService",
            priority=EventPriority.NORMAL,
        )
        await self.event_bus.publish(indexed_event)

    async def _index_to_db(
        self,
        instrument_id: str,
        embedding: List[float],
        provider: str,
    ) -> None:
        """Index to vector database (simulated)."""
        # In production: call Pinecone/Weaviate/Milvus/etc
        await asyncio.sleep(0.1)  # Simulate DB write
        self.indexed_items[instrument_id] = f"indexed_{provider}"
        self._log_operation("_index_to_db", "success", {
            "instrument_id": instrument_id
        })


class SearchService(BaseService):
    """Service: Handles search operations.
    
    Responsibilities:
    - Execute searches
    - Query vector DB
    - Return results
    
    Does NOT:
    - Generate embeddings
    - Manage instruments
    - Handle indexing
    
    Subscribes to:
    - InstrumentSearchRequestedEvent
    
    Publishes:
    - InstrumentSearchCompletedEvent
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        super().__init__("SearchService")
        self.event_bus = event_bus or get_event_bus()

    async def initialize(self) -> None:
        """Initialize event subscriptions."""
        await self.event_bus.subscribe(
            InstrumentSearchRequestedEvent,
            self._handle_search_requested,
        )
        logger.info("SearchService initialized and subscribed to events")

    async def _handle_search_requested(
        self,
        event: InstrumentSearchRequestedEvent,
    ) -> None:
        """Execute search and publish results."""
        self._log_operation("_handle_search_requested", "processing", {
            "query": event.query
        })
        
        # Simulate search
        results = await self._search_db(
            event.query,
            event.limit,
            event.instrument_type,
        )
        
        # Publish completion
        completion_event = InstrumentSearchCompletedEvent(
            query=event.query,
            results_count=len(results),
            duration_ms=50.0,
            source="SearchService",
            priority=EventPriority.NORMAL,
        )
        await self.event_bus.publish(completion_event)

    async def _search_db(
        self,
        query: str,
        limit: int,
        instrument_type: Optional[str],
    ) -> List[Dict]:
        """Search vector database (simulated)."""
        # In production: call vector DB search API
        await asyncio.sleep(0.05)  # Simulate search latency
        return [{"id": f"result_{i}", "score": 0.95} for i in range(min(limit, 5))]

    async def search(
        self,
        query: str,
        limit: int = 10,
        instrument_type: Optional[str] = None,
    ) -> Result[List[Dict]]:
        """Execute search (synchronous interface)."""
        try:
            event = InstrumentSearchRequestedEvent(
                query=query,
                limit=limit,
                instrument_type=instrument_type,
                source="SearchService",
                priority=EventPriority.HIGH,
            )
            await self.event_bus.publish(event)
            
            # In production, would wait for async result via callback/queue
            results = await self._search_db(query, limit, instrument_type)
            return Result(data=results)
            
        except Exception as e:
            return Result(error=e)


# ======================= Service Orchestration =======================

class ServiceOrchestrator:
    """Orchestrates service initialization and event bus setup.
    
    Handles:
    - Service creation
    - Event bus configuration
    - Service startup/shutdown
    - Lifecycle management
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_event_bus()
        self.instrument_service: Optional[InstrumentService] = None
        self.embedding_service: Optional[EmbeddingService] = None
        self.indexing_service: Optional[IndexingService] = None
        self.search_service: Optional[SearchService] = None

    async def initialize(self) -> None:
        """Initialize all services."""
        logger.info("Initializing ServiceOrchestrator")
        
        # Create services
        self.instrument_service = InstrumentService(self.event_bus)
        self.embedding_service = EmbeddingService(self.event_bus)
        self.indexing_service = IndexingService(self.event_bus)
        self.search_service = SearchService(self.event_bus)
        
        # Initialize subscriber services (those that listen to events)
        await self.embedding_service.initialize()
        await self.indexing_service.initialize()
        await self.search_service.initialize()
        
        logger.info("ServiceOrchestrator initialized successfully")

    async def shutdown(self) -> None:
        """Shutdown all services."""
        logger.info("Shutting down ServiceOrchestrator")
        # In production: cleanup connections, flush caches, etc.

    def get_statistics(self) -> Dict:
        """Get event bus and service statistics."""
        return {
            "event_bus": self.event_bus.get_statistics(),
            "services": {
                "instrument": self.instrument_service.__class__.__name__,
                "embedding": self.embedding_service.__class__.__name__,
                "indexing": self.indexing_service.__class__.__name__,
                "search": self.search_service.__class__.__name__,
            }
        }
