"""
Lean Service Foundation - Core Base Classes for Scalable Architecture

This module provides minimal, focused base classes:
- Service base class with logging
- Repository pattern for data access
- Cache abstraction
- Custom exception hierarchy
- Result wrapper for consistent error handling

Design principles:
- Single Responsibility: Each class has one purpose
- Dependency Inversion: Depend on abstractions
- Minimal cruft: Only essential functionality
- High cohesion: Related functionality grouped
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Generic, Optional, TypeVar, Any



# ======================= Exceptions =======================

class ErrorCode(str, Enum):
    """Standard error codes for exception handling."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"


class PAMHoYAException(Exception):
    """Base exception for all PAMHoYA errors.
    
    Attributes:
        code: Error code enum
        message: Human-readable message
        details: Additional context
    """
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict] = None,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{code.value}] {message}")


class ValidationError(PAMHoYAException):
    """Raised when validation fails."""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(ErrorCode.VALIDATION_ERROR, message, details)


class NotFoundError(PAMHoYAException):
    """Raised when resource not found."""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            ErrorCode.NOT_FOUND,
            f"{resource} not found",
            {"resource": resource, "identifier": identifier},
        )


class ConflictError(PAMHoYAException):
    """Raised on resource conflict."""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(ErrorCode.CONFLICT, message, details)


class UnauthorizedError(PAMHoYAException):
    """Raised on authorization failure."""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(ErrorCode.UNAUTHORIZED, message)


# ======================= Result Wrapper =======================

@dataclass
class Result:
    """Standardized response wrapper for all service operations.
    
    Provides:
    - Success/error status
    - Return data
    - Error information
    - Metadata
    
    Usage:
        >>> result = Result(data={"id": "123"})
        >>> if result.success:
        ...     print(result.data)
    """
    data: Optional[Any] = None
    error: Optional[Exception] = None
    message: str = ""
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def success(self) -> bool:
        """Whether operation succeeded."""
        return self.error is None

    def __repr__(self) -> str:
        if self.success:
            return f"Result(success, data={type(self.data).__name__})"
        return f"Result(error={self.error.__class__.__name__})"


# ======================= Base Service =======================

class BaseService(ABC):
    """Base class for all services.
    
    Provides:
    - Consistent logging with _log_operation
    - Service naming
    - Error handling patterns
    
    Usage:
        >>> class MyService(BaseService):
        ...     def __init__(self):
        ...         super().__init__("MyService")
        ...
        ...     async def do_work(self) -> Result:
        ...         self._log_operation("do_work", "started")
        ...         try:
        ...             result = await some_operation()
        ...             self._log_operation("do_work", "success")
        ...             return Result(data=result)
        ...         except Exception as e:
        ...             self._log_operation("do_work", "failed", {"error": str(e)})
        ...             return Result(error=e)
    """

    def __init__(self, service_name: str):
        """Initialize service.
        
        Args:
            service_name: Descriptive service name for logging
        """
        self.service_name = service_name
        self._logger = logging.getLogger(f"{__name__}.{service_name}")

    def _log_operation(
        self,
        operation: str,
        status: str,
        details: Optional[Dict] = None,
    ) -> None:
        """Log an operation with structured context.
        
        Args:
            operation: Operation name
            status: Status (started, success, failed)
            details: Additional context
        """
        details = details or {}
        log_message = f"[{self.service_name}] {operation}: {status}"
        
        if status == "failed":
            self._logger.error(log_message, extra=details)
        elif status == "started":
            self._logger.debug(log_message, extra=details)
        else:
            self._logger.info(log_message, extra=details)


# ======================= Repository Pattern =======================

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """Repository interface for data access abstraction.
    
    Enables:
    - Pluggable storage backends
    - Easy testing with mocks
    - Separation of concerns
    """

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create and persist entity.
        
        Args:
            entity: Entity to create
            
        Returns:
            Created entity with generated ID
        """
        pass

    @abstractmethod
    async def read(self, entity_id: str) -> Optional[T]:
        """Read entity by ID.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Entity or None if not found
        """
        pass

    @abstractmethod
    async def update(self, entity_id: str, entity: T) -> Optional[T]:
        """Update entity.
        
        Args:
            entity_id: Entity identifier
            entity: Updated entity
            
        Returns:
            Updated entity or None if not found
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete entity.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100) -> list[T]:
        """List entities with pagination.
        
        Args:
            skip: Number of entities to skip
            limit: Maximum entities to return
            
        Returns:
            List of entities
        """
        pass


class BaseRepository(BaseService, IRepository[T], Generic[T]):
    """Base repository implementation with common CRUD operations.
    
    In-memory storage for demonstration. Override for actual databases.
    """

    def __init__(self, repository_name: str):
        super().__init__(repository_name)
        self._storage: Dict[str, T] = {}

    async def create(self, entity: T) -> T:
        """Create entity (requires id attribute)."""
        self._log_operation("create", "started")
        try:
            self._storage[entity.id] = entity
            self._log_operation("create", "success", {"id": entity.id})
            return entity
        except Exception as e:
            self._log_operation("create", "failed", {"error": str(e)})
            raise

    async def read(self, entity_id: str) -> Optional[T]:
        """Read entity by ID."""
        return self._storage.get(entity_id)

    async def update(self, entity_id: str, entity: T) -> Optional[T]:
        """Update entity."""
        self._log_operation("update", "started", {"id": entity_id})
        try:
            if entity_id not in self._storage:
                return None
            self._storage[entity_id] = entity
            self._log_operation("update", "success", {"id": entity_id})
            return entity
        except Exception as e:
            self._log_operation("update", "failed", {"error": str(e)})
            raise

    async def delete(self, entity_id: str) -> bool:
        """Delete entity."""
        self._log_operation("delete", "started", {"id": entity_id})
        try:
            if entity_id not in self._storage:
                return False
            del self._storage[entity_id]
            self._log_operation("delete", "success", {"id": entity_id})
            return True
        except Exception as e:
            self._log_operation("delete", "failed", {"error": str(e)})
            raise

    async def list(self, skip: int = 0, limit: int = 100) -> list[T]:
        """List entities with pagination."""
        items = list(self._storage.values())
        return items[skip : skip + limit]


# ======================= Cache Abstraction =======================

class ICache(ABC, Generic[T]):
    """Cache interface for pluggable storage."""

    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL (seconds)."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear entire cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass


class BaseCache(BaseService, ICache[T], Generic[T]):
    """In-memory cache with TTL support.
    
    For production: Replace with Redis, Memcached, etc.
    """

    def __init__(self, cache_name: str):
        super().__init__(cache_name)
        self._cache: Dict[str, tuple[T, Optional[datetime]]] = {}

    async def get(self, key: str) -> Optional[T]:
        """Get value, checking expiration."""
        if key not in self._cache:
            return None

        value, expiry = self._cache[key]

        # Check if expired
        if expiry and datetime.utcnow() > expiry:
            await self.delete(key)
            return None

        return value

    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set value with optional TTL."""
        expiry = None
        if ttl:
            expiry = datetime.utcnow() + timedelta(seconds=ttl)

        self._cache[key] = (value, expiry)

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key not in self._cache:
            return False
        del self._cache[key]
        return True

    async def clear(self) -> None:
        """Clear entire cache."""
        self._cache.clear()

    async def exists(self, key: str) -> bool:
        """Check if key exists (and not expired)."""
        return await self.get(key) is not None

        if self.is_success:
            result["data"] = self.data
        else:
            result["error"] = str(self.error)
        
        return result
