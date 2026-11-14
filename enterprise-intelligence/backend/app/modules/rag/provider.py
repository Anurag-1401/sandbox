
from __future__ import annotations

from groq import Groq

from app.core.config import settings


class LLMProviderError(RuntimeError):
    """Base exception for LLM provider failures."""


class LLMConfigurationError(LLMProviderError):
    """Raised when Groq configuration is missing or invalid."""


class LLMRateLimitError(LLMProviderError):
    """Raised when Groq rate limits the request."""


class LLMGenerationError(LLMProviderError):
    """Raised when Groq cannot generate a valid response."""


RAG_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {
            "type": "string",
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                    },
                    "evidence_ids": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                    },
                },
                "required": [
                    "text",
                    "evidence_ids",
                ],
                "additionalProperties": False,
            },
        },
        "limitations": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "insufficient_evidence": {
            "type": "boolean",
        },
    },
    "required": [
        "answer",
        "findings",
        "limitations",
        "insufficient_evidence",
    ],
    "additionalProperties": False,
}


class GroqLLMProvider:
    """
    Groq-backed LLM provider.

    Uses Groq Chat Completions with strict JSON Schema output.
    The rest of the RAG module depends on this provider interface,
    not on the Groq SDK directly.
    """

    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise LLMConfigurationError(
                "GROQ_API_KEY is not configured."
            )

        if not settings.groq_model:
            raise LLMConfigurationError(
                "GROQ_MODEL is not configured."
            )

        self.model = settings.groq_model

        try:
            self.client = Groq(
                api_key=settings.groq_api_key,
                timeout=settings.groq_timeout_seconds,
                max_retries=settings.groq_max_retries,
            )
        except Exception as exc:
            raise LLMConfigurationError(
                "Could not initialize the Groq client."
            ) from exc

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        if not system_prompt.strip():
            raise ValueError("System prompt cannot be empty.")

        if not user_prompt.strip():
            raise ValueError("User prompt cannot be empty.")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "rag_research_response",
                        "strict": True,
                        "schema": RAG_RESPONSE_JSON_SCHEMA,
                    },
                },
                max_completion_tokens=(
                    settings.groq_max_completion_tokens
                ),
            )

            if not response.choices:
                raise LLMGenerationError(
                    "Groq returned no completion choices."
                )

            choice = response.choices[0]

            if choice.finish_reason == "length":
                raise LLMGenerationError(
                    "Groq response reached the completion token limit."
                )

            content = choice.message.content

            if not isinstance(content, str) or not content.strip():
                raise LLMGenerationError(
                    "Groq returned an empty response."
                )

            return content

        except LLMGenerationError:
            raise

        except Exception as exc:
            error_name = type(exc).__name__

            if error_name == "RateLimitError":
                raise LLMRateLimitError(
                    "Groq rate limit reached. Retry after a short delay."
                ) from exc

            if error_name in {
                "AuthenticationError",
                "PermissionDeniedError",
            }:
                raise LLMConfigurationError(
                    "Groq authentication or permission failed. "
                    "Check the API key and model access."
                ) from exc

            raise LLMGenerationError(
                "Groq could not complete the generation request."
            ) from exc
