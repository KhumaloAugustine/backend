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

router = APIRouter(prefix="/summarise", tags=["Summarisation"])

# Service instance
service = create_summarisation_service()


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
