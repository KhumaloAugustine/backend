"""
PAMHoYA - Data Discovery Router

API endpoints for comprehensive data discovery features:
- Global full-text search across all dataset fields
- Construct-based filtering (mental health disorders)
- Access type management (Open, Restricted, Formal Request)
- Dataset details with linked studies
- Access request management

Implements API Layer of 3-layer architecture.
Applies DRY principles with reusable helper functions and decorators.

Copyright (c) 2025 PAMHoYA Team
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence
Lead Developer: Augustine Khumalo
"""

from fastapi import APIRouter, Body, status, Query, HTTPException
from typing import Optional, List, Callable, Any, Dict
from datetime import datetime
from functools import wraps

from harmony_api.services.data_discovery_service import (
    create_data_discovery_service,
    DataDiscoveryService,
    DatasetStatus,
    AccessType
)
from harmony_api.services.mental_health_studies_loader import get_mental_health_studies_loader
from harmony_api.core.middleware import handle_errors
from harmony_api.core.exceptions import EntityNotFoundException, ValidationException

router = APIRouter(prefix="/discovery", tags=["Data Discovery"])

# Service instances
service = create_data_discovery_service()
studies_loader = get_mental_health_studies_loader()


# ============================================================================
# DRY HELPER FUNCTIONS & DECORATORS
# ============================================================================

# handle_errors now imported from middleware module for DRY


def paginate_results(results: List[Dict], limit: int = 50) -> List[Dict]:
    """Paginate results (DRY - reusable pagination)"""
    return results[:limit]


def format_search_response(query: str, results: List[Dict], 
                          filters: Optional[Dict] = None) -> Dict:
    """Format search response consistently (DRY - reusable response formatting)"""
    response = {
        "query": query,
        "count": len(results),
        "datasets": results
    }
    if filters:
        response.update(filters)
    return response


def format_collection_response(items: List[Dict], label: str) -> Dict:
    """Format collection response (DRY - reusable for any collection)"""
    return {
        "count": len(items),
        label: items
    }


def get_dataset_or_404(dataset_id: str) -> Dict:
    """Get dataset or raise 404 (DRY - reusable validation)"""
    details = service.get_dataset_details(dataset_id)
    if not details:
        raise EntityNotFoundException("Dataset", dataset_id)
    return details


# ============================================================================
# DATASET RETRIEVAL & LISTING
# ============================================================================

@router.get(
    path="/datasets",
    summary="List all datasets",
    description="Get all approved datasets with full details"
)
@handle_errors
async def list_datasets() -> Dict:
    """
    Retrieve all approved datasets from the catalogue.
    Returns complete dataset information including constructs, instruments, and studies.
    Also includes mental health studies from the metadata sources.
    """
    datasets = service.get_all_datasets()
    
    # Load mental health studies and convert to dataset-like format
    studies_loader.load_all_studies()
    mh_studies = studies_loader.get_all_studies()
    
    # Convert mental health studies to dataset format
    converted_studies = []
    for study in mh_studies:
        study_dict = study.to_dict()
        converted_study = {
            "id": study_dict["study_id"],
            "name": study_dict["title"],
            "description": study_dict["abstract"],
            "source": ", ".join([p.get("name", "") for p in study_dict["producers"]]) if study_dict["producers"] else "Research Institution",
            "constructs": study_dict.get("keywords", []),
            "instrument": "Observational/Research Data",
            "access_type": "Research Database",
            "status": "approved",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "studies": [],
            "study_count": 0,
            "access_url": None,
            "request_email": None,
            "is_research_study": True
        }
        converted_studies.append(converted_study)
    
    # Combine datasets and converted studies
    all_datasets = datasets + converted_studies
    return format_collection_response(all_datasets, "datasets")


