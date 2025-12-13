# PAMHoYA Microservices Architecture

## Overview

This document outlines the microservices architecture for PAMHoYA (Platform for Advancing Mental Health in Youth and Adolescence). The current implementation follows a **modular monolith** pattern with clear service boundaries, making it ready for future decomposition into independent microservices.

## Design Principles

### SOLID Principles

1. **Single Responsibility Principle (SRP)**
   - Each service handles one business domain
   - Each class has one reason to change
   - Example: `DataDiscoveryService` only handles dataset discovery operations

2. **Open/Closed Principle (OCP)**
   - Services are open for extension but closed for modification
   - Base classes (`BaseService`, `BaseRepository`) can be extended
   - Example: New filter strategies can be added without modifying existing code

3. **Liskov Substitution Principle (LSP)**
   - All services can be substituted through their base interfaces
   - Any `BaseService` implementation can be used interchangeably
   - Example: All repositories implement `IRepository` interface

4. **Interface Segregation Principle (ISP)**
   - Clients depend only on methods they use
   - Separate interfaces for repositories (`IRepository`) and services (`IService`)
   - No client is forced to depend on unused methods

5. **Dependency Inversion Principle (DIP)**
   - High-level modules don't depend on low-level modules
   - Both depend on abstractions
   - Example: Services depend on `IRepository` interface, not concrete implementations

### DRY (Don't Repeat Yourself)

- **Base Classes**: Common functionality extracted to `BaseService` and `BaseRepository`
- **Centralized Error Handling**: All exceptions extend `PAMHoYAException`
- **Middleware**: Reusable error handling, logging, and performance monitoring
- **Helper Methods**: Shared utilities in base classes (`_validate_entity_exists`, `_to_dict_list`)

## Service Boundaries

### 1. Data Discovery Service

**Domain**: Mental health dataset catalogue and search

**Responsibilities**:
- Dataset metadata management
- Full-text search across datasets
- Construct-based filtering
- Access request management
- Study-dataset linking

**Key Entities**:
- `Dataset`
- `Study`
- `AccessRequest`

**API Endpoints**: `/discovery/*`

**Database**: Dataset catalogue, studies, access requests

**Future Microservice**:
- Independent search service with Elasticsearch
- Separate database for datasets
- REST API with versioning
- Could scale independently based on search load

### 2. Data Harmonisation Service

**Domain**: Data alignment and schema mapping

**Responsibilities**:
- Schema analysis and comparison
- Column mapping creation
- Data normalization
- Dataset merging
- Harmonisation job management

**Key Entities**:
- `HarmonisationJob`
- `ColumnMapping`

**API Endpoints**: `/harmonise/*`

**Database**: Harmonisation jobs, mappings, harmonised datasets

**Future Microservice**:
- Heavy computation service (can be containerized with more resources)
- Message queue for async processing (RabbitMQ/Kafka)
- Separate compute instances for large dataset processing
- Could use Apache Spark for distributed processing

### 3. Summarisation Service

**Domain**: Research study summarization and plain-language translation

**Responsibilities**:
- Summary generation (NLP/LLM)
- Version management
- Review workflow
- Approval process
- Publication management

**Key Entities**:
- `StudySummary`
- `SummaryVersion`

**API Endpoints**: `/summarise/*`

**Database**: Summaries, versions, review comments

**Future Microservice**:
- Integration with LLM providers (OpenAI, Vertex AI)
- Separate processing queue for expensive LLM calls
- Version control system for summaries
- Could benefit from caching layer (Redis)

### 4. Analytics Service

**Domain**: Role-based dashboards and reporting

**Responsibilities**:
- Dashboard creation and management
- Metrics collection
- User activity tracking
- Harmonisation analytics
- Role-based data aggregation

**Key Entities**:
- `Dashboard` (Researcher, LocalExpert, Policymaker, Admin)
- `Metric`

**API Endpoints**: `/analytics/*`

**Database**: Dashboards, metrics, activity logs

**Future Microservice**:
- Time-series database for metrics (InfluxDB, TimescaleDB)
- Real-time analytics with streaming (Apache Kafka, Flink)
- Separate read-optimized database (OLAP)
- Dashboard generator as independent service

## Three-Layer Architecture

All services follow a consistent 3-layer architecture:

```
┌─────────────────────────────────────┐
│     API Layer (Routers)             │
│  - Request validation                │
│  - Response formatting               │
│  - Error handling                    │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│   Business Logic Layer (Services)   │
│  - Domain logic                      │
│  - Business rules                    │
│  - Orchestration                     │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│   Data Access Layer (Repositories)  │
│  - CRUD operations                   │
│  - Query logic                       │
│  - Data persistence                  │
└─────────────────────────────────────┘
```

## Inter-Service Communication

### Current (Modular Monolith)
- Direct method calls within same process
- Shared in-memory data structures
- Synchronous communication

### Future Microservices
- **REST APIs**: Service-to-service HTTP calls with versioning
- **Message Queues**: Async events (RabbitMQ, Apache Kafka)
  - `DatasetCreated`, `HarmonisationCompleted`, `SummaryApproved`
