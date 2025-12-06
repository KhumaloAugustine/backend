# PAMHoYA Data Discovery Service - Full Implementation

**Status**: ✅ **COMPLETE**  
**Date**: December 6, 2025  
**Lead Developer**: Augustine Khumalo  
**Team**: PAMHoYA Team

---

## Overview

The Data Discovery Service has been fully implemented based on the wireframe design found in `Wireframe_Discovery.html`. The service provides comprehensive mental health dataset discovery, search, and access management with multilingual support across South African contexts.

### Key Implementation Features

✅ **Dataset-centric architecture** - Datasets are first-class citizens  
✅ **Global full-text search** - Search all dataset fields simultaneously  
✅ **Construct-based filtering** - Filter by mental health disorders/conditions  
✅ **Access type management** - Open, Restricted, Formal Request flows  
✅ **Study/evidence linking** - Datasets connected to evidence of use  
✅ **Smart access actions** - Pre-filled emails, direct portal links  
✅ **5 test datasets pre-loaded** - Ready-to-use South African mental health data  
✅ **3 mental health constructs** - Depression, PTSD, Emotional & Behavioural  

---

## Architecture

### 3-Layer Pattern

```
┌─────────────────────────────────────────────────────┐
│         API LAYER (FastAPI Router)                  │
│  - HTTP endpoints with request/response handling    │
│  - Status codes and error handling                  │
│  - Request validation                               │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│     BUSINESS LOGIC LAYER (Service)                  │
│  - Search algorithms                                │
│  - Filtering logic                                  │
│  - Data validation                                  │
│  - Business rules                                   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│      DATA ACCESS LAYER (Repository)                 │
│  - Dataset storage/retrieval                        │
│  - Access request management                        │
│  - Data persistence                                 │
└─────────────────────────────────────────────────────┘
```

### Data Models

#### Dataset
```python
Dataset:
  - id: UUID
  - name: str (dataset name)
  - source: str (curator/data source)
  - description: str (detailed description)
  - constructs: List[str] (mental health constructs)
  - instrument: str (assessment tool)
  - access_type: str (Open | Restricted | Formal Request)
  - access_url: Optional[str] (direct portal link)
  - request_email: Optional[str] (data custodian email)
  - studies: List[Study] (linked evidence)
  - status: str (approved, pending, etc.)
  - created_at: datetime
  - updated_at: datetime
  - metadata_hash: str (for deduplication)
```

#### Study
```python
Study:
  - id: UUID
  - citation: str (study reference/citation)
  - created_at: datetime
```

#### AccessRequest
```python
AccessRequest:
  - id: UUID
  - dataset_id: str
  - user_id: str
  - reason: str
  - contact_email: str
  - status: str (pending, approved, rejected)
  - created_at: datetime
```

---

## Test Data Pre-Loaded

### 1. National Income Dynamics Study (NIDS), wave 4
- **Source**: DataFirst
- **Access**: Open
- **Construct**: Depressive Disorder
- **Instrument**: CES-D 10
- **Studies**: 1
- **Portal**: https://url.za.m.mimecastprotect.com/s/HsX0C2RqnrcZq396FnfVC5Rqaw

### 2. Agincourt HDSS
- **Source**: Agincourt
- **Access**: Restricted
- **Construct**: Emotional and Behavioural difficulties
- **Instrument**: SDQ - Teacher-report scales
- **Studies**: 1
- **Portal**: https://url.za.m.mimecastprotect.com/s/POC9C48vpwc9N5v6CBirC4kBvu

### 3. SHaW study
- **Source**: Professor Stephen Stansfeld
- **Access**: Formal Request
- **Construct**: Depressive Disorder
- **Instrument**: RCADS
- **Email**: s.a.stansfeld@qmul.ac.uk
- **Studies**: 1

### 4. Hiscox et al [Dataset]
- **Source**: Lucy V. Hiscox
- **Access**: Formal Request
- **Construct**: PTSD
- **Instrument**: CPSS-SR-5
- **Email**: lh2235@bath.ac.uk
- **Studies**: 1