@router.get(
    path="/datasets/{dataset_id}",
    summary="Get dataset details",
    description="Retrieve complete information about a specific dataset"
)
@handle_errors
async def get_dataset_details_endpoint(dataset_id: str) -> Dict:
    """
    Get comprehensive details about a dataset including:
    - Description and metadata
    - Mental health constructs & instruments
    - All linked studies
    - Access information
    - Contact details
    
    Also retrieves mental health studies by their study ID.
    """
    # First try to get as a regular dataset
    details = service.get_dataset_details(dataset_id)
    if details:
        return details
    
    # If not found, try to get as a mental health study
    studies_loader.load_all_studies()
    study = studies_loader.get_study(dataset_id)
    
    if study:
        # Convert mental health study to dataset format
        study_dict = study.to_dict()
        return {
            "id": study_dict["study_id"],
            "name": study_dict["title"],
            "description": study_dict["abstract"],
            "source": ", ".join([p.get("name", "") for p in study_dict["producers"]]) if study_dict["producers"] else "Research Institution",
            "constructs": study_dict.get("keywords", []),
            "instrument": "Observational/Research Data",
            "access_type": "Research Database",
            "status": "approved",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "studies": [],
            "study_count": 0,
            "access_url": None,
            "request_email": None,
            "is_research_study": True,
            "metadata": study_dict
        }
    
    # Not found as either dataset or study
    raise EntityNotFoundException("Dataset or Study", dataset_id)


# ============================================================================
# SEARCH & DISCOVERY - ALL USING REUSABLE PATTERNS
# ============================================================================

