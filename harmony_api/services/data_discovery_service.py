"""
PAMHoYA - Data Discovery Service

Manages mental health dataset metadata catalogue with comprehensive search,
curation, deduplication, and discovery features. Implements dataset-centric
discovery with hierarchical organization: Constructs -> Datasets -> Studies.

Features:
- Global full-text search across all dataset fields
- Construct-based filtering (mental health disorders/conditions)
- Access type management (Open, Restricted, Formal Request)
- Smart access actions (direct links, pre-filled emails, portal navigation)
- Dataset modal with linked studies and evidence
- Deduplication and data quality checks

Follows 3-layer architecture: API Layer -> Business Logic -> Data Access Layer
Implements SOLID principles and DRY (Don't Repeat Yourself)

Copyright (c) 2025 PAMHoYA Team
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence
Lead Developer: Augustine Khumalo
"""

from datetime import datetime
from typing import List, Optional, Any, Dict, Set, Callable
from enum import Enum
import uuid
import hashlib
from abc import ABC, abstractmethod

# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class AccessType(str, Enum):
    """Dataset access type enumerations"""
    OPEN = "Open"
    RESTRICTED = "Restricted"
    FORMAL_REQUEST = "Formal Request"


class DatasetStatus(str, Enum):
    """Dataset status enumerations"""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class RequestStatus(str, Enum):
    """Access request status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ============================================================================
# UTILITY CLASSES (SRP - Single Responsibility Principle)
# ============================================================================

class Serializable(ABC):
    """Abstract base class for serializable models (Interface Segregation)"""
    @abstractmethod
    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        pass


class EntityWithTimestamp(Serializable):
    """Base class for entities with timestamps (DRY)"""
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def _to_dict_base(self) -> dict:
        """Base dictionary representation"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class TextSearchable:
    """Mixin for full-text search capability (DRY)"""
    def get_searchable_text(self) -> str:
        """Get all text fields as single searchable string"""
        raise NotImplementedError
    
    def matches_query(self, query: str) -> bool:
        """Check if entity matches query string"""
        return query.lower() in self.get_searchable_text().lower()


# ============================================================================
# MODELS
# ============================================================================

class Study(EntityWithTimestamp):
    """Study model - evidence/context linked to datasets"""
    def __init__(self, citation: str, study_id: str = None):
        super().__init__()
        if study_id:
            self.id = study_id
        self.citation = citation
    
    def to_dict(self) -> dict:
        data = self._to_dict_base()
        data.update({
            "citation": self.citation
        })
        return data


