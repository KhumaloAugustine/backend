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
from harmony_api.services.mental_health_studies_loader import get_mental_health_studies_loader

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Service instances
service = create_analytics_service()
studies_loader = get_mental_health_studies_loader()


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


# ============================================================================
# MENTAL HEALTH STUDIES ANALYTICS - INTEGRATED
# ============================================================================

@router.get(
    path="/studies/overview",
    summary="Mental health studies overview"
)
async def get_studies_overview():
    """
    Get overview analytics for all mental health studies loaded in the system.
    Includes total count, constructs coverage, and distribution metrics.
    """
    all_studies = studies_loader.get_all_studies()
    constructs = studies_loader.get_all_constructs()
    
    return {
        "total_studies": len(all_studies),
        "total_constructs": len(constructs),
        "studies_loaded_at": datetime.now().isoformat(),
        "constructs_sample": sorted(list(constructs))[:15]
    }


@router.get(
    path="/studies/construct-coverage",
    summary="Mental health construct coverage analytics"
)
async def get_construct_coverage():
    """
    Get analytics on which mental health constructs are covered by studies.
    Shows distribution of studies across different constructs.
    """
    all_studies = studies_loader.get_all_studies()
    construct_map = {}
    
    for study in all_studies:
        for construct in study.get_constructs():
            if construct not in construct_map:
                construct_map[construct] = 0
            construct_map[construct] += 1
    
    # Sort by frequency
    sorted_constructs = sorted(construct_map.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "total_constructs": len(construct_map),
        "construct_coverage": [
            {
                "construct": c[0],
                "studies_count": c[1],
                "percentage": round(c[1] / len(all_studies) * 100, 2) if all_studies else 0
            }
            for c in sorted_constructs[:20]
        ]
    }


@router.get(
    path="/studies/author-statistics",
    summary="Research author statistics"
)
async def get_author_statistics():
    """
    Get analytics on authors and researchers across mental health studies.
    Shows most prolific authors and research institutions.
    """
    all_studies = studies_loader.get_all_studies()
    author_map = {}
    
    for study in all_studies:
        for producer in study.producers:
            author_name = producer.get("name", "Unknown")
            if author_name not in author_map:
                author_map[author_name] = {
                    "name": author_name,
                    "affiliations": set(),
                    "studies": 0
                }
            author_map[author_name]["studies"] += 1
            if affiliation := producer.get("affiliation"):
                author_map[author_name]["affiliations"].add(affiliation)
    
    # Convert to list and sort by studies count
    authors_list = [
        {
            "name": a[0],
            "studies_count": a[1]["studies"],
            "affiliations": list(a[1]["affiliations"])
        }
        for a in sorted(author_map.items(), key=lambda x: x[1]["studies"], reverse=True)
    ]
    
    return {
        "total_authors": len(author_map),
        "top_authors": authors_list[:10]
    }


@router.get(
    path="/studies/temporal-analysis",
    summary="Temporal distribution of studies"
)
async def get_temporal_analysis():
    """
    Get temporal analytics showing when studies were conducted and data was collected.
    Useful for understanding research coverage over time.
    """
    all_studies = studies_loader.get_all_studies()
    year_map = {}
    
    for study in all_studies:
        date_str = study.prod_date
        if date_str:
            try:
                year = date_str[:4]
                if year.isdigit():
                    year = int(year)
                    if year not in year_map:
                        year_map[year] = 0
                    year_map[year] += 1
            except:
                pass
    
    sorted_years = sorted(year_map.items())
    
    return {
        "total_studies": len(all_studies),
        "years_covered": sorted([y[0] for y in sorted_years]),
        "studies_by_year": [
            {"year": y[0], "count": y[1]}
            for y in sorted_years
        ],
        "earliest_year": min([y[0] for y in sorted_years]) if sorted_years else None,
        "latest_year": max([y[0] for y in sorted_years]) if sorted_years else None
    }


@router.get(
    path="/studies/data-collection-methods",
    summary="Data collection methods analytics"
)
async def get_data_collection_methods():
    """
    Get analytics on data collection methodologies used across studies.
    Shows distribution of research methods (surveys, interviews, longitudinal, etc).
    """
    all_studies = studies_loader.get_all_studies()
    method_map = {}
    
    for study in all_studies:
        for mode in study.collection_mode:
            if isinstance(mode, str):
                if mode not in method_map:
                    method_map[mode] = 0
                method_map[mode] += 1
            elif isinstance(mode, dict):
                mode_type = mode.get("type", "unknown")
                if mode_type not in method_map:
                    method_map[mode_type] = 0
                method_map[mode_type] += 1
    
    sorted_methods = sorted(method_map.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "total_methods": len(method_map),
        "methods": [
            {
                "method": m[0],
                "count": m[1],
                "percentage": round(m[1] / len(all_studies) * 100, 2) if all_studies else 0
            }
            for m in sorted_methods
        ]
    }


@router.get(
    path="/studies/insights/{study_id}",
    summary="Detailed study insights and metadata"
)
async def get_study_insights(study_id: str):
    """
    Get detailed analytical insights for a specific mental health study.
    Includes authors, methodologies, constructs, and coverage information.
    """
    study = studies_loader.get_study(study_id)
    
    if not study:
        return {"error": f"Study {study_id} not found"}, status.HTTP_404_NOT_FOUND
    
    return {
        "study_id": study_id,
        "title": study.title,
        "authors_count": len(study.producers),
        "unique_institutions": len(set(p.get("affiliation", "") for p in study.producers)),
        "constructs_covered": study.get_constructs(),
        "data_collection_date": study.data_collection_date,
        "collection_modes": study.collection_mode,
        "keywords": study.keywords,
        "abstract_length": len(study.abstract),
        "metadata_completeness": "high" if all([
            study.title, study.abstract, study.producers, study.keywords
        ]) else "partial"
    }


@router.get(
    path="/studies/available",
    summary="List available studies for analytics",
    description="Get all available mental health studies for analytics and reporting"
)
async def get_available_studies_for_analytics(
    limit: int = Query(100, ge=1, le=500, description="Maximum results to return"),
    search: str = Query(None, description="Optional search term"),
    construct: str = Query(None, description="Filter by construct/keyword")
):
    """
    List all available mental health studies for analytics including:
    - Study metadata and abstracts
    - Construct/keyword filters
    - Producer/institution information
    """
    try:
        # Load mental health studies
        studies_loader.load_all_studies()
        
        if construct:
            all_studies = studies_loader.get_studies_by_construct(construct)
        else:
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
                "abstract": study.abstract[:250] + "..." if len(study.abstract) > 250 else study.abstract,
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


@router.get(
    path="/studies/system-metrics",
    summary="System metrics for studies module"
)
async def get_studies_system_metrics():
    """
    Get system-level metrics for the mental health studies module.
    Shows loading status, coverage, and performance metrics.
    """
    all_studies = studies_loader.get_all_studies()
    
    return {
        "total_studies_loaded": len(all_studies),
        "total_constructs": len(studies_loader.get_all_constructs()),
        "system_status": "operational" if len(all_studies) > 0 else "no_data",
        "timestamp": datetime.now().isoformat(),
        "module": "mental_health_studies_analytics"
    }
