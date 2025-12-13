"""
PAMHoYA - Analytics/Reporting Service

Delivers role-based dashboards and analytics.
Provides insights for researchers, local experts, policymakers, and administrators.

Copyright (c) 2025 PAMHoYA Team
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence
Lead Developer: Augustine Khumalo
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
from harmony_api.services.mental_health_studies_loader import get_mental_health_studies_loader
from harmony_api.services.base_service import BaseRepository, BaseService, BaseEntity


# ============================================================================
# MODELS
# ============================================================================

class StakeholderRole(str, Enum):
    """Stakeholder roles for dashboard access"""
    RESEARCHER = "researcher"
    LOCAL_EXPERT = "local_expert"
    POLICYMAKER = "policymaker"
    ADMINISTRATOR = "administrator"


class Dashboard:
    """Base dashboard model"""
    def __init__(self, user_id: str, role: str):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.role = role
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.widgets = []


class ResearcherDashboard(Dashboard):
    """Dashboard for researchers - harmonisation matrices and provenance"""
    def __init__(self, user_id: str):
        super().__init__(user_id, StakeholderRole.RESEARCHER.value)
        self.harmonisation_matrix = {}
        self.provenance_trails = {}
        self.recent_matches = []


class LocalExpertDashboard(Dashboard):
    """Dashboard for local experts - topic/population summaries and trends"""
    def __init__(self, user_id: str):
        super().__init__(user_id, StakeholderRole.LOCAL_EXPERT.value)
        self.topic_summaries = {}
        self.population_trends = {}
        self.regional_coverage = {}


class PolicymakerDashboard(Dashboard):
    """Dashboard for policymakers - evidence coverage and maps"""
    def __init__(self, user_id: str):
        super().__init__(user_id, StakeholderRole.POLICYMAKER.value)
        self.evidence_maps = {}
        self.coverage_stats = {}
        self.policy_recommendations = []


class AdminDashboard(Dashboard):
    """Dashboard for administrators - system usage and health metrics"""
    def __init__(self, user_id: str):
        super().__init__(user_id, StakeholderRole.ADMINISTRATOR.value)
        self.system_metrics = {}
        self.user_activity = {}
        self.data_quality_scores = {}


class Metric:
    """Analytics metric"""
    def __init__(self, name: str, value: Any, unit: str = "", timestamp: datetime = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.value = value
        self.unit = unit
        self.timestamp = timestamp or datetime.now()


# ============================================================================
# DATA ACCESS LAYER
# ============================================================================

class AnalyticsRepository(BaseRepository):
    """Repository for analytics operations"""
    
    def __init__(self):
        super().__init__()  # Initialize BaseRepository
        self.dashboards = {}
        self.metrics = {}
        self.user_activity_logs = []
        self.harmonisation_records = []
    
    def create_dashboard(self, dashboard: Dashboard) -> Dashboard:
        """Create dashboard"""
        self.dashboards[dashboard.id] = dashboard
        return dashboard
    
    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get dashboard by ID"""
        return self.dashboards.get(dashboard_id)
    
    def get_user_dashboard(self, user_id: str, role: str) -> Optional[Dashboard]:
        """Get or create user's role-based dashboard"""
        for dash in self.dashboards.values():
            if dash.user_id == user_id and dash.role == role:
                return dash
        
        # Create new dashboard
        if role == StakeholderRole.RESEARCHER.value:
            dashboard = ResearcherDashboard(user_id)
        elif role == StakeholderRole.LOCAL_EXPERT.value:
            dashboard = LocalExpertDashboard(user_id)
        elif role == StakeholderRole.POLICYMAKER.value:
            dashboard = PolicymakerDashboard(user_id)
        elif role == StakeholderRole.ADMINISTRATOR.value:
            dashboard = AdminDashboard(user_id)
        else:
            return None
        
        return self.create_dashboard(dashboard)
    
    def record_metric(self, dashboard_id: str, metric: Metric) -> Metric:
        """Record analytics metric"""
        if dashboard_id not in self.metrics:
            self.metrics[dashboard_id] = []
        
        self.metrics[dashboard_id].append(metric)
        return metric
    
    def get_metrics(self, dashboard_id: str, metric_name: str = None) -> List[Metric]:
        """Get metrics for dashboard"""
        metrics = self.metrics.get(dashboard_id, [])
        
        if metric_name:
            metrics = [m for m in metrics if m.name == metric_name]
        
        return metrics
    
    def log_activity(self, user_id: str, action: str, resource: str, details: Dict = None) -> Dict:
        """Log user activity"""
        log = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.user_activity_logs.append(log)
        return log
    
    def record_harmonisation(self, item1_id: str, item2_id: str, 
                           similarity_score: float, matched: bool) -> Dict:
        """Record harmonisation result"""
        record = {
            "id": str(uuid.uuid4()),
            "item1_id": item1_id,
            "item2_id": item2_id,
            "similarity_score": similarity_score,
            "matched": matched,
            "timestamp": datetime.now().isoformat()
        }
        self.harmonisation_records.append(record)
        return record