class Dataset(EntityWithTimestamp, TextSearchable):
    """Enhanced dataset model with full wireframe support"""
    def __init__(self, name: str, source: str, description: str, 
                 constructs: List[str], instrument: str, access_type: str,
                 access_url: Optional[str] = None, request_email: Optional[str] = None):
        super().__init__()
        self.name = name
        self.source = source
        self.description = description
        self.constructs = constructs
        self.instrument = instrument
        self.access_type = access_type
        self.access_url = access_url
        self.request_email = request_email
        self.studies: List[Study] = []
        self.status = DatasetStatus.APPROVED.value
        self.metadata_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute hash for deduplication"""
        content = f"{self.name}_{self.source}_{self.description}".lower()
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_study(self, study: Study) -> None:
        """Add study evidence to dataset"""
        self.studies.append(study)
        self.updated_at = datetime.now()
    
    def get_searchable_text(self) -> str:
        """Get all searchable fields concatenated"""
        return " ".join([
            self.name or "",
            self.source or "",
            self.description or "",
            " ".join(self.constructs or []),
            self.instrument or "",
            " ".join([s.citation for s in self.studies]),
            self.access_url or "",
            self.request_email or ""
        ])
    
    def to_dict(self) -> dict:
        data = self._to_dict_base()
        data.update({
            "name": self.name,
            "source": self.source,
            "description": self.description,
            "constructs": self.constructs,
            "instrument": self.instrument,
            "access_type": self.access_type,
            "access_url": self.access_url,
            "request_email": self.request_email,
            "studies": [s.to_dict() for s in self.studies],
            "study_count": len(self.studies),
            "status": self.status
        })
        return data


class AccessRequest(EntityWithTimestamp):
    """Access request model for restricted dataset requests"""
    def __init__(self, dataset_id: str, user_id: str, reason: str, contact_email: str):
        super().__init__()
        self.dataset_id = dataset_id
        self.user_id = user_id
        self.reason = reason
        self.contact_email = contact_email
        self.status = RequestStatus.PENDING.value
    
    def to_dict(self) -> dict:
        data = self._to_dict_base()
        data.update({
            "dataset_id": self.dataset_id,
            "user_id": self.user_id,
            "reason": self.reason,
            "contact_email": self.contact_email,
            "status": self.status
        })
        return data


# ============================================================================
# REPOSITORY LAYER - Data Access with DRY Principle
# ============================================================================

class BaseRepository(ABC):
    """Abstract base repository (Single Responsibility Principle)"""
    
    def __init__(self):
        self.storage: Dict[str, Any] = {}
    
    def create(self, entity: Any) -> Any:
        """Create entity"""
        self.storage[entity.id] = entity
        return entity
    
    def get(self, entity_id: str) -> Optional[Any]:
        """Get entity by ID"""
        return self.storage.get(entity_id)
    
    def list(self, filter_func: Optional[Callable] = None) -> List[Any]:
        """List all entities, optionally filtered"""
        entities = list(self.storage.values())
        if filter_func:
            entities = [e for e in entities if filter_func(e)]
        return entities
    
    def update(self, entity_id: str, **kwargs) -> Optional[Any]:
        """Update entity fields"""
        entity = self.get(entity_id)
        if not entity:
            return None
        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        if hasattr(entity, 'updated_at'):
            entity.updated_at = datetime.now()
        return entity
    
    def delete(self, entity_id: str) -> bool:
        """Delete entity"""
        if entity_id in self.storage:
            del self.storage[entity_id]
            return True
        return False


class DatasetRepository(BaseRepository):
    """Repository for dataset operations"""
    
    def __init__(self, session: Optional[Any] = None):
        super().__init__()
        self.session = session
        self.access_requests: Dict[str, AccessRequest] = {}
        self._initialize_test_data()
    
    TEST_DATASETS = [
        {
            "name": "National Income Dynamics Study (NIDS), wave 4",
            "source": "DataFirst",
            "description": "The National Income Dynamics Study (NIDS) is South Africa's first national longitudinal household survey. It tracks the socio-economic well-being of South Africans over time.",
            "constructs": ["Depressive Disorder"],
            "instrument": "CES-D 10",
            "access_type": AccessType.OPEN.value,
            "access_url": "https://url.za.m.mimecastprotect.com/s/HsX0C2RqnrcZq396FnfVC5Rqaw",
            "studies": ["Ajaero, C.K., C.T. Nzeadibe, and E.E. Igboeli, Rural–urban differences in depressive symptoms among South African adults using NIDS Wave 4 data. South African Journal of Child Health, 2018. 12: p. s71–s74."]
        },
        {
            "name": "Agincourt HDSS",
            "source": "Agincourt",
            "description": "The Agincourt HDSS website facilitates published data access, with levels of data extraction and access dependent on appropriate ethical approvals.",
            "constructs": ["Emotional and Behavioural difficulties"],
            "instrument": "Strengths and Difficulties Questionnaire (SDQ) - Teacher-report scales",
            "access_type": AccessType.RESTRICTED.value,
            "access_url": "https://url.za.m.mimecastprotect.com/s/POC9C48vpwc9N5v6CBirC4kBvu",
            "studies": ["Cortina, M.A., et al., Childhood psychological problems in school settings in rural South Africa: Findings from the Agincourt HDSS. Social Psychiatry and Psychiatric Epidemiology, 2013. 48: p. 379–393."]
        },
        {
            "name": "SHaW study",
            "source": "Professor Stephen Stansfeld",
            "description": "The SHaW study examines mental health outcomes among South African adolescents with detailed information on school environments and social determinants.",
            "constructs": ["Depressive Disorder"],
            "instrument": "Revised Child Anxiety and Depression Scale (RCADS)",
            "access_type": AccessType.FORMAL_REQUEST.value,
            "request_email": "s.a.stansfeld@qmul.ac.uk",
            "studies": ["Das-Munshi J, Lund C, Mathews C, Clark C, Rothon C, Nthethe N, et al. (2023). Gender-specific pathways to depression among South African adolescents: Longitudinal findings from the SHaW study."]
        },
        {
            "name": "Hiscox et al [Dataset]",
            "source": "Lucy V. Hiscox",
            "description": "Dataset associated with Hiscox et al. study on sex differences in post-traumatic stress disorder among South African youth.",
            "constructs": ["PTSD"],
            "instrument": "Child PTSD Symptom Scale - Self Report for DSM-5 (CPSS-SR-5)",
            "access_type": AccessType.FORMAL_REQUEST.value,
            "request_email": "lh2235@bath.ac.uk",
            "studies": ["Hiscox, L.V., et al., Sex differences in post-traumatic stress disorder among South African adolescents: Evidence from school-based surveys. European Journal of Psychotraumatology, 2021. 12(1): 1978669."]
        },
        {
            "name": "Center for Public Mental Health (CPMH) Data",
            "source": "Mirriam Mkhize",
            "description": "This study recruited a total of 621 participants aged 13–18 years from rural and semi-urban communities in the Western Cape Province.",
            "constructs": ["Depressive Disorder"],
            "instrument": "PHQ-A",
            "access_type": AccessType.FORMAL_REQUEST.value,
            "request_email": "mkhmir003@myuct.ac.za",
            "studies": ["Mkhize, M., van der Westhuizen, C., & Sorsdahl, K. (2024). Depression among South African adolescents in low-resource communities. Comprehensive Psychiatry, 131, 152469."]
        }
    ]
    
    def _initialize_test_data(self) -> None:
        """Initialize with wireframe test data (DRY - single source)"""
        for ds_data in self.TEST_DATASETS:
            dataset = self._create_dataset_from_dict(ds_data)
            self.create(dataset)
    
    @staticmethod
    def _create_dataset_from_dict(data: dict) -> Dataset:
        """Factory method to create dataset from dictionary (DRY)"""
        dataset = Dataset(
            name=data["name"],
            source=data["source"],
            description=data["description"],
            constructs=data["constructs"],
            instrument=data["instrument"],
            access_type=data["access_type"],
            access_url=data.get("access_url"),
            request_email=data.get("request_email")
        )
        for study_citation in data.get("studies", []):
            dataset.add_study(Study(study_citation))
        return dataset
    
    def list_datasets(self, status: Optional[str] = None) -> List[Dataset]:
        """List datasets with optional status filter"""
        return self.list(filter_func=lambda d: d.status == status if status else True)
    
    def find_duplicates(self, metadata_hash: str) -> List[Dataset]:
        """Find duplicate datasets by hash"""
        return self.list(filter_func=lambda d: d.metadata_hash == metadata_hash)
    
    def get_all_constructs(self) -> Set[str]:
        """Extract unique constructs from all datasets (DRY)"""
        constructs = set()
        for dataset in self.list():
            constructs.update(dataset.constructs)
        return constructs
    
    def create_access_request(self, request: AccessRequest) -> AccessRequest:
        """Create access request"""
        self.access_requests[request.id] = request
        return request
    
    def get_access_requests(self, dataset_id: str) -> List[AccessRequest]:
        """Get access requests for dataset"""
        return [r for r in self.access_requests.values() if r.dataset_id == dataset_id]


# ============================================================================
# BUSINESS LOGIC LAYER - Service with SOLID Principles
# ============================================================================

class FilterStrategy(ABC):
    """Abstract filter strategy (Strategy Pattern for DRY filtering)"""
    @abstractmethod
    def apply(self, dataset: Dataset) -> bool:
        """Apply filter to dataset"""
        pass


class ConstructFilter(FilterStrategy):
    """Filter by mental health construct"""
    def __init__(self, construct: str):
        self.construct = construct.lower()
    
    def apply(self, dataset: Dataset) -> bool:
        return any(c.lower() == self.construct for c in dataset.constructs)


class AccessTypeFilter(FilterStrategy):
    """Filter by access type"""
    def __init__(self, access_type: str):
        self.access_type = access_type
    
    def apply(self, dataset: Dataset) -> bool:
        return dataset.access_type == self.access_type


class StatusFilter(FilterStrategy):
    """Filter by status"""
    def __init__(self, status: str):
        self.status = status
    
    def apply(self, dataset: Dataset) -> bool:
        return dataset.status == self.status


class QueryFilter(FilterStrategy):
    """Full-text search filter"""
    def __init__(self, query: str):
        self.query = query.lower()
    
    def apply(self, dataset: Dataset) -> bool:
        return self.query in dataset.get_searchable_text().lower()


class DataDiscoveryService:
    """Data Discovery Service - core business logic (DRY & SOLID)"""
    
    def __init__(self, repository: DatasetRepository):
        self.repository = repository
    
    # ========= HELPER METHODS (DRY - used by multiple search methods) =========
    
    def _apply_filters(self, filters: List[FilterStrategy]) -> List[Dataset]:
        """Apply multiple filters to datasets (DRY - single filter logic)"""
        datasets = self.repository.list()
        for filter_strategy in filters:
            datasets = [d for d in datasets if filter_strategy.apply(d)]
        return datasets
    
    def _to_dict_list(self, datasets: List[Dataset]) -> List[Dict]:
        """Convert datasets to dictionaries (DRY - reusable conversion)"""
        return [d.to_dict() for d in datasets]
    
    def _validate_dataset_exists(self, dataset_id: str) -> Optional[Dataset]:
        """Validate dataset exists and return it (DRY - reusable validation)"""
        dataset = self.repository.get(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        return dataset
    
    # ========= PRIMARY SEARCH METHODS =========
    
    def get_all_datasets(self, status: Optional[str] = None) -> List[Dict]:
        """Get all datasets, optionally filtered by status"""
        filters = [StatusFilter(status)] if status else [StatusFilter(DatasetStatus.APPROVED.value)]
        datasets = self._apply_filters(filters)
        return self._to_dict_list(datasets)
    
    def get_dataset_details(self, dataset_id: str) -> Optional[Dict]:
        """Get dataset details"""
        dataset = self.repository.get(dataset_id)
        return dataset.to_dict() if dataset else None
    
    def global_search(self, query: str) -> List[Dict]:
        """Global full-text search (DRY - uses QueryFilter)"""
        filters = [
            StatusFilter(DatasetStatus.APPROVED.value),
            QueryFilter(query)
        ]
        datasets = self._apply_filters(filters)
        return self._to_dict_list(datasets)
    
    def search_by_construct(self, construct: str) -> List[Dict]:
        """Search by construct (DRY - uses ConstructFilter)"""
        filters = [
            StatusFilter(DatasetStatus.APPROVED.value),
            ConstructFilter(construct)
        ]
        datasets = self._apply_filters(filters)
        return self._to_dict_list(datasets)
    
    def filter_by_access_type(self, access_type: str) -> List[Dict]:
        """Filter by access type (DRY - uses AccessTypeFilter)"""
        filters = [
            StatusFilter(DatasetStatus.APPROVED.value),
            AccessTypeFilter(access_type)
        ]
        datasets = self._apply_filters(filters)
        return self._to_dict_list(datasets)
    
    def advanced_filter(self, query: Optional[str] = None, 
                       construct: Optional[str] = None,
                       access_type: Optional[str] = None) -> List[Dict]:
        """Advanced filtering combining multiple criteria (DRY - reuses filters)"""
        filters = [StatusFilter(DatasetStatus.APPROVED.value)]
        
        if construct:
            filters.append(ConstructFilter(construct))
        if access_type:
            filters.append(AccessTypeFilter(access_type))
        if query:
            filters.append(QueryFilter(query))
        
        datasets = self._apply_filters(filters)
        return self._to_dict_list(datasets)
    
    def get_unique_constructs(self) -> List[str]:
        """Get all unique constructs"""
        constructs = self.repository.get_all_constructs()
        return sorted(list(constructs))
    
    # ========= DATASET MANAGEMENT =========
    
    def submit_dataset(self, name: str, source: str, description: str,
                      constructs: List[str], instrument: str, 
                      access_type: str, access_url: Optional[str] = None,
                      request_email: Optional[str] = None) -> Dict:
        """Submit new dataset"""
        dataset = Dataset(
            name=name, source=source, description=description,
            constructs=constructs, instrument=instrument,
            access_type=access_type, access_url=access_url,
            request_email=request_email
        )
        
        if self.repository.find_duplicates(dataset.metadata_hash):
            raise ValueError("Dataset appears to be duplicate")
        
        created = self.repository.create(dataset)
        return created.to_dict()
    
    def add_study_to_dataset(self, dataset_id: str, citation: str) -> Dict:
        """Add study to dataset (DRY - uses validation helper)"""
        dataset = self._validate_dataset_exists(dataset_id)
        dataset.add_study(Study(citation))
        return dataset.to_dict()
    
    def request_dataset_access(self, dataset_id: str, user_id: str, 
                              reason: str, contact_email: str) -> Dict:
        """Request access to dataset (DRY - uses validation helper)"""
        dataset = self._validate_dataset_exists(dataset_id)
        
        if dataset.access_type != AccessType.FORMAL_REQUEST.value:
            raise ValueError("Dataset does not require formal access request")
        
        access_request = AccessRequest(dataset_id, user_id, reason, contact_email)
        created = self.repository.create_access_request(access_request)
        return created.to_dict()
    
    def get_access_requests(self, dataset_id: str) -> List[Dict]:
        """Get access requests for dataset"""
        requests = self.repository.get_access_requests(dataset_id)
        return [r.to_dict() for r in requests]


# ============================================================================
# INITIALIZATION
# ============================================================================

def create_data_discovery_service(session: Optional[Any] = None) -> DataDiscoveryService:
    """Factory function to create Data Discovery Service with repository"""
    repository = DatasetRepository(session)
    return DataDiscoveryService(repository)
