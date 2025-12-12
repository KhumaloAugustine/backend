"""
MIT License

Copyright (c) 2025 PAMHoYA Team (https://pamhoya.ac.uk)
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence

Data Loader Service for loading and processing datasets from various formats
(CSV, Stata, Excel, JSON, Parquet, etc.)
"""

import logging
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json

logger = logging.getLogger(__name__)


class DataLoader:
    """Service for loading datasets from various sources"""
    
    def __init__(self, base_path: str = "Datasets"):
        """
        Initialize the data loader.
        
        Args:
            base_path: Base path where datasets are stored
        """
        self.base_path = Path(base_path)
        self.loaded_datasets: Dict[str, Dict[str, Any]] = {}
        self.available_sources = self._discover_available_sources()
    
    def _discover_available_sources(self) -> Dict[str, List[str]]:
        """Discover all available data sources in the Datasets directory"""
        sources = {}
        
        if not self.base_path.exists():
            logger.warning(f"Datasets directory not found: {self.base_path}")
            return sources
        
        # Scan for NIDS
        nids_path = self.base_path / "NIDS 2008-2017"
        if nids_path.exists():
            sources["NIDS"] = [f.name for f in nids_path.glob("*.zip")]
        
        # Scan for NIDS-CRAM
        nids_cram_path = self.base_path / "NIDS-CRAM"
        if nids_cram_path.exists():
            sources["NIDS_CRAM"] = [f.name for f in nids_cram_path.glob("*.zip")]
        
        # Scan for SAPRIN
        saprin_path = self.base_path / "SAPRIN"
        if saprin_path.exists():
            sources["SAPRIN"] = [f.name for f in saprin_path.glob("*.zip")]
        
        logger.info(f"Discovered data sources: {sources}")
        return sources
    
    def get_available_sources(self) -> Dict[str, List[str]]:
        """Get list of all available data sources and files"""
        return self.available_sources
    
    def get_source_files(self, source_type: str) -> List[str]:
        """Get all files for a specific source type"""
        return self.available_sources.get(source_type, [])
    
    def load_dataset_metadata(
        self,
        source_type: str,
        file_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load metadata about a dataset without loading all data.
        Useful for discovering dataset structure.
        
        Args:
            source_type: Type of source (NIDS, NIDS_CRAM, SAPRIN)
            file_name: Name of the dataset file
            
        Returns:
            Dictionary with dataset metadata
        """
        source_path_map = {
            "NIDS": "NIDS 2008-2017",
            "NIDS_CRAM": "NIDS-CRAM",
            "SAPRIN": "SAPRIN"
        }
        
        source_dir = source_path_map.get(source_type)
        if not source_dir:
            logger.error(f"Unknown source type: {source_type}")
            return None
        
        file_path = self.base_path / source_dir / file_name
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        metadata = {
            "source_type": source_type,
            "file_name": file_name,
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "file_format": file_path.suffix,
            "available": True
        }
        
        # For zip files, list contents
        if file_path.suffix == ".zip":
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    metadata["contents"] = zip_ref.namelist()
                    metadata["file_count"] = len(zip_ref.namelist())
            except Exception as e:
                logger.error(f"Error reading zip file {file_path}: {e}")
                metadata["error"] = str(e)
        
        return metadata
    
    def list_dataset_contents(
        self,
        source_type: str,
        file_name: str
    ) -> Optional[List[str]]:
        """
        List the contents of a dataset file (useful for zip files).
        
        Args:
            source_type: Type of source
            file_name: Name of the file
            
        Returns:
            List of file names in the dataset
        """
        metadata = self.load_dataset_metadata(source_type, file_name)
        if not metadata:
            return None
        return metadata.get("contents")
    
    def get_data_dictionary(
        self,
        source_type: str,
        file_name: str,
        expected_variables: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get data dictionary/variable definitions for a dataset.
        
        Args:
            source_type: Type of source
            file_name: Name of the file
            expected_variables: List of variables to focus on
            
        Returns:
            Dictionary with variable definitions and metadata
        """
        # This would typically parse Stata .dct files, DDI documentation, or data files
        # For now, return a template structure
        
        metadata = self.load_dataset_metadata(source_type, file_name)
        if not metadata:
            return None
        
        data_dict = {
            "dataset": file_name,
            "source_type": source_type,
            "variables": [],
            "documentation_available": False
        }
        
        # In a real implementation, this would:
        # 1. Parse .dct (Stata dictionary) files
        # 2. Extract variable information from DDI documentation
        # 3. Analyze actual data files for structure
        
        return data_dict
    
    def create_dataset_summary(
        self,
        source_type: str
    ) -> Dict[str, Any]:
        """
        Create a summary of all datasets available from a source.
        
        Args:
            source_type: Type of source
            
        Returns:
            Summary of available datasets
        """
        files = self.get_source_files(source_type)
        
        datasets = []
        for file_name in files:
            metadata = self.load_dataset_metadata(source_type, file_name)
            if metadata:
                datasets.append(metadata)
        
        return {
            "source_type": source_type,
            "total_datasets": len(datasets),
            "datasets": datasets
        }
    
    def get_all_sources_summary(self) -> Dict[str, Any]:
        """Get summary of all available data sources"""
        summary = {
            "total_sources": len(self.available_sources),
            "sources": {}
        }
        
        for source_type in self.available_sources.keys():
            summary["sources"][source_type] = self.create_dataset_summary(source_type)
        
        return summary


# Global instance
_data_loader_instance: Optional[DataLoader] = None


def get_data_loader(base_path: str = "Datasets") -> DataLoader:
    """Get or create the global data loader instance"""
    global _data_loader_instance
    if _data_loader_instance is None:
        _data_loader_instance = DataLoader(base_path)
    return _data_loader_instance
