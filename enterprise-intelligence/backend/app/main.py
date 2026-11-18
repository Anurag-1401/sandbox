
from fastapi import FastAPI
import os
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.documents import router as documents_router
from app.modules.search.router import router as search_router
from app.modules.rag.router import router as rag_router
from app.modules.investigations.router import (
    router as investigations_router,
)

from app.modules.ml_intelligence.router import router as ml_router
from app.modules.enterprise.router import router as enterprise_router

from app.modules.regulatory_monitoring.router import (
    router as regulatory_router,
)

from app.modules.knowledge_graph.router import (
    router as knowledge_graph_router,
)

from app.modules.graph_investigation.router import (
    router as graph_investigation_router,
)

app = FastAPI(
    title="Enterprise Intelligence Platform",
    description=(
        "AI-powered enterprise research and investigation platform"
    ),
    version="0.3.0",
)

allowed_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Organization-ID",
        "Accept",
    ],
)

API_PREFIX = "/api/v1"

app.include_router(
    documents_router,
    prefix=API_PREFIX,
)

app.include_router(
    search_router,
    prefix=API_PREFIX,
)

app.include_router(
    rag_router,
    prefix=API_PREFIX,
)

app.include_router(
    investigations_router,
    prefix=API_PREFIX,
)

app.include_router(
    ml_router,
    prefix=API_PREFIX,
)

app.include_router(
    enterprise_router,
    prefix=API_PREFIX,
)

app.include_router(
    regulatory_router,
    prefix=API_PREFIX,
)

app.include_router(
    knowledge_graph_router,
    prefix="/api/v1",
)

app.include_router(
    graph_investigation_router,
    prefix="/api/v1",
)

@app.get("/")
def root():
    return {
        "application": "Enterprise Intelligence Platform",
        "status": "running",
        "api_version": app.version,
        "milestone": 7,
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }
