embedding_model: str = (
    "sentence-transformers/all-MiniLM-L6-v2"
)

embedding_dimension: int = 384

chunk_size_tokens: int = 450

chunk_overlap_tokens: int = 70

max_candidates: int = 40

reranker_model: str = (
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

enable_reranker: bool = True

from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv
import os
from uuid import UUID
from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE, override=False)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        f"DATABASE_URL is missing. Expected environment file: {ENV_FILE}"
    )

class Settings(BaseSettings):
    app_name: str = "Enterprise Intelligence Platform"
    app_env: str = "development"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    database_url: str = DATABASE_URL

    oidc_issuer: str = Field(
        default="",
        validation_alias="OIDC_ISSUER",
    )

    oidc_audience: str = Field(
        default="",
        validation_alias="OIDC_AUDIENCE",
    )

    oidc_jwks_url: str = Field(
        default="",
        validation_alias="OIDC_JWKS_URL",
    )

    storage_root: Path = Path("./storage")
    max_upload_size_mb: int = 50

    default_organization_id: UUID = UUID(
        "00000000-0000-4000-8000-000000000001"
    )
    default_organization_name: str = "Development Organization"

    embedding_model: str = (
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    embedding_dimension: int = 384
    chunk_size: int = 220
    chunk_overlap: int = 40

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    
        # ---------------------------------------------------------
    # Milestone 3: Groq LLM configuration
    # ---------------------------------------------------------

    groq_api_key: str = Field(
        default="",
        validation_alias="GROQ_API_KEY",
    )

    groq_model: str = Field(
        default="openai/gpt-oss-120b",
        validation_alias="GROQ_MODEL",
    )

    groq_timeout_seconds: int = Field(
        default=90,
        validation_alias="GROQ_TIMEOUT_SECONDS",
    )

    groq_max_retries: int = Field(
        default=2,
        validation_alias="GROQ_MAX_RETRIES",
    )

    groq_max_completion_tokens: int = Field(
        default=4096,
        validation_alias="GROQ_MAX_COMPLETION_TOKENS",
    )

    rag_top_k: int = 8

    rag_candidate_limit: int = 40

    rag_max_context_chars: int = 24000

    rag_max_question_chars: int = 4000

    rag_require_citations: bool = True

         # ---------------------------------------------------------
    # Milestone 4: Investigation engine - Groq
    # ---------------------------------------------------------

    groq_api_key: str = Field(
        default="",
        validation_alias="GROQ_API_KEY",
    )

    groq_base_url: str = Field(
        default="https://api.groq.com/openai/v1",
        validation_alias="GROQ_BASE_URL",
    )

    investigation_model: str = Field(
        default="llama-3.3-70b-versatile",
        validation_alias="INVESTIGATION_MODEL",
    )

    investigation_temperature: float = 0.0

    investigation_timeout_seconds: int = 90

    investigation_max_tasks: int = 6

    investigation_max_evidence_per_task: int = 8

    investigation_max_total_evidence: int = 30

    investigation_max_context_chars: int = 30000

        # ---------------------------------------------------------
    # Milestone 6: Model Intelligence
    # ---------------------------------------------------------

    ml_model_root: Path = Field(
        default=Path("./artifacts/models"),
        validation_alias="ML_MODEL_ROOT",
    )

    ml_device: str = Field(
        default="auto",
        validation_alias="ML_DEVICE",
    )

    ml_enable_transformers: bool = Field(
        default=False,
        validation_alias="ML_ENABLE_TRANSFORMERS",
    )

    ml_ner_model_path: str = Field(
        default="",
        validation_alias="ML_NER_MODEL_PATH",
    )

    ml_document_classifier_path: str = Field(
        default="./artifacts/models/document-classifier/latest.joblib",
        validation_alias="ML_DOCUMENT_CLASSIFIER_PATH",
    )

    ml_sentence_transformer: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        validation_alias="ML_SENTENCE_TRANSFORMER",
    )

    ml_nli_model_path: str = Field(
        default="",
        validation_alias="ML_NLI_MODEL_PATH",
    )

    ml_similarity_threshold: float = Field(
        default=0.88,
        ge=0.0,
        le=1.0,
        validation_alias="ML_SIMILARITY_THRESHOLD",
    )

    ml_max_text_chars: int = Field(
        default=30000,
        ge=1000,
        le=200000,
        validation_alias="ML_MAX_TEXT_CHARS",
    )

    ml_batch_size: int = Field(
        default=16,
        ge=1,
        le=128,
        validation_alias="ML_BATCH_SIZE",
    )

        # ---------------------------------------------------------
    # Milestone 8: Regulatory Monitoring
    # ---------------------------------------------------------

    regulatory_monitoring_enabled: bool = Field(
        default=True,
        validation_alias="REGULATORY_MONITORING_ENABLED",
    )

    regulatory_scan_interval_seconds: int = Field(
        default=300,
        ge=60,
        le=86400,
        validation_alias="REGULATORY_SCAN_INTERVAL_SECONDS",
    )

    regulatory_http_timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=120,
        validation_alias="REGULATORY_HTTP_TIMEOUT_SECONDS",
    )

    regulatory_max_download_mb: int = Field(
        default=30,
        ge=1,
        le=100,
        validation_alias="REGULATORY_MAX_DOWNLOAD_MB",
    )

    regulatory_max_items_per_scan: int = Field(
        default=100,
        ge=1,
        le=1000,
        validation_alias="REGULATORY_MAX_ITEMS_PER_SCAN",
    )

    regulatory_user_agent: str = Field(
        default="EnterpriseIntelligenceBot/1.0",
        validation_alias="REGULATORY_USER_AGENT",
    )

    regulatory_worker_database_url: str = Field(
        default="",
        validation_alias="REGULATORY_WORKER_DATABASE_URL",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()