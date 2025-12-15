"""
PAMHoYA - Data Harmonisation Router

API endpoints for data harmonisation service.

Copyright (c) 2025 PAMHoYA Team
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence
Lead Developer: Augustine Khumalo
"""

from fastapi import APIRouter, Body, status, Query
from datetime import datetime

from harmony_api.services.data_harmonisation_service import (
    create_data_harmonisation_service,
    ColumnMapping
)
from harmony_api.services.mental_health_studies_loader import get_mental_health_studies_loader

router = APIRouter(prefix="/harmonise", tags=["Data Harmonisation"])

# Service instance
service = create_data_harmonisation_service()
studies_loader = get_mental_health_studies_loader()


@router.post(
    path="/jobs/initiate",
    status_code=status.HTTP_201_CREATED,
    summary="Initiate data harmonisation job"
)
async def initiate_harmonisation(
    source_dataset_id: str = Body(...),
    target_dataset_id: str = Body(...),
    created_by: str = Body(...)
):
    """Initiate new data harmonisation job."""
    job = service.initiate_harmonisation(source_dataset_id, target_dataset_id, created_by)
    
    return {
        "job_id": job.id,
        "status": job.status,
        "created_at": job.created_at.isoformat()
    }


@router.get(
    path="/jobs/{job_id}",
    summary="Get harmonisation job status"
)
async def get_job_status(job_id: str):
    """Get status and details of harmonisation job."""
    job = service.repository.get_job(job_id)
    
    if not job:
        return {"error": "Job not found"}, status.HTTP_404_NOT_FOUND
    
    return {
        "job_id": job.id,
        "status": job.status,
        "source_dataset": job.source_dataset_id,
        "target_dataset": job.target_dataset_id,
        "mappings_count": len(job.mappings),
        "result_dataset_id": job.result_dataset_id,
        "report": job.report
    }


@router.post(
    path="/jobs/{job_id}/analyze-schema",
    summary="Analyze dataset schema"
)
async def analyze_schema(
    job_id: str,
    dataset_id: str = Body(...)
):
    """Analyze schema of a dataset."""
    schema = service.analyze_schema(dataset_id)
    
    return {
        "dataset_id": dataset_id,
        "schema": schema
    }


@router.post(
    path="/jobs/{job_id}/create-mapping",
    summary="Create column mapping"
)
async def create_mapping(
    job_id: str,
    source_column: str = Body(...),
    target_column: str = Body(...),
    transformation: str = Body(default="identity")
):
    """Create mapping between source and target columns."""
    mapping = service.create_mapping(job_id, source_column, target_column, transformation)
    
    return {
        "mapping": {
            "source": mapping.source_col,
            "target": mapping.target_col,
            "transformation": mapping.transformation
        }
    }


@router.post(
    path="/jobs/{job_id}/execute",
    summary="Execute harmonisation"
)
async def execute_harmonisation(
    job_id: str,
    source_dataset_id: str = Body(...),
    target_dataset_id: str = Body(...)
):
    """Execute the harmonisation workflow."""
    job = service.harmonise(job_id, source_dataset_id, target_dataset_id)
    
    if not job:
        return {"error": "Job not found"}, status.HTTP_404_NOT_FOUND
    
    return {
        "job_id": job.id,
        "status": job.status,
        "result_dataset_id": job.result_dataset_id,
        "report": job.report
    }


@router.get(
    path="/available-datasets",
    summary="List available datasets and studies for harmonization",
    description="Get all available datasets and mental health studies for harmonization"
)
async def get_available_datasets(
    limit: int = Query(100, ge=1, le=500, description="Maximum results to return"),
    search: str = Query(None, description="Optional search term")
):
    """
    List all available datasets and studies for harmonization including:
    - Mental health research studies from metadata sources
    - Datasets already in the system
    """
    try:
        # Load mental health studies
        studies_loader.load_all_studies()
        all_studies = studies_loader.get_all_studies()
        
        # Filter by search if provided
        if search:
            all_studies = [s for s in all_studies if search.lower() in s.get_searchable_text().lower()]
        
        # Limit results
        all_studies = all_studies[:limit]
        
        # Convert to response format
        datasets = []
        for study in all_studies:
            questions = study.get_questions()
            dataset_dict = {
                "id": study.study_id,
                "name": study.title,
                "type": "research_study",
                "abstract": study.abstract[:200] + "..." if len(study.abstract) > 200 else study.abstract,
                "keywords": study.keywords,
                "producers": [p.get("name", "") for p in study.producers] if study.producers else [],
                "date": study.prod_date
            }
            
            # Add question count if available
            if questions:
                dataset_dict["total_questions"] = len(questions)
                dataset_dict["language"] = study.metadata.get("doc_desc", {}).get("language", "English")
            
            datasets.append(dataset_dict)
        
        return {
            "count": len(datasets),
            "total_available": len(all_studies),
            "datasets_and_studies": datasets
        }
    except Exception as e:
        return {
            "count": 0,
            "total_available": 0,
            "datasets_and_studies": [],
            "error": str(e)
        }, status.HTTP_200_OK


@router.get(
    path="/health",
    summary="Health check"
)
async def health_check():
    """Data Harmonisation Service health check."""
    return {
        "service": "data_harmonisation",
        "status": "healthy",
        "timestamp": str(datetime.now())
    }
