"""
Test refactored services to ensure base classes work correctly.
Tests the SOLID principles implementation.
"""

import pytest
from harmony_api.services.data_discovery_service import (
    create_data_discovery_service,
    DatasetStatus,
    AccessType
)
from harmony_api.services.analytics_service import create_analytics_service, StakeholderRole
from harmony_api.services.data_harmonisation_service import create_data_harmonisation_service
from harmony_api.services.summarisation_service import create_summarisation_service
from harmony_api.core.exceptions import (
    EntityNotFoundException,
    DuplicateEntityException,
    ValidationException
)


class TestDataDiscoveryService:
    """Test Data Discovery Service with base classes"""
    
    def test_service_initialization(self):
        """Test service initializes correctly with BaseService"""
        service = create_data_discovery_service()
        assert service is not None
        assert service.repository is not None
    
    def test_get_all_datasets(self):
        """Test getting all datasets returns approved datasets"""
        service = create_data_discovery_service()
        datasets = service.get_all_datasets()
        
        assert isinstance(datasets, list)
        assert len(datasets) > 0
        assert all(d["status"] == DatasetStatus.APPROVED.value for d in datasets)
    
    def test_global_search(self):
        """Test global search functionality"""
        service = create_data_discovery_service()
        results = service.global_search("NIDS")
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert any("NIDS" in d["name"] for d in results)
    
    def test_search_by_construct(self):
        """Test construct-based filtering"""
        service = create_data_discovery_service()
        results = service.search_by_construct("Depressive Disorder")
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert all("Depressive Disorder" in d["constructs"] for d in results)
    
    def test_get_dataset_details(self):
        """Test getting individual dataset details"""
        service = create_data_discovery_service()
        datasets = service.get_all_datasets()
        
        if datasets:
            dataset_id = datasets[0]["id"]
            details = service.get_dataset_details(dataset_id)
            
            assert details is not None
            assert details["id"] == dataset_id
            assert "name" in details
            assert "constructs" in details
    
    def test_get_unique_constructs(self):
        """Test getting unique constructs"""
        service = create_data_discovery_service()
        constructs = service.get_unique_constructs()
        
        assert isinstance(constructs, list)
        assert len(constructs) > 0
        assert all(isinstance(c, str) for c in constructs)
    
    def test_submit_dataset_duplicate_detection(self):
        """Test duplicate dataset detection raises proper exception"""
        service = create_data_discovery_service()
        
        # Submit first dataset
        dataset1 = service.submit_dataset(
            name="Test Dataset",
            source="Test Source",
            description="Test Description",
            constructs=["Test Construct"],
            instrument="Test Instrument",
            access_type=AccessType.OPEN.value,
            access_url="https://test.com"
        )
        
        # Try to submit duplicate - should raise DuplicateEntityException
        with pytest.raises(DuplicateEntityException):
            service.submit_dataset(
                name="Test Dataset",
                source="Test Source",
                description="Test Description",
                constructs=["Test Construct"],
                instrument="Test Instrument",
                access_type=AccessType.OPEN.value,
                access_url="https://test.com"
            )
    
    def test_add_study_to_dataset(self):
        """Test adding study to dataset"""
        service = create_data_discovery_service()
        datasets = service.get_all_datasets()
        
        if datasets:
            dataset_id = datasets[0]["id"]
            original_count = datasets[0]["study_count"]
            
            updated = service.add_study_to_dataset(
                dataset_id,
                "Test Citation"
            )
            
            assert updated["study_count"] == original_count + 1


class TestAnalyticsService:
    """Test Analytics Service with base classes"""
    
    def test_service_initialization(self):
        """Test service initializes correctly"""
        service = create_analytics_service()
        assert service is not None
        assert service.repository is not None
    
    def test_get_researcher_dashboard(self):
        """Test researcher dashboard creation"""
        service = create_analytics_service()
        dashboard = service.get_researcher_dashboard("user123")
        
        assert dashboard is not None
        assert dashboard["role"] == StakeholderRole.RESEARCHER.value
        assert "metrics" in dashboard
        assert "harmonisation_matrix" in dashboard["metrics"]


class TestDataHarmonisationService:
    """Test Data Harmonisation Service with base classes"""
    
    def test_service_initialization(self):
        """Test service initializes correctly"""
        service = create_data_harmonisation_service()
        assert service is not None
        assert service.repository is not None
    
    def test_initiate_harmonisation(self):
        """Test initiating harmonisation job"""
        service = create_data_harmonisation_service()
        job = service.initiate_harmonisation(
            source_dataset_id="source123",
            target_dataset_id="target456",
            created_by="user789"
        )
        
        assert job is not None
        assert job.id is not None
        assert job.source_dataset_id == "source123"
        assert job.target_dataset_id == "target456"
        assert job.status == "pending"


class TestSummarisationService:
    """Test Summarisation Service with base classes"""
    
    def test_service_initialization(self):
        """Test service initializes correctly"""
        service = create_summarisation_service()
        assert service is not None
        assert service.repository is not None
    
    def test_initiate_summarisation(self):
        """Test initiating summarisation workflow"""
        service = create_summarisation_service()
        summary = service.initiate_summarisation(
            study_id="study123",
            study_title="Test Study",
            study_abstract="This is a test abstract."
        )
        
        assert summary is not None
        assert summary.id is not None
        assert summary.study_id == "study123"
        assert summary.status == "draft"
    
    def test_deduplication(self):
        """Test summary deduplication"""
        service = create_summarisation_service()
        
        # Create first summary
        summary1 = service.initiate_summarisation(
            study_id="study456",
            study_title="Test Study 2",
            study_abstract="Another test abstract."
        )
        
        # Try to create duplicate - should return existing
        summary2 = service.initiate_summarisation(
            study_id="study456",
            study_title="Test Study 2",
            study_abstract="Another test abstract."
        )
        
        assert summary1.id == summary2.id


class TestBaseServicePatterns:
    """Test base service patterns work correctly"""
    
    def test_to_dict_list_helper(self):
        """Test inherited _to_dict_list helper works"""
        service = create_data_discovery_service()
        datasets = service.repository.list()
        
        # Use inherited helper
        dict_list = service._to_dict_list(datasets)
        
        assert isinstance(dict_list, list)
        assert all(isinstance(d, dict) for d in dict_list)
        assert all("id" in d for d in dict_list)
    
    def test_validate_entity_exists_helper(self):
        """Test inherited _validate_entity_exists helper works"""
        service = create_data_discovery_service()
        datasets = service.get_all_datasets()
        
        if datasets:
            dataset_id = datasets[0]["id"]
            
            # Should not raise exception
            entity = service._validate_entity_exists(dataset_id, "Dataset")
            assert entity is not None
            
            # Should raise EntityNotFoundException
            with pytest.raises(ValueError):  # BaseService raises ValueError, router converts to EntityNotFoundException
                service._validate_entity_exists("nonexistent_id", "Dataset")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
