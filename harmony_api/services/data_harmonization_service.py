"""
MIT License

Copyright (c) 2025 PAMHoYA Team (https://pamhoya.ac.uk)
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence

Data Harmonization Service for normalizing and standardizing data
across different sources (NIDS, NIDS-CRAM, SAPRIN, etc.)
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class HarmonizedVariable:
    """Represents a harmonized variable across data sources"""
    original_name: str
    harmonized_name: str
    data_type: str
    source: str
    description: Optional[str] = None
    valid_values: Optional[List[str]] = None
    missing_values: Optional[List[str]] = None
    transformation_rules: Optional[Dict[str, str]] = None


@dataclass
class HarmonizedDataset:
    """Represents a harmonized dataset"""
    dataset_id: str
    source_name: str
    source_type: str  # NIDS, NIDS_CRAM, SAPRIN, etc.
    title: str
    description: str
    variables: List[HarmonizedVariable]
    record_count: Optional[int] = None
    variable_count: Optional[int] = None
    time_period: Optional[str] = None
    harmonization_date: str = ""
    harmonization_status: str = "pending"  # pending, in_progress, completed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "dataset_id": self.dataset_id,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "title": self.title,
            "description": self.description,
            "variables": [asdict(v) for v in self.variables],
            "record_count": self.record_count,
            "variable_count": self.variable_count,
            "time_period": self.time_period,
            "harmonization_date": self.harmonization_date,
            "harmonization_status": self.harmonization_status
        }


class DataHarmonizer:
    """Service for harmonizing data across different sources"""
    
    def __init__(self):
        """Initialize the data harmonizer"""
        self.harmonized_datasets: Dict[str, HarmonizedDataset] = {}
        self.variable_mappings: Dict[str, List[Tuple[str, str]]] = {}  # Map harmonized vars to source vars
        self.data_sources_config = self._load_data_sources_config()
    
    def _load_data_sources_config(self) -> Dict[str, Any]:
        """Load configuration for all data sources"""
        return {
            "NIDS": {
                "path": "Datasets/NIDS 2008-2017",
                "type": "stata",
                "waves": [1, 2, 3, 4, 5],
                "key_variables": {
                    "pid": "pid",  # Person ID
                    "hhid": "hhid",  # Household ID
                    "age": "age",
                    "gender": "gender",
                    "employment": "employed",
                    "income": "income"
                }
            },
            "NIDS_CRAM": {
                "path": "Datasets/NIDS-CRAM",
                "type": "stata",
                "waves": [1, 2, 3, 4, 5],
                "key_variables": {
                    "pid": "pid",
                    "hhid": "hhid",
                    "age": "age",
                    "gender": "gender",
                    "depression": "depression_score",
                    "anxiety": "anxiety_score",
                    "mental_health": "mental_health_scale"
                }
            },
            "SAPRIN": {
                "path": "Datasets/SAPRIN",
                "type": "stata",
                "datasets": ["MHDPIEE", "MHDISO", "MHDICS", "MHDHHS", "MHDHHCS", "MHDHHAS"],
                "key_variables": {
                    "pid": "pid",
                    "hhid": "hhid",
                    "mental_health": "mental_health_indicator",
                    "depression": "depression_indicator"
                }
            }
        }
    
    def create_harmonized_dataset(
        self,
        source_name: str,
        source_type: str,
        title: str,
        description: str,
        variables: List[Dict[str, Any]]
    ) -> HarmonizedDataset:
        """
        Create a harmonized dataset from source variables.
        
        Args:
            source_name: Name of the data source
            source_type: Type of source (NIDS, NIDS_CRAM, SAPRIN)
            title: Dataset title
            description: Dataset description
            variables: List of variable definitions
            
        Returns:
            HarmonizedDataset instance
        """
        # Generate dataset ID
        dataset_id = self._generate_dataset_id(source_name)
        
        # Create harmonized variables
        harmonized_vars = []
        for var in variables:
            harmonized_var = HarmonizedVariable(
                original_name=var.get("original_name", ""),
                harmonized_name=var.get("harmonized_name", ""),
                data_type=var.get("data_type", "string"),
                source=source_name,
                description=var.get("description"),
                valid_values=var.get("valid_values"),
                missing_values=var.get("missing_values"),
                transformation_rules=var.get("transformation_rules")
            )
            harmonized_vars.append(harmonized_var)
        
        # Create harmonized dataset
        dataset = HarmonizedDataset(
            dataset_id=dataset_id,
            source_name=source_name,
            source_type=source_type,
            title=title,
            description=description,
            variables=harmonized_vars,
            variable_count=len(harmonized_vars),
            harmonization_date=datetime.now().isoformat(),
            harmonization_status="completed"
        )
        
        # Store dataset
        self.harmonized_datasets[dataset_id] = dataset
        
        # Update variable mappings
        self._update_variable_mappings(dataset)
        
        logger.info(f"Created harmonized dataset {dataset_id} from {source_name}")
        return dataset
    
    def _generate_dataset_id(self, source_name: str) -> str:
        """Generate a unique dataset ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        source_hash = hashlib.md5(source_name.encode()).hexdigest()[:8]
        return f"HARM_{timestamp}_{source_hash}"
    
    def _update_variable_mappings(self, dataset: HarmonizedDataset) -> None:
        """Update variable mappings for the dataset"""
        for var in dataset.variables:
            harmonized_name = var.harmonized_name
            if harmonized_name not in self.variable_mappings:
                self.variable_mappings[harmonized_name] = []
            
            self.variable_mappings[harmonized_name].append(
                (dataset.source_name, var.original_name)
            )
    
    def get_dataset(self, dataset_id: str) -> Optional[HarmonizedDataset]:
        """Get a harmonized dataset by ID"""
        return self.harmonized_datasets.get(dataset_id)
    
    def get_all_datasets(self) -> List[HarmonizedDataset]:
        """Get all harmonized datasets"""
        return list(self.harmonized_datasets.values())
    
    def get_datasets_by_source(self, source_type: str) -> List[HarmonizedDataset]:
        """Get all datasets from a specific source type"""
        return [
            ds for ds in self.harmonized_datasets.values()
            if ds.source_type == source_type
        ]
    
    def get_variable_mappings(self, harmonized_var_name: str) -> List[Tuple[str, str]]:
        """Get all source variables mapped to a harmonized variable"""
        return self.variable_mappings.get(harmonized_var_name, [])
    
    def harmonize_variable_value(
        self,
        dataset_id: str,
        variable_name: str,
        value: Any
    ) -> Any:
        """
        Apply transformation rules to harmonize a variable value.
        
        Args:
            dataset_id: ID of the dataset
            variable_name: Name of the variable
            value: Original value
            
        Returns:
            Harmonized value
        """
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return value
        
        # Find variable
        var = next(
            (v for v in dataset.variables if v.harmonized_name == variable_name),
            None
        )
        
        if not var or not var.transformation_rules:
            return value
        
        # Apply transformation
        return var.transformation_rules.get(str(value), value)
    
    def export_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Export a dataset as a dictionary"""
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return None
        return dataset.to_dict()
    
    def export_all_datasets(self) -> Dict[str, Any]:
        """Export all datasets"""
        return {
            "datasets": [ds.to_dict() for ds in self.get_all_datasets()],
            "total_count": len(self.harmonized_datasets),
            "export_date": datetime.now().isoformat()
        }


# Global instance
_harmonizer_instance: Optional[DataHarmonizer] = None


def get_data_harmonizer() -> DataHarmonizer:
    """Get or create the global data harmonizer instance"""
    global _harmonizer_instance
    if _harmonizer_instance is None:
        _harmonizer_instance = DataHarmonizer()
    return _harmonizer_instance
