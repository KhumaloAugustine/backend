"""
PAMHoYA - Data Harmonisation Service

Aligns and merges datasets into consistent structure.
PoC implementation following 3-layer architecture.

Copyright (c) 2025 PAMHoYA Team
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence
Lead Developer: Augustine Khumalo
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
import json

from harmony_api.services.base_service import BaseRepository, BaseService, BaseEntity
from harmony_api.core.exceptions import EntityNotFoundException, OperationFailedException


# ============================================================================
# MODELS
# ============================================================================

class HarmonisationStatus(str, Enum):
    """Harmonisation job status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ColumnMapping:
    """Represents mapping between source and target columns"""
    def __init__(self, source_col: str, target_col: str, transformation: str = "identity"):
        self.source_col = source_col
        self.target_col = target_col
        self.transformation = transformation  # identity, normalize, convert, etc.


class HarmonisationJob:
    """Harmonisation job model"""
    def __init__(self, source_dataset_id: str, target_dataset_id: str, 
                 created_by: str, target_schema: Dict[str, Any] = None):
        self.id = str(uuid.uuid4())
        self.source_dataset_id = source_dataset_id
        self.target_dataset_id = target_dataset_id
        self.created_by = created_by
        self.status = HarmonisationStatus.PENDING.value
        self.target_schema = target_schema or {}
        self.mappings: List[ColumnMapping] = []
        self.result_dataset_id: Optional[str] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.report = {}


# ============================================================================
# DATA ACCESS LAYER
# ============================================================================

