# PAMHoYA Coding Standards

## Overview

This document defines coding standards for the PAMHoYA project to ensure consistency, maintainability, and adherence to SOLID principles and DRY (Don't Repeat Yourself) patterns.

## SOLID Principles

### 1. Single Responsibility Principle (SRP)
**Rule**: Each class should have only one reason to change.

**✅ Good Example**:
```python
class DatasetRepository(BaseRepository):
    """Handles only data access for datasets"""
    def create(self, dataset: Dataset) -> Dataset:
        return super().create(dataset)

class DataDiscoveryService(BaseService):
    """Handles only business logic for dataset discovery"""
    def search_datasets(self, query: str) -> List[Dict]:
        # Business logic here
        pass
```

**❌ Bad Example**:
```python
class DatasetService:
    """Violates SRP - mixes data access and business logic"""
    def create_dataset(self, data: Dict):
        # Data access
        self.db.insert(data)
        # Business logic
        self.send_notification()
        # Email sending
        self.smtp.send_email()
```

### 2. Open/Closed Principle (OCP)
**Rule**: Classes should be open for extension but closed for modification.

**✅ Good Example**:
```python
class FilterStrategy(ABC):
    @abstractmethod
    def apply(self, dataset: Dataset) -> bool:
        pass

class ConstructFilter(FilterStrategy):
    """New filter added without modifying existing code"""
    def apply(self, dataset: Dataset) -> bool:
        return self.construct in dataset.constructs
```

**❌ Bad Example**:
```python
def filter_datasets(datasets, filter_type, value):
    if filter_type == "construct":
        # Adding new filter requires modifying this function
        return [d for d in datasets if value in d.constructs]
    elif filter_type == "access_type":
        return [d for d in datasets if d.access_type == value]
    # Need to keep adding elif statements
```

### 3. Liskov Substitution Principle (LSP)
**Rule**: Derived classes must be substitutable for their base classes.

**✅ Good Example**:
```python
def process_repository(repo: IRepository):
    """Works with any IRepository implementation"""
    entity = repo.get("123")
    return entity

# Can use any repository
process_repository(DatasetRepository())
process_repository(SummaryRepository())
```

### 4. Interface Segregation Principle (ISP)
**Rule**: No client should be forced to depend on methods it doesn't use.

**✅ Good Example**:
```python
class IRepository(ABC):
    """Minimal interface for repositories"""
    @abstractmethod
    def create(self, entity): pass
    @abstractmethod
    def get(self, id): pass

class ISearchable(ABC):
    """Separate interface for search capability"""
    @abstractmethod
    def search(self, query): pass

class DatasetRepository(IRepository, ISearchable):
    """Only implement what's needed"""
    pass
```

### 5. Dependency Inversion Principle (DIP)
**Rule**: Depend on abstractions, not concretions.

**✅ Good Example**:
```python
class DataDiscoveryService(BaseService):
    def __init__(self, repository: IRepository):
        """Depends on interface, not concrete class"""
        super().__init__(repository)
```

**❌ Bad Example**:
```python
class DataDiscoveryService:
    def __init__(self):
        """Hard-coded dependency on concrete class"""
        self.repository = DatasetRepository()
```

## DRY (Don't Repeat Yourself)

### Principle
**Rule**: Every piece of knowledge should have a single, authoritative representation.

### Common Patterns

#### 1. Extract Duplicate Code to Base Classes

**✅ Good**:
```python
class BaseService:
    def _validate_entity_exists(self, entity_id: str, entity_name: str):
        """Reusable validation in base class"""
        entity = self.repository.get(entity_id)
        if not entity:
            raise EntityNotFoundException(entity_name, entity_id)
        return entity

class DataDiscoveryService(BaseService):
    def add_study(self, dataset_id: str):
        dataset = self._validate_entity_exists(dataset_id, "Dataset")
        # Use validated dataset
```

**❌ Bad**:
```python
class DataDiscoveryService:
    def add_study(self, dataset_id: str):
        dataset = self.repository.get(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")

class SummarisationService:
    def edit_summary(self, summary_id: str):
        summary = self.repository.get(summary_id)
        if not summary:
            raise ValueError(f"Summary {summary_id} not found")
```

#### 2. Use Helper Methods

**✅ Good**:
```python
class DataDiscoveryService(BaseService):
    def get_all_datasets(self):
        datasets = self.repository.list()
        return self._to_dict_list(datasets)  # Helper from base class
```

#### 3. Centralize Configuration

**✅ Good**:
```python
# harmony_api/core/settings.py
class Settings:
    APP_TITLE: str = "PAMHoYA API"
    PORT: int = 8000

# Use everywhere
from harmony_api.core.settings import settings
```

## Code Organization

### File Structure
```
harmony_api/
├── core/
│   ├── settings.py          # Configuration
│   ├── exceptions.py        # Custom exceptions
│   ├── middleware.py        # Middleware components
│   └── logger.py            # Logging setup
├── services/
│   ├── base_service.py      # Base classes
│   ├── data_discovery_service.py
│   ├── data_harmonisation_service.py
│   ├── summarisation_service.py
│   └── analytics_service.py
├── routers/
│   ├── data_discovery_router.py
│   ├── data_harmonisation_router.py
│   └── ...
└── utils/
    └── helpers.py           # Utility functions
```

### Naming Conventions

#### Classes
- **PascalCase** for class names
- **Descriptive names** indicating purpose
```python
class DataDiscoveryService:  # ✅ Good
class DDS:  # ❌ Bad - unclear abbreviation
```

#### Methods/Functions
- **snake_case** for method names
- **Verb-first** for actions
```python
def get_dataset(self, id: str):  # ✅ Good
def dataset(self, id: str):  # ❌ Bad - not clear it's a getter
```

#### Variables
- **snake_case** for variables
- **Descriptive names** avoiding abbreviations
```python
dataset_repository = DatasetRepository()  # ✅ Good
ds_repo = DatasetRepository()  # ❌ Bad
```

#### Constants
- **UPPER_SNAKE_CASE** for constants
```python
MAX_RESULTS_PER_PAGE = 100  # ✅ Good
maxResultsPerPage = 100  # ❌ Bad
```

## Error Handling

### Always Use Custom Exceptions

**✅ Good**:
```python
from harmony_api.core.exceptions import EntityNotFoundException

def get_dataset(self, dataset_id: str):
    dataset = self.repository.get(dataset_id)
    if not dataset:
        raise EntityNotFoundException("Dataset", dataset_id)
    return dataset
```

**❌ Bad**:
```python
def get_dataset(self, dataset_id: str):
    dataset = self.repository.get(dataset_id)
    if not dataset:
        raise Exception("Dataset not found")  # Generic exception
    return dataset
```

### Exception Hierarchy
```python
PAMHoYAException (base)
├── EntityNotFoundException
├── DuplicateEntityException
├── ValidationException
├── BusinessRuleException
└── OperationFailedException
```

## Type Hints

### Always Use Type Hints

**✅ Good**:
```python
def search_datasets(self, query: str, limit: int = 10) -> List[Dict]:
    pass
```

**❌ Bad**:
```python
def search_datasets(self, query, limit=10):
    pass
```

### Import Types
```python
from typing import List, Dict, Optional, Any, Callable
```

## Documentation

### Docstrings
Use Google-style docstrings for all public methods:

```python
def search_datasets(self, query: str, construct: Optional[str] = None) -> List[Dict]:
    """
    Search datasets by query and optional construct filter.
    
    Args:
        query: Search query string
        construct: Optional mental health construct to filter by
    
    Returns:
        List of dataset dictionaries matching criteria
    
    Raises:
        ValidationException: If query is empty
        OperationFailedException: If search operation fails
    
    Example:
        >>> service.search_datasets("depression", construct="Depressive Disorder")
        [{"id": "123", "name": "NIDS Wave 4", ...}]
    """
    pass
```

### Comments
- Use comments for **why**, not **what**
- Code should be self-explanatory

**✅ Good**:
```python
# Calculate hash for deduplication detection
metadata_hash = self._compute_hash(dataset)
```

**❌ Bad**:
```python
# Set x to 5
x = 5
```

## Testing

### Structure Tests Same as Code
```
tests/
├── services/
│   ├── test_data_discovery_service.py
│   └── test_analytics_service.py
└── routers/
    └── test_data_discovery_router.py
```

### Test Naming
```python
def test_search_datasets_returns_matching_results():
    # Test implementation
```

### Use Fixtures for Setup
```python
import pytest

@pytest.fixture
def dataset_repository():
    return DatasetRepository()

@pytest.fixture
def discovery_service(dataset_repository):
    return DataDiscoveryService(dataset_repository)

def test_get_dataset(discovery_service):
    # Use fixtures
    result = discovery_service.get_dataset("123")
    assert result is not None
```

## Best Practices

### 1. Keep Functions Small
- Aim for functions under 20 lines
- Extract complex logic to helper methods

### 2. Avoid Deep Nesting
**✅ Good**:
```python
def process_dataset(dataset_id: str):
    dataset = self._get_dataset(dataset_id)
    if not dataset:
        return None
    
    if not self._is_valid(dataset):
        return None
    
    return self._transform(dataset)
```

**❌ Bad**:
```python
def process_dataset(dataset_id: str):
    dataset = self._get_dataset(dataset_id)
    if dataset:
        if self._is_valid(dataset):
            return self._transform(dataset)
        else:
            return None
    else:
        return None
```

### 3. Use List Comprehensions
**✅ Good**:
```python
active_datasets = [d for d in datasets if d.status == "active"]
```

**❌ Bad**:
```python
active_datasets = []
for d in datasets:
    if d.status == "active":
        active_datasets.append(d)
```

### 4. Use Context Managers
```python
# For resources that need cleanup
with open("file.txt", "r") as f:
    content = f.read()
```

### 5. Avoid Magic Numbers
**✅ Good**:
```python
MAX_RETRY_ATTEMPTS = 3
for attempt in range(MAX_RETRY_ATTEMPTS):
    pass
```

**❌ Bad**:
```python
for attempt in range(3):
    pass
```

## Git Commit Messages

### Format
```
<type>: <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation changes
- `test`: Test additions/changes
- `chore`: Maintenance tasks

### Example
```
feat: Add dataset deduplication detection

- Implement metadata hash computation
- Add duplicate detection in DatasetRepository
- Raise DuplicateEntityException when duplicate found

Closes #123
```

## Code Review Checklist

- [ ] Follows SOLID principles
- [ ] No code duplication (DRY)
- [ ] Type hints provided
- [ ] Docstrings for public methods
- [ ] Custom exceptions used
- [ ] Tests added/updated
- [ ] No hard-coded values
- [ ] Error handling present
- [ ] Naming conventions followed
- [ ] No commented-out code

## Tools

### Recommended Linters
- **black**: Code formatting
- **pylint**: Code analysis
- **mypy**: Type checking
- **isort**: Import sorting

### Configuration
```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py38']

[tool.mypy]
python_version = "3.8"
strict = true

[tool.pylint]
max-line-length = 100
```

## Conclusion

Following these standards ensures:
- ✅ Consistent code across the project
- ✅ Easy maintenance and refactoring
- ✅ Better collaboration among team members
- ✅ Reduced bugs and technical debt
- ✅ Smooth transition to microservices
