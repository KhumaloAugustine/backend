"""
PAMHoYA - Base Service Classes

Provides base classes and interfaces for all services following SOLID principles.
Implements Interface Segregation, Single Responsibility, and Dependency Inversion.

Copyright (c) 2025 PAMHoYA Team
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence
Lead Developer: Augustine Khumalo
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic, Callable
from datetime import datetime
import uuid


# ============================================================================
# GENERIC TYPE DEFINITIONS
# ============================================================================

TEntity = TypeVar('TEntity')
TRepository = TypeVar('TRepository', bound='BaseRepository')


# ============================================================================
# INTERFACE SEGREGATION PRINCIPLE - Separate Interfaces
# ============================================================================

class IRepository(ABC):
    """
    Base repository interface (Interface Segregation Principle).
    All repositories must implement these core methods.
    """
    
    @abstractmethod
    def create(self, entity: Any) -> Any:
        """Create a new entity"""
        pass
    
    @abstractmethod
    def get(self, entity_id: str) -> Optional[Any]:
        """Get entity by ID"""
        pass
    
    @abstractmethod
    def list(self) -> List[Any]:
        """List all entities"""
        pass
    
    @abstractmethod
    def update(self, entity_id: str, **kwargs) -> Optional[Any]:
        """Update an entity"""
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete an entity"""
        pass


class IService(ABC):
    """
    Base service interface (Interface Segregation Principle).
    All services must implement initialization.
    """
    
    @abstractmethod
    def __init__(self, repository: IRepository):
        """Initialize service with repository (Dependency Inversion)"""
        pass


# ============================================================================
# BASE REPOSITORY IMPLEMENTATION (DRY Principle)
# ============================================================================

class BaseRepository(IRepository, Generic[TEntity]):
    """
    Base repository implementation providing common CRUD operations.
    Follows Single Responsibility and DRY principles.
    """
    
    def __init__(self):
        self.storage: Dict[str, TEntity] = {}
    
    def create(self, entity: TEntity) -> TEntity:
        """Create entity (DRY - common implementation)"""
        if not hasattr(entity, 'id'):
            raise ValueError("Entity must have an 'id' attribute")
        self.storage[entity.id] = entity
        return entity
    
    def get(self, entity_id: str) -> Optional[TEntity]:
        """Get entity by ID (DRY - common implementation)"""
        return self.storage.get(entity_id)
    
    def list(self) -> List[TEntity]:
        """List all entities (DRY - common implementation)"""
        return list(self.storage.values())
    
    def update(self, entity_id: str, **kwargs) -> Optional[TEntity]:
        """
        Update entity fields (DRY - common implementation).
        Automatically updates 'updated_at' if present.
        """
        entity = self.get(entity_id)
        if not entity:
            return None
        
        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        # Auto-update timestamp if entity has updated_at field
        if hasattr(entity, 'updated_at'):
            entity.updated_at = datetime.now()
        
        return entity
    
    def delete(self, entity_id: str) -> bool:
        """Delete entity (DRY - common implementation)"""
        if entity_id in self.storage:
            del self.storage[entity_id]
            return True
        return False
    
    def filter(self, predicate: Callable) -> List[TEntity]:
        """
        Filter entities by predicate (DRY - reusable filtering).
        Follows Open/Closed Principle - extensible without modification.
        """
        return [entity for entity in self.storage.values() if predicate(entity)]
    
    def exists(self, entity_id: str) -> bool:
        """Check if entity exists (DRY - common operation)"""
        return entity_id in self.storage
    
    def count(self) -> int:
        """Count total entities (DRY - common operation)"""
        return len(self.storage)


# ============================================================================
# BASE SERVICE IMPLEMENTATION (DRY Principle)
# ============================================================================

class BaseService(IService, Generic[TRepository]):
    """
    Base service implementation.
    Follows Single Responsibility and Dependency Inversion principles.
    """
    
    def __init__(self, repository: TRepository):
        """
        Initialize service with repository (Dependency Inversion Principle).
        Services depend on abstractions (IRepository), not concrete implementations.
        """
        if not isinstance(repository, IRepository):
            raise TypeError("Repository must implement IRepository interface")
        self.repository = repository
    
    def _validate_entity_exists(self, entity_id: str, entity_name: str = "Entity") -> Any:
        """
        Validate entity exists and return it (DRY - reusable validation).
        Raises ValueError if not found.
        """
        entity = self.repository.get(entity_id)
        if not entity:
            raise ValueError(f"{entity_name} with ID '{entity_id}' not found")
        return entity
    
    def _to_dict(self, entity: Any) -> Dict:
        """
        Convert entity to dictionary (DRY - reusable conversion).
        Assumes entity has a to_dict method.
        """
        if hasattr(entity, 'to_dict'):
            return entity.to_dict()
        raise NotImplementedError(f"Entity {type(entity).__name__} must implement to_dict method")
    
    def _to_dict_list(self, entities: List[Any]) -> List[Dict]:
        """Convert list of entities to dictionaries (DRY - reusable conversion)"""
        return [self._to_dict(entity) for entity in entities]


# ============================================================================
# BASE ENTITY MODELS (DRY Principle)
# ============================================================================

class BaseEntity(ABC):
    """
    Base entity with common fields.
    Follows Single Responsibility and DRY principles.
    """
    
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    @abstractmethod
    def to_dict(self) -> Dict:
        """Convert entity to dictionary (must be implemented by subclasses)"""
        pass
    
    def _base_dict(self) -> Dict:
        """
        Get base dictionary fields (DRY - reusable in subclass to_dict).
        Subclasses should call this and extend with their own fields.
        """
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class EntityWithTimestamp(BaseEntity):
    """
    Entity with timestamp management (already existed, keeping for compatibility).
    Now extends BaseEntity for consistency.
    """
    pass


# ============================================================================
# FACTORY PATTERN (DRY for Service Creation)
# ============================================================================

class ServiceFactory:
    """
    Factory for creating services (Single Responsibility Principle).
    Centralizes service instantiation logic.
    """
    
    @staticmethod
    def create_service(service_class: type, repository_class: type, *args, **kwargs):
        """
        Create service instance with repository.
        Follows Dependency Inversion - creates both repository and service.
        """
        repository = repository_class(*args, **kwargs)
        return service_class(repository)
