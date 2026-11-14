from __future__ import annotations

import argparse
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from app.core.config import settings
from app.db.session import SessionLocal
from app.modules.regulatory_monitoring.service import (
    RegulatoryMonitoringService,
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def create_worker_session_factory():
    url = settings.regulatory_worker_database_url

    if not url:
        raise RuntimeError(
            "REGULATORY_WORKER_DATABASE_URL is required for "
            "cross-organization regulatory monitoring."
        )

    if url.startswith("postgresql://"):
        url = url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=2,
        pool_recycle=1800,
    )

    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


WorkerSessionLocal = create_worker_session_factory()


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s %(levelname)s "
        "%(name)s %(message)s"
    ),
)

logger = logging.getLogger(__name__)


def scan_job():
    if not settings.regulatory_monitoring_enabled:
        logger.info("Regulatory monitoring is disabled.")
        return

    db = WorkerSessionLocal()

    try:
        service = RegulatoryMonitoringService()
        results = service.scan_due_sources(db, limit=20)

        for result in results:
            logger.info(
                "Regulatory scan result: %s",
                result,
            )

    except Exception:
        db.rollback()
        logger.exception("Regulatory monitoring worker failed.")

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one scan cycle and exit.",
    )
    args = parser.parse_args()

    if args.once:
        scan_job()
        return

    scheduler = BlockingScheduler(timezone="UTC")

    scheduler.add_job(
        scan_job,
        trigger="interval",
        seconds=settings.regulatory_scan_interval_seconds,
        id="regulatory-monitoring",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )

    logger.info("Starting regulatory monitoring worker.")
    scan_job()
    scheduler.start()


if __name__ == "__main__":
    main()