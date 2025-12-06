"""
PAMHoYA - Summarisation Service

Generates plain-language summaries of research studies.
Combines NLP/LLM with human review workflows.

Copyright (c) 2025 PAMHoYA Team
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence
Lead Developer: Augustine Khumalo
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid


# ============================================================================
# MODELS
# ============================================================================

class SummaryStatus(str, Enum):
    """Summary approval workflow status"""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class StudySummary:
    """Research study summary model"""
    def __init__(self, study_id: str, study_title: str, study_abstract: str):
        self.id = str(uuid.uuid4())
        self.study_id = study_id
        self.study_title = study_title
        self.study_abstract = study_abstract
        self.status = SummaryStatus.DRAFT.value
        self.versions: List[Dict] = []
        self.current_version = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.review_comments = []
        self.approved_by: Optional[str] = None
        self.published_at: Optional[datetime] = None


class SummaryVersion:
    """Version of a summary (tracks edits)"""
    def __init__(self, summary_id: str, plain_language_text: str, 
                 created_by: str, version_number: int = 1):
        self.id = str(uuid.uuid4())
        self.summary_id = summary_id
        self.plain_language_text = plain_language_text
        self.created_by = created_by
        self.version_number = version_number
        self.created_at = datetime.now()
        self.metadata = {}


# ============================================================================
# DATA ACCESS LAYER
# ============================================================================

class SummarisationRepository:
    """Repository for summarisation operations"""
    
    def __init__(self):
        self.summaries = {}
        self.versions = {}
        self.deduplication_cache = {}  # study_id -> summary_id mapping
    
    def create_summary(self, summary: StudySummary) -> StudySummary:
        """Create new study summary"""
        self.summaries[summary.id] = summary
        self.deduplication_cache[summary.study_id] = summary.id
        return summary
    
    def get_summary(self, summary_id: str) -> Optional[StudySummary]:
        """Get summary by ID"""
        return self.summaries.get(summary_id)
    
    def find_existing_summary(self, study_id: str) -> Optional[StudySummary]:
        """Check if summary already exists for study (deduplication)"""
        summary_id = self.deduplication_cache.get(study_id)
        if summary_id:
            return self.summaries.get(summary_id)
        return None
    
    def list_summaries(self, status: Optional[str] = None) -> List[StudySummary]:
        """List summaries, optionally filtered by status"""
        summaries = list(self.summaries.values())
        if status:
            summaries = [s for s in summaries if s.status == status]
        return summaries
    
    def create_version(self, version: SummaryVersion) -> SummaryVersion:
        """Create new version of summary"""
        if version.summary_id not in self.versions:
            self.versions[version.summary_id] = []
        
        self.versions[version.summary_id].append(version)
        
        # Update summary's current version
        if version.summary_id in self.summaries:
            self.summaries[version.summary_id].current_version = version.id
            self.summaries[version.summary_id].versions.append({
                "version_number": version.version_number,
                "created_by": version.created_by,
                "created_at": version.created_at.isoformat()
            })
        
        return version
    
    def get_version(self, version_id: str) -> Optional[SummaryVersion]:
        """Get specific version"""
        for versions in self.versions.values():
            for v in versions:
                if v.id == version_id:
                    return v
        return None
    
    def get_version_history(self, summary_id: str) -> List[SummaryVersion]:
        """Get all versions for a summary"""
        return self.versions.get(summary_id, [])
    
    def update_summary_status(self, summary_id: str, status: str) -> Optional[StudySummary]:
        """Update summary status"""
        if summary_id in self.summaries:
            self.summaries[summary_id].status = status
            self.summaries[summary_id].updated_at = datetime.now()
            return self.summaries[summary_id]
        return None
    
    def add_review_comment(self, summary_id: str, reviewer_id: str, comment: str) -> Dict:
        """Add review comment"""
        if summary_id in self.summaries:
            review = {
                "id": str(uuid.uuid4()),
                "reviewer_id": reviewer_id,
                "comment": comment,
                "created_at": datetime.now().isoformat()
            }
            self.summaries[summary_id].review_comments.append(review)
            return review
        return None


# ============================================================================
# BUSINESS LOGIC LAYER
# ============================================================================

class SummarisationService:
    """Summarisation Service - Core business logic"""
    
    def __init__(self, repository: SummarisationRepository):
        self.repository = repository
        self.nlp_model = None  # Placeholder for actual LLM/NLP model
    
    def initiate_summarisation(self, study_id: str, study_title: str, 
                              study_abstract: str) -> Optional[StudySummary]:
        """Initiate summarisation workflow"""
        # Check for existing summary (deduplication)
        existing = self.repository.find_existing_summary(study_id)
        if existing:
            return existing
        
        # Create new summary
        summary = StudySummary(study_id, study_title, study_abstract)
        return self.repository.create_summary(summary)
    
    def generate_draft_summary(self, summary_id: str, created_by: str = "system") -> SummaryVersion:
        """Generate automated plain-language summary draft"""
        summary = self.repository.get_summary(summary_id)
        if not summary:
            return None
        
        # Generate plain-language text (simplified for PoC)
        plain_text = self._generate_plain_language_text(
            summary.study_title,
            summary.study_abstract
        )
        
        # Create version
        version = SummaryVersion(
            summary_id=summary_id,
            plain_language_text=plain_text,
            created_by=created_by,
            version_number=1
        )
        
        saved_version = self.repository.create_version(version)
        
        # Update summary status
        self.repository.update_summary_status(summary_id, SummaryStatus.IN_REVIEW.value)
        
        return saved_version
    
    def _generate_plain_language_text(self, title: str, abstract: str) -> str:
        """Generate plain-language summary from academic text"""
        # Simplified implementation - would use actual NLP/LLM in production
        
        lines = abstract.split('.')
        key_points = []
        
        for line in lines[:3]:  # Take first 3 sentences
            if len(line.strip()) > 20:
                key_points.append(line.strip())
        
        plain_text = f"""
