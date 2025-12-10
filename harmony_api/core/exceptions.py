"""
PAMHoYA - Centralized Exception Handling

Provides custom exceptions and error handling utilities.
Follows DRY principle by centralizing error handling logic.

Copyright (c) 2025 PAMHoYA Team
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence
Lead Developer: Augustine Khumalo
"""

from typing import Optional, Dict, Any, Callable
from fastapi import status


# ============================================================================
# BASE EXCEPTIONS (DRY - Reusable Error Classes)
# ============================================================================

class PAMHoYAException(Exception):
    """
    Base exception for all PAMHoYA errors.
    Follows Single Responsibility Principle.
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


# ============================================================================
# DOMAIN-SPECIFIC EXCEPTIONS (Single Responsibility)
# ============================================================================

class EntityNotFoundException(PAMHoYAException):
    """Raised when an entity is not found"""
    
    def __init__(self, entity_type: str, entity_id: str, details: Optional[Dict] = None):
        message = f"{entity_type} with ID '{entity_id}' not found"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details or {"entity_type": entity_type, "entity_id": entity_id}
        )


class DuplicateEntityException(PAMHoYAException):
    """Raised when attempting to create a duplicate entity"""
    
    def __init__(self, entity_type: str, identifier: str, details: Optional[Dict] = None):
        message = f"{entity_type} '{identifier}' already exists"
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details or {"entity_type": entity_type, "identifier": identifier}
        )


class ValidationException(PAMHoYAException):
    """Raised when validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=error_details
        )


class BusinessRuleException(PAMHoYAException):
    """Raised when a business rule is violated"""
    
    def __init__(self, message: str, rule: Optional[str] = None, details: Optional[Dict] = None):
        error_details = details or {}
        if rule:
            error_details["rule"] = rule
        
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=error_details
        )


class UnauthorizedException(PAMHoYAException):
    """Raised when user lacks authorization"""
    
    def __init__(self, message: str = "Unauthorized access", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class OperationFailedException(PAMHoYAException):
    """Raised when an operation fails"""
    
    def __init__(self, operation: str, reason: str, details: Optional[Dict] = None):
        message = f"Operation '{operation}' failed: {reason}"
        error_details = details or {}
        error_details.update({"operation": operation, "reason": reason})
        
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=error_details
        )


# ============================================================================
# SERVICE-SPECIFIC EXCEPTIONS
# ============================================================================

class DatasetNotFoundException(EntityNotFoundException):
    """Raised when a dataset is not found"""
    
    def __init__(self, dataset_id: str, details: Optional[Dict] = None):
        super().__init__(
            entity_type="Dataset",
            entity_id=dataset_id,
            details=details
        )


class HarmonisationJobNotFoundException(EntityNotFoundException):
    """Raised when a harmonisation job is not found"""
    
    def __init__(self, job_id: str, details: Optional[Dict] = None):
        super().__init__(
            entity_type="Harmonisation Job",
            entity_id=job_id,
            details=details
        )


class SummaryNotFoundException(EntityNotFoundException):
    """Raised when a summary is not found"""
    
    def __init__(self, summary_id: str, details: Optional[Dict] = None):
        super().__init__(
            entity_type="Summary",
            entity_id=summary_id,
            details=details
        )


class InvalidAccessTypeException(ValidationException):
    """Raised when an invalid access type is provided"""
    
    def __init__(self, access_type: str, valid_types: list, details: Optional[Dict] = None):
        message = f"Invalid access type '{access_type}'. Valid types: {', '.join(valid_types)}"
        error_details = details or {}
        error_details.update({
            "provided": access_type,
            "valid_types": valid_types
        })
        super().__init__(message=message, field="access_type", details=error_details)


# ============================================================================
# ERROR HANDLING UTILITIES (DRY - Reusable Functions)
# ============================================================================

def handle_repository_error(error: Exception, entity_type: str, operation: str) -> PAMHoYAException:
    """
    Convert repository errors to appropriate PAMHoYA exceptions.
    Follows DRY principle - centralized error conversion logic.
    """
    if isinstance(error, PAMHoYAException):
        return error
    
    if isinstance(error, ValueError):
        return ValidationException(str(error))
    
    if isinstance(error, KeyError):
        return EntityNotFoundException(entity_type, str(error))
    
    # Default to operation failed
    return OperationFailedException(
        operation=operation,
        reason=str(error),
        details={"entity_type": entity_type}
    )


def safe_execute(func: Callable, *args, **kwargs) -> Any:
    """
    Execute function and convert exceptions to PAMHoYA exceptions.
    Follows DRY principle - reusable error handling wrapper.
    """
    try:
        return func(*args, **kwargs)
    except PAMHoYAException:
        raise
    except Exception as e:
        raise OperationFailedException(
            operation=func.__name__,
            reason=str(e)
        )
