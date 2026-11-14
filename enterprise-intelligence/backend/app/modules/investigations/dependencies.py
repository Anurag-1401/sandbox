from functools import lru_cache

from app.modules.investigations.repository import (
    InvestigationRepository,
)
from app.modules.investigations.service import (
    InvestigationService,
)


@lru_cache(maxsize=1)
def get_investigation_repository():
    return InvestigationRepository()


@lru_cache(maxsize=1)
def get_investigation_service():
    return InvestigationService(
        repository=get_investigation_repository(),
    )