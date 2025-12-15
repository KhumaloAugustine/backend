"""
Mental Health Studies Loader Service

Loads mental health studies from metadata_sources/ directory and integrates them
into the discovery, summarisation, and analytics services.

Copyright (c) 2025 PAMHoYA Team
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class MentalHealthStudy:
    """Represents a mental health study loaded from metadata"""
    
    def __init__(self, study_id: str, metadata: Dict[str, Any]):
        self.study_id = study_id
        self.metadata = metadata
        self._extract_fields()
    
    def _extract_fields(self):
        """Extract key fields from metadata"""
        doc_desc = self.metadata.get("doc_desc", {})
        study_desc = self.metadata.get("study_desc", {})
        
        self.title = doc_desc.get("title", "") or study_desc.get("title_statement", {}).get("title", "")
        self.producers = doc_desc.get("producers", [])
        self.prod_date = doc_desc.get("prod_date", "")
        
        study_info = study_desc.get("study_info", {})
        self.keywords = [kw.get("keyword", "") for kw in study_info.get("keywords", [])]
        self.abstract = study_info.get("abstract", "")
        self.data_collection = study_info.get("data_collection", [])
        
        method = self.data_collection[0] if self.data_collection else {}
        self.data_collection_date = method.get("data_collection_date", "")
        self.collection_mode = method.get("collection_mode", [])
        
        # Extract questions if available (for instruments with survey items)
        self.questions = self.metadata.get("questions", [])
        self.instrument_details = self.metadata.get("instrument_details", {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "study_id": self.study_id,
            "title": self.title,
            "producers": self.producers,
            "date": self.prod_date,
            "keywords": self.keywords,
            "abstract": self.abstract,
            "data_collection_date": self.data_collection_date,
            "collection_modes": self.collection_mode
        }
    
    def get_searchable_text(self) -> str:
        """Get all text fields as single searchable string for full-text search"""
        text_parts = [
            self.title,
            self.abstract,
            " ".join(self.keywords),
            " ".join([p.get("name", "") for p in self.producers]),
            " ".join([p.get("affiliation", "") for p in self.producers])
        ]
        return " ".join(filter(None, text_parts))
    
    def get_constructs(self) -> List[str]:
        """Extract mental health constructs/keywords from study"""
        return self.keywords
    
    def get_questions(self) -> List[Dict[str, Any]]:
        """Get all questions/items from the instrument"""
        return self.questions
    
    def get_questions_as_text(self) -> List[str]:
        """Get all questions as text strings for matching"""
        return [q.get("question_text", "") for q in self.questions if q.get("question_text")]
    
    def get_full_summary(self) -> str:
        """Get comprehensive summary including title, abstract, and questions"""
        summary_parts = [
            f"Title: {self.title}",
            f"Abstract: {self.abstract}",
            f"Keywords: {', '.join(self.keywords)}"
        ]
        
        if self.questions:
            summary_parts.append(f"Questions ({len(self.questions)} items):")
            for q in self.questions:
                q_no = q.get("question_no", "")
                q_text = q.get("question_text", "")
                summary_parts.append(f"  {q_no}. {q_text}")
        
        return "\n".join(summary_parts)


class MentalHealthStudiesLoader:
    """Loads all mental health studies from metadata_sources directory"""
    
    def __init__(self, metadata_sources_path: str = "metadata_sources"):
        self.metadata_sources_path = Path(metadata_sources_path)
        self.studies: Dict[str, MentalHealthStudy] = {}
        self.loaded_count = 0
    
    def load_all_studies(self) -> Dict[str, MentalHealthStudy]:
        """Load all mental health studies from metadata_sources/*.json"""
        if not self.metadata_sources_path.exists():
            logger.warning(f"Metadata sources directory not found: {self.metadata_sources_path}")
            return self.studies
        
        # Load all mh_study_*.json files
        study_files = sorted(self.metadata_sources_path.glob("mh_study_*.json"))
        logger.info(f"Found {len(study_files)} mental health study files")
        
        for study_file in study_files:
            try:
                with open(study_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                study_id = study_file.stem  # e.g., "mh_study_000"
                study = MentalHealthStudy(study_id, metadata)
                self.studies[study_id] = study
                self.loaded_count += 1
                logger.info(f"Loaded study {study_id}: {study.title[:60]}...")
            
            except Exception as e:
                logger.error(f"Error loading {study_file}: {str(e)}")
        
        logger.info(f"Successfully loaded {self.loaded_count} mental health studies")
        return self.studies
    
    def get_study(self, study_id: str) -> Optional[MentalHealthStudy]:
        """Get a specific study by ID"""
        return self.studies.get(study_id)
    
    def get_all_studies(self) -> List[MentalHealthStudy]:
        """Get all loaded studies"""
        return list(self.studies.values())
    
    def search_studies(self, query: str) -> List[MentalHealthStudy]:
        """Search studies by full-text search"""
        query_lower = query.lower()
        results = []
        
        for study in self.studies.values():
            if query_lower in study.get_searchable_text().lower():
                results.append(study)
        
        return results
    
    def get_studies_by_construct(self, construct: str) -> List[MentalHealthStudy]:
        """Get studies that have a specific construct/keyword"""
        construct_lower = construct.lower()
        return [
            study for study in self.studies.values()
            if any(construct_lower in kw.lower() for kw in study.get_constructs())
        ]
    
    def get_all_constructs(self) -> set:
        """Get all unique constructs/keywords across all studies"""
        all_constructs = set()
        for study in self.studies.values():
            all_constructs.update(study.get_constructs())
        return all_constructs


# Global loader instance (singleton pattern)
_loader: Optional[MentalHealthStudiesLoader] = None


def get_mental_health_studies_loader(metadata_path: str = "metadata_sources") -> MentalHealthStudiesLoader:
    """Get or create the global mental health studies loader (singleton)"""
    global _loader
    
    if _loader is None:
        _loader = MentalHealthStudiesLoader(metadata_path)
        _loader.load_all_studies()
    
    return _loader
