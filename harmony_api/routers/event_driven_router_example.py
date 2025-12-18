"""
Event-Driven API Router Example

Demonstrates how to use the event-driven services in FastAPI routers
with clean separation of concerns and scalable architecture.

Key patterns:
- Dependency injection for services
- Async event-driven operations
- Clean error handling
- Consistent response formatting
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from harmony_api.core.base import Result
from harmony_api.core.events import EventBus, get_event_bus
from harmony_api.services.event_driven_services import (
    ServiceOrchestrator,
    InstrumentService,
    EmbeddingService,
    SearchService,
    InstrumentSearchRequestedEvent,
)


# ======================= Pydantic Models =======================

class InstrumentCreateRequest(BaseModel):
    """Request to create an instrument."""
    id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., min_length=1, max_length=50)
    data: dict = Field(default_factory=dict)


class InstrumentResponse(BaseModel):
    """Instrument response model."""
    id: str
    name: str
    category: str
    provider: str
    data: dict


class EmbeddingResponse(BaseModel):
    """Embedding response model."""
    instrument_id: str
    embedding: List[float]
    provider: str


class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    instrument_type: Optional[str] = None


class SearchResult(BaseModel):
    """Search result model."""
    id: str
    name: str
    score: float


class SearchResponse(BaseModel):
    """Search response model."""
    query: str
    results: List[SearchResult]
    count: int


class ApiResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    message: str = ""


# ======================= Dependency Injection =======================

# Global orchestrator instance (in production, use proper DI)
_orchestrator: Optional[ServiceOrchestrator] = None


async def get_orchestrator() -> ServiceOrchestrator:
    """Get or initialize service orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        event_bus = get_event_bus()
        _orchestrator = ServiceOrchestrator(event_bus)
        await _orchestrator.initialize()
    return _orchestrator


async def get_instrument_service(
    orchestrator: ServiceOrchestrator = Depends(get_orchestrator),
) -> InstrumentService:
    """Inject InstrumentService."""
    return orchestrator.instrument_service


async def get_embedding_service(
    orchestrator: ServiceOrchestrator = Depends(get_orchestrator),
) -> EmbeddingService:
    """Inject EmbeddingService."""
    return orchestrator.embedding_service


async def get_search_service(
    orchestrator: ServiceOrchestrator = Depends(get_orchestrator),
) -> SearchService:
    """Inject SearchService."""
    return orchestrator.search_service


# ======================= Router Setup =======================

router = APIRouter(
    prefix="/api/v1/instruments",
    tags=["instruments"],
    responses={404: {"description": "Not found"}},
)


# ======================= Endpoints =======================

