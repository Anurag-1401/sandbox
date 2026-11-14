from __future__ import annotations

import argparse
import json

from pathlib import Path
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.regulatory import RegulatorySource
from app.modules.regulatory_monitoring.fetcher import SafeSourceFetcher


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    args = parser.parse_args()

    config_path = Path(args.file)

    if not config_path.is_file():
        raise FileNotFoundError(config_path)

    data = json.loads(
        config_path.read_text(encoding="utf-8")
    )

    sources = data.get("sources", [])

    if not isinstance(sources, list):
        raise ValueError("'sources' must be a JSON array.")

    fetcher = SafeSourceFetcher()
    db = SessionLocal()

    try:
        for item in sources:
            required = [
                "code",
                "name",
                "authority",
                "source_type",
                "listing_url",
                "allowed_hosts",
            ]

            missing = [
                key for key in required
                if not item.get(key)
            ]

            if missing:
                raise ValueError(
                    f"Missing fields for source: {missing}"
                )

            source_type = item["source_type"]

            if source_type not in {"rss", "atom", "html"}:
                raise ValueError("Unsupported source type.")

            allowed_hosts = [
                str(host).lower().strip()
                for host in item["allowed_hosts"]
            ]

            fetcher.validate_url(
                item["listing_url"],
                allowed_hosts,
            )

            source = db.execute(
                select(RegulatorySource).where(
                    RegulatorySource.code == item["code"]
                )
            ).scalar_one_or_none()

            values = {
                "name": item["name"],
                "authority": item["authority"],
                "jurisdiction": item.get(
                    "jurisdiction",
                    "India",
                ),
                "source_type": source_type,
                "listing_url": item["listing_url"],
                "allowed_hosts": allowed_hosts,
                "selectors": item.get("selectors", {}),
                "scan_interval_minutes": int(
                    item.get("scan_interval_minutes", 60)
                ),
                "enabled": bool(item.get("enabled", True)),
            }

            if source:
                for key, value in values.items():
                    setattr(source, key, value)
            else:
                source = RegulatorySource(
                    code=item["code"],
                    **values,
                )
                db.add(source)

            print(
                f"Registered source: {item['code']}"
            )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()