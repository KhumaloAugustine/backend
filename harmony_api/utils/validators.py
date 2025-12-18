"""
utils/validators.py

Centralized validation logic (DRY principle).
Reusable validators for common validation tasks.

Copyright (c) 2025 PAMHoYA Team
"""

import re
from typing import Any, List, Dict, Optional, Pattern
from enum import Enum

from harmony_api.core.base import ValidationError


# ============================================================================
# VALIDATION PATTERNS (Self-documented, Reusable)
# ============================================================================

class ValidationPattern(Enum):
    """Common validation patterns."""
    EMAIL = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    UUID = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    URL = r'^https?://[^\s/$.?#].[^\s]*$'
    ALPHANUMERIC = r'^[a-zA-Z0-9_-]+$'


# ============================================================================
# VALIDATOR CLASSES (Single Responsibility, Testable)
# ============================================================================

class StringValidator:
    """Validates string values."""
    
    @staticmethod
    def validate_not_empty(value: str, field_name: str = "value") -> str:
        """
        Validate string is not empty.
        
        Args:
            value: String to validate
            field_name: Field name for error message
            
        Returns:
            The validated string
            
        Raises:
            ValidationError: If string is empty
        """
        if not value or not value.strip():
            raise ValidationError(
                f"{field_name} cannot be empty",
                code="EMPTY_STRING",
                details={"field": field_name}
            )
        return value.strip()
    
    @staticmethod
    def validate_length(
        value: str,
        min_length: int = 0,
        max_length: Optional[int] = None,
        field_name: str = "value"
    ) -> str:
        """
        Validate string length.
        
        Args:
            value: String to validate
            min_length: Minimum length
            max_length: Maximum length (None = unlimited)
            field_name: Field name for error message
            
        Returns:
            The validated string
            
        Raises:
            ValidationError: If length is invalid
        """
        length = len(value)
        
        if length < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters",
                code="STRING_TOO_SHORT",
                details={
                    "field": field_name,
                    "min_length": min_length,
                    "actual_length": length
                }
            )
        
        if max_length and length > max_length:
            raise ValidationError(
                f"{field_name} must be at most {max_length} characters",
                code="STRING_TOO_LONG",
                details={
                    "field": field_name,
                    "max_length": max_length,
                    "actual_length": length
                }
            )
        
        return value
    
    @staticmethod
    def validate_pattern(
        value: str,
        pattern: Pattern | ValidationPattern,
        field_name: str = "value"
    ) -> str:
        """
        Validate string matches pattern.
        
        Args:
            value: String to validate
            pattern: Regex pattern or ValidationPattern enum
            field_name: Field name for error message
            
        Returns:
            The validated string
            
        Raises:
            ValidationError: If pattern doesn't match
        """
        regex = pattern.value if isinstance(pattern, ValidationPattern) else pattern
        
        if not re.match(regex, value):
            raise ValidationError(
                f"{field_name} has invalid format",
                code="INVALID_FORMAT",
                details={
                    "field": field_name,
                    "pattern": regex if isinstance(pattern, str) else "custom"
                }
            )
        
        return value


class ListValidator:
    """Validates list/collection values."""
    
    @staticmethod
    def validate_not_empty(
        value: List[Any],
        field_name: str = "value"
    ) -> List[Any]:
        """
        Validate list is not empty.
        
        Args:
            value: List to validate
            field_name: Field name for error message
            
        Returns:
            The validated list
            
        Raises:
            ValidationError: If list is empty
        """
        if not value or len(value) == 0:
            raise ValidationError(
                f"{field_name} cannot be empty",
                code="EMPTY_LIST",
                details={"field": field_name}
            )
        return value
    
    @staticmethod
    def validate_size(
        value: List[Any],
        min_size: int = 0,
        max_size: Optional[int] = None,
        field_name: str = "value"
    ) -> List[Any]:
        """
        Validate list size.
        
        Args:
            value: List to validate
            min_size: Minimum items
            max_size: Maximum items (None = unlimited)
            field_name: Field name for error message
            
        Returns:
            The validated list
            
        Raises:
            ValidationError: If size is invalid
        """
        size = len(value)
        
        if size < min_size:
            raise ValidationError(
                f"{field_name} must have at least {min_size} items",
                code="LIST_TOO_SHORT",
                details={
                    "field": field_name,
                    "min_size": min_size,
                    "actual_size": size
                }
            )
        
        if max_size and size > max_size:
            raise ValidationError(
                f"{field_name} must have at most {max_size} items",
                code="LIST_TOO_LONG",
                details={
                    "field": field_name,
                    "max_size": max_size,
                    "actual_size": size
                }
            )
        
        return value
    
    @staticmethod
    def validate_unique(
        value: List[Any],
        field_name: str = "value"
    ) -> List[Any]:
        """
        Validate list contains unique items.
        
        Args:
            value: List to validate
            field_name: Field name for error message
            
        Returns:
            The validated list
            
        Raises:
            ValidationError: If duplicates found
        """
        if len(value) != len(set(value)):
            raise ValidationError(
                f"{field_name} contains duplicate items",
                code="DUPLICATE_ITEMS",
                details={"field": field_name}
            )
        return value