@router.post(
    "",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an instrument",
    description="Create a new instrument. Triggers embedding and indexing automatically.",
)
async def create_instrument(
    request: InstrumentCreateRequest,
    service: InstrumentService = Depends(get_instrument_service),
) -> ApiResponse:
    """Create a new instrument.
    
    Event flow:
    1. InstrumentService creates instrument
    2. Publishes InstrumentCreatedEvent
    3. EmbeddingService picks it up and generates embeddings
    4. IndexingService indexes the embeddings
    5. Returns immediately to client
    
    Args:
        request: Instrument creation request
        service: Injected InstrumentService
        
    Returns:
        ApiResponse with created instrument ID
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        result = await service.create_instrument(
            instrument_id=request.id,
            name=request.name,
            category=request.category,
            provider=request.provider,
            data=request.data,
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(result.error),
            )
        
        return ApiResponse(
            success=True,
            data=result.data,
            message="Instrument created successfully",
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create instrument: {str(e)}",
        )


@router.get(
    "/{instrument_id}",
    response_model=ApiResponse,
    summary="Get instrument by ID",
    description="Retrieve instrument metadata.",
)
async def get_instrument(
    instrument_id: str,
    service: InstrumentService = Depends(get_instrument_service),
) -> ApiResponse:
    """Get instrument by ID.
    
    Args:
        instrument_id: Instrument identifier
        service: Injected InstrumentService
        
    Returns:
        ApiResponse with instrument data
        
    Raises:
        HTTPException: If not found
    """
    try:
        result = await service.get_instrument(instrument_id)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Instrument {instrument_id} not found",
            )
        
        return ApiResponse(
            success=True,
            data=result.data,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "",
    response_model=ApiResponse,
    summary="List all instruments",
    description="Retrieve paginated list of instruments.",
)
async def list_instruments(
    skip: int = 0,
    limit: int = 10,
    service: InstrumentService = Depends(get_instrument_service),
) -> ApiResponse:
    """List all instruments with pagination.
    
    Args:
        skip: Number to skip
        limit: Maximum to return
        service: Injected InstrumentService
        
    Returns:
        ApiResponse with list of instruments
    """
    try:
        result = await service.list_instruments()
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(result.error),
            )
        
        # Apply pagination
        items = result.data[skip : skip + limit]
        
        return ApiResponse(
            success=True,
            data={
                "items": items,
                "total": len(result.data),
                "skip": skip,
                "limit": limit,
            },
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{instrument_id}/embedding",
    response_model=ApiResponse,
    summary="Get instrument embedding",
    description="Retrieve cached embedding for instrument.",
)
async def get_embedding(
    instrument_id: str,
    service: EmbeddingService = Depends(get_embedding_service),
) -> ApiResponse:
    """Get embedding for instrument.
    
    Note: Embedding is generated automatically when instrument is created.
    This endpoint just retrieves the cached embedding.
    
    Args:
        instrument_id: Instrument identifier
        service: Injected EmbeddingService
        
    Returns:
        ApiResponse with embedding vector
        
    Raises:
        HTTPException: If embedding not found
    """
    try:
        result = await service.get_embedding(instrument_id)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Embedding for {instrument_id} not found",
            )
        
        return ApiResponse(
            success=True,
            data={
                "instrument_id": instrument_id,
                "embedding": result.data,
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/search",
    response_model=ApiResponse,
    summary="Search instruments",
    description="Search for instruments by query.",
)
async def search_instruments(
    request: SearchRequest,
    service: SearchService = Depends(get_search_service),
) -> ApiResponse:
    """Search for instruments.
    
    This is a synchronous endpoint that publishes a search event
    and returns results immediately (from vector DB).
    
    Args:
        request: Search request
        service: Injected SearchService
        
    Returns:
        ApiResponse with search results
        
    Raises:
        HTTPException: If search fails
    """
    try:
        result = await service.search(
            query=request.query,
            limit=request.limit,
            instrument_type=request.instrument_type,
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(result.error),
            )
        
        # Format search results
        search_results = [
            SearchResult(
                id=item.get("id", ""),
                name=item.get("name", ""),
                score=item.get("score", 0.0),
            )
            for item in result.data
        ]
        
        return ApiResponse(
            success=True,
            data={
                "query": request.query,
                "results": [r.dict() for r in search_results],
                "count": len(search_results),
            },
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/health/event-bus",
    response_model=ApiResponse,
    summary="Event bus health check",
    description="Get event bus statistics and health status.",
)
async def event_bus_health(
    orchestrator: ServiceOrchestrator = Depends(get_orchestrator),
) -> ApiResponse:
    """Get event bus health and statistics.
    
    Args:
        orchestrator: Injected ServiceOrchestrator
        
    Returns:
        ApiResponse with event bus statistics
    """
    try:
        stats = orchestrator.get_statistics()
        
        return ApiResponse(
            success=True,
            data=stats,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ======================= Error Handlers =======================

@router.get(
    "/test/publish-event",
    summary="Test event publishing",
    description="For testing only - publish a test event.",
    tags=["testing"],
)
async def test_publish_event(
    orchestrator: ServiceOrchestrator = Depends(get_orchestrator),
) -> ApiResponse:
    """Publish a test event (for development only).
    
    Args:
        orchestrator: Injected ServiceOrchestrator
        
    Returns:
        ApiResponse confirming event published
    """
    try:
        # Publish a test search event
        event = InstrumentSearchRequestedEvent(
            query="test query",
            limit=5,
            source="test-endpoint",
        )
        
        await orchestrator.instrument_service.event_bus.publish(event)
        
        return ApiResponse(
            success=True,
            message="Test event published successfully",
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ======================= Event Handlers =======================

async def setup_event_handlers(orchestrator: ServiceOrchestrator) -> None:
    """Setup any custom event handlers.
    
    Args:
        orchestrator: Service orchestrator
    """
    # Example: Log all completed indexing
    async def log_indexing_complete(event):
        print(f"✓ Instrument {event.instrument_id} indexed in {event.index_name}")
    
    await orchestrator.instrument_service.event_bus.subscribe(
        from harmony_api.services.event_driven_services import InstrumentIndexedEvent,
        log_indexing_complete,
    )


# ======================= Router Initialization =======================

async def init_router(app):
    """Initialize router and event handlers.
    
    Call this in your main.py startup:
    
    @app.on_event("startup")
    async def startup():
        orchestrator = await get_orchestrator()
        await setup_event_handlers(orchestrator)
        app.include_router(router)
    
    Args:
        app: FastAPI application
    """
    orchestrator = await get_orchestrator()
    await setup_event_handlers(orchestrator)