class HarmonisationRepository(BaseRepository):
    """Repository for harmonisation operations"""
    
    def __init__(self):
        super().__init__()  # Initialize BaseRepository
        self.jobs = {}
        self.datasets = {}
        self.mappings = {}
    
    def create_job(self, job: HarmonisationJob) -> HarmonisationJob:
        """Create new harmonisation job"""
        self.jobs[job.id] = job
        return job
    
    def get_job(self, job_id: str) -> Optional[HarmonisationJob]:
        """Get harmonisation job by ID"""
        return self.jobs.get(job_id)
    
    def update_job_status(self, job_id: str, status: str, report: Dict = None) -> Optional[HarmonisationJob]:
        """Update job status and report"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            job.status = status
            job.updated_at = datetime.now()
            if report:
                job.report = report
            return job
        return None
    
    def store_mapping(self, job_id: str, mapping: ColumnMapping) -> None:
        """Store column mapping"""
        if job_id not in self.mappings:
            self.mappings[job_id] = []
        self.mappings[job_id].append(mapping)
    
    def get_mappings(self, job_id: str) -> List[ColumnMapping]:
        """Get all mappings for a job"""
        return self.mappings.get(job_id, [])
    
    def store_dataset(self, dataset_id: str, data: Dict) -> None:
        """Store dataset"""
        self.datasets[dataset_id] = data
    
    def get_dataset(self, dataset_id: str) -> Optional[Dict]:
        """Get dataset"""
        return self.datasets.get(dataset_id)


# ============================================================================
# BUSINESS LOGIC LAYER
# ============================================================================

class DataHarmonisationService(BaseService[HarmonisationRepository]):
    """Data Harmonisation Service - Core business logic"""
    
    def __init__(self, repository: HarmonisationRepository):
        super().__init__(repository)  # Leverage BaseService
    
    def initiate_harmonisation(self, source_dataset_id: str, target_dataset_id: str,
                              created_by: str) -> HarmonisationJob:
        """Initiate data harmonisation job"""
        job = HarmonisationJob(source_dataset_id, target_dataset_id, created_by)
        return self.repository.create_job(job)
    
    def analyze_schema(self, dataset_id: str) -> Dict[str, Any]:
        """Analyze dataset schema"""
        dataset = self.repository.get_dataset(dataset_id)
        if not dataset:
            return {}
        
        schema = {
            "columns": list(dataset.keys()) if isinstance(dataset, dict) else [],
            "row_count": len(dataset) if isinstance(dataset, list) else 0,
            "column_types": {}
        }
        
        # Infer types
        if isinstance(dataset, dict):
            for col, val in dataset.items():
                schema["column_types"][col] = type(val).__name__
        
        return schema
    
    def detect_column_differences(self, source_schema: Dict, target_schema: Dict) -> Dict:
        """Detect differences between schemas"""
        source_cols = set(source_schema.get("columns", []))
        target_cols = set(target_schema.get("columns", []))
        
        return {
            "only_in_source": list(source_cols - target_cols),
            "only_in_target": list(target_cols - source_cols),
            "common": list(source_cols & target_cols),
            "type_mismatches": self._detect_type_mismatches(source_schema, target_schema)
        }
    
    def _detect_type_mismatches(self, source_schema: Dict, target_schema: Dict) -> Dict:
        """Detect type mismatches in common columns"""
        mismatches = {}
        source_types = source_schema.get("column_types", {})
        target_types = target_schema.get("column_types", {})
        
        for col in source_types:
            if col in target_types and source_types[col] != target_types[col]:
                mismatches[col] = {
                    "source_type": source_types[col],
                    "target_type": target_types[col]
                }
        
        return mismatches
    
    def create_mapping(self, job_id: str, source_col: str, target_col: str,
                      transformation: str = "identity") -> ColumnMapping:
        """Create column mapping"""
        mapping = ColumnMapping(source_col, target_col, transformation)
        self.repository.store_mapping(job_id, mapping)
        return mapping
    
    def normalize_values(self, values: List[Any], normalization_type: str = "lowercase") -> List[Any]:
        """Normalize dataset values"""
        if normalization_type == "lowercase":
            return [str(v).lower() if v is not None else None for v in values]
        elif normalization_type == "trim":
            return [str(v).strip() if v is not None else None for v in values]
        elif normalization_type == "numeric":
            result = []
            for v in values:
                try:
                    result.append(float(v) if v is not None else None)
                except (ValueError, TypeError):
                    result.append(None)
            return result
        return values
    
    def merge_datasets(self, job_id: str, source_data: Dict, target_data: Dict,
                      mappings: List[ColumnMapping]) -> Dict:
        """Merge two datasets using mappings"""
        harmonised_data = {}
        
        for mapping in mappings:
            if mapping.source_col in source_data:
                # Apply transformation
                value = source_data[mapping.source_col]
                if mapping.transformation == "normalize":
                    value = self.normalize_values([value])[0]
                
                harmonised_data[mapping.target_col] = value
        
        # Keep target data fields not in source
        for key, val in target_data.items():
            if key not in harmonised_data:
                harmonised_data[key] = val
        
        return harmonised_data
    
    def harmonise(self, job_id: str, source_dataset_id: str, 
                 target_dataset_id: str) -> HarmonisationJob:
        """Execute full harmonisation workflow"""
        job = self.repository.get_job(job_id)
        if not job:
            return None
        
        # Update status
        self.repository.update_job_status(job_id, HarmonisationStatus.IN_PROGRESS.value)
        
        try:
            # Analyze schemas
            source_dataset = self.repository.get_dataset(source_dataset_id)
            target_dataset = self.repository.get_dataset(target_dataset_id)
            
            if not source_dataset or not target_dataset:
                raise ValueError("Datasets not found")
            
            source_schema = self.analyze_schema(source_dataset_id)
            target_schema = self.analyze_schema(target_dataset_id)
            
            # Detect differences
            differences = self.detect_column_differences(source_schema, target_schema)
            
            # Generate report
            report = {
                "source_schema": source_schema,
                "target_schema": target_schema,
                "differences": differences,
                "mappings_applied": len(job.mappings),
                "timestamp": datetime.now().isoformat()
            }
            
            # Create harmonised dataset
            harmonised_id = str(uuid.uuid4())
            harmonised_data = self.merge_datasets(job_id, source_dataset, target_dataset, job.mappings)
            self.repository.store_dataset(harmonised_id, harmonised_data)
            
            job.result_dataset_id = harmonised_id
            self.repository.update_job_status(job_id, HarmonisationStatus.COMPLETED.value, report)
            
        except Exception as e:
            error_report = {"error": str(e), "timestamp": datetime.now().isoformat()}
            self.repository.update_job_status(job_id, HarmonisationStatus.FAILED.value, error_report)
        
        return job


# ============================================================================
# INITIALIZATION
# ============================================================================

def create_data_harmonisation_service() -> DataHarmonisationService:
    """Factory function to create Data Harmonisation Service"""
    repository = HarmonisationRepository()
    return DataHarmonisationService(repository)
