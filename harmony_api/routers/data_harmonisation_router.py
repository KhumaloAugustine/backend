"""
MIT License

Copyright (c) 2025 PAMHoYA Team (https://pamhoya.ac.uk)
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence

API Router for data harmonization endpoints
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from harmony_api.services.data_harmonization_service import get_data_harmonizer
from harmony_api.services.data_loader import get_data_loader

router = APIRouter(prefix="/data-harmonisation", tags=["Data Harmonisation"])


class VariableDefinition(BaseModel):
    """Definition of a variable"""
    original_name: str
    harmonized_name: str
    data_type: str
    description: Optional[str] = None
    valid_values: Optional[List[str]] = None
    transformation_rules: Optional[Dict[str, str]] = None


class HarmonizeDatasetRequest(BaseModel):
    """Request to harmonize a dataset"""
    source_name: str
    source_type: str  # NIDS, NIDS_CRAM, SAPRIN
    title: str
    description: str
    variables: List[VariableDefinition]


class DatasetSummaryResponse(BaseModel):
    """Summary of a harmonized dataset"""
    dataset_id: str
    source_name: str
    source_type: str
    title: str
    variable_count: int
    harmonization_status: str


@router.get("/sources", response_model=Dict[str, Any], status_code=200)
async def get_available_sources():
    """Get all available data sources and their files"""
    try:
        loader = get_data_loader()
        return loader.get_all_sources_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sources: {str(e)}")


@router.get("/sources/{source_type}", response_model=Dict[str, Any], status_code=200)
async def get_source_files(source_type: str):
    """Get all files available for a specific source type"""
    try:
        loader = get_data_loader()
        return loader.create_dataset_summary(source_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching source files: {str(e)}")


@router.get("/sources/{source_type}/{file_name}/metadata", response_model=Dict[str, Any], status_code=200)
async def get_dataset_metadata(source_type: str, file_name: str):
    """Get metadata about a specific dataset file"""
    try:
        loader = get_data_loader()
        metadata = loader.load_dataset_metadata(source_type, file_name)
        if not metadata:
            raise HTTPException(status_code=404, detail=f"Dataset not found: {file_name}")
        return metadata
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading metadata: {str(e)}")


@router.get("/datasets", response_model=List[DatasetSummaryResponse], status_code=200)
async def list_harmonized_datasets():
    """List all harmonized datasets"""
    try:
        harmonizer = get_data_harmonizer()
        datasets = harmonizer.get_all_datasets()
        return [
            DatasetSummaryResponse(
                dataset_id=ds.dataset_id,
                source_name=ds.source_name,
                source_type=ds.source_type,
                title=ds.title,
                variable_count=ds.variable_count or 0,
                harmonization_status=ds.harmonization_status
            )
            for ds in datasets
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing datasets: {str(e)}")


@router.get("/datasets/{dataset_id}", response_model=Dict[str, Any], status_code=200)
async def get_harmonized_dataset(dataset_id: str):
    """Get details of a harmonized dataset"""
    try:
        harmonizer = get_data_harmonizer()
        dataset = harmonizer.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
        return dataset.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dataset: {str(e)}")


@router.post("/datasets/harmonize", response_model=DatasetSummaryResponse, status_code=201)
async def harmonize_dataset(request: HarmonizeDatasetRequest):
    """Harmonize a new dataset"""
    try:
        harmonizer = get_data_harmonizer()
        
        # Convert variable definitions to dict
        variables = [
            {
                "original_name": v.original_name,
                "harmonized_name": v.harmonized_name,
                "data_type": v.data_type,
                "description": v.description,
                "valid_values": v.valid_values,
                "transformation_rules": v.transformation_rules
            }
            for v in request.variables
        ]
        
        # Create harmonized dataset
        dataset = harmonizer.create_harmonized_dataset(
            source_name=request.source_name,
            source_type=request.source_type,
            title=request.title,
            description=request.description,
            variables=variables
        )
        
        return DatasetSummaryResponse(
            dataset_id=dataset.dataset_id,
            source_name=dataset.source_name,
            source_type=dataset.source_type,
            title=dataset.title,
            variable_count=dataset.variable_count or 0,
            harmonization_status=dataset.harmonization_status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error harmonizing dataset: {str(e)}")


@router.get("/datasets/{dataset_id}/variables", response_model=Dict[str, Any], status_code=200)
async def get_dataset_variables(dataset_id: str):
    """Get all variables in a harmonized dataset"""
    try:
        harmonizer = get_data_harmonizer()
        dataset = harmonizer.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
        
        return {
            "dataset_id": dataset_id,
            "variable_count": len(dataset.variables),
            "variables": [
                {
                    "original_name": v.original_name,
                    "harmonized_name": v.harmonized_name,
                    "data_type": v.data_type,
                    "description": v.description
                }
                for v in dataset.variables
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching variables: {str(e)}")


@router.get("/variable-mappings/{harmonized_var_name}", response_model=Dict[str, Any], status_code=200)
async def get_variable_mappings(harmonized_var_name: str):
    """Get all source variables mapped to a harmonized variable"""
    try:
        harmonizer = get_data_harmonizer()
        mappings = harmonizer.get_variable_mappings(harmonized_var_name)
        
        return {
            "harmonized_variable": harmonized_var_name,
            "mapping_count": len(mappings),
            "mappings": [
                {"source": source, "variable": var}
                for source, var in mappings
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching mappings: {str(e)}")


@router.get("/statistics", response_model=Dict[str, Any], status_code=200)
async def get_harmonization_statistics():
    """Get statistics about harmonized data"""
    try:
        harmonizer = get_data_harmonizer()
        loader = get_data_loader()
        
        datasets = harmonizer.get_all_datasets()
        sources = loader.get_available_sources()
        
        return {
            "harmonized_datasets": len(datasets),
            "available_sources": len(sources),
            "sources": sources,
            "harmonized_by_type": {
                source_type: len(harmonizer.get_datasets_by_source(source_type))
                for source_type in sources.keys()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")
