"""
routers/instruments_router.py

Example of refactored router following clean code and SOLID principles.

Key improvements:
- Thin router layer (routes only)
- Business logic in services
- Comprehensive error handling
- Type hints and documentation
- DRY validation using reusable validators

Copyright (c) 2025 PAMHoYA Team
"""

from typing import List, Optional, Dict, Any
import logging

from fastapi import APIRouter, HTTPException, Query, Depends, Body, status
from fastapi.responses import JSONResponse

from harmony_api.core.base import (
    ValidationError,
    NotFoundError,
    ServiceError,
    Result
)
from harmony_api.models.instrument import Instrument
from harmony_api.schemas.responses import (
    InstrumentResponse,
    InstrumentsListResponse,
    ErrorResponse
)
from harmony_api.utils.validators import (
    StringValidator,
    ListValidator,
    CompositeValidator
)
from harmony_api.services.instrument_service import InstrumentService
from harmony_api.services.embeddings_cache import EmbeddingsCache

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/instruments", tags=["instruments"])

# Dependencies (Dependency Injection)
def get_instrument_service() -> InstrumentService:
    """Dependency: Get instrument service instance"""
    return InstrumentService()

def get_embeddings_cache() -> EmbeddingsCache:
    """Dependency: Get embeddings cache instance"""
    return EmbeddingsCache()


# ============================================================================
# INSTRUMENTS ENDPOINTS
# ============================================================================

@router.get(
    "",
    response_model=InstrumentsListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Instruments",
    description="Retrieve list of available mental health instruments"
)
async def list_instruments(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    search: Optional[str] = Query(None, description="Filter by instrument name"),
    service: InstrumentService = Depends(get_instrument_service)
) -> InstrumentsListResponse:
    """
    List all available instruments with optional filtering and pagination.
    
    Args:
        skip: Number of instruments to skip (pagination)
        limit: Maximum instruments to return (max 100)
        search: Filter by instrument name (partial match)
        service: Injected instrument service
        
    Returns:
        InstrumentsListResponse with list of instruments and metadata
        
    Raises:
        HTTPException: If service encounters error
    """
    try:
        logger.info(f"Listing instruments: skip={skip}, limit={limit}, search={search}")
        
        # Call service (all business logic)
        result: Result[Dict[str, Any]] = service.list_instruments(
            skip=skip,
            limit=limit,
            search=search
        )
        
        # Handle service result
        if result.is_error:
            logger.error(f"Service error: {result.error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve instruments"
            )
        
        # Return formatted response
        return InstrumentsListResponse(
            instruments=result.data["instruments"],
            total=result.data["total"],
            skip=skip,
            limit=limit,
            metadata=result.metadata
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in list_instruments")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/{instrument_id}",
    response_model=InstrumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Instrument Details",
    description="Retrieve detailed information about a specific instrument"
)
async def get_instrument(
    instrument_id: str = Query(..., description="Instrument ID"),
    service: InstrumentService = Depends(get_instrument_service)
) -> InstrumentResponse:
    """
    Get detailed information about an instrument.
    
    Args:
        instrument_id: Unique identifier of instrument
        service: Injected instrument service
        
    Returns:
        InstrumentResponse with complete instrument details
        
    Raises:
        HTTPException: If instrument not found or service error
    """
    try:
        logger.info(f"Getting instrument: {instrument_id}")
        
        # Validate input
        StringValidator.validate_not_empty(instrument_id, "instrument_id")
        
        # Call service
        result: Result[Instrument] = service.get_instrument(instrument_id)
        
        # Handle service result
        if result.is_error:
            if isinstance(result.error, NotFoundError):
                logger.warning(f"Instrument not found: {instrument_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Instrument {instrument_id} not found"
                )
            
            logger.error(f"Service error: {result.error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve instrument"
            )
        
        # Return response
        return InstrumentResponse(
            data=result.data,
            metadata=result.metadata
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error getting instrument {instrument_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/search",
    response_model=InstrumentsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Instruments",
    description="Search instruments by name, keywords, or description"
)
async def search_instruments(
    query: str = Body(..., embed=True, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    service: InstrumentService = Depends(get_instrument_service)
) -> InstrumentsListResponse:
    """
    Search instruments using keyword matching.
    
    Args:
        query: Search query string
        limit: Maximum results to return
        service: Injected instrument service
        
    Returns:
        InstrumentsListResponse with matching instruments
        
    Raises:
        HTTPException: If validation fails or service error
    """
    try:
        logger.info(f"Searching instruments: query='{query}', limit={limit}")
        
        # Validate input using reusable validators (DRY)
        query = StringValidator.validate_not_empty(query, "query")
        query = StringValidator.validate_length(query, min_length=2, max_length=200, field_name="query")
        
        # Call service
        result: Result[Dict[str, Any]] = service.search_instruments(
            query=query,
            limit=limit
        )
        
        # Handle service result
        if result.is_error:
            logger.error(f"Service error: {result.error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Search failed"
            )
        
        # Return formatted response
        return InstrumentsListResponse(
            instruments=result.data["instruments"],
            total=result.data["total"],
            skip=0,
            limit=limit,
            metadata={
                **result.metadata,
                "query": query
            }
        )
    
    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error searching instruments")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/{instrument_id}/embeddings",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get Instrument Embeddings",
    description="Get semantic embeddings for instrument questions"
)
async def get_embeddings(
    instrument_id: str,
    model: Optional[str] = Query("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
    cache: EmbeddingsCache = Depends(get_embeddings_cache),
    service: InstrumentService = Depends(get_instrument_service)
) -> Dict[str, Any]:
    """
    Get semantic embeddings for instrument questions.
    
    Uses caching to avoid redundant computation.
    
    Args:
        instrument_id: Instrument ID
        model: Embedding model to use
        cache: Injected embeddings cache
        service: Injected instrument service
        
    Returns:
        Dictionary with embeddings and metadata
        
    Raises:
        HTTPException: If instrument not found or embedding fails
    """
    try:
        logger.info(f"Getting embeddings: instrument={instrument_id}, model={model}")
        
        # Validate input
        StringValidator.validate_not_empty(instrument_id, "instrument_id")
        StringValidator.validate_not_empty(model, "model")
        
        # Check cache first
        cache_key = f"{instrument_id}:{model}"
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit: {cache_key}")
            return {
                "embeddings": cached,
                "cached": True,
                "model": model,
                "instrument_id": instrument_id
            }
        
        # Get instrument from service
        inst_result = service.get_instrument(instrument_id)
        if inst_result.is_error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Instrument not found"
            )
        
        # Generate embeddings
        embed_result = service.generate_embeddings(
            instrument=inst_result.data,
            model=model
        )
        
        if embed_result.is_error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate embeddings"
            )
        
        # Cache result
        cache.set(cache_key, embed_result.data, ttl=3600)  # 1 hour TTL
        
        logger.info(f"Successfully generated embeddings: {cache_key}")
        
        return {
            "embeddings": embed_result.data,
            "cached": False,
            "model": model,
            "instrument_id": instrument_id
        }
    
    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error getting embeddings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# ERROR HANDLER (Global error handling)
