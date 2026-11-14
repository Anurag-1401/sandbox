
from functools import lru_cache

from app.modules.intelligence.service import IntelligenceService
from app.modules.investigations.llm import get_investigation_llm


@lru_cache(maxsize=1)
def get_intelligence_service():
    return IntelligenceService(
        llm=get_investigation_llm(),
    )
