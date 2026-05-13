# SoloCRM v1 Architecture Design

**Date:** 2026-05-12
**Status:** Approved
**Based on:** Monica CRM analysis + current scaffolding audit

---

## 1. Architecture Overview

Domain-modular layered architecture: Feature domains each contain their own models, schemas, repository, service, and router. Shared base classes provide cross-cutting concerns (CRUD templates, session injection, errors).

```
Frontend (React + Vite + TailwindCSS)
    |
    | HTTP REST (axios)
    |
API Layer (FastAPI Routers per domain)
    |
Service Layer (per-domain, injected via Depends)
    |
Repository Layer (per-domain, extends BaseRepository)
    |
SQLAlchemy Models → PostgreSQL 16 + pgvector
    |
AI Client (OpenAI-compatible) / Utils (ASR, Web Search)
```

Dependency direction: Router → Service → Repository → Model. Domains do not depend on each other.

---

## 2. Backend Directory Structure

```
backend/app/
├── main.py                        # FastAPI entry, route registration, lifespan
├── config.py                      # ✅ existing, Settings via pydantic-settings
├── database.py                    # 🆕 DB engine, session factory, pgvector init
│
├── shared/                        # 🆕 cross-cutting
│   ├── base_repository.py         #    CRUD template with type generics
│   ├── base_service.py            #    DB session injection
│   ├── exceptions.py              #    Unified exception hierarchy
│   └── schemas.py                 #    Pagination, unified response wrapper
│
├── domains/                       # 🆕 business domains
│   ├── case/                      #    success case domain
│   │   ├── models.py              #       SuccessCase ORM model
│   │   ├── schemas.py             #       Pydantic request/response
│   │   ├── repository.py          #       Data access
│   │   ├── service.py             #       Business logic + embedding
│   │   └── router.py              #       FastAPI routes
│   ├── customer/                  #    customer domain
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   └── router.py
│   ├── visit/                     #    visit plans + records
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   └── router.py
│   ├── todo/                      #    todos
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── repository.py
│   │   └── router.py
│   └── search/                    #    hybrid search
│       ├── service.py             #       vector + structured retrieval
│       └── router.py
│
├── ai/                            # 🆕 AI capability layer
│   ├── client.py                  #    OpenAI-compatible LLM client
│   ├── embedding.py               #    text → vector(1024)
│   └── prompts/                   #    user-editable prompt templates
│       ├── case_extraction.md
│       ├── visit_summary.md
│       ├── meddic_review.md
│       └── generate_opening.md
│
└── utils/                         # Utility layer
    ├── speech.py                  # ✅ existing, ASR transcription
    └── web_search.py              # 🆕 web scraping for customer intel
```

---

## 3. Frontend Directory Structure

```
frontend/src/
├── main.jsx                       # React entry
├── App.jsx                        # Root with React Router
│
├── features/                      # 🆕 feature domains
│   ├── customer/                  #    CustomerList, CustomerDetail
│   ├── case/                      #    CaseForm, CaseList
│   ├── visit/                     #    VisitPlanForm, VisitRecordDetail
│   ├── todo/                      #    TodoBoard, KanbanView
│   ├── search/                    #    SearchResults, CustomerMatch
│   └── dashboard/                 #    HomeDashboard
│
├── shared/                        # 🆕 reusable components
│   ├── ui/                        #    Button, Card, Modal, Input, etc.
│   ├── layout/                    #    AppShell, Sidebar, Header
│   └── map/                       #    Leaflet wrapper
│
├── services/                      # API call layer
│   └── api.js                     # axios instance + interceptors
├── store/                         # Zustand global state
│   └── appStore.js
└── config.js                      # Frontend config
```

---

## 4. Database Schema

All tables use UUID primary keys. Vector columns use `vector(1024)` for OpenAI text-embedding-3-small compatibility.

### 4.1 success_cases

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| title | VARCHAR(200) | Case title |
| company_name | VARCHAR(200) | Client company |
| industry | VARCHAR(100) | Industry |
| city | VARCHAR(100) | City |
| product | VARCHAR(200) | Product/solution delivered |
| deal_size | NUMERIC | Contract amount (optional) |
| summary | TEXT | Case summary |
| key_points | JSONB | Success factors [{k,v}] |
| embedding | vector(1024) | Text embedding |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### 4.2 customers

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| name | VARCHAR(100) | Contact name |
| company | VARCHAR(200) | Company name |
| title | VARCHAR(100) | Job title |
| industry | VARCHAR(100) | Industry |
| city | VARCHAR(100) | City |
| contact_info | JSONB | {phone,email,wechat} |
| source | VARCHAR(50) | search/manual/import |
| status | VARCHAR(30) | new/contacted/meeting/negotiation/won/lost |
| notes | TEXT | Free notes |
| tags | TEXT[] | Tag array |
| meddic_json | JSONB | MEDDIC dimensions {metrics,economic_buyer,decision_criteria,decision_process,pain_points,champion,health_score,gaps,last_review_at} |
| embedding | vector(1024) | Text embedding |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### 4.3 visit_plans

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| customer_id | UUID (FK→customers) | |
| planned_date | TIMESTAMP | Scheduled time |
| location | VARCHAR(300) | Location |
| latitude | DOUBLE PRECISION | Map coordinate |
| longitude | DOUBLE PRECISION | Map coordinate |
| purpose | TEXT | Visit purpose |
| notes | TEXT | |
| status | VARCHAR(20) | planned/completed/cancelled |
| created_at | TIMESTAMP | |

