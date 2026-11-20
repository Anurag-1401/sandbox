# Enterprise Intelligence Platform

An AI-powered enterprise intelligence and investigation platform for transforming organizational documents, regulatory publications, and connected knowledge into searchable, evidence-backed intelligence.

The platform combines document intelligence, hybrid search, retrieval-augmented generation (RAG), agentic investigations, claim verification, regulatory monitoring, machine learning, knowledge graphs, and graph-based impact analysis in a multi-organization application.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Platform Architecture](#platform-architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Frontend](#frontend)
- [Backend](#backend)
- [Database and Migrations](#database-and-migrations)
- [Prerequisites](#prerequisites)
- [Installation and Setup](#installation-and-setup)
- [Environment Configuration](#environment-configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Security and Organization Isolation](#security-and-organization-isolation)
- [Regulatory Monitoring Worker](#regulatory-monitoring-worker)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Current Implementation Notes](#current-implementation-notes)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Enterprise Intelligence Platform is designed to help organizations process large collections of documents and transform unstructured information into actionable, traceable intelligence.

Instead of treating document management, search, research, investigations, regulatory monitoring, and knowledge discovery as isolated activities, the platform brings them together in a unified intelligence workflow.

The system supports:

1. Document ingestion, validation, extraction, and versioning.
2. Semantic, keyword, and hybrid information retrieval.
3. AI-powered research with evidence and citation validation.
4. Multi-step agentic investigations.
5. Intelligence verification and contradiction analysis.
6. Machine-learning-based document and entity intelligence.
7. Regulatory publication monitoring and impact assessment.
8. Enterprise knowledge graph exploration.
9. Graph-based investigation and impact analysis.
10. Organization-aware access control and workspace management.

The architecture follows a modular-monolith approach, with a React frontend and a FastAPI backend connected to PostgreSQL and pgvector.

---

## Key Features

### 1. Document Intelligence

The document intelligence subsystem provides the foundation for enterprise knowledge processing.

Features include:

- PDF document upload.
- File type and signature validation.
- File structure validation.
- Document fingerprinting and hashing.
- Duplicate detection.
- PDF text extraction.
- Document metadata processing.
- Document version management.
- Document storage.
- Text chunking for retrieval.
- Document indexing.

The ingestion pipeline is designed to prepare uploaded documents for downstream search, research, and investigation workflows.

### 2. Hybrid Search and Retrieval

The search subsystem combines multiple retrieval strategies to improve information discovery.

Supported capabilities include:

- Keyword-based search.
- Semantic vector search.
- Hybrid retrieval.
- Candidate retrieval.
- Result reranking.
- Organization-scoped document retrieval.
- Search evaluation utilities.

The vector retrieval infrastructure uses PostgreSQL with pgvector.

### 3. AI Research Assistant and RAG

The research subsystem uses Retrieval-Augmented Generation to generate answers grounded in indexed enterprise information.

Capabilities include:

- Natural-language questions.
- Retrieval of relevant document chunks.
- Context construction.
- LLM-powered answer generation.
- Citation validation.
- Evidence-grounded responses.
- Configurable retrieval limits.
- RAG evaluation utilities.

The objective is to provide traceable answers based on available evidence rather than relying only on a language model's internal knowledge.

### 4. Agentic Investigation Engine

The investigation subsystem supports structured, multi-step intelligence workflows.

Its architecture includes specialized agents for:

- Investigation planning.
- Document analysis.
- Research.
- Evidence comparison.
- Verification.

The workflow is implemented using a graph-based investigation architecture.

Investigation capabilities include:

- Investigation creation.
- Multi-step execution.
- Evidence gathering.
- Document comparison.
- Finding generation.
- Investigation reporting.
- Review workflows.

### 5. Intelligence Verification

The intelligence subsystem provides analytical components for evaluating claims and their supporting evidence.

Capabilities include:

- Claim extraction.
- Groundedness analysis.
- Contradiction detection.
- Source reliability assessment.
- Applicability analysis.
- Confidence and priority scoring.
- Intelligence reporting.

Generated assessments should be treated as decision-support outputs and reviewed against their underlying evidence.

### 6. Machine Learning Intelligence

The ML intelligence subsystem contains components for:

- Named entity recognition.
- Document classification.
- Natural language inference.
- Similarity analysis.
- Obligation extraction.
- Text preprocessing.
- Model registration and runtime management.

Model paths, device selection, embedding models, and optional transformer execution are configurable through backend settings.

### 7. Regulatory Intelligence and Continuous Monitoring

The regulatory monitoring subsystem is designed to collect and process regulatory publications from configured sources.

Capabilities include:

- Regulatory source management.
- Publication fetching.
- Safe external source access.
- Publication snapshot storage.
- Publication version tracking.
- Change and difference analysis.
- Organization-specific subscriptions.
- Regulatory alert generation.
- Subscription relevance evaluation.
- Alert review and applicability decisions.
- Background monitoring through a dedicated worker.

Regulatory relevance scores and automated impact assessments are decision-support signals. They do not replace legal interpretation or professional compliance review.

### 8. Enterprise Knowledge Graph

The knowledge graph subsystem represents relationships between enterprise intelligence entities.

Supported entity categories include:

- Regulations.
- Clauses.
- Amendments.
- Obligations.
- Standards.
- Products.
- Organizations.
- Authorities.
- Concepts.

The graph provides a structured way to explore relationships and connected information.

### 9. Graph-Powered Investigation and Impact Analysis

The graph investigation subsystem supports bounded graph traversal and finding generation.

Capabilities include:

- Root-node selection.
- Configurable traversal depth.
- Relationship-type filtering.
- Node-type filtering.
- Evidence-aware analysis.
- Finding prioritization.
- Investigation history.
- Finding review.
- Review decisions.
- Impact reporting.

The prioritization score is an analytical ranking mechanism. It should not be interpreted as a probability of legal or business impact.

### 10. Enterprise Workspace and Access Management

The enterprise subsystem provides organization and workspace-related functionality.

The application includes frontend modules for:

- Workspace selection.
- Team management.
- Department management.
- Workspace settings.
- Audit log viewing.
- User profile management.
- Authentication-related pages.
- Permission-aware UI components.

Backend authorization and database-level organization isolation remain the security boundaries; frontend visibility controls alone are not sufficient authorization.

---

## Platform Architecture

The platform follows a modular-monolith architecture.

```text
                         USERS
                           |
                           v
              +-------------------------+
              |     React Frontend      |
              |-------------------------|
              | Dashboard               |
              | Document Management     |
              | Search and AI Research  |
              | Investigations          |
              | Verification            |
              | Regulatory Intelligence|
              | Knowledge Graph         |
              | Impact Analysis         |
              | Organization Management|
              +------------+------------+
                           |
                           | HTTP / REST API
                           | Bearer Authentication
                           | Organization Context
                           v
              +-------------------------+
              |      FastAPI Backend    |
              |-------------------------|
              | Document Intelligence  |
              | Search and Retrieval   |
              | RAG and LLM Integration|
              | Investigation Engine   |
              | Intelligence Services  |
              | ML Intelligence        |
              | Regulatory Monitoring  |
              | Knowledge Graph        |
              | Graph Investigation    |
              | Enterprise Services    |
              +------------+------------+
                           |
              +------------+-------------+
              |                          |
              v                          v
    +----------------------+   +----------------------+
    | PostgreSQL           |   | AI / ML Components   |
    |----------------------|   |----------------------|
    | Application Data     |   | LLM Provider         |
    | Documents            |   | Embeddings           |
    | Document Chunks      |   | Reranking            |
    | Organization Data    |   | Classification       |
    | Investigations       |   | NER / NLI            |
    | Knowledge Graph      |   +----------------------+
    | pgvector             |
    +----------------------+
              |
              v
    +----------------------+
    | File Storage         |
    |----------------------|
    | Original Documents   |
    | Document Versions    |
    | Regulatory Snapshots |
    +----------------------+

              +----------------------+
              | Regulatory Worker    |
              |----------------------|
              | Source Fetching      |
              | Publication Scanning|
              | Alert Generation     |
              +----------------------+
```

### Architectural Principles

- Modular backend organization.
- Separation of frontend and backend responsibilities.
- Organization-aware data access.
- Reusable document-processing services.
- Retrieval and generation separation.
- Evidence-grounded intelligence.
- Configurable AI and ML components.
- Database migrations managed through Alembic.
- API-based communication between application layers.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React 19, TypeScript |
| Build Tool | Vite |
| Routing | React Router |
| Server State | TanStack Query |
| HTTP Client | Axios |
| UI Icons | Lucide React |
| Authentication Client | oidc-client-ts |
| Backend | Python, FastAPI |
| Data Validation | Pydantic |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Vector Search | pgvector |
| Database Migrations | Alembic |
| Retrieval | Keyword, semantic and hybrid search |
| Embeddings | Sentence Transformers |
| RAG | Retrieval-Augmented Generation |
| LLM Integration | Groq-compatible API configuration |
| Investigation Workflows | Graph-based agent workflow |
| ML | Transformers and Sentence Transformers |
| Background Jobs | APScheduler |
| Frontend Testing | Vitest |
| Backend Testing | Pytest |

---

## Project Structure

```text
enterprise-intelligence/
│
├── backend/
│   ├── alembic/
│   │   └── versions/
│   │
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │
│   │   ├── core/
│   │   │   └── security/
│   │   │
│   │   ├── db/
│   │   │   ├── models/
│   │   │   └── session.py
│   │   │
│   │   ├── models/
│   │   │
│   │   ├── modules/
│   │   │   ├── document_intelligence/
│   │   │   ├── enterprise/
│   │   │   ├── graph_investigation/
│   │   │   ├── intelligence/
│   │   │   ├── investigations/
│   │   │   ├── knowledge_graph/
│   │   │   ├── ml_intelligence/
│   │   │   ├── rag/
│   │   │   ├── regulatory_monitoring/
│   │   │   └── search/
│   │   │
│   │   ├── schemas/
│   │   ├── storage/
│   │   └── main.py
│   │
│   ├── sample_documents/
│   ├── storage/
│   ├── tests/
│   ├── alembic.ini
│   ├── pytest.ini
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   └── ui/
│   │   │
│   │   ├── config/
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   ├── dashboard/
│   │   │   ├── documents/
│   │   │   ├── impact-analysis/
│   │   │   ├── investigations/
│   │   │   ├── knowledge-graph/
│   │   │   ├── organization/
│   │   │   ├── profile/
│   │   │   ├── regulatory/
│   │   │   ├── research/
│   │   │   ├── search/
│   │   │   └── verification/
│   │   │
│   │   ├── lib/
│   │   ├── styles/
│   │   ├── types/
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── vitest.config.ts
│
├── data/
│   ├── processed/
│   ├── raw/
│   └── sample_documents/
│
├── docker/
│
├── research/
│   ├── dry_runs/
│   ├── experiments/
│   ├── mathematics/
│   └── theory/
│
├── .gitignore
├── docker-compose.yml
└── README.md
```

---

## Frontend

The frontend is a React and TypeScript single-page application built using Vite.

### Frontend Modules

| Module | Responsibility |
|---|---|
| Dashboard | Main application overview |
| Documents | Document upload, listing and details |
| Search | Enterprise information retrieval |
| Research | AI-powered research |
| Investigations | Investigation creation and review |
| Verification | Claim and evidence verification |
| Regulatory | Regulatory sources, subscriptions and alerts |
| Knowledge Graph | Entity and relationship exploration |
| Impact Analysis | Graph-based impact investigations |
| Organization | Workspace, team and department management |
| Profile | User profile |
| Authentication | Login and callback pages |

### Frontend Installation

```powershell
cd frontend
npm ci
```

### Development Server

```powershell
npm run dev
```

Default development URL:

```text
http://localhost:5173
```

### Type Checking

```powershell
npm run typecheck
```

### Frontend Tests

```powershell
npm run test
```

Run tests in watch mode:

```powershell
npm run test:watch
```

### Production Build

```powershell
npm run build
```

Preview the production build:

```powershell
npm run preview
```

The production output is generated in:

```text
frontend/dist/
```

---

## Backend

The backend is implemented using FastAPI and organized into independent application modules.

### Backend Modules

| Module | Responsibility |
|---|---|
| Document Intelligence | Validation, parsing, hashing and ingestion |
| Search | Chunking, embeddings, indexing and retrieval |
| RAG | Context construction, generation and citations |
| Investigations | Multi-step investigation workflows |
| Intelligence | Groundedness, contradiction and applicability |
| ML Intelligence | Classification, NER, NLI and similarity |
| Enterprise | Workspace and organization services |
| Regulatory Monitoring | Source fetching, subscriptions and alerts |
| Knowledge Graph | Graph entity and relationship operations |
| Graph Investigation | Graph traversal and impact findings |

### Backend Installation

Create and activate a virtual environment:

```powershell
cd backend

python -m venv .venv

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
```

Install the declared requirements:

```powershell
pip install -r requirements.txt
```

**Dependency note:** The current `requirements.txt` is not a complete dependency lock for every imported backend module. Install the remaining application dependencies and compatible versions before starting the backend. The project should maintain a complete, tested dependency specification for reproducible installation.

### Run the Backend

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Default backend URL:

```text
http://127.0.0.1:8000
```

Health endpoint:

```text
http://127.0.0.1:8000/health
```

---

## Database and Migrations

The application uses PostgreSQL as its primary relational database and pgvector for vector storage and similarity retrieval.

### Create the Database

```sql
CREATE DATABASE enterprise_intelligence;
```

Enable pgvector:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Verify the extension:

```sql
SELECT extname
FROM pg_extension
WHERE extname = 'vector';
```

### Configure the Database URL

Example:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/enterprise_intelligence
```

### Apply Migrations

Run from the backend directory:

```powershell
alembic heads
alembic current
alembic history
```

Apply pending migrations:

```powershell
alembic upgrade head
```

Verify the resulting revision:

```powershell
alembic current
```

Migrations are maintained in:

```text
backend/alembic/versions/
```

Do not use migration stamping as a replacement for applying migrations to a new database.

---

## Prerequisites

Before running the application, install:

- Python compatible with the backend dependencies.
- Node.js and npm.
- PostgreSQL.
- PostgreSQL pgvector extension.
- A configured OIDC identity provider for authenticated workflows.
- An LLM API credential for AI-powered functionality.
- Network connectivity for any configured external model or regulatory sources.

Optional ML models may need to be downloaded or configured locally.

---

## Installation and Setup

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd enterprise-intelligence
```

### 2. Configure PostgreSQL

Create the application database and enable pgvector using the instructions in [Database and Migrations](#database-and-migrations).

### 3. Configure Backend Environment

Create:

```text
backend/.env
```

Example configuration:

```env
APP_ENV=development
ENVIRONMENT=development
DEBUG=true

DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/enterprise_intelligence

OIDC_ISSUER=https://YOUR_IDENTITY_PROVIDER
OIDC_AUDIENCE=YOUR_API_AUDIENCE
OIDC_JWKS_URL=https://YOUR_IDENTITY_PROVIDER/.well-known/jwks.json

GROQ_API_KEY=YOUR_GROQ_API_KEY
GROQ_MODEL=openai/gpt-oss-120b
GROQ_BASE_URL=https://api.groq.com/openai/v1

INVESTIGATION_MODEL=llama-3.3-70b-versatile

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

ML_DEVICE=auto
ML_ENABLE_TRANSFORMERS=false

REGULATORY_MONITORING_ENABLED=false
REGULATORY_SCAN_INTERVAL_SECONDS=3600
REGULATORY_HTTP_TIMEOUT_SECONDS=30
REGULATORY_MAX_DOWNLOAD_MB=25
REGULATORY_MAX_ITEMS_PER_SCAN=20
REGULATORY_USER_AGENT=EnterpriseIntelligencePlatform/1.0

REGULATORY_WORKER_DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/enterprise_intelligence
```

These are example values. Verify all settings against the backend configuration and the features you intend to run.

### 4. Configure Frontend Environment

Create:

```text
frontend/.env
```

Example:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_AUTH_ENABLED=true

VITE_OIDC_AUTHORITY=https://YOUR_IDENTITY_PROVIDER
VITE_OIDC_CLIENT_ID=YOUR_CLIENT_ID

VITE_OIDC_REDIRECT_URI=http://localhost:5173/auth/callback
VITE_OIDC_POST_LOGOUT_REDIRECT_URI=http://localhost:5173/login

VITE_OIDC_SCOPE=openid profile email
```

Configure the same callback URLs in the OIDC provider.

Never store database passwords, LLM API keys, OIDC client secrets, or other private credentials in frontend environment variables.

### 5. Install Dependencies

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Install any additional backend dependencies required by the modules you use.

Frontend:

```powershell
cd frontend
npm ci
```

### 6. Apply Database Migrations

```powershell
cd backend
alembic upgrade head
```

### 7. Start the Backend and Frontend

Start the backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a separate terminal, start the frontend:

```powershell
cd frontend
npm run dev
```

---

## Running the Application

Once the services are running:

| Component | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend | http://127.0.0.1:8000 |
| API Health | http://127.0.0.1:8000/health |
| Swagger UI | http://127.0.0.1:8000/docs |
| OpenAPI Schema | http://127.0.0.1:8000/openapi.json |

The frontend communicates with the backend through its configured API base URL and API prefix.

The backend currently mounts its feature routers under:

```text
/api/v1
```

---

## API Documentation

FastAPI generates interactive API documentation automatically.

Open:

```text
http://127.0.0.1:8000/docs
```

Alternative documentation:

```text
http://127.0.0.1:8000/redoc
```

OpenAPI JSON:

```text
http://127.0.0.1:8000/openapi.json
```

The API documentation can be used to inspect registered endpoints, request schemas, response schemas, and authentication requirements.

Protected API requests use bearer authentication and, where required, an organization context header:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
X-Organization-ID: YOUR_ORGANIZATION_UUID
```

Use real tokens and organization IDs issued through the configured authentication and workspace flow.

---

## Testing

Testing should cover individual modules, API integration, end-to-end workflows, and organization-level security.

### Frontend Tests

```powershell
cd frontend

npm run typecheck

npm run test

npm run build
```

### Backend Tests

```powershell
cd backend

.\.venv\Scripts\Activate.ps1

pytest -q
```

Verbose test execution:

```powershell
pytest -v
```

Run a specific test:

```powershell
pytest tests/test_chunking.py -v
```

### Recommended Functional Test Scenarios

| Area | Test Scenarios |
|---|---|
| Authentication | Login, callback, session restoration, logout |
| Organization | Workspace selection and switching |
| RBAC | Owner, admin, analyst and reviewer permissions |
| Documents | Valid upload, invalid upload, indexing and versioning |
| Search | Keyword, semantic and hybrid retrieval |
| RAG | Grounded answers and citation validation |
| Investigations | Creation, execution, findings and review |
| Verification | Supporting, contradictory and insufficient evidence |
| Regulatory | Sources, subscriptions, scanning and alert review |
| Knowledge Graph | Nodes, relationships and traversal |
| Impact Analysis | Root selection, depth, findings and review |
| Security | Expired tokens and cross-organization access |

### Organization Isolation Testing

Use separate test organizations and users to verify that:

- Users can access only authorized organization resources.
- Organization membership is checked by the backend.
- Unauthorized role operations are rejected.
- Cross-organization document access is blocked.
- Organization context is consistently applied.
- Database row-level security policies are effective.

A successful frontend test does not prove that backend authorization and database isolation are correct.

---

## Security and Organization Isolation

Security is a core architectural requirement.

The backend includes authentication and authorization components, organization-aware principal resolution, and database security context handling.

Important security practices:

- Validate access tokens through the configured OIDC provider.
- Keep credentials and private keys on the backend.
- Enforce authorization in backend endpoints.
- Apply organization context consistently.
- Enforce tenant isolation through database policies.
- Validate uploaded file types and structures.
- Restrict external regulatory source fetching.
- Use HTTPS in production.
- Keep production CORS origins restricted.
- Protect worker credentials and database connection strings.
- Avoid exposing sensitive document content in logs.
- Review database migrations and row-level security policies before deployment.

### Environment Variables

Never commit:

```text
backend/.env
frontend/.env
.env
.env.*
```

Commit safe example files only, such as:

```text
backend/.env.example
frontend/.env.example
```

Before publishing the repository, check Git history and tracked files for secrets. Removing a secret from the latest commit does not remove it from earlier Git history; rotate exposed credentials.

---

## Regulatory Monitoring Worker

Regulatory monitoring runs separately from the main API process.

The worker is located at:

```text
backend/app/modules/regulatory_monitoring/worker.py
```

A single scan can be started using:

```powershell
cd backend

.\.venv\Scripts\Activate.ps1

python -m app.modules.regulatory_monitoring.worker --once
```

For continuous monitoring:

```powershell
python -m app.modules.regulatory_monitoring.worker
```

Configure the worker database connection through:

```env
REGULATORY_WORKER_DATABASE_URL=YOUR_WORKER_DATABASE_URL
```

The worker requires appropriate database permissions and external network access to configured regulatory sources.

Keep it running as a separate process or managed background service in production.

---

## Production Deployment

Before production deployment, complete the following steps.

### Frontend

1. Configure the production API URL.
2. Configure the production OIDC authority and callback URLs.
3. Run TypeScript checks.
4. Run frontend tests.
5. Build the production bundle.
6. Deploy the contents of `frontend/dist/`.
7. Configure the hosting provider to serve `index.html` for application routes.
8. Enable HTTPS.

Build command:

```bash
npm ci
npm run typecheck
npm run test
npm run build
```

### Backend

1. Configure production database credentials.
2. Configure OIDC issuer, audience and JWKS URL.
3. Configure allowed frontend origins.
4. Apply database migrations.
5. Configure secure file storage.
6. Configure LLM and embedding services.
7. Configure regulatory worker access.
8. Disable development-only behavior.
9. Enable structured logging and monitoring.
10. Configure database backups and recovery procedures.
11. Run backend tests and security checks.
12. Deploy behind HTTPS and an appropriate production server.

### CORS Configuration

The backend reads allowed origins from:

```env
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
```

Use explicit production origins. Avoid wildcard origins when credentials are enabled.

### Production Checklist

- [ ] Production database configured.
- [ ] pgvector enabled.
- [ ] Database migrations applied.
- [ ] OIDC configuration verified.
- [ ] Production frontend URL configured.
- [ ] CORS restricted.
- [ ] Secrets stored securely.
- [ ] Storage configured.
- [ ] RLS and tenant isolation tested.
- [ ] Role permissions tested.
- [ ] Frontend production build successful.
- [ ] Backend tests successful.
- [ ] Regulatory worker configured if required.
- [ ] HTTPS enabled.
- [ ] Logging and monitoring enabled.
- [ ] Backup and recovery strategy tested.

---

## Troubleshooting

### Backend: DATABASE_URL is missing

Ensure that:

- `backend/.env` exists.
- `DATABASE_URL` is defined.
- The connection string is valid.
- The PostgreSQL service is running.

### PostgreSQL: vector extension not found

Connect to the application database and execute:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Ensure pgvector is installed on the PostgreSQL server.

### Backend: Migration errors

Inspect:

```powershell
alembic heads
alembic current
alembic history
```

Resolve migration conflicts before upgrading. Do not mark migrations as applied without checking the actual database schema.

### Frontend: API connection errors

Verify:

- Backend is running.
- API base URL is correct.
- Vite proxy configuration is correct.
- CORS allows the frontend origin.
- Browser network requests point to the expected backend.

### HTTP 401

Check the access token, OIDC configuration, issuer, audience, expiry and JWKS URL.

### HTTP 403

Check the user's organization membership, role and required permissions.

### HTTP 422

Check the request payload against the API schema.

### AI or embedding errors

Check:

- LLM API credentials.
- Model configuration.
- Embedding model availability.
- Network connectivity.
- Installed ML dependencies.
- Model download and cache permissions.

### Regulatory worker errors

Check:

- `REGULATORY_WORKER_DATABASE_URL`.
- Database permissions.
- Worker environment variables.
- External source availability.
- Source allowlist and URL validation.
- Network connectivity.

---

## Current Implementation Notes

This repository contains the frontend and backend modules described above, but successful deployment and operation depend on completing environment-specific configuration and verification.

In particular:

- The backend dependency file must be completed and tested for reproducible installation.
- Authentication routes and workspace selection must be connected to the application router and validated with the configured identity provider.
- Database migrations must be applied to the target database.
- AI provider credentials and model availability must be configured.
- Regulatory monitoring requires its separate worker process.
- Integration, tenant-isolation, and production tests must be performed in the target environment.
- The repository's Docker Compose file is not currently a configured application deployment; use the documented manual startup procedure unless a Compose configuration is added and validated.

Do not interpret the presence of a module or frontend page as proof that its production workflow has been verified.

---

## Contributing

Contributions are welcome.

Suggested contribution workflow:

1. Fork the repository.
2. Create a feature branch.
3. Follow the existing modular architecture.
4. Keep frontend and backend responsibilities separated.
5. Add or update tests.
6. Preserve organization-level security.
7. Document environment changes.
8. Run relevant checks before submitting a pull request.

Example:

```bash
git checkout -b feature/your-feature-name
```

Commit changes:

```bash
git add .
git commit -m "Add: your feature description"
git push origin feature/your-feature-name
```

Open a pull request with a description of the implementation, testing performed, and any migration or environment changes.

---

## License

No license has been specified in this repository yet.

Add a `LICENSE` file before distributing or permitting reuse of the project. Until then, do not assume that the source code is open for unrestricted reuse.

---

## Project

**Enterprise Intelligence Platform**

AI-powered document intelligence, enterprise research, regulatory monitoring, investigation workflows, and graph-based impact analysis.

Built with React, TypeScript, FastAPI, PostgreSQL, pgvector, and machine-learning technologies.

