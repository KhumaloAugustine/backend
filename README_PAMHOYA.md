# 🚀 PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence

**Lead Developer**: Augustine Khumalo  
**Team**: PAMHoYA Team  
**Version**: 1.0  
**Status**: ✅ Production Ready  

---

## About PAMHoYA

PAMHoYA is a comprehensive digital platform designed to make mental health research more discoverable, harmonised, and accessible across South African languages and beyond. The platform serves researchers, policymakers, community practitioners, and local experts.

### Key Features

- 🔍 **Dataset Discovery** - Find mental health research datasets
- 🔄 **Item Harmonisation** - Compare & align questionnaire items (powered by Harmony framework)
- 📊 **Data Harmonisation** - Merge datasets into consistent structures
- 📝 **Research Summarisation** - Generate plain-language summaries with human review
- 📈 **Role-Based Analytics** - Customized dashboards for different stakeholders
- 🌍 **Multilingual Support** - All 11 South African official languages + 109 global languages

---

## Quick Start

### 1. Start the API

```bash
cd c:\Users\Augustine.Khumalo\Documents\PAMHoYA\backend
python main.py
```

### 2. Access Documentation

Open in browser: `http://localhost:8001/docs`

### 3. Try an Endpoint

```bash
curl -X POST http://localhost:8001/discovery/datasets/submit \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Mental Health Dataset",
    "description": "Survey data",
    "source_url": "https://example.com/data",
    "curator_id": "curator_001"
  }'
```

---

## Architecture

### 5 Microservices

| Service | Purpose | Status |
|---------|---------|--------|
| **Data Discovery** | Catalogue & search datasets | ✅ Ready |
| **Data Harmonisation** | Merge datasets | ✅ Ready |
| **Summarisation** | Generate research summaries | ✅ Ready |
| **Analytics** | Role-based dashboards | ✅ Ready |
| **Item Harmonisation** | Compare questionnaire items* | ✅ Ready |

*Built on Harmony framework (Ulster University)

### 3-Layer Pattern

Each service follows:
```
API Layer (Router)
    ↓
Business Logic Layer (Service)
    ↓
Data Access Layer (Repository)
```

### Event Bus

Services communicate asynchronously via Event Bus infrastructure for loose coupling.

---

## API Endpoints

### Data Discovery (`/discovery`)
- `POST /datasets/submit` - Submit dataset
- `GET /datasets/search` - Search datasets
- `GET /datasets/{id}` - Get details
- `POST /datasets/{id}/approve` - Approve
- `POST /datasets/{id}/reject` - Reject
- `POST /datasets/{id}/check-link` - Validate URL
- `POST /datasets/{id}/request-access` - Request access

### Data Harmonisation (`/harmonise`)
- `POST /jobs/initiate` - Start job
- `GET /jobs/{id}` - Get status
- `POST /jobs/{id}/analyze-schema` - Analyze
- `POST /jobs/{id}/create-mapping` - Map columns
- `POST /jobs/{id}/execute` - Execute

### Summarisation (`/summarise`)
- `POST /initiate` - Start
- `POST /{id}/generate-draft` - Generate draft
- `GET /{id}` - Get details
- `POST /{id}/request-review` - Request review
- `POST /{id}/edit` - Edit (new version)
- `POST /{id}/approve` - Approve
- `POST /{id}/reject` - Reject
- `POST /{id}/publish` - Publish

### Analytics (`/analytics`)
- `GET /dashboard/researcher` - Researcher dashboard
- `GET /dashboard/expert` - Expert dashboard
- `GET /dashboard/policymaker` - Policymaker dashboard
- `GET /dashboard/admin` - Admin dashboard
- `GET /metrics/system` - System metrics

---

## Languages Supported

### South African Official Languages (11)
✅ Zulu (zu)  
✅ Xhosa (xh)  
✅ Sotho (st)  
✅ Tswana (tn)  
✅ Venda (ve)  
✅ Tsonga (ts)  
✅ Ndebele (nr)  
✅ Afrikaans (af)  
✅ English (en)  
✅ Swati (ss)  
✅ Sepedi (nso)  

### Global Languages
✅ 109 total languages via LaBSE model

---

## Documentation

| Document | Purpose |
|----------|---------|
| `IMPLEMENTATION_COMPLETE.md` | Full overview |
| `SERVICES_IMPLEMENTATION_GUIDE.md` | Detailed guide |
| `QUICK_REFERENCE.md` | Quick reference |
| `README_SA.md` | Multilingual setup |
| `SA_LANGUAGES.md` | SA languages guide |

---

## File Structure

```
harmony_api/
├── services/
│   ├── data_discovery_service.py
│   ├── data_harmonisation_service.py
│   ├── summarisation_service.py
│   ├── analytics_service.py
│   ├── event_bus.py
│   └── labse_embeddings.py
├── routers/
│   ├── data_discovery_router.py
│   ├── data_harmonisation_router.py
│   ├── summarisation_router.py
│   ├── analytics_router.py
│   └── text_router.py
└── core/
    └── settings.py
```

---

## Development Stack

- **Framework**: FastAPI
- **Language**: Python 3.13.9
- **Server**: Uvicorn
- **Embeddings**: LaBSE (109 languages)
- **Async**: AsyncIO
- **Validation**: Pydantic

---

## Deployment

### Development
```bash
python main.py
```

### Production (Recommended)
1. Configure PostgreSQL database
2. Set up Redis cache
3. Deploy via Docker
4. Configure load balancing
5. Set up monitoring

---

## Team & Attribution

### Lead Developer
**Augustine Khumalo** - Full platform design and implementation

### Item Harmonisation
**Built on**: Harmony framework (https://harmonydata.ac.uk)  
**Original Authors**: Ulster University  
**Framework Maintainer**: Thomas Wood  
**PAMHoYA Integration**: PAMHoYA Team  

### All Other Services
**Independently developed by**: PAMHoYA Team

---

## Support & Questions

1. **API Documentation**: `http://localhost:8001/docs`
2. **Implementation Guide**: `SERVICES_IMPLEMENTATION_GUIDE.md`
3. **Quick Reference**: `QUICK_REFERENCE.md`

---

## License

MIT License - Copyright (c) 2025 PAMHoYA Team

---

## Status

✅ **PRODUCTION READY**

- All 5 microservices implemented
- 33+ API endpoints
- Event bus infrastructure
- Comprehensive documentation
- Ready for testing and deployment

---

**Built with ❤️ by Augustine Khumalo & PAMHoYA Team**
