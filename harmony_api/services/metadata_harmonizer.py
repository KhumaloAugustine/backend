"""
MIT License

Copyright (c) 2025 PAMHoYA Team (https://pamhoya.ac.uk)
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence

Metadata Harmonization Service for normalizing and standardizing metadata
from various data sources including SAPRIN, NIDS, and other research studies.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import hashlib
import re

from harmony_api.schemas.metadata_schemas import (
    MetadataSchema,
    HarmonizedMetadataSchema,
    ProducerSchema,
    ContactSchema,
)

logger = logging.getLogger(__name__)


class FieldExtractor:
    """Extracts and normalizes specific metadata fields following Single Responsibility Principle."""

    @staticmethod
    def extract_from_dict(data: Dict[str, Any], path: str, default: Any = None) -> Any:
        """
        Extract value from nested dictionary using dot notation path.
        
        Args:
            data: Dictionary to extract from
            path: Dot-separated path (e.g., "study_info.keywords")
            default: Default value if path not found
            
        Returns:
            Extracted value or default
        """
        keys = path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return default
        return current if current is not None else default

    @staticmethod
    def extract_list_items(items: List[Any], key: str, default: str = "") -> List[str]:
        """
        Extract specific key from list of dictionaries, handling both dict and string items.
        
        Args:
            items: List to extract from
            key: Key to extract from each dict
            default: Default value for items
            
        Returns:
            List of extracted values
        """
        results = []
        for item in (items or []):
            if isinstance(item, dict):
                value = item.get(key, default)
            elif isinstance(item, str):
                value = item
            else:
                continue
            if value:
                results.append(value)
        return results

    @staticmethod
    def extract_doi(text: str) -> Optional[str]:
        """Extract DOI from text using regex."""
        match = re.search(r"https://doi\.org/[^\s]+", text or "")
        return match.group(0) if match else None

    @staticmethod
    def normalize_text(text: Optional[str]) -> Optional[str]:
        """Normalize text by stripping whitespace."""
        return text.strip() if text else None


class MetadataHarmonizer:
    """
    Service for harmonizing metadata from various sources into a standardized format.
    
    This service:
    - Ingests raw metadata from DDI JSON format
    - Extracts and normalizes key metadata fields
    - Applies harmonization rules for consistency
    - Stores harmonized metadata for API access
    """

    def __init__(self):
        """Initialize the metadata harmonizer"""
        self.harmonized_metadata: Dict[str, HarmonizedMetadataSchema] = {}
        self.metadata_index: Dict[str, List[str]] = {}  # For searching

    def harmonize_ddi_metadata(
        self,
        raw_metadata: Dict[str, Any],
        source_name: str,
        source_url: Optional[str] = None,
    ) -> HarmonizedMetadataSchema:
        """
        Harmonize DDI-formatted metadata into standardized schema.

        Args:
            raw_metadata: Raw metadata dictionary in DDI format
            source_name: Name of the data source
            source_url: Optional URL source of the metadata

        Returns:
            HarmonizedMetadataSchema: Standardized metadata object
        """
        try:
            # Parse the metadata
            metadata = MetadataSchema(**raw_metadata)

            # Extract document description
            doc_desc = metadata.doc_desc or {}
            study_desc = metadata.study_desc or {}

            # Generate source ID
            source_id = self._generate_source_id(source_name, study_desc)

            # Extract study information
            title = self._extract_title(study_desc)
            abstract = self._extract_abstract(study_desc)
            keywords = self._extract_keywords(study_desc)
            dates = self._extract_dates(study_desc)
            countries = self._extract_countries(study_desc)
            geographic_coverage = self._extract_geographic_coverage(study_desc)

            # Extract contributors
            producers = self._extract_producers(
                study_desc, doc_desc
            )
            contributors = self._extract_contributors(study_desc)
            funding_agencies = self._extract_funding_agencies(study_desc)

            # Extract access information
            data_access = study_desc.get("data_access", {})
            access_conditions = self._extract_access_conditions(data_access)
            citation_requirement = self._extract_citation_requirement(data_access)
            contact = self._extract_contact(data_access)

            # Create harmonized metadata
            harmonized = HarmonizedMetadataSchema(
                source_id=source_id,
                source_name=source_name,
                title=title,
                abstract=abstract,
                keywords=keywords,
                start_date=dates.get("start"),
                end_date=dates.get("end"),
                countries=countries,
                geographic_coverage=geographic_coverage,
                data_kind=study_desc.get("study_info", {}).get("data_kind"),
                analysis_unit=study_desc.get("study_info", {}).get("analysis_unit"),
                universe=study_desc.get("study_info", {}).get("universe"),
                producers=producers,
                contributors=contributors,
                funding_agencies=funding_agencies,
                doi=self._extract_doi(study_desc),
                version=self._extract_version(doc_desc, study_desc),
                license=self._extract_license(study_desc),
                access_conditions=access_conditions,
                citation_requirement=citation_requirement,
                contact_email=contact.get("email"),
                contact_uri=contact.get("uri"),
                harmonization_status="harmonized",
                raw_metadata=raw_metadata,
            )

            # Store in index
            self.harmonized_metadata[source_id] = harmonized
            self._update_index(source_id, harmonized)

            logger.info(f"Successfully harmonized metadata for {source_name}")
            return harmonized

        except Exception as e:
            logger.error(f"Error harmonizing metadata for {source_name}: {str(e)}")
            raise

    def _generate_source_id(
        self, source_name: str, study_desc: Dict[str, Any]
    ) -> str:
        """Generate a unique source ID"""
        idno = FieldExtractor.extract_from_dict(
            study_desc, "title_statement.idno", ""
        )

        if idno:
            return idno.replace(" ", "_").lower()

        content = f"{source_name}{FieldExtractor.extract_from_dict(study_desc, 'title_statement.title', '')}"
        hash_suffix = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{source_name.replace(' ', '_').lower()}_{hash_suffix}"

    def _extract_title(self, study_desc: Dict[str, Any]) -> str:
        """Extract study title"""
        return FieldExtractor.extract_from_dict(
            study_desc, "title_statement.title", "Unknown Study"
        )

    def _extract_abstract(self, study_desc: Dict[str, Any]) -> Optional[str]:
        """Extract study abstract"""
        return FieldExtractor.normalize_text(
            FieldExtractor.extract_from_dict(study_desc, "study_info.abstract")
        )

    def _extract_keywords(self, study_desc: Dict[str, Any]) -> List[str]:
        """Extract keywords from study"""
        study_info = FieldExtractor.extract_from_dict(study_desc, "study_info", {})
        
        keywords = []
        keywords.extend(FieldExtractor.extract_list_items(
            study_info.get("keywords", []), "keyword"
        ))
        keywords.extend(FieldExtractor.extract_list_items(
            study_info.get("topics", []), "topic"
        ))
        
        return [kw for kw in keywords if kw]

    def _extract_dates(self, study_desc: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """Extract study start and end dates"""
        study_info = FieldExtractor.extract_from_dict(study_desc, "study_info", {})
        time_periods = study_info.get("time_periods", []) or study_info.get("coll_dates", [])

        if not time_periods:
            return {"start": None, "end": None}

        return {
            "start": time_periods[0].get("start") if isinstance(time_periods[0], dict) else None,
            "end": time_periods[-1].get("end") if isinstance(time_periods[-1], dict) else None,
        }

    def _extract_countries(self, study_desc: Dict[str, Any]) -> List[str]:
        """Extract countries covered by the study"""
        return FieldExtractor.extract_list_items(
            FieldExtractor.extract_from_dict(study_desc, "study_info.nation", []),
            "name"
        )

    def _extract_geographic_coverage(
        self, study_desc: Dict[str, Any]
    ) -> Optional[str]:
        """Extract geographic coverage description"""
        return FieldExtractor.normalize_text(
            FieldExtractor.extract_from_dict(study_desc, "study_info.geog_coverage")
        )

    def _extract_producers(
        self,
        study_desc: Dict[str, Any],
        doc_desc: Dict[str, Any],
    ) -> List[ProducerSchema]:
        """Extract data producers"""
        # Try from production statement first, fallback to document description
        producers_data = FieldExtractor.extract_from_dict(
            study_desc, "production_statement.producers", []
        ) or FieldExtractor.extract_from_dict(doc_desc, "producers", [])
        
        return [ProducerSchema(**p) for p in producers_data if isinstance(p, dict)]

    def _extract_contributors(
        self, study_desc: Dict[str, Any]
    ) -> List[ContactSchema]:
        """Extract contributors"""
        contributors = []
        
        # From authoring entity
        for entity in FieldExtractor.extract_from_dict(study_desc, "authoring_entity", []):
            if isinstance(entity, dict):
                contributors.append(ContactSchema(
                    name=entity.get("name", ""),
                    affiliation=entity.get("affiliation"),
                ))
        
        # From other identifiable persons
        for person in FieldExtractor.extract_from_dict(study_desc, "oth_id", []):
            if isinstance(person, dict):
                contributors.append(ContactSchema(**person))
        
        return contributors

    def _extract_funding_agencies(self, study_desc: Dict[str, Any]) -> List[str]:
        """Extract funding agencies"""
        return FieldExtractor.extract_list_items(
            FieldExtractor.extract_from_dict(
                study_desc, "production_statement.funding_agencies", []
            ),
            "name"
        )

    def _extract_doi(self, study_desc: Dict[str, Any]) -> Optional[str]:
        """Extract DOI from study description"""
        cit_req = FieldExtractor.extract_from_dict(
            study_desc, "data_access.dataset_use.cit_req", ""
        )
        return FieldExtractor.extract_doi(cit_req) if cit_req else None

    def _extract_version(
        self, doc_desc: Dict[str, Any], study_desc: Dict[str, Any]
    ) -> Optional[str]:
        """Extract version information"""
        return FieldExtractor.extract_from_dict(
            doc_desc, "version_statement.version"
        ) or FieldExtractor.extract_from_dict(
            study_desc, "version_statement.version"
        )

    def _extract_license(self, study_desc: Dict[str, Any]) -> Optional[str]:
        """Extract license information"""
        return FieldExtractor.normalize_text(
            FieldExtractor.extract_from_dict(
                study_desc, "production_statement.copyright"
            )
        )

    def _extract_access_conditions(self, data_access: Dict[str, Any]) -> Optional[str]:
        """Extract data access conditions"""
        return FieldExtractor.normalize_text(
            FieldExtractor.extract_from_dict(
                data_access, "dataset_use.conditions"
            )
        )

    def _extract_citation_requirement(self, data_access: Dict[str, Any]) -> Optional[str]:
        """Extract citation requirement"""
        return FieldExtractor.normalize_text(
            FieldExtractor.extract_from_dict(
                data_access, "dataset_use.cit_req"
            )
        )

    def _extract_contact(self, data_access: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """Extract contact information"""
        contacts = FieldExtractor.extract_from_dict(data_access, "contact", [])
        
        if contacts and isinstance(contacts[0], dict):
            return {
                "email": contacts[0].get("email"),
                "uri": contacts[0].get("uri"),
            }
        
        return {"email": None, "uri": None}

    def _update_index(self, source_id: str, harmonized: HarmonizedMetadataSchema):
        """Update search index with harmonized metadata"""
        # Index by various fields for search
        index_terms = []

        # Add source name and ID
        index_terms.extend(harmonized.source_name.lower().split())
        index_terms.append(source_id.lower())

        # Add title terms
        index_terms.extend(harmonized.title.lower().split())

        # Add keywords
        for kw in harmonized.keywords:
            index_terms.extend(kw.lower().split())

        # Add countries
        index_terms.extend(harmonized.countries)

        # Store in index
        for term in index_terms:
            if term not in self.metadata_index:
                self.metadata_index[term] = []
            if source_id not in self.metadata_index[term]:
                self.metadata_index[term].append(source_id)

    def search_metadata(self, query: str) -> List[HarmonizedMetadataSchema]:
        """
        Search harmonized metadata by query string.

        Args:
            query: Search query string

        Returns:
            List of matching harmonized metadata objects
        """
        query_lower = query.lower()
        matching_ids = set()

        # Search in index
        for term in query_lower.split():
            if term in self.metadata_index:
                matching_ids.update(self.metadata_index[term])

        # Also search in full text fields
        for source_id, metadata in self.harmonized_metadata.items():
            if (
                query_lower in metadata.source_name.lower()
                or query_lower in metadata.title.lower()
                or (metadata.abstract and query_lower in metadata.abstract.lower())
            ):
                matching_ids.add(source_id)

        return [
            self.harmonized_metadata[source_id]
            for source_id in matching_ids
            if source_id in self.harmonized_metadata
        ]

    def get_metadata_by_id(self, source_id: str) -> Optional[HarmonizedMetadataSchema]:
        """Get harmonized metadata by source ID"""
        return self.harmonized_metadata.get(source_id)

    def get_all_metadata(self) -> List[HarmonizedMetadataSchema]:
        """Get all harmonized metadata"""
        return list(self.harmonized_metadata.values())

    def save_metadata_to_file(self, filepath: str):
        """Save all harmonized metadata to a JSON file"""
        metadata_list = [
            json.loads(metadata.model_dump_json())
            for metadata in self.harmonized_metadata.values()
        ]
        with open(filepath, "w") as f:
            json.dump(metadata_list, f, indent=2, default=str)
        logger.info(f"Saved {len(metadata_list)} metadata records to {filepath}")

    def load_metadata_from_file(self, filepath: str):
        """Load harmonized metadata from a JSON file"""
        with open(filepath, "r") as f:
            metadata_list = json.load(f)

        for metadata_dict in metadata_list:
            # Convert datetime strings back to datetime objects
            for date_field in ["created_at", "updated_at"]:
                if date_field in metadata_dict and isinstance(metadata_dict[date_field], str):
                    metadata_dict[date_field] = datetime.fromisoformat(
                        metadata_dict[date_field]
                    )

            metadata = HarmonizedMetadataSchema(**metadata_dict)
            source_id = metadata.source_id
            self.harmonized_metadata[source_id] = metadata
            self._update_index(source_id, metadata)

        logger.info(f"Loaded {len(metadata_list)} metadata records from {filepath}")


# Global instance for use across the application
_harmonizer_instance: Optional[MetadataHarmonizer] = None


def get_harmonizer() -> MetadataHarmonizer:
    """Get or create the global metadata harmonizer instance"""
    global _harmonizer_instance
    if _harmonizer_instance is None:
        _harmonizer_instance = MetadataHarmonizer()
    return _harmonizer_instance
