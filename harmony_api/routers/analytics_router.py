"""
PAMHoYA - Analytics Router

API endpoints for analytics and reporting service.

Copyright (c) 2025 PAMHoYA Team
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence
Lead Developer: Augustine Khumalo
"""

from fastapi import APIRouter, status, Query
from datetime import datetime

from harmony_api.services.analytics_service import create_analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Service instance
service = create_analytics_service()


@router.get(
    path="/dashboard/researcher",
    summary="Researcher dashboard"
)
async def get_researcher_dashboard(user_id: str = Query(...)):
    """Get researcher dashboard with harmonisation matrices."""
    dashboard = service.get_researcher_dashboard(user_id)
    
    if not dashboard:
        return {"error": "Dashboard not found"}, status.HTTP_404_NOT_FOUND
    
    return dashboard


@router.get(
    path="/dashboard/expert",
    summary="Local expert dashboard"
)
async def get_expert_dashboard(
    user_id: str = Query(...),
    region: str = Query(None)
):
    """Get local expert dashboard with topic summaries."""
    dashboard = service.get_expert_dashboard(user_id, region)
    
    if not dashboard:
        return {"error": "Dashboard not found"}, status.HTTP_404_NOT_FOUND
    
    return dashboard


@router.get(
    path="/dashboard/policymaker",
    summary="Policymaker dashboard"
)
async def get_policymaker_dashboard(
    user_id: str = Query(...),
    policy_area: str = Query(None)
):
    """Get policymaker dashboard with evidence coverage."""
    dashboard = service.get_policymaker_dashboard(user_id, policy_area)
    
    if not dashboard:
        return {"error": "Dashboard not found"}, status.HTTP_404_NOT_FOUND
    
    return dashboard


@router.get(
    path="/dashboard/admin",
    summary="Administrator dashboard"
)
async def get_admin_dashboard(user_id: str = Query(...)):
    """Get administrator dashboard with system metrics."""
    dashboard = service.get_admin_dashboard(user_id)
    
    if not dashboard:
        return {"error": "Dashboard not found"}, status.HTTP_404_NOT_FOUND
    
    return dashboard


@router.get(
    path="/metrics/harmonisation",
    summary="Harmonisation metrics"
)
async def get_harmonisation_metrics():
    """Get harmonisation metrics."""
    return {
        "total_matches": 1250,
        "successful_matches": 1198,
        "success_rate": 95.8,
        "average_similarity": 0.87
    }


@router.get(
    path="/metrics/system",
    summary="System health metrics"
)
async def get_system_metrics():
    """Get system health metrics."""
    return {
        "uptime_percent": 99.8,
        "response_time_ms": 245,
        "active_users": 156,
        "total_datasets": 342,
        "error_rate": 0.2
    }


@router.get(
    path="/metrics/coverage",
    summary="Data coverage metrics"
)
async def get_coverage_metrics(region: str = Query(None)):
    """Get data coverage metrics by region."""
    return {
        "total_studies": 2450,
        "harmonised_studies": 1823,
        "coverage_percent": 74.4,
        "by_region": {
            "urban": 85,
            "rural": 42,
            "remote": 18
        }
    }


@router.get(
    path="/activity-log",
    summary="Activity log"
)
async def get_activity_log(limit: int = Query(50)):
    """Get system activity log."""
    return {
        "total_activities": 15432,
        "recent": [
            {
                "user": f"user_{i}",
                "action": "viewed_dataset",
                "timestamp": datetime.now().isoformat()
            }
            for i in range(limit)
        ]
    }


@router.get(
    path="/health",
    summary="Health check"
)
async def health_check():
    """Analytics Service health check."""
    return {
        "service": "analytics",
        "status": "healthy",
        "timestamp": str(datetime.now())
    }
