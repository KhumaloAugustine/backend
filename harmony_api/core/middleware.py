"""
PAMHoYA - Middleware Components

Provides reusable middleware for error handling, logging, and cross-cutting concerns.
Follows DRY principle and Single Responsibility Principle.

Copyright (c) 2025 PAMHoYA Team
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence
Lead Developer: Augustine Khumalo
"""

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from typing import Callable, Any, Dict
from functools import wraps
import traceback
import time

from harmony_api.core.exceptions import PAMHoYAException


# ============================================================================
# ERROR HANDLING MIDDLEWARE (DRY - Centralized Error Handling)
# ============================================================================

async def error_handling_middleware(request: Request, call_next: Callable) -> Response:
    """
    Global error handling middleware.
    Catches all exceptions and returns consistent error responses.
    Follows Single Responsibility Principle.
    """
    try:
        response = await call_next(request)
        return response
    
    except PAMHoYAException as e:
        # Handle our custom exceptions
        return JSONResponse(
            status_code=e.status_code,
            content=e.to_dict()
        )
    
    except Exception as e:
        # Handle unexpected exceptions
        error_response = {
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "details": {
                "type": type(e).__name__,
                "message": str(e)
            }
        }
        
        # In development, include traceback
        # TODO: Make this conditional based on environment
        # error_response["traceback"] = traceback.format_exc()
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response
        )


# ============================================================================
# LOGGING MIDDLEWARE (DRY - Centralized Request Logging)
# ============================================================================

async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """
    Request/response logging middleware.
    Logs all API requests and responses with timing.
    Follows Single Responsibility Principle.
    """
    start_time = time.time()
    
    # Log request
    request_info = {
        "method": request.method,
        "url": str(request.url),
        "client": request.client.host if request.client else "unknown"
    }
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log response
    log_data = {
        **request_info,
        "status_code": response.status_code,
        "duration_ms": round(duration * 1000, 2)
    }
    
    # TODO: Integrate with actual logging system
    # logger.info(f"Request processed", extra=log_data)
    
    # Add custom header with processing time
    response.headers["X-Process-Time"] = str(duration)
    
    return response


# ============================================================================
# DECORATOR-BASED ERROR HANDLING (DRY - Reusable for Endpoints)
# ============================================================================

def handle_errors(func: Callable) -> Callable:
    """
    Decorator for consistent error handling in route handlers.
    Follows DRY principle - apply to any route handler.
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Dict:
        try:
            return await func(*args, **kwargs)
        except PAMHoYAException:
            # Re-raise our custom exceptions to be handled by middleware
            raise
        except ValueError as e:
            # Convert common Python exceptions to our custom exceptions
            from harmony_api.core.exceptions import ValidationException
            raise ValidationException(str(e))
        except KeyError as e:
            from harmony_api.core.exceptions import EntityNotFoundException
            raise EntityNotFoundException("Entity", str(e))
        except Exception as e:
            from harmony_api.core.exceptions import OperationFailedException
            raise OperationFailedException(
                operation=func.__name__,
                reason=str(e)
            )
    
    return wrapper


# ============================================================================
# PERFORMANCE MONITORING DECORATOR (DRY - Reusable Performance Tracking)
# ============================================================================

def monitor_performance(threshold_ms: float = 1000.0):
    """
    Decorator to monitor endpoint performance.
    Logs warning if execution exceeds threshold.
    Follows Single Responsibility Principle.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            result = await func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000  # Convert to ms
            
            if duration > threshold_ms:
                # TODO: Integrate with actual logging system
                # logger.warning(
                #     f"Slow endpoint: {func.__name__} took {duration:.2f}ms"
                # )
                pass
            
            return result
        
        return wrapper
    
    return decorator


# ============================================================================
# VALIDATION DECORATOR (DRY - Reusable Input Validation)
# ============================================================================

def validate_input(validation_func: Callable) -> Callable:
    """
    Decorator to validate input before processing.
    Follows Single Responsibility and DRY principles.
    
    Example:
        @validate_input(lambda x: x > 0)
        def process_positive_number(x: int):
            return x * 2
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Validate inputs
            try:
                validation_func(*args, **kwargs)
            except Exception as e:
                from harmony_api.core.exceptions import ValidationException
                raise ValidationException(f"Validation failed: {str(e)}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# ============================================================================
# CACHING DECORATOR (DRY - Reusable Response Caching)
# ============================================================================

class SimpleCache:
    """
    Simple in-memory cache for demonstration.
    In production, use Redis or similar.
    Follows Single Responsibility Principle.
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
    
    def get(self, key: str) -> Any:
        """Get value from cache"""
        return self._cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        self._cache[key] = value
    
    def clear(self) -> None:
        """Clear all cache"""
        self._cache.clear()


# Global cache instance
_cache = SimpleCache()


def cache_response(ttl_seconds: int = 300):
    """
    Decorator to cache endpoint responses.
    Follows DRY principle - apply to any endpoint.
    
    Args:
        ttl_seconds: Time to live for cached response (not implemented yet)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute and cache result
            result = await func(*args, **kwargs)
            _cache.set(cache_key, result)
            
            return result
        
        return wrapper
    
    return decorator