### 5. Center for Public Mental Health (CPMH) Data
- **Source**: Mirriam Mkhize
- **Access**: Formal Request
- **Construct**: Depressive Disorder
- **Instrument**: PHQ-A
- **Email**: mkhmir003@myuct.ac.za
- **Studies**: 1

---

## API Endpoints

### Base Path: `/discovery`

#### 1. **List All Datasets**
```
GET /discovery/datasets

Response:
{
  "count": 5,
  "datasets": [...]
}
```

#### 2. **Get Dataset Details**
```
GET /discovery/datasets/{dataset_id}

Response:
{
  "id": "uuid",
  "name": "Dataset Name",
  "source": "Source Name",
  "description": "...",
  "constructs": ["Depressive Disorder"],
  "instrument": "CES-D 10",
  "access_type": "Open",
  "access_url": "https://...",
  "request_email": null,
  "studies": [
    {
      "id": "uuid",
      "citation": "Study citation...",
      "created_at": "2025-12-06T..."
    }
  ],
  "study_count": 1,
  "status": "approved",
  "created_at": "...",
  "updated_at": "..."
}
```

#### 3. **Global Full-Text Search**
```
GET /discovery/search?query=depression&limit=50

Searches:
  - Dataset name
  - Source/curator
  - Description
  - Constructs
  - Instruments
  - Study citations
  - URLs
  - Emails

Response:
{
  "query": "depression",
  "count": 2,
  "datasets": [...]
}
```

#### 4. **Get All Constructs**
```
GET /discovery/constructs

Response:
{
  "count": 3,
  "constructs": [
    "Depressive Disorder",
    "Emotional and Behavioural difficulties",
    "PTSD"
  ]
}
```

#### 5. **Filter by Construct**
```
GET /discovery/constructs/filter?construct=Depressive%20Disorder

Response:
{
  "construct": "Depressive Disorder",
  "count": 3,
  "datasets": [...]
}
```

#### 6. **Get Access Types**
```
GET /discovery/access-types

Response:
{
  "access_types": [
    {
      "type": "Open",
      "description": "Direct access - download from open portal"
    },
    {
      "type": "Restricted",
      "description": "Access requires ethical approval"
    },
    {
      "type": "Formal Request",
      "description": "Access requires formal request to data custodian"
    }
  ]
}
```

#### 7. **Filter by Access Type**
```
GET /discovery/access-types/filter?access_type=Formal%20Request

Response:
{
  "access_type": "Formal Request",
  "count": 3,
  "datasets": [...]
}
```

#### 8. **Advanced Multi-Criteria Search**
```
GET /discovery/advanced-search?query=south%20african&construct=Depressive%20Disorder&access_type=Open&limit=50

Combines:
  - Full-text search
  - Construct filter
  - Access type filter

Response:
{
  "query": "south african",
  "construct_filter": "Depressive Disorder",
  "access_type_filter": "Open",
  "count": 1,
  "datasets": [...]
}
```

#### 9. **Submit New Dataset**
```
POST /discovery/datasets/submit

Request Body:
{
  "name": "New Dataset Name",
  "source": "Data Source",
  "description": "Description...",
  "constructs": ["Depressive Disorder"],
  "instrument": "Assessment Tool",
  "access_type": "Open",
  "access_url": "https://portal.example.com",
  "request_email": null
}

Response:
{
  "status": "submitted",
  "dataset": {...}
}
```

#### 10. **Add Study to Dataset**
```
POST /discovery/datasets/{dataset_id}/studies

Request Body:
{
  "citation": "Author et al. (2025). Study title. Journal Name, vol(issue), pp."
}

Response:
{
  "status": "study_added",
  "dataset": {...}
}
```

#### 11. **Request Dataset Access**
```
POST /discovery/datasets/{dataset_id}/request-access

Request Body:
{
  "user_id": "user-uuid",
  "reason": "Research on adolescent depression in South Africa",
  "contact_email": "researcher@university.ac.za"
}

Response:
{
  "status": "request_submitted",
  "access_request": {
    "id": "request-uuid",
    "dataset_id": "dataset-uuid",
    "status": "pending",
    "created_at": "2025-12-06T..."
  }
}
```