### 4.4 visit_records

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| customer_id | UUID (FK→customers) | |
| visit_date | TIMESTAMP | Actual visit time |
| audio_path | VARCHAR(500) | Recording file path |
| transcript | TEXT | ASR full text |
| summary | TEXT | AI summary |
| key_people | JSONB | Attendees [{name,role,notes}] |
| meddic_update | JSONB | MEDDIC changes from this visit |
| action_items | JSONB | Follow-up actions [{action,owner,ddl}] |
| raw_notes | TEXT | Raw notes |
| created_at | TIMESTAMP | |

### 4.5 todos

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| customer_id | UUID (FK→customers, nullable) | |
| title | VARCHAR(300) | Todo title |
| description | TEXT | Details |
| priority | INTEGER | Priority (1=highest) |
| meddic_dim | VARCHAR(30) | Linked MEDDIC dimension |
| due_date | DATE | Deadline |
| status | VARCHAR(20) | pending/in_progress/done |
| source | VARCHAR(30) | meddic_review/manual/etc |
| created_at | TIMESTAMP | |

### 4.6 user_product_config

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| product_name | VARCHAR(200) | Product name |
| description | TEXT | Product description |
| features | JSONB | Core features [{name,desc}] |
| target_industries | TEXT[] | Target industries |
| embedding | vector(1024) | Text embedding |
| created_at | TIMESTAMP | |

---

## 5. API Design

### Unified Response Format

```json
{
  "code": 0,
  "data": { ... },
  "message": "success"
}
```

code=0 success, code=1 error (per existing convention).

### RESTful Endpoints (per domain)

```
/cases            GET     list    | POST   create
/cases/{id}       GET     detail  | PUT    update  | DELETE delete
/customers/       GET     list    | POST   create
/customers/{id}   GET     detail  | PUT    update  | DELETE delete
/visits/plans     GET     list    | POST   create
/visits/plans/{id} GET    detail  | PUT    update  | DELETE delete
/visits/records   GET     list    | POST   create (audio upload)
/visits/records/{id} GET   detail | PUT    update
/todos            GET     list    | POST   create
/todos/{id}       GET     detail  | PUT    update  | DELETE delete
/search/customers POST    hybrid search (body: {city,industry,query})
/ai/summary       POST    generate visit summary
/ai/meddic        POST    MEDDIC review
/ai/opening       POST    generate opening script
/health           GET     health check
```

---

## 6. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| MEDDIC as JSONB not relational | Single-user, no cross-customer MEDDIC aggregation needed. JSONB allows flexible evolution without migrations. |
| embedding vector(1024) | OpenAI text-embedding-3-small default. 1024 covers most embedding models. Under-dimension + knowledge graph augmentation for recall. |
| UUID PKs | Distribution-safe, no record count exposure, frontend-safe. |
| Tags as TEXT[] not join table | <100 tags expected. PG native array avoids unnecessary JOINs. |
| visit_plans + visit_records split | Plan and execution have different lifecycles. |
| Prompt templates as standalone .md files | Users can edit prompts without touching code. |

---

## 7. Implementation Phases

### Phase A: Infrastructure Foundation
Target: All 39 empty stubs become runnable skeleton code.
Gates: backend starts, frontend renders, `/health` returns 200, Docker Compose works.

### Phase B: Core Business Chain
Target: "Add case → Find customer → Record visit" end-to-end.
Gates: Full flow works inside Docker Compose.

### Phase C: AI Depth + MEDDIC Closure
Target: All 8 modules complete. AI-driven MEDDIC review, knowledge graph, multi-view browsing.
Gates: Full 8-module walkthrough in Docker Compose.

---

## 8. Tech Stack

| Layer | Choice | Version |
|-------|--------|---------|
| Frontend | React + Vite + TailwindCSS | React 18, Vite 5 |
| State | Zustand | 4.x |
| Routing | React Router DOM | 6.x |
| Maps | Leaflet + React-Leaflet | 1.x |
| Backend | Python + FastAPI | 3.11, 0.109 |
| ORM | SQLAlchemy (async) | 2.0 |
| DB | PostgreSQL + pgvector | PG16 |
| AI | OpenAI-compatible API | 1.x |
| ASR | SiliconFlow TeleSpeechASR | HTTP |
| Deployment | Docker Compose | 3.8 |