# ============================================================================

@router.exception_handler(ValidationError)
async def validation_error_handler(request, exc: ValidationError):
    """Handle validation errors with consistent format"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": exc.message,
            "code": exc.code,
            "details": exc.details
        }
    )


@router.exception_handler(ServiceError)
async def service_error_handler(request, exc: ServiceError):
    """Handle service errors with consistent format"""
    logger.error(f"Service error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "ServiceError",
            "message": "Service processing failed",
            "code": exc.code,
            "details": exc.details
        }
    )


# ============================================================================
# ROUTER PATTERNS & PRINCIPLES APPLIED
# ============================================================================

"""
PATTERNS USED:
1. Dependency Injection - Services injected via Depends()
2. Result Wrapper - Services return Result[T] for consistent error handling
3. Reusable Validators - DRY principle applied
4. Thin Router Layer - Business logic in services, not routes
5. Comprehensive Error Handling - All exceptions caught and formatted
6. Logging - All operations logged at appropriate levels
7. Type Hints - Full type annotations
8. Docstrings - Comprehensive documentation
9. HTTP Status Codes - Appropriate codes for each scenario
10. Consistent Response Format - All responses follow pattern

BENEFITS:
✅ Easy to test (services are mockable)
✅ Easy to understand (separation of concerns)
✅ Easy to maintain (business logic isolated)
✅ Easy to extend (add new endpoints without changing existing code)
✅ Reliable error handling (consistent error responses)
✅ Good performance (caching support)
✅ Self-documented (type hints and docstrings)
"""