#### 12. **Get Access Requests for Dataset**
```
GET /discovery/datasets/{dataset_id}/access-requests

Response:
{
  "dataset_id": "dataset-uuid",
  "count": 2,
  "requests": [
    {
      "id": "request-uuid",
      "dataset_id": "dataset-uuid",
      "user_id": "user-uuid",
      "reason": "...",
      "contact_email": "...",
      "status": "pending",
      "created_at": "..."
    }
  ]
}
```

#### 13. **Get Catalogue Statistics**
```
GET /discovery/statistics

Response:
{
  "total_datasets": 5,
  "total_constructs": 3,
  "total_studies": 5,
  "by_access_type": {
    "Open": 1,
    "Restricted": 1,
    "Formal Request": 3
  },
  "constructs_available": 3
}
```

#### 14. **Health Check**
```
GET /discovery/health

Response:
{
  "service": "data_discovery",
  "status": "healthy",
  "timestamp": "2025-12-06T...",
  "version": "1.0"
}
```

---

## Search Examples

### Example 1: Find datasets mentioning "South African adolescents"
```bash
curl "http://localhost:8001/discovery/search?query=South%20African%20adolescents"
```
Returns datasets matching South African contexts

### Example 2: Find all depression-related datasets
```bash
curl "http://localhost:8001/discovery/constructs/filter?construct=Depressive%20Disorder"
```
Returns 3 datasets measuring depression

### Example 3: Find formal request datasets
```bash
curl "http://localhost:8001/discovery/access-types/filter?access_type=Formal%20Request"
```
Returns 3 datasets requiring email requests

### Example 4: Advanced search - Open access depression datasets
```bash
curl "http://localhost:8001/discovery/advanced-search?construct=Depressive%20Disorder&access_type=Open"
```
Returns 1 result: NIDS Wave 4

### Example 5: Search across all fields
```bash
curl "http://localhost:8001/discovery/search?query=PTSD"
```
Searches dataset names, descriptions, constructs, instruments, studies, citations

---

## Testing

Run the comprehensive test suite:
```bash
python test_discovery_service.py
```

**Test Coverage**:
- ✅ Load test datasets (5 datasets)
- ✅ Retrieve unique constructs (3 constructs)
- ✅ Global full-text search
- ✅ Construct-based filtering
- ✅ Access type filtering
- ✅ Advanced multi-criteria filtering
- ✅ Dataset details retrieval
- ✅ Study/evidence management

All tests passing ✅

---

## Features by Category

### Search Features
- **Global Search**: Query any field across all datasets
- **Full-Text Search**: Natural language queries
- **Advanced Filtering**: Combine query + construct + access type
- **Construct Filtering**: Browse by mental health disorders
- **Access Type Filtering**: Browse by access level

### Dataset Features
- **Rich Metadata**: Name, source, description, constructs, instruments
- **Linked Studies**: Each dataset can have multiple evidence citations
- **Access Management**: Open, Restricted, or Formal Request flows
- **Direct Access**: URLs for open datasets
- **Email Requests**: Pre-filled email templates for formal requests

### Access Management
- **Access Type Badges**: Visual indicators for access level
- **Direct Links**: One-click access to open datasets
- **Automatic Email Generation**: Pre-filled requests with dataset info
- **Request Tracking**: Monitor all access requests

### Data Quality
- **Deduplication**: Detect duplicate datasets by metadata hash
- **Status Management**: Pending, approved, rejected, archived
- **Timestamp Tracking**: Creation and update timestamps

---

## Integration with PAMHoYA Platform

### Event Bus Integration
The service publishes events to the Event Bus for other services:
```python
# Events that can be published:
- "dataset.created"
- "dataset.updated"
- "access_request.created"
- "access_request.approved"
```

### Multilingual Support
Integrates with LaBSE embeddings service for South African language support:
- Support for all 11 official SA languages
- Cross-language search capabilities (future enhancement)

