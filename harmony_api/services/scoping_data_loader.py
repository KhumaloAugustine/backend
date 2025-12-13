"""
Mental Health Studies and Datasets Scoping Data Loader

Loads all mental health studies, datasets, and research from the scoping documents
and integrates them into the PAMHoYA platform for discovery and harmonization.
"""

import openpyxl
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

class MentalHealthStudy:
    """Represents a mental health study from the scoping review"""
    def __init__(
        self,
        authors: str,
        year: str,
        title: str,
        citation: str,
        data_source: str,
        data_collection_period: str,
        data_collection_method: str,
        geographic_location: str,
        population: str = "",
        mental_health_measures: List[str] = None,
        url: str = ""
    ):
        self.authors = authors
        self.year = year
        self.title = title
        self.citation = citation
        self.data_source = data_source
        self.data_collection_period = data_collection_period
        self.data_collection_method = data_collection_method
        self.geographic_location = geographic_location
        self.population = population
        self.mental_health_measures = mental_health_measures or []
        self.url = url
    
    def to_metadata_json(self) -> Dict[str, Any]:
        """Convert to metadata JSON format"""
        producers = [
            {
                "name": author.strip(),
                "affiliation": "South Africa",
                "role": "Researcher"
            }
            for author in (self.authors or "").split(",")[:3]
        ]
        keywords = [
            {"keyword": "mental health"},
            {"keyword": "South Africa"},
            {"keyword": self.data_source}
        ]
        keywords.extend([{"keyword": m} for m in self.mental_health_measures])
        
        return {
            "doc_desc": {
                "title": self.title,
                "idno": f"DDI.MH.{self.year}.{self.authors[:10].replace(' ', '').upper()}",
                "producers": producers,
                "prod_date": f"{self.year}-01-01",
                "version_statement": {
                    "version": "1.0",
                    "version_notes": f"Data from {self.data_collection_period}"
                }
            },
            "study_desc": {
                "title_statement": {
                    "idno": f"MH.{self.year}.{self.authors[:5].upper()}",
                    "title": self.title
                },
                "study_info": {
                    "keywords": keywords,
                    "topics": [
                        {"topic": "mental health"},
                        {"topic": "psychology"},
                        {"topic": "public health"}
                    ],
                    "abstract": self.title,
                    "time_periods": [
                        {
                            "start": "2000-01-01" if not self.data_collection_period else self.data_collection_period,
                            "end": "2024-12-31"
                        }
                    ],
                    "coll_dates": [
                        {
                            "start": self.data_collection_period if self.data_collection_period else "Unknown",
                            "end": self.data_collection_period if self.data_collection_period else "Unknown"
                        }
                    ],
                    "nation": [{"name": "South Africa", "abbreviation": "RSA"}],
                    "geog_coverage": self.geographic_location,
                    "analysis_unit": self.population or "Individuals/Communities",
                    "data_kind": f"{self.data_source} - {self.data_collection_method}"
                }
            },
            "schematype": "survey"
        }
    
    def to_discovery_dict(self) -> Dict[str, Any]:
        """Convert to data discovery format"""
        return {
            "dataset_id": f"MH_{self.year}_{self.authors[:5]}",
            "name": self.title,
            "description": f"{self.title}. Authors: {self.authors}. Year: {self.year}",
            "source_type": self.data_source,
            "data_collection_method": self.data_collection_method,
            "year": self.year,
            "geographic_location": self.geographic_location,
            "population": self.population,
            "mental_health_measures": self.mental_health_measures,
            "citation": self.citation,
            "access_type": "Restricted"  # Default - can be updated
        }


def load_scoping_data() -> List[MentalHealthStudy]:
    """Load all mental health studies from scoping Excel files"""
    studies = []
    
    scoping_file = Path(r'c:\Users\Augustine.Khumalo\Documents\PAMHoYA\backend\Scoping for mental health data\Scoping - Mental Health Datasets in SA.xlsx')
    
    if not scoping_file.exists():
        print(f"Scoping file not found: {scoping_file}")
        return studies
    
    wb = openpyxl.load_workbook(scoping_file)
    ws = wb.active
    
    # Skip header row
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if not row[0]:  # Skip empty rows
            continue
        
        authors = str(row[0]) if row[0] else ""
        year = str(row[1]) if row[1] else ""
        title = str(row[2]) if row[2] else ""
        citation = str(row[3]) if row[3] else ""
        data_source = str(row[4]) if row[4] else ""
        data_period = str(row[5]) if row[5] else ""
        method = str(row[6]) if row[6] else ""
        location = str(row[7]) if row[7] else ""
        
        study = MentalHealthStudy(
            authors=authors,
            year=year,
            title=title,
            citation=citation,
            data_source=data_source,
            data_collection_period=data_period,
            data_collection_method=method,
            geographic_location=location,
            mental_health_measures=["depression", "anxiety", "psychological distress"]
        )
        studies.append(study)
    
    return studies


if __name__ == "__main__":
    studies = load_scoping_data()
    print(f"Loaded {len(studies)} mental health studies")
    
    # Create metadata files
    metadata_dir = Path(r'c:\Users\Augustine.Khumalo\Documents\PAMHoYA\backend\metadata_sources')
    metadata_dir.mkdir(exist_ok=True)
    
    for i, study in enumerate(studies):  # Create metadata for all studies
        filename = f"mh_study_{i:03d}.json"
        filepath = metadata_dir / filename
        
        metadata = study.to_metadata_json()
        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"Created {filename}")
    
    print(f"Successfully created {len(studies)} metadata files")