class DictValidator:
    """Validates dictionary values."""
    
    @staticmethod
    def validate_required_keys(
        value: Dict[str, Any],
        required_keys: List[str],
        field_name: str = "value"
    ) -> Dict[str, Any]:
        """
        Validate dictionary contains required keys.
        
        Args:
            value: Dictionary to validate
            required_keys: List of required key names
            field_name: Field name for error message
            
        Returns:
            The validated dictionary
            
        Raises:
            ValidationError: If required keys missing
        """
        missing_keys = set(required_keys) - set(value.keys())
        
        if missing_keys:
            raise ValidationError(
                f"{field_name} missing required keys",
                code="MISSING_KEYS",
                details={
                    "field": field_name,
                    "missing_keys": list(missing_keys)
                }
            )
        
        return value
    
    @staticmethod
    def validate_no_extra_keys(
        value: Dict[str, Any],
        allowed_keys: List[str],
        field_name: str = "value"
    ) -> Dict[str, Any]:
        """
        Validate dictionary doesn't contain extra keys.
        
        Args:
            value: Dictionary to validate
            allowed_keys: List of allowed key names
            field_name: Field name for error message
            
        Returns:
            The validated dictionary
            
        Raises:
            ValidationError: If extra keys found
        """
        extra_keys = set(value.keys()) - set(allowed_keys)
        
        if extra_keys:
            raise ValidationError(
                f"{field_name} contains unexpected keys",
                code="EXTRA_KEYS",
                details={
                    "field": field_name,
                    "extra_keys": list(extra_keys)
                }
            )
        
        return value


class NumericValidator:
    """Validates numeric values."""
    
    @staticmethod
    def validate_range(
        value: int | float,
        min_value: Optional[int | float] = None,
        max_value: Optional[int | float] = None,
        field_name: str = "value"
    ) -> int | float:
        """
        Validate numeric value is in range.
        
        Args:
            value: Number to validate
            min_value: Minimum value (None = no minimum)
            max_value: Maximum value (None = no maximum)
            field_name: Field name for error message
            
        Returns:
            The validated number
            
        Raises:
            ValidationError: If value out of range
        """
        if min_value is not None and value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}",
                code="VALUE_TOO_LOW",
                details={
                    "field": field_name,
                    "min_value": min_value,
                    "actual_value": value
                }
            )
        
        if max_value is not None and value > max_value:
            raise ValidationError(
                f"{field_name} must be at most {max_value}",
                code="VALUE_TOO_HIGH",
                details={
                    "field": field_name,
                    "max_value": max_value,
                    "actual_value": value
                }
            )
        
        return value


# ============================================================================
# COMPOSITION VALIDATOR (DRY - Reuse validators)
# ============================================================================

class CompositeValidator:
    """Combines multiple validators (DRY principle)."""
    
    def __init__(self, validators: List[Any]):
        """
        Initialize with list of validators.
        
        Args:
            validators: List of validator functions/callables
        """
        self.validators = validators
    
    def validate(self, value: Any) -> Any:
        """
        Run all validators.
        
        Args:
            value: Value to validate
            
        Returns:
            Validated value if all validators pass
            
        Raises:
            ValidationError: If any validator fails
        """
        result = value
        for validator in self.validators:
            result = validator(result)
        return result


# ============================================================================
# USAGE EXAMPLES (Self-documented)
# ============================================================================

"""
# Single validator
StringValidator.validate_not_empty("instrument_name")

# Multiple validators (DRY)
validators = CompositeValidator([
    lambda x: StringValidator.validate_not_empty(x, "name"),
    lambda x: StringValidator.validate_length(x, min_length=3, max_length=100),
    lambda x: StringValidator.validate_pattern(x, ValidationPattern.ALPHANUMERIC),
])
validated_name = validators.validate("GAD-7")

# List validation
ListValidator.validate_not_empty(instruments, "instruments")
ListValidator.validate_size(instruments, min_size=1, max_size=50)
ListValidator.validate_unique(instrument_ids)
"""
