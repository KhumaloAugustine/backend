"""
PAMHoYA - Summarisation Router

API endpoints for summarisation service.

Copyright (c) 2025 PAMHoYA Team
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence
Lead Developer: Augustine Khumalo
"""

from fastapi import APIRouter, Body, status, Query
from datetime import datetime

from harmony_api.services.summarisation_service import create_summarisation_service
from harmony_api.services.mental_health_studies_loader import get_mental_health_studies_loader

router = APIRouter(prefix="/summarise", tags=["Summarisation"])

# Service instances
service = create_summarisation_service()
studies_loader = get_mental_health_studies_loader()


@router.post(
    path="",
    status_code=status.HTTP_200_OK,
    summary="Generate study summary (quick endpoint)"
)
async def generate_summary(
    text: str = Body(..., description="Text or study abstract to summarize"),
    style: str = Body("brief", description="Summarization style: brief, detailed, or academic"),
    study_title: str = Body(None, description="Optional study title"),
    study_id: str = Body(None, description="Optional study ID")
):
    """Generate a plain-language summary of research text."""
    try:
        # Create a summary entry
        summary = service.initiate_summarisation(
            study_id=study_id or "auto_" + str(datetime.now().timestamp()),
            study_title=study_title or "Untitled",
            study_abstract=text
        )
        
        if not summary:
            return {"error": "Could not create summary"}, status.HTTP_400_BAD_REQUEST
        
        # Generate draft automatically
        version = service.generate_draft_summary(summary.id)
        
        if not version:
            return {"error": "Could not generate summary"}, status.HTTP_500_INTERNAL_SERVER_ERROR
        
        return {
            "success": True,
            "summary_id": summary.id,
            "study_id": summary.study_id,
            "study_title": summary.study_title,
            "plain_language_summary": version.plain_language_text,
            "style": style,
            "status": "generated",
            "created_at": summary.created_at.isoformat()
        }
    except Exception as e:
        return {"error": f"Error generating summary: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR


@router.post(
    path="/initiate",
    status_code=status.HTTP_201_CREATED,
    summary="Initiate study summarisation"
)
async def initiate_summarisation(
    study_id: str = Body(...),
    study_title: str = Body(...),
    study_abstract: str = Body(...)
):
    """Initiate summarisation of a research study."""
    summary = service.initiate_summarisation(study_id, study_title, study_abstract)
    
    if not summary:
        return {"error": "Summary already exists"}, status.HTTP_409_CONFLICT
    
    return {
        "summary_id": summary.id,
        "study_id": summary.study_id,
        "status": summary.status,
        "created_at": summary.created_at.isoformat()
    }


@router.post(
    path="/{summary_id}/generate-draft",
    summary="Generate automated draft summary"
)
async def generate_draft(summary_id: str):
    """Generate plain-language draft summary using NLP/LLM."""
    version = service.generate_draft_summary(summary_id)
    
    if not version:
        return {"error": "Summary not found"}, status.HTTP_404_NOT_FOUND
    
    return {
        "version_id": version.id,
        "summary_id": summary_id,
        "version_number": version.version_number,
        "plain_language_text": version.plain_language_text,
        "status": "draft"
    }


@router.get(
    path="/{summary_id}",
    summary="Get summary details"
)
async def get_summary(summary_id: str):
    """Get complete summary details."""
    details = service.get_summary_details(summary_id)
    
    if not details:
        return {"error": "Summary not found"}, status.HTTP_404_NOT_FOUND
    
    return details


@router.post(
    path="/{summary_id}/request-review",
    summary="Move to review queue"
)
async def request_review(summary_id: str):
    """Move summary to review queue."""
    summary = service.request_review(summary_id)
    
    if not summary:
        return {"error": "Summary not found"}, status.HTTP_404_NOT_FOUND
    
    return {
        "summary_id": summary.id,
        "status": summary.status
    }


@router.post(
    path="/{summary_id}/add-comment",
    summary="Add reviewer comment"
)
async def add_reviewer_comment(
    summary_id: str,
    reviewer_id: str = Body(...),
    comment: str = Body(...)
):
    """Add comment during review process."""
    result = service.add_reviewer_comment(summary_id, reviewer_id, comment)
    
    if not result:
        return {"error": "Summary not found"}, status.HTTP_404_NOT_FOUND
    
    return result


@router.post(
    path="/{summary_id}/edit",
    summary="Edit summary (creates new version)"
)
async def edit_summary(
    summary_id: str,
    new_text: str = Body(...),
    editor_id: str = Body(...)
):
    """Edit summary and create new version."""
    version = service.edit_summary(summary_id, new_text, editor_id)
    
    if not version:
        return {"error": "Summary not found"}, status.HTTP_404_NOT_FOUND
    
    return {
        "version_id": version.id,
        "summary_id": summary_id,
        "version_number": version.version_number,
        "created_at": version.created_at.isoformat()
    }


@router.post(
    path="/{summary_id}/approve",
    summary="Approve summary"
)
async def approve_summary(
    summary_id: str,
    reviewer_id: str = Body(...)
):
    """Approve summary for publication."""
    summary = service.approve_summary(summary_id, reviewer_id)
    
    if not summary:
        return {"error": "Summary not found"}, status.HTTP_404_NOT_FOUND
    
    return {
        "summary_id": summary.id,
        "status": summary.status,
        "approved_by": reviewer_id
    }


@router.post(
    path="/{summary_id}/reject",
    summary="Reject summary"
)
async def reject_summary(
    summary_id: str,
    rejection_reason: str = Body(...)
):
    """Reject summary with feedback."""
    summary = service.reject_summary(summary_id, rejection_reason)
    
    if not summary:
        return {"error": "Summary not found"}, status.HTTP_404_NOT_FOUND
    
    return {
        "summary_id": summary.id,
        "status": summary.status,
        "reason": rejection_reason
    }


@router.post(
    path="/{summary_id}/publish",
    summary="Publish approved summary"
)
async def publish_summary(summary_id: str):
    """Publish approved summary."""
    summary = service.publish_summary(summary_id)
    
    if not summary:
        return {"error": "Summary not found"}, status.HTTP_404_NOT_FOUND
    
    return {
        "summary_id": summary.id,
        "status": summary.status,
        "published_at": summary.published_at.isoformat()
    }


@router.get(
    path="/health",
    summary="Health check"
)
async def health_check():
    """Summarisation Service health check."""
    return {
        "service": "summarisation",
        "status": "healthy",
        "timestamp": str(datetime.now())
    }


@router.get(
    path="/available-studies",
    summary="List available studies for summarization",
    description="Get all available studies (both research studies and datasets) for summarization"
)
async def get_available_studies(
    limit: int = Query(100, ge=1, le=500, description="Maximum results to return"),
    search: str = Query(None, description="Optional search term")
):
    """
    List all available studies for summarization including:
    - Mental health research studies from metadata sources
    - Research datasets already in the system
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
        studies = []
        for study in all_studies:
            studies.append({
                "study_id": study.study_id,
                "title": study.title,
                "abstract": study.abstract[:300] + "..." if len(study.abstract) > 300 else study.abstract,
                "keywords": study.keywords,
                "producers": [p.get("name", "") for p in study.producers] if study.producers else [],
                "date": study.prod_date,
                "type": "research_study"
            })
        
        return {
            "count": len(studies),
            "total_available": len(all_studies),
            "studies": studies
        }
    except Exception as e:
        return {
            "count": 0,
            "total_available": 0,
            "studies": [],
            "error": str(e)
        }, status.HTTP_200_OK


# ============================================================================
# MENTAL HEALTH STUDIES SUMMARISATION - INTEGRATED
# ============================================================================

@router.get(
    path="/studies/{study_id}/abstract",
    summary="Get study abstract summary",
    description="Get the abstract for a mental health study"
)
async def get_study_abstract(study_id: str):
    """Get the abstract from a mental health study loaded from scoping review."""
    study = studies_loader.get_study(study_id)
    
    if not study:
        return {"error": f"Study {study_id} not found"}, status.HTTP_404_NOT_FOUND
    
    return {
        "study_id": study_id,
        "title": study.title,
        "abstract": study.abstract,
        "keywords": study.keywords,
        "date": study.prod_date
    }


@router.post(
    path="/studies/{study_id}/summarize",
    status_code=status.HTTP_200_OK,
    summary="Generate plain-language summary for mental health study"
)
async def summarize_study(
    study_id: str,
    style: str = Body("brief", description="Summarization style: brief, detailed, or academic")
):
    """
    Generate a plain-language summary of a mental health study.
    
    Parameters:
    - study_id: ID of the mental health study (e.g., mh_study_000)
    - style: Summary style (brief, detailed, academic)
    
    Uses the study's abstract and metadata to create an accessible summary.
    """
    study = studies_loader.get_study(study_id)
    
    if not study:
        return {"error": f"Study {study_id} not found"}, status.HTTP_404_NOT_FOUND
    
    try:
        # Create a summary entry from the study
        summary = service.initiate_summarisation(
            study_id=study_id,
            study_title=study.title,
            study_abstract=study.abstract
        )
        
        if not summary:
            return {"error": "Could not create summary"}, status.HTTP_400_BAD_REQUEST
        
        # Generate draft automatically
        version = service.generate_draft_summary(summary.id)
        
        if not version:
            return {"error": "Could not generate summary"}, status.HTTP_500_INTERNAL_SERVER_ERROR
        
        return {
            "success": True,
            "summary_id": summary.id,
            "study_id": study_id,
            "study_title": study.title,
            "plain_language_summary": version.plain_language_text,
            "style": style,
            "status": "generated",
            "keywords": study.keywords,
            "created_at": summary.created_at.isoformat()
        }
    except Exception as e:
        return {"error": f"Error generating summary: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR


@router.get(
    path="/studies/bulk/summaries",
    summary="Get summaries for multiple mental health studies",
    description="Batch retrieve abstracts/summaries for multiple studies"
)
async def get_studies_summaries(
    limit: int = Query(20, ge=1, le=100, description="Maximum studies to return")
):
    """
    Get summaries for all mental health studies with their abstracts and metadata.
    Useful for batch processing and overview.
    """
    all_studies = studies_loader.get_all_studies()[:limit]
    
    summaries = []
    for study in all_studies:
        summaries.append({
            "study_id": study.study_id,
            "title": study.title,
            "abstract": study.abstract[:200] + "..." if len(study.abstract) > 200 else study.abstract,
            "keywords": study.keywords,
            "date": study.prod_date,
            "producers": [p.get("name", "") for p in study.producers]
        })
    
    return {
        "count": len(summaries),
        "studies": summaries
    }


@router.post(
    path="/studies/search/by-construct/{construct}",
    status_code=status.HTTP_200_OK,
    summary="Search and summarize studies by construct"
)
async def search_and_summarize_by_construct(
    construct: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
):
    """
    Find mental health studies related to a specific construct and get their summaries.
    Combines discovery and summarization.
    """
    studies = studies_loader.get_studies_by_construct(construct)[:limit]
    
    summaries = []
    for study in studies:
        summaries.append({
            "study_id": study.study_id,
            "title": study.title,
            "abstract": study.abstract[:150] + "..." if len(study.abstract) > 150 else study.abstract,
            "keywords": [kw for kw in study.keywords if construct.lower() in kw.lower()]
        })
    
    return {
        "construct": construct,
        "count": len(summaries),
        "studies": summaries
    }