@router.get(
    path="/search",
    summary="Global full-text search",
    description="Search all dataset fields with a single query"
)
@handle_errors
async def global_search(
    query: str = Query(..., description="Search query - searches all fields"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results to return")
) -> Dict:
    """
    Perform global full-text search across ALL dataset fields:
    - Dataset name
    - Source/curator
    - Description
    - Mental health constructs
    - Instruments used
    - Study citations
    - Access URLs
    - Contact emails
    
    Also searches mental health research studies from metadata sources.
    Returns only approved datasets and studies.
    """
    # Search existing datasets
    dataset_results = service.global_search(query)
    
    # Search mental health studies
    studies_loader.load_all_studies()
    study_results = studies_loader.search_studies(query)
    
    # Convert study results to dataset format
    converted_studies = []
    for study in study_results:
        study_dict = study.to_dict()
        converted_study = {
            "id": study_dict["study_id"],
            "name": study_dict["title"],
            "description": study_dict["abstract"],
            "source": ", ".join([p.get("name", "") for p in study_dict["producers"]]) if study_dict["producers"] else "Research Institution",
            "constructs": study_dict.get("keywords", []),
            "instrument": "Observational/Research Data",
            "access_type": "Research Database",
            "status": "approved",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "studies": [],
            "study_count": 0,
            "access_url": None,
            "request_email": None,
            "is_research_study": True
        }
        converted_studies.append(converted_study)
    
    # Combine results
    combined_results = dataset_results + converted_studies
    return format_search_response(query, paginate_results(combined_results, limit))


@router.get(
    path="/constructs",
    summary="List all mental health constructs",
    description="Get unique list of all mental health constructs in catalogue"
)
@handle_errors
async def get_constructs() -> Dict:
    """
    Retrieve all unique mental health constructs (disorders/conditions) 
    that are represented in the dataset catalogue and mental health studies.
    """
    # Get constructs from datasets
    dataset_constructs = service.get_unique_constructs()
    
    # Get constructs from mental health studies
    studies_loader.load_all_studies()
    study_constructs = list(studies_loader.get_all_constructs())
    
    # Combine and deduplicate
    all_constructs = list(set(dataset_constructs + study_constructs))
    return format_collection_response(all_constructs, "constructs")


@router.get(
    path="/constructs/filter",
    summary="Filter datasets by construct",
    description="Get all datasets that measure a specific mental health construct"
)
@handle_errors
async def filter_by_construct(
    construct: str = Query(..., description="Mental health construct name")
) -> Dict:
    """
    Filter datasets and mental health studies by specific mental health construct.
    """
    # Get datasets with construct
    dataset_results = service.search_by_construct(construct)
    
    # Get studies with construct
    studies_loader.load_all_studies()
    study_results = studies_loader.get_studies_by_construct(construct)
    
    # Convert study results to dataset format
    converted_studies = []
    for study in study_results:
        study_dict = study.to_dict()
        converted_study = {
            "id": study_dict["study_id"],
            "name": study_dict["title"],
            "description": study_dict["abstract"],
            "source": ", ".join([p.get("name", "") for p in study_dict["producers"]]) if study_dict["producers"] else "Research Institution",
            "constructs": study_dict.get("keywords", []),
            "instrument": "Observational/Research Data",
            "access_type": "Research Database",
            "status": "approved",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "studies": [],
            "study_count": 0,
            "access_url": None,
            "request_email": None,
            "is_research_study": True
        }
        converted_studies.append(converted_study)
    
    # Combine results
    combined_results = dataset_results + converted_studies
    return format_search_response(construct, combined_results, {"construct_filter": construct})


@router.get(
    path="/access-types",
    summary="List available access types",
    description="Get all access type options"
)
@handle_errors
async def get_access_types() -> Dict:
    """
    Retrieve available dataset access types and their descriptions.
    """
    access_types = [
        {
            "type": AccessType.OPEN.value,
            "description": "Direct access - download from open portal"
        },
        {
            "type": AccessType.RESTRICTED.value,
            "description": "Access requires ethical approval"
        },
        {
            "type": AccessType.FORMAL_REQUEST.value,
            "description": "Access requires formal request to data custodian"
        }
    ]
    return format_collection_response(access_types, "access_types")


@router.get(
    path="/access-types/filter",
    summary="Filter datasets by access type",
    description="Get all datasets with specific access type"
)
@handle_errors
async def filter_by_access_type(
    access_type: str = Query(..., description="Access type: Open, Restricted, or Formal Request")
) -> Dict:
    """
    Filter datasets by access type.
    """
    results = service.filter_by_access_type(access_type)
    return format_search_response(access_type, results, {"access_type_filter": access_type})


@router.get(
    path="/advanced-search",
    summary="Advanced filtering",
    description="Filter datasets by multiple criteria"
)
@handle_errors
async def advanced_search(
    query: Optional[str] = Query(None, description="Full-text search query"),
    construct: Optional[str] = Query(None, description="Filter by construct"),
    access_type: Optional[str] = Query(None, description="Filter by access type"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results")
) -> Dict:
    """
    Advanced search combining multiple filters:
    - Full-text query (searches all fields)
    - Mental health construct
    - Access type
    
    All parameters are optional. Omit parameters to skip that filter.
    """
    results = service.advanced_filter(query, construct, access_type)
    response = {
        "query": query,
        "construct_filter": construct,
        "access_type_filter": access_type,
        "count": len(results),
        "datasets": paginate_results(results, limit)
    }
    return response


# ============================================================================
# DATASET SUBMISSION & MANAGEMENT
# ============================================================================

@router.post(
    path="/datasets/submit",
    status_code=status.HTTP_201_CREATED,
    summary="Submit new dataset"
)
@handle_errors
async def submit_dataset(
    name: str = Body(..., description="Dataset name"),
    source: str = Body(..., description="Data source/curator"),
    description: str = Body(..., description="Dataset description"),
    constructs: List[str] = Body(..., description="Mental health constructs"),
    instrument: str = Body(..., description="Assessment instrument used"),
    access_type: str = Body(..., description="Access type: Open, Restricted, or Formal Request"),
    access_url: Optional[str] = Body(None, description="Direct access portal URL (for Open/Restricted)"),
    request_email: Optional[str] = Body(None, description="Contact email (for Formal Request)")
) -> Dict:
    """
    Submit a new dataset to the discovery catalogue.
    
    Requires:
    - name: Dataset name
    - source: Data source or curator
    - description: What the dataset contains
    - constructs: Mental health constructs covered
    - instrument: Assessment tool used
    - access_type: Open, Restricted, or Formal Request
    - access_url: For Open/Restricted access types
    - request_email: For Formal Request access type
    """
    dataset = service.submit_dataset(
        name=name,
        source=source,
        description=description,
        constructs=constructs,
        instrument=instrument,
        access_type=access_type,
        access_url=access_url,
        request_email=request_email
    )
    return {
        "status": "submitted",
        "dataset": dataset
    }


@router.post(
    path="/datasets/{dataset_id}/studies",
    status_code=status.HTTP_201_CREATED,
    summary="Add study to dataset"
)
@handle_errors
async def add_study(
    dataset_id: str,
    citation: str = Body(..., description="Study citation/reference")
) -> Dict:
    """
    Add evidence (study) to a dataset.
    Studies provide context about how the dataset has been used.
    
    Parameters:
    - dataset_id: ID of dataset to link study to
    - citation: Study citation or reference
    """
    updated = service.add_study_to_dataset(dataset_id, citation)
    return {
        "status": "study_added",
        "dataset": updated
    }


# ============================================================================
# ACCESS REQUESTS
# ============================================================================

@router.post(
    path="/datasets/{dataset_id}/request-access",
    status_code=status.HTTP_201_CREATED,
    summary="Request dataset access"
)
@handle_errors
async def request_access(
    dataset_id: str,
    user_id: str = Body(..., description="Requesting user ID"),
    reason: str = Body(..., description="Reason for access request"),
    contact_email: str = Body(..., description="Contact email")
) -> Dict:
    """
    Submit access request for formal request datasets.
    Generates pre-filled email to data custodian.
    
    Parameters:
    - dataset_id: Dataset to request access for
    - user_id: User requesting access
    - reason: Why access is needed
    - contact_email: How to contact requester
    """
    request_obj = service.request_dataset_access(dataset_id, user_id, reason, contact_email)
    return {
        "status": "request_submitted",
        "access_request": request_obj
    }


@router.get(
    path="/datasets/{dataset_id}/access-requests",
    summary="Get access requests for dataset"
)
@handle_errors
async def get_access_requests(dataset_id: str) -> Dict:
    """
    Retrieve all access requests for a dataset.
    For dataset custodians to review requests.
    """
    requests = service.get_access_requests(dataset_id)
    return format_collection_response(requests, "access_requests")


# ============================================================================
# STATISTICS & METADATA
# ============================================================================

@router.get(
    path="/statistics",
    summary="Get catalogue statistics"
)
@handle_errors
async def get_statistics() -> Dict:
    """
    Get overview statistics about the dataset catalogue:
    - Total datasets available
    - Mental health constructs covered
    - Studies/citations linked
    - Distribution by access type
    - Mental health research studies count
    """
    all_datasets = service.get_all_datasets()
    constructs = service.get_unique_constructs()
    
    # Load mental health studies
    studies_loader.load_all_studies()
    mh_studies = studies_loader.get_all_studies()
    mh_constructs = list(studies_loader.get_all_constructs())
    
    # Combine all constructs
    all_constructs = list(set(constructs + mh_constructs))
    
    # Count by access type (DRY: reusable pattern)
    access_counts = {}
    for ds in all_datasets:
        access_type = ds.get("access_type", "Unknown")
        access_counts[access_type] = access_counts.get(access_type, 0) + 1
    
    # Total studies (DRY: reusable aggregation)
    total_studies = sum(ds.get("study_count", 0) for ds in all_datasets)
    
    return {
        "total_datasets": len(all_datasets),
        "total_research_studies": len(mh_studies),
        "total_constructs": len(all_constructs),
        "total_studies": total_studies + len(mh_studies),
        "by_access_type": access_counts,
        "constructs_available": len(all_constructs)
    }


@router.get(
    path="/health",
    summary="Service health check"
)
@handle_errors
async def health_check() -> Dict:
    """
    Data Discovery Service health status.
    """
    return {
        "service": "data_discovery",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0"
    }


# ============================================================================
# MENTAL HEALTH STUDIES - INTEGRATED INTO DISCOVERY SERVICE
# ============================================================================

@router.get(
    path="/studies",
    summary="List all mental health studies",
    description="Get all mental health studies from scoping review"
)
@handle_errors
async def list_studies(
    limit: int = Query(100, ge=1, le=500, description="Maximum results to return")
) -> Dict:
    """
    Retrieve all mental health studies loaded from the scoping review.
    These studies provide research evidence and context for mental health constructs.
    """
    all_studies = studies_loader.get_all_studies()
    studies_data = [s.to_dict() for s in all_studies[:limit]]
    return format_collection_response(studies_data, "studies")


@router.get(
    path="/studies/{study_id}",
    summary="Get study details",
    description="Retrieve complete information about a specific mental health study"
)
@handle_errors
async def get_study_details(study_id: str) -> Dict:
    """
    Get comprehensive details about a mental health study including:
    - Title and authors
    - Abstract and keywords
    - Data collection methodology
    - Geographic scope
    - Linked constructs
    """
    study = studies_loader.get_study(study_id)
    if not study:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
    return {
        "study": study.to_dict()
    }


@router.get(
    path="/studies/search/full-text",
    summary="Search mental health studies by full-text",
    description="Search study metadata, titles, abstracts, and keywords"
)
@handle_errors
async def search_studies(
    query: str = Query(..., description="Search query - searches title, abstract, keywords"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results to return")
) -> Dict:
    """
    Perform full-text search across all mental health studies:
    - Study titles
    - Abstracts
    - Keywords
    - Author names and affiliations
    
    Returns matched studies with relevance.
    """
    results = studies_loader.search_studies(query)
    studies_data = [s.to_dict() for s in results[:limit]]
    return format_search_response(query, studies_data)


@router.get(
    path="/studies/by-construct/{construct}",
    summary="Get studies by mental health construct",
    description="Find all studies measuring a specific mental health construct"
)
@handle_errors
async def get_studies_by_construct(
    construct: str,
    limit: int = Query(50, ge=1, le=500, description="Maximum results to return")
) -> Dict:
    """
    Get all mental health studies that measure or focus on a specific construct
    (e.g., depression, anxiety, bipolar disorder, etc.).
    """
    results = studies_loader.get_studies_by_construct(construct)
    studies_data = [s.to_dict() for s in results[:limit]]
    return format_search_response(construct, studies_data, {"construct_filter": construct})


@router.get(
    path="/studies/constructs/all",
    summary="List all mental health constructs in studies",
    description="Get unique list of all mental health constructs covered in studies"
)
@handle_errors
async def get_study_constructs() -> Dict:
    """
    Retrieve all unique mental health constructs (keywords) represented across
    all loaded mental health studies. Useful for filtering and categorization.
    """
    constructs = sorted(list(studies_loader.get_all_constructs()))
    return format_collection_response(constructs, "constructs")


@router.get(
    path="/studies/statistics",
    summary="Get mental health studies statistics"
)
@handle_errors
async def get_studies_statistics() -> Dict:
    """
    Get overview statistics about mental health studies:
    - Total number of studies loaded
    - Number of unique constructs
    - Keywords/constructs covered
    """
    all_studies = studies_loader.get_all_studies()
    constructs = studies_loader.get_all_constructs()
    
    return {
        "total_studies": len(all_studies),
        "total_constructs": len(constructs),
        "constructs_sample": sorted(list(constructs))[:20],
        "loaded_at": datetime.now().isoformat()
    }
