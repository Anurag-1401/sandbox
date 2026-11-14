
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from openai import OpenAI

from app.core.config import settings


class InvestigationLLMError(RuntimeError):
    pass


class InvestigationLLM:

    def __init__(self):
        if not settings.groq_api_key:
            raise InvestigationLLMError(
                "GROQ_API_KEY is not configured."
            )

        self.client = OpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            timeout=settings.investigation_timeout_seconds,
            max_retries=2,
        )

        self.model = settings.investigation_model

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=settings.investigation_temperature,
                response_format={
                    "type": "json_object",
                },
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
            )

            content = response.choices[0].message.content

            if not content:
                raise InvestigationLLMError(
                    "Groq returned an empty response."
                )

            result = json.loads(content)

            if not isinstance(result, dict):
                raise InvestigationLLMError(
                    "Groq response must be a JSON object."
                )

            return result

        except InvestigationLLMError:
            raise

        except Exception as exc:
            raise InvestigationLLMError(
                "Groq model generation failed."
            ) from exc


@lru_cache(maxsize=1)
def get_investigation_llm() -> InvestigationLLM:
    return InvestigationLLM()
