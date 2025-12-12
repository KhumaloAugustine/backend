"""
MIT License

Copyright (c) 2025 PAMHoYA Team (https://pamhoya.ac.uk)
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence

Metadata Ingestion Service for loading metadata from various sources.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

from harmony_api.services.metadata_harmonizer import MetadataHarmonizer

logger = logging.getLogger(__name__)


class MetadataLoader:
    """Service for loading and ingesting metadata from various sources."""

    def __init__(self, harmonizer: MetadataHarmonizer):
        """
        Initialize the metadata loader.

        Args:
            harmonizer: MetadataHarmonizer instance for processing metadata
        """
        self.harmonizer = harmonizer
        self.loaded_sources: List[str] = []

    def _harmonize_safely(
        self,
        metadata: Dict[str, Any],
        source_name: str,
        source_url: Optional[str] = None,
    ) -> bool:
        """
        Safely harmonize metadata with error handling.
        
        Args:
            metadata: Dictionary containing metadata
            source_name: Name of the data source
            source_url: Optional URL source
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.harmonizer.harmonize_ddi_metadata(
                metadata, source_name=source_name, source_url=source_url
            )
            self.loaded_sources.append(source_name)
            logger.info(f"Successfully loaded metadata from {source_name}")
            return True
        except Exception as e:
            logger.error(f"Error harmonizing metadata for {source_name}: {str(e)}")
            return False

    def load_from_json_string(
        self,
        json_string: str,
        source_name: str,
        source_url: Optional[str] = None,
    ) -> bool:
        """Load metadata from a JSON string."""
        try:
            metadata = json.loads(json_string)
            return self._harmonize_safely(metadata, source_name, source_url)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON for {source_name}: {str(e)}")
            return False

    def load_from_json_file(
        self,
        filepath: str,
        source_name: Optional[str] = None,
    ) -> bool:
        """Load metadata from a JSON file."""
        try:
            path = Path(filepath)

            if not path.exists():
                logger.error(f"File not found: {filepath}")
                return False

            with open(path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            if not source_name:
                source_name = path.stem.replace("_", " ").title()

            return self._harmonize_safely(metadata, source_name, str(path.absolute()))

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filepath}: {str(e)}")
            return False

    def load_from_directory(
        self,
        directory_path: str,
        pattern: str = "*.json",
        source_name_prefix: Optional[str] = None,
    ) -> Dict[str, bool]:
        """Load metadata from all JSON files in a directory."""
        results = {}
        dir_path = Path(directory_path)

        if not dir_path.exists():
            logger.error(f"Directory not found: {directory_path}")
            return results

        json_files = list(dir_path.rglob(pattern))
        logger.info(f"Found {len(json_files)} JSON files in {directory_path}")

        for json_file in json_files:
            try:
                relative_path = json_file.relative_to(dir_path)
                source_name = str(relative_path.parent / relative_path.stem).replace(
                    "\\", " - "
                ).replace("/", " - ")

                if source_name_prefix:
                    source_name = f"{source_name_prefix} - {source_name}"

                results[str(relative_path)] = self.load_from_json_file(
                    str(json_file), source_name
                )
            except Exception as e:
                logger.error(f"Error processing {json_file}: {str(e)}")
                results[str(relative_path)] = False

        return results

    def load_saprin_metadata(self) -> Dict[str, Any]:
        """
        Load SAPRIN metadata from standard locations.

        Returns:
            Dict with loading results
        """
        results = {
            "saprin_2022": False,
            "saprin_2024": False,
            "other_sources": {},
            "details": {}
        }

        # SAPRIN 2022 Mental Health Data Prize
        saprin_2022_json = """{
  "doc_desc": {
    "title": "SAPRIN Mental Health Data Prize 2022",
    "idno": "DDI.SAPRIN.SMHDP2022V1",
    "producers": [
      {"name": "Molulaqhooa Linda Maoyi", "abbr": "MLM", "affiliation": "SAPRIN", "role": "Documentation of Study and Review of the metadata"},
      {"name": "Kobus Herbst", "abbr": "KH", "affiliation": "SAPRIN", "role": "Documentation of Study and Review of the metadata"}
    ],
    "prod_date": "2025-07-01",
    "version_statement": {"version": "Version 2 (July 2025)", "version_notes": "V2: Edited metadata for public distribution"}
  },
  "study_desc": {
    "title_statement": {"idno": "SAPRIN.SMHDP2022V1", "title": "SAPRIN Mental Health Data Prize 2022"},
    "study_info": {
      "keywords": [{"keyword": "Mental Health, Covid-19"}],
      "topics": [{"topic": "Mental Health, Covid-19"}],
      "abstract": "SAPRIN Mental Health Data Prize 2022 dataset containing mental health screening data collected across three SAPRIN nodes in South Africa.",
      "time_periods": [{"start": "1993-01-01", "end": "2022-05-31", "cycle": "Agincourt"}],
      "coll_dates": [{"start": "1993-01-01", "end": "2022-04-30", "cycle": "Agincourt"}],
      "nation": [{"name": "South Africa", "abbreviation": "RSA"}],
      "geog_coverage": "SAPRIN nodes: Agincourt, DIMAMO, AHRI",
      "analysis_unit": "Individual and household interviews",
      "data_kind": "Event history data"
    }
  },
  "schematype": "survey"
}"""

        # SAPRIN 2024 Mental Health Datasets
        saprin_2024_json = """{
  "doc_desc": {
    "title": "SAPRIN Mental Health Datasets 2024",
    "idno": "DDI.SAPRIN.SMHD2024V1",
    "producers": [
      {"name": "Molulaqhooa Linda Maoyi", "abbr": "MLM", "affiliation": "SAPRIN", "role": "Documentation of Study and Review of the metadata"},
      {"name": "Augustine Khumalo", "abbr": "AK", "affiliation": "SAPRIN", "role": "Documentation of Study and Review of the metadata"}
    ],
    "prod_date": "2025-07-01",
    "version_statement": {"version": "Version 2 (July 2025)", "version_notes": "V2: Edited metadata for public distribution"}
  },
  "study_desc": {
    "title_statement": {"idno": "SAPRIN.SMHD2024V1", "title": "SAPRIN Mental Health Datasets 2024"},
    "study_info": {
      "keywords": [{"keyword": "Mental Health, Covid-19"}],
      "topics": [{"topic": "Mental Health, Covid-19"}],
      "abstract": "SAPRIN Mental Health 2024 datasets containing mental health screening data collected across seven SAPRIN nodes in South Africa.",
      "time_periods": [{"start": "1993-01-01", "end": "2023-12-31", "cycle": "Agincourt"}],
      "coll_dates": [{"start": "1993-01-01", "end": "2023-12-31", "cycle": "Agincourt"}],
      "nation": [{"name": "South Africa", "abbreviation": "RSA"}],
      "geog_coverage": "SAPRIN network of seven HDSS nodes across South Africa",
      "analysis_unit": "Individual and household interviews",
      "data_kind": "Event history data"
    }
  },
  "schematype": "survey"
}"""

        # Load both SAPRIN datasets
        results["saprin_2022"] = self.load_from_json_string(
            saprin_2022_json,
            source_name="SAPRIN Mental Health Data Prize 2022",
            source_url="https://saprindata.samrc.ac.za/index.php/metadata/export/80/json"
        )
        results["details"]["saprin_2022"] = "Loaded SAPRIN 2022 Mental Health Data Prize"

        results["saprin_2024"] = self.load_from_json_string(
            saprin_2024_json,
            source_name="SAPRIN Mental Health Datasets 2024",
            source_url="https://saprindata.samrc.ac.za/index.php/metadata/export/87/json"
        )
        results["details"]["saprin_2024"] = "Loaded SAPRIN 2024 Mental Health Datasets"

        # Load metadata from metadata_sources directory
        metadata_dir = Path(__file__).parent.parent.parent / "metadata_sources"
        if metadata_dir.exists():
            dir_results = self.load_from_directory(
                str(metadata_dir),
                pattern="*.json"
            )
            results["other_sources"] = dir_results
            for file_path, success in dir_results.items():
                if success:
                    results["details"][file_path] = f"Successfully loaded {file_path}"

        return results

    def get_loaded_sources(self) -> List[str]:
        """Get list of all loaded data sources"""
        return self.loaded_sources

    def get_harmonizer(self) -> MetadataHarmonizer:
        """Get the metadata harmonizer instance"""
        return self.harmonizer
