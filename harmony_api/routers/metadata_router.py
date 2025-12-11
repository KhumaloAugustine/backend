"""
MIT License

Copyright (c) 2025 PAMHoYA Team (https://pamhoya.ac.uk)
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence

API Router for metadata harmonization and access endpoints.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from harmony_api.schemas.metadata_schemas import (
    HarmonizedMetadataSchema,
    MetadataSearchResponseSchema,
    MetadataUploadSchema,
)
from harmony_api.services.metadata_harmonizer import get_harmonizer
from harmony_api.services.metadata_loader import MetadataLoader

router = APIRouter(prefix="/metadata", tags=["Metadata Harmonization"])


class ResponseModel(BaseModel):
    """Base response model with common fields"""
    success: bool
    message: str


class MetadataLoadResponse(ResponseModel):
    """Response model for metadata loading"""
    sources_loaded: List[str]
    details: Optional[Dict[str, Any]] = None


class MetadataUploadResponse(ResponseModel):
    """Response model for metadata upload"""
    source_id: str
    source_name: str


class MetadataStatsResponse(BaseModel):
    """Response model for metadata statistics"""
    total_sources: int
    harmonized_count: int
    sources: List[Dict[str, str]]


def _handle_error(error: Exception, message: str) -> None:
    """Common error handling for API endpoints."""
    raise HTTPException(status_code=500, detail=f"{message}: {str(error)}")


@router.post("/load-saprin", response_model=MetadataLoadResponse, status_code=200)
async def load_saprin_metadata():
    """Load SAPRIN Mental Health metadata into the system."""
    try:
        harmonizer = get_harmonizer()
        loader = MetadataLoader(harmonizer)
        results = loader.load_saprin_metadata()
        sources_loaded = loader.get_loaded_sources()

        return MetadataLoadResponse(
            success=True,
            message=f"Successfully loaded {len(sources_loaded)} SAPRIN datasets",
            sources_loaded=sources_loaded,
            details=results,
        )
    except Exception as e:
        _handle_error(e, "Error loading SAPRIN metadata")


@router.post("/upload", response_model=MetadataUploadResponse, status_code=201)
async def upload_metadata(metadata: MetadataUploadSchema):
    """Upload and harmonize metadata from a JSON source."""
    try:
        harmonizer = get_harmonizer()
        harmonized = harmonizer.harmonize_ddi_metadata(
            raw_metadata=metadata.metadata_json,
            source_name=metadata.source_name,
            source_url=metadata.source_url,
        )

        return MetadataUploadResponse(
            success=True,
            message=f"Successfully harmonized metadata for {metadata.source_name}",
            source_id=harmonized.source_id,
            source_name=harmonized.source_name,
        )
    except Exception as e:
        _handle_error(e, "Error harmonizing metadata")


@router.get("/search", response_model=MetadataSearchResponseSchema, status_code=200)
async def search_metadata(
    q: str = Query(..., description="Search query string"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Results per page"),
):
    """Search harmonized metadata by query across title, abstract, keywords, and source name."""
    try:
        harmonizer = get_harmonizer()
        results = harmonizer.search_metadata(q)

        # Apply pagination
        total = len(results)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        return MetadataSearchResponseSchema(
            total=total,
            page=page,
            page_size=page_size,
            results=results[start_idx:end_idx],
        )
    except Exception as e:
        _handle_error(e, "Error searching metadata")


@router.get("/{source_id}", response_model=HarmonizedMetadataSchema, status_code=200)
async def get_metadata(source_id: str):
    """Get harmonized metadata by source ID."""
    try:
        harmonizer = get_harmonizer()
        metadata = harmonizer.get_metadata_by_id(source_id)

        if not metadata:
            raise HTTPException(status_code=404, detail=f"Metadata not found: {source_id}")

        return metadata
    except HTTPException:
        raise
    except Exception as e:
        _handle_error(e, "Error retrieving metadata")


@router.get("", response_model=List[HarmonizedMetadataSchema], status_code=200)
async def list_all_metadata(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum records to return"),
):
    """List all harmonized metadata with pagination."""
    try:
        harmonizer = get_harmonizer()
        all_metadata = harmonizer.get_all_metadata()
        return all_metadata[skip : skip + limit]
    except Exception as e:
        _handle_error(e, "Error listing metadata")


@router.get("/stats/summary", response_model=MetadataStatsResponse, status_code=200)
async def get_metadata_stats():
    """Get summary statistics about harmonized metadata."""
    try:
        harmonizer = get_harmonizer()
        all_metadata = harmonizer.get_all_metadata()

        return MetadataStatsResponse(
            total_sources=len(all_metadata),
            harmonized_count=sum(
                1 for m in all_metadata if m.harmonization_status == "harmonized"
            ),
            sources=[
                {"source_id": m.source_id, "source_name": m.source_name}
                for m in all_metadata
            ],
        )
    except Exception as e:
        _handle_error(e, "Error getting metadata statistics")


@router.get("/countries/list", response_model=Dict[str, List[str]], status_code=200)
async def get_countries():
    """Get list of all countries covered by available datasets."""
    try:
        harmonizer = get_harmonizer()
        countries = set()
        for metadata in harmonizer.get_all_metadata():
            countries.update(metadata.countries)
        return {"countries": sorted(list(countries))}
    except Exception as e:
        _handle_error(e, "Error getting countries")


@router.get("/keywords/list", response_model=Dict[str, List[str]], status_code=200)
async def get_keywords():
    """Get list of all keywords across datasets."""
    try:
        harmonizer = get_harmonizer()
        keywords = set()
        for metadata in harmonizer.get_all_metadata():
            keywords.update(metadata.keywords)
        return {"keywords": sorted(list(keywords))}
    except Exception as e:
        _handle_error(e, "Error getting keywords")