### Analytics Integration
Data Discovery statistics feed into Analytics Service:
- Total datasets in catalogue
- Construct distribution
- Access type breakdown
- Popularity metrics

---

## File Structure

```
harmony_api/
├── services/
│   └── data_discovery_service.py      # Service implementation (570+ lines)
│       - AccessType enum
│       - DatasetStatus enum
│       - Study model
│       - Dataset model
│       - AccessRequest model
│       - DatasetRepository (data access layer)
│       - DataDiscoveryService (business logic)
│
├── routers/
│   └── data_discovery_router.py        # API routes (440+ lines)
│       - GET  /discovery/datasets
│       - GET  /discovery/datasets/{id}
│       - GET  /discovery/search
│       - GET  /discovery/constructs
│       - GET  /discovery/constructs/filter
│       - GET  /discovery/access-types
│       - GET  /discovery/access-types/filter
│       - GET  /discovery/advanced-search
│       - POST /discovery/datasets/submit
│       - POST /discovery/datasets/{id}/studies
│       - POST /discovery/datasets/{id}/request-access
│       - GET  /discovery/datasets/{id}/access-requests
│       - GET  /discovery/statistics
│       - GET  /discovery/health

test_discovery_service.py               # Comprehensive test suite
```

---

## Implementation Highlights

### 1. Global Search Algorithm
```python
def global_search(self, query: str) -> List[Dict]:
    """
    Concatenates all searchable fields:
    - Dataset name + source + description
    - All constructs
    - Instrument
    - All study citations
    - Access URLs and emails
    
    Returns datasets where query appears in any field
    """
```

### 2. Advanced Filtering
```python
def advanced_filter(self, query, construct, access_type) -> List[Dict]:
    """
    1. Filter by construct (if provided)
    2. Filter by access type (if provided)
    3. Filter by full-text query (if provided)
    
    All filters are optional and can be combined
    """
```

### 3. Deduplication
```python
def find_duplicates(self, metadata_hash: str) -> List[Dataset]:
    """
    Computes MD5 hash of:
    - Dataset name
    - Source
    - Description
    
    Prevents duplicate datasets in catalogue
    """
```

### 4. Access Type Management
```python
# Each dataset has:
- access_type: "Open" | "Restricted" | "Formal Request"
- access_url: For Open/Restricted datasets
- request_email: For Formal Request datasets

# Smart access actions generated by API
```

---

## Next Steps / Future Enhancements

1. **Database Integration**
   - Replace in-memory storage with PostgreSQL
   - Add dataset versioning
   - Implement audit trails

2. **Advanced Features**
   - Cross-language search (using LaBSE)
   - Semantic similarity matching
   - Dataset recommendations
   - Popularity/usage metrics

3. **Frontend Components**
   - Implement wireframe UI
   - Interactive dataset browser
   - Advanced search interface
   - Mobile-responsive design

4. **Access Control**
   - Role-based access (researcher, curator, admin)
   - Authentication/authorization
   - Dataset publication workflow

5. **Integration**
   - Connect Data Harmonisation Service
   - Integrate with Analytics dashboards
   - Event bus notifications

---

## Status

| Component | Status | Notes |
|-----------|--------|-------|
| Service Implementation | ✅ Complete | All features implemented |
| API Endpoints | ✅ Complete | 14 endpoints fully functional |
| Test Data | ✅ Complete | 5 real SA datasets pre-loaded |
| Unit Tests | ✅ Complete | All features tested and passing |
| Documentation | ✅ Complete | Comprehensive API docs |
| PAMHoYA Branding | ✅ Complete | Rebranded from Harmony |
| Production Ready | 🟡 Partial | Ready for dev/test, needs DB |

---

## Contact & Attribution

**Lead Developer**: Augustine Khumalo  
**Team**: PAMHoYA Team  
**Project**: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence

**Wireframe Design**: Based on `Wireframe_Discovery.html`  
**Test Data**: South African mental health datasets (NIDS, Agincourt, SHaW, Hiscox, CPMH)

---

*Last Updated: December 6, 2025*  
*Version: 1.0 - Full Implementation*
