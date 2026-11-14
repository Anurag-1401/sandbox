from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import settings


class ModelLoadError(RuntimeError):
    pass


def get_device() -> str:
    configured = settings.ml_device.lower()

    if configured != "auto":
        return configured

    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


@lru_cache(maxsize=8)
def load_token_classifier(model_path: str):
    if not settings.ml_enable_transformers:
        raise ModelLoadError("Transformer inference is disabled.")

    if not model_path:
        raise ModelLoadError("NER model path is not configured.")

    path = Path(model_path)
    if not path.exists():
        raise ModelLoadError(f"NER model does not exist: {path}")

    try:
        from transformers import pipeline

        return pipeline(
            "token-classification",
            model=str(path),
            tokenizer=str(path),
            aggregation_strategy="simple",
            device=0 if get_device() == "cuda" else -1,
        )
    except Exception as exc:
        raise ModelLoadError("Unable to load NER model.") from exc


@lru_cache(maxsize=4)
def load_text_classifier(model_path: str):
    if not model_path:
        raise ModelLoadError("Classification model path is not configured.")

    path = Path(model_path)
    if not path.exists():
        raise ModelLoadError(f"Classifier does not exist: {path}")

    try:
        import joblib
        return joblib.load(path)
    except Exception as exc:
        raise ModelLoadError("Unable to load document classifier.") from exc


@lru_cache(maxsize=4)
def load_sentence_model(model_name: str):
    if not settings.ml_enable_transformers:
        raise ModelLoadError("Transformer inference is disabled.")

    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(
            model_name,
            device=get_device(),
        )
    except Exception as exc:
        raise ModelLoadError("Unable to load sentence transformer.") from exc


@lru_cache(maxsize=4)
def load_nli_pipeline(model_path: str):
    if not settings.ml_enable_transformers:
        raise ModelLoadError("Transformer inference is disabled.")

    if not model_path:
        raise ModelLoadError("NLI model path is not configured.")

    path = Path(model_path)
    if not path.exists():
        raise ModelLoadError(f"NLI model does not exist: {path}")

    try:
        from transformers import pipeline

        return pipeline(
            "text-classification",
            model=str(path),
            tokenizer=str(path),
            device=0 if get_device() == "cuda" else -1,
            top_k=None,
        )
    except Exception as exc:
        raise ModelLoadError("Unable to load NLI model.") from exc