- **Service Mesh**: Istio for service discovery, load balancing
- **API Gateway**: Kong or AWS API Gateway for routing

## Data Management

### Current
- In-memory repositories (POC)
- Shared data structures

### Future
- **Database per Service**: Each microservice owns its data
- **Event Sourcing**: Audit trail and event replay
- **CQRS**: Separate read/write models for analytics
- **Data Replication**: Sync between services when needed

## Cross-Cutting Concerns

### 1. Error Handling
- **Current**: Centralized exceptions in `harmony_api/core/exceptions.py`
- **Future**: Standard error codes across services, error translation gateway

### 2. Logging
- **Current**: Middleware-based logging
- **Future**: Centralized logging (ELK Stack, CloudWatch)

### 3. Monitoring
- **Current**: Performance decorators
- **Future**: Distributed tracing (Jaeger, OpenTelemetry), metrics (Prometheus)

### 4. Security
- **Current**: Shared authentication in monolith
- **Future**: OAuth2/JWT tokens, API keys per service, rate limiting

### 5. Configuration
- **Current**: Environment variables
- **Future**: Config server (Spring Cloud Config, Consul), secrets management (Vault)

## Migration Path to Microservices

### Phase 1: Modular Monolith (Current) ✅
- Clear service boundaries
- Dependency injection
- Interface-based design
- Separate routers per domain

### Phase 2: Prepare for Extraction
1. **Add API Versioning**: `/api/v1/discovery/...`
2. **Externalize Configuration**: Use config server
3. **Add Message Queue**: Implement event bus for async operations
4. **Database Separation**: Migrate from shared DB to separate schemas

### Phase 3: Extract First Service
1. **Choose Independent Service**: Start with Analytics (least dependencies)
2. **Deploy as Separate Container**: Docker + Kubernetes
3. **Set Up Service Discovery**: Consul or Kubernetes DNS
4. **Implement API Gateway**: Route external requests

### Phase 4: Extract Remaining Services
1. Data Discovery Service
2. Harmonisation Service
3. Summarisation Service

### Phase 5: Optimize
1. Add caching (Redis)
2. Implement CQRS where beneficial
3. Add service mesh
4. Set up centralized monitoring

## Service Dependencies

```
Analytics Service
    ↓ (reads harmonisation data)
Data Harmonisation Service
    ↓ (reads datasets)
Data Discovery Service
    ← (provides summaries)
Summarisation Service
```

## Technology Stack

### Current
- **Framework**: FastAPI (Python)
- **Data**: In-memory (POC)
- **Communication**: Direct calls

### Recommended Future Stack
- **API Gateway**: Kong, AWS API Gateway
- **Service Mesh**: Istio
- **Container Orchestration**: Kubernetes
- **Message Queue**: RabbitMQ, Apache Kafka
- **Service Discovery**: Consul, Kubernetes DNS
- **Databases**: PostgreSQL (primary), MongoDB (documents), Redis (cache)
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: Jaeger, OpenTelemetry
- **CI/CD**: GitHub Actions, ArgoCD

## Scalability Considerations

### Horizontal Scaling
- Each service can scale independently
- Load balancer distributes traffic
- Stateless services for easy scaling

### Vertical Scaling
- Harmonisation service may need more memory/CPU
- Analytics service may need more CPU for computations

### Data Scaling
- Read replicas for heavy read services (Discovery)
- Sharding for large datasets
- Caching for frequently accessed data

## Testing Strategy

### Unit Tests
- Test each service in isolation
- Mock repository dependencies
- Test business logic without external dependencies

### Integration Tests
- Test service with real repository
- Test inter-service communication
- Test database interactions

### Contract Tests
- Define API contracts between services
- Use Pact or OpenAPI specs
- Verify contracts don't break

### End-to-End Tests
- Test complete user workflows
- Test cross-service scenarios
- Test failure scenarios

## Monitoring and Observability

### Metrics to Track
- Request rate per service
- Response time (p50, p95, p99)
- Error rate
- Service availability
- Resource utilization (CPU, memory, disk)

### Logs to Collect
- Request/response logs
- Error logs with stack traces
- Business event logs
- Audit logs

### Traces to Capture
- Request flow across services
- Database queries
- External API calls
- Message queue operations

## Security Considerations

### Authentication & Authorization
- JWT tokens for user identity
- Service-to-service authentication
- Role-based access control (RBAC)

### Data Protection
- Encryption in transit (TLS)
- Encryption at rest
- PII data handling
- Data residency compliance

### Network Security
- Service mesh for mTLS
- Network policies in Kubernetes
- API rate limiting
- DDoS protection

## Conclusion

PAMHoYA is architected as a modular monolith with clear service boundaries, following SOLID principles and DRY patterns. This design makes future decomposition into independent microservices straightforward while maintaining code quality and maintainability in the current implementation.

The architecture supports:
- ✅ Independent development of services
- ✅ Clear separation of concerns
- ✅ Testability through dependency injection
- ✅ Scalability through modular design
- ✅ Maintainability through consistent patterns
- ✅ Future migration to microservices with minimal refactoring
