"""
MIT License

Copyright (c) 2025 PAMHoYA Team (https://pamhoya.ac.uk)
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence
Lead Developer: Augustine Khumalo

This software extends and builds upon the Harmony framework 
(Copyright (c) 2023 Ulster University - https://harmonydata.ac.uk)
for item harmonisation functionality.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ProducerSchema(BaseModel):
    """Schema for metadata producers/contributors"""
    name: str
    abbr: Optional[str] = None
    affiliation: Optional[str] = None
    role: Optional[str] = None


class ContactSchema(BaseModel):
    """Schema for contact information"""
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None
    uri: Optional[str] = None
    role: Optional[str] = None


class TimeperiodSchema(BaseModel):
    """Schema for time periods in data collection"""
    start: str
    end: str
    cycle: Optional[str] = None


class VersionStatementSchema(BaseModel):
    """Schema for version information"""
    version: str
    version_date: Optional[str] = None
    version_notes: Optional[str] = None


class FundingAgencySchema(BaseModel):
    """Schema for funding agencies"""
    name: str
    abbr: Optional[str] = None
    role: Optional[str] = None


class KeywordSchema(BaseModel):
    """Schema for keywords/topics"""
    keyword: Optional[str] = None
    topic: Optional[str] = None
    vocab: Optional[str] = None
    uri: Optional[str] = None
    
    def __init__(self, **data):
        """Allow both 'keyword' and 'topic' fields, preferring 'keyword' if both present"""
        if 'topic' in data and 'keyword' not in data:
            data['keyword'] = data.pop('topic')
        super().__init__(**data)


class DocumentDescriptionSchema(BaseModel):
    """Schema for document description metadata"""
    title: str
    idno: str
    producers: List[ProducerSchema] = []
    prod_date: Optional[str] = None
    version_statement: Optional[VersionStatementSchema] = None


class TitleStatementSchema(BaseModel):
    """Schema for title statement"""
    idno: str
    title: str


class ProductionStatementSchema(BaseModel):
    """Schema for production statement"""
    producers: List[ProducerSchema] = []
    copyright: Optional[str] = None
    funding_agencies: List[FundingAgencySchema] = []


class DistributionStatementSchema(BaseModel):
    """Schema for distribution statement"""
    contact: List[ContactSchema] = []


class SeriesStatementSchema(BaseModel):
    """Schema for series statement"""
    series_name: Optional[str] = None
    series_info: Optional[str] = None


class DataCollectionMethodSchema(BaseModel):
    """Schema for data collection methodology"""
    time_method: Optional[str] = None
    sampling_procedure: Optional[str] = None
    coll_mode: List[str] = []
    research_instrument: Optional[str] = None
    coll_situation: Optional[str] = None
    cleaning_operations: Optional[str] = None


class MethodSchema(BaseModel):
    """Schema for methodology information"""
    data_collection: Optional[DataCollectionMethodSchema] = None
    analysis_info: Optional[Dict[str, Any]] = None


class StudyInfoSchema(BaseModel):
    """Schema for study information"""
    keywords: List[KeywordSchema] = []
    topics: List[KeywordSchema] = []
    abstract: Optional[str] = None
    time_periods: List[TimeperiodSchema] = []
    coll_dates: List[TimeperiodSchema] = []
    nation: List[Dict[str, str]] = []
    geog_coverage: Optional[str] = None
    analysis_unit: Optional[str] = None
    universe: Optional[str] = None
    data_kind: Optional[str] = None
    notes: Optional[str] = None


class DataAccessSchema(BaseModel):
    """Schema for data access information"""
    contact: List[ContactSchema] = []
    cit_req: Optional[str] = None
    conditions: Optional[str] = None
    disclaimer: Optional[str] = None


class DatasetAccessSchema(BaseModel):
    """Schema for dataset availability and use"""
    access_place: Optional[str] = None
    access_place_url: Optional[str] = None
    dataset_use: Optional[DataAccessSchema] = None


class StudyDescriptionSchema(BaseModel):
    """Schema for complete study description"""
    title_statement: TitleStatementSchema
    authoring_entity: List[ProducerSchema] = []
    oth_id: List[ContactSchema] = []
    production_statement: Optional[ProductionStatementSchema] = None
    distribution_statement: Optional[DistributionStatementSchema] = None
    series_statement: Optional[SeriesStatementSchema] = None
    version_statement: Optional[VersionStatementSchema] = None
    study_notes: Optional[str] = None
    study_info: Optional[StudyInfoSchema] = None
    method: Optional[MethodSchema] = None
    data_access: Optional[DatasetAccessSchema] = None


class MetadataSchema(BaseModel):
    """Complete metadata schema following DDI structure"""
    doc_desc: Optional[DocumentDescriptionSchema] = None
    study_desc: Optional[StudyDescriptionSchema] = None
    schematype: Optional[str] = None


class HarmonizedMetadataSchema(BaseModel):
    """Schema for harmonized metadata with standardized fields"""
    source_id: str = Field(..., description="Unique identifier for the source")
    source_name: str = Field(..., description="Name of the data source")
    title: str = Field(..., description="Title of the study/dataset")
    abstract: Optional[str] = Field(None, description="Study abstract")
    keywords: List[str] = Field(default_factory=list, description="Keywords for the dataset")
    start_date: Optional[str] = Field(None, description="Data collection start date")
    end_date: Optional[str] = Field(None, description="Data collection end date")
    countries: List[str] = Field(default_factory=list, description="Countries covered")
    geographic_coverage: Optional[str] = Field(None, description="Geographic coverage description")
    data_kind: Optional[str] = Field(None, description="Type of data collected")
    analysis_unit: Optional[str] = Field(None, description="Unit of analysis")
    universe: Optional[str] = Field(None, description="Population universe")
    producers: List[ProducerSchema] = Field(default_factory=list, description="Data producers")
    contributors: List[ContactSchema] = Field(default_factory=list, description="Contributors")
    funding_agencies: List[str] = Field(default_factory=list, description="Funding organizations")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    version: Optional[str] = Field(None, description="Dataset version")
    license: Optional[str] = Field(None, description="Data license")
    access_conditions: Optional[str] = Field(None, description="Data access conditions")
    citation_requirement: Optional[str] = Field(None, description="Citation requirement")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_uri: Optional[str] = Field(None, description="Contact website/URI")
    harmonization_status: str = Field(default="raw", description="Status of harmonization")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When record was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When record was last updated")
    raw_metadata: Optional[Dict[str, Any]] = Field(None, description="Original raw metadata")


class MetadataSearchResponseSchema(BaseModel):
    """Schema for metadata search response"""
    total: int = Field(..., description="Total number of results")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Results per page")
    results: List[HarmonizedMetadataSchema] = Field(..., description="Search results")


class MetadataUploadSchema(BaseModel):
    """Schema for uploading metadata"""
    source_name: str = Field(..., description="Name of the data source")
    metadata_json: Dict[str, Any] = Field(..., description="Raw metadata in JSON format")
    source_url: Optional[str] = Field(None, description="URL source of metadata")