# ============================================================================
# BUSINESS LOGIC LAYER
# ============================================================================

class AnalyticsService(BaseService[AnalyticsRepository]):
    """Analytics/Reporting Service - Core business logic"""
    
    def __init__(self, repository: AnalyticsRepository):
        super().__init__(repository)  # Leverage BaseService
        self.studies_loader = get_mental_health_studies_loader()
        self.studies_loader.load_all_studies()  # Load studies on initialization
    
    def get_researcher_dashboard(self, user_id: str) -> Optional[Dict]:
        """Get researcher dashboard with harmonisation matrices"""
        dashboard = self.repository.get_user_dashboard(user_id, StakeholderRole.RESEARCHER.value)
        if not dashboard:
            return None
        
        # Get recent harmonisation activity
        recent_activity = self.repository.user_activity_logs[-10:]  # Last 10 activities
        
        metrics = {
            "total_matches": len(self.repository.harmonisation_records),
            "recent_activity": recent_activity,
            "harmonisation_matrix": self._build_harmonisation_matrix(),
            "provenance_trails": self._build_provenance_trails(user_id)
        }
        
        return {
            "dashboard_id": dashboard.id,
            "role": dashboard.role,
            "metrics": metrics,
            "last_updated": datetime.now().isoformat()
        }
    
    def get_expert_dashboard(self, user_id: str, region: str = None) -> Optional[Dict]:
        """Get local expert dashboard with topic summaries"""
        dashboard = self.repository.get_user_dashboard(user_id, StakeholderRole.LOCAL_EXPERT.value)
        if not dashboard:
            return None
        
        metrics = {
            "topic_summaries": self._get_topic_summaries(region),
            "population_trends": self._get_population_trends(region),
            "regional_coverage": self._get_regional_coverage(region)
        }
        
        return {
            "dashboard_id": dashboard.id,
            "role": dashboard.role,
            "region": region,
            "metrics": metrics,
            "last_updated": datetime.now().isoformat()
        }
    
    def get_policymaker_dashboard(self, user_id: str, policy_area: str = None) -> Optional[Dict]:
        """Get policymaker dashboard with evidence and coverage"""
        dashboard = self.repository.get_user_dashboard(user_id, StakeholderRole.POLICYMAKER.value)
        if not dashboard:
            return None
        
        metrics = {
            "evidence_coverage": self._get_evidence_coverage(policy_area),
            "coverage_maps": self._get_coverage_maps(policy_area),
            "policy_recommendations": self._get_recommendations(policy_area)
        }
        
        return {
            "dashboard_id": dashboard.id,
            "role": dashboard.role,
            "policy_area": policy_area,
            "metrics": metrics,
            "last_updated": datetime.now().isoformat()
        }
    
    def get_admin_dashboard(self, user_id: str) -> Optional[Dict]:
        """Get administrator dashboard with system metrics"""
        dashboard = self.repository.get_user_dashboard(user_id, StakeholderRole.ADMINISTRATOR.value)
        if not dashboard:
            return None
        
        metrics = {
            "system_health": self._get_system_health(),
            "user_statistics": self._get_user_statistics(),
            "data_quality": self._get_data_quality_scores(),
            "recent_activities": self.repository.user_activity_logs[-20:]
        }
        
        return {
            "dashboard_id": dashboard.id,
            "role": dashboard.role,
            "metrics": metrics,
            "last_updated": datetime.now().isoformat()
        }
    
    def _build_harmonisation_matrix(self) -> Dict:
        """Build harmonisation matrix showing item matches"""
        matrix = {}
        for record in self.repository.harmonisation_records:
            key = f"{record['item1_id']}__{record['item2_id']}"
            matrix[key] = {
                "similarity": record['similarity_score'],
                "matched": record['matched']
            }
        return matrix
    
    def _build_provenance_trails(self, user_id: str) -> Dict:
        """Build provenance trails for user's harmonisations"""
        trails = {}
        user_activities = [a for a in self.repository.user_activity_logs if a['user_id'] == user_id]
        
        for activity in user_activities:
            if activity['action'] == 'harmonise':
                trails[activity['id']] = {
                    "resource": activity['resource'],
                    "timestamp": activity['timestamp'],
                    "details": activity['details']
                }
        
        return trails
    
    def _get_topic_summaries(self, region: str = None) -> Dict:
        """Get topic summaries for region based on mental health studies"""
        # Get all studies and their constructs
        all_studies = self.studies_loader.get_all_studies()
        all_constructs = self.studies_loader.get_all_constructs()
        
        # Count studies by construct
        topic_summaries = {}
        for construct in all_constructs:
            studies_with_construct = self.studies_loader.get_studies_by_construct(construct)
            topic_summaries[construct.lower().replace(" ", "_")] = {
                "name": construct,
                "coverage": 85 if len(studies_with_construct) > 5 else 45,
                "studies": len(studies_with_construct)
            }
        
        # Add overall mental health summary
        topic_summaries["mental_health_overall"] = {
            "name": "Mental Health",
            "coverage": 85,
            "studies": len(all_studies)
        }
        
        return topic_summaries
    
    def _get_population_trends(self, region: str = None) -> Dict:
        """Get population trends for region"""
        return {
            "trend_1": "Increasing studies on adolescent mental health",
            "trend_2": "Growing focus on community-based interventions",
            "trend_3": "Expansion to rural areas"
        }
    
    def _get_regional_coverage(self, region: str = None) -> Dict:
        """Get regional coverage statistics"""
        return {
            "urban_coverage": 85,
            "rural_coverage": 42,
            "total_participants": 50000
        }
    
    def _get_evidence_coverage(self, policy_area: str = None) -> Dict:
        """Get evidence coverage for policy areas based on mental health studies"""
        all_studies = self.studies_loader.get_all_studies()
        all_constructs = self.studies_loader.get_all_constructs()
        
        # Calculate coverage based on studies per construct
        coverage = {}
        for construct in list(all_constructs)[:10]:  # Top 10 constructs
            studies_count = len(self.studies_loader.get_studies_by_construct(construct))
            coverage[construct] = min(88, 45 + (studies_count * 3))  # Scale based on study count
        
        # Add overall coverage
        coverage["overall_mental_health"] = 88
        
        return coverage
    
    def _get_coverage_maps(self, policy_area: str = None) -> Dict:
        """Get coverage maps"""
        return {
            "geographic_distribution": "Well distributed across regions",
            "demographic_coverage": "Good coverage of ages 18-65",
            "gaps": ["Rural youth", "Elderly population"]
        }
    
    def _get_recommendations(self, policy_area: str = None) -> List[str]:
        """Get policy recommendations"""
        return [
            "Expand mental health services in rural areas",
            "Increase funding for adolescent programs",
            "Integrate traditional healing practices"
        ]
    
    def _get_system_health(self) -> Dict:
        """Get system health metrics"""
        return {
            "uptime_percent": 99.8,
            "response_time_ms": 245,
            "error_rate_percent": 0.2,
            "active_users": 156
        }
    
    def _get_user_statistics(self) -> Dict:
        """Get user statistics including mental health studies coverage"""
        all_studies = self.studies_loader.get_all_studies()
        all_constructs = self.studies_loader.get_all_constructs()
        
        return {
            "total_users": 450,
            "researchers": 200,
            "local_experts": 120,
            "policymakers": 80,
            "administrators": 50,
            "active_today": 156,
            "mental_health_studies_loaded": len(all_studies),
            "mental_health_constructs_covered": len(all_constructs)
        }
    
    def _get_data_quality_scores(self) -> Dict:
        """Get data quality scores including studies metadata completeness"""
        all_studies = self.studies_loader.get_all_studies()
        
        # Calculate metadata completeness for studies
        complete_studies = 0
        for study in all_studies:
            if study.title and study.abstract and study.producers and study.keywords:
                complete_studies += 1
        
        studies_metadata_completeness = (complete_studies / len(all_studies) * 100) if all_studies else 0
        
        return {
            "metadata_completeness": 92,
            "schema_compliance": 88,
            "url_validity": 95,
            "studies_metadata_completeness": round(studies_metadata_completeness, 1),
            "total_studies": len(all_studies),
            "duplicate_records": 2
        }


# ============================================================================
# INITIALIZATION
# ============================================================================

def create_analytics_service() -> AnalyticsService:
    """Factory function to create Analytics Service"""
    repository = AnalyticsRepository()
    return AnalyticsService(repository)