Study Title: {title}

What was the study about?
{key_points[0] if key_points else "This study examined a specific health topic."}

Key Findings:
{key_points[1] if len(key_points) > 1 else "The researchers found important insights."}

Why does it matter?
{key_points[2] if len(key_points) > 2 else "These findings may help inform health practices and policies."}
        """.strip()
        
        return plain_text
    
    def request_review(self, summary_id: str) -> Optional[StudySummary]:
        """Move summary to review queue"""
        summary = self.repository.get_summary(summary_id)
        if not summary:
            return None
        
        return self.repository.update_summary_status(summary_id, SummaryStatus.IN_REVIEW.value)
    
    def add_reviewer_comment(self, summary_id: str, reviewer_id: str, comment: str) -> Dict:
        """Add reviewer comment during review process"""
        return self.repository.add_review_comment(summary_id, reviewer_id, comment)
    
    def edit_summary(self, summary_id: str, new_text: str, editor_id: str) -> SummaryVersion:
        """Edit summary and create new version"""
        summary = self.repository.get_summary(summary_id)
        if not summary:
            return None
        
        # Get current version number
        version_history = self.repository.get_version_history(summary_id)
        next_version = len(version_history) + 1
        
        # Create new version
        version = SummaryVersion(
            summary_id=summary_id,
            plain_language_text=new_text,
            created_by=editor_id,
            version_number=next_version
        )
        
        return self.repository.create_version(version)
    
    def approve_summary(self, summary_id: str, reviewer_id: str) -> Optional[StudySummary]:
        """Approve summary for publication"""
        summary = self.repository.get_summary(summary_id)
        if not summary:
            return None
        
        summary.approved_by = reviewer_id
        return self.repository.update_summary_status(summary_id, SummaryStatus.APPROVED.value)
    
    def reject_summary(self, summary_id: str, rejection_reason: str) -> Optional[StudySummary]:
        """Reject summary with feedback"""
        summary = self.repository.get_summary(summary_id)
        if not summary:
            return None
        
        summary.review_comments.append({
            "type": "rejection",
            "reason": rejection_reason,
            "created_at": datetime.now().isoformat()
        })
        
        return self.repository.update_summary_status(summary_id, SummaryStatus.REJECTED.value)
    
    def publish_summary(self, summary_id: str) -> Optional[StudySummary]:
        """Publish approved summary"""
        summary = self.repository.get_summary(summary_id)
        if not summary:
            return None
        
        summary.published_at = datetime.now()
        return self.repository.update_summary_status(summary_id, SummaryStatus.PUBLISHED.value)
    
    def get_summary_details(self, summary_id: str) -> Optional[Dict]:
        """Get complete summary details"""
        summary = self.repository.get_summary(summary_id)
        if not summary:
            return None
        
        current_version = self.repository.get_version(summary.current_version) if summary.current_version else None
        
        return {
            "id": summary.id,
            "study_id": summary.study_id,
            "study_title": summary.study_title,
            "status": summary.status,
            "current_text": current_version.plain_language_text if current_version else None,
            "version_count": len(summary.versions),
            "approved_by": summary.approved_by,
            "published_at": summary.published_at.isoformat() if summary.published_at else None,
            "review_comments_count": len(summary.review_comments),
            "created_at": summary.created_at.isoformat(),
            "updated_at": summary.updated_at.isoformat()
        }


# ============================================================================
# INITIALIZATION
# ============================================================================

def create_summarisation_service() -> SummarisationService:
    """Factory function to create Summarisation Service"""
    repository = SummarisationRepository()
    return SummarisationService(repository)
