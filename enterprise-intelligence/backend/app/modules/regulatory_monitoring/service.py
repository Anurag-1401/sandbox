from __future__ import annotations

import difflib
import hashlib
import logging
import re
import tempfile

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.identity import Organization
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.regulatory import (
    RegulatorySource,
    RegulatoryPublication,
    RegulatoryPublicationVersion,
    RegulatorySubscription,
    RegulatoryDocumentLink,
    RegulatoryAlert,
)
from app.modules.document_intelligence.parsers.pdf_parser import extract_pdf
from app.modules.search.chunking import DocumentChunker
from app.modules.search.embeddings import EmbeddingService
from app.modules.search.embedding_service import DocumentEmbeddingService
from app.modules.search.indexing import DocumentIndexingService
from app.modules.regulatory_monitoring.fetcher import (
    SafeSourceFetcher,
    PublicationCandidate,
)
from app.modules.regulatory_monitoring.impact import (
    evaluate_subscription_impact,
)
from app.storage.local_storage import LocalFileStorage


logger = logging.getLogger(__name__)


def build_indexing_service():
    return DocumentIndexingService(
        chunker=DocumentChunker(),
        embedding_service=DocumentEmbeddingService(
            embedding_service=EmbeddingService(),
        ),
    )


class RegulatoryMonitoringService:

    def __init__(self):
        self.fetcher = SafeSourceFetcher()
        self.storage = LocalFileStorage()
        self.indexing = build_indexing_service()

    @staticmethod
    def _hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def _extract_text(pages: list[dict]) -> str:
        parts = []

        for page in pages:
            page_number = page.get("page_number")
            page_text = (page.get("text") or "").strip()

            if not page_text:
                continue

            parts.append(
                f"\n[Page {page_number}]\n{page_text}"
            )

        return "\n".join(parts)[:2_000_000]

    @staticmethod
    def _diff_summary(
        previous_text: str,
        current_text: str,
    ) -> dict:
        old_lines = previous_text.splitlines()
        new_lines = current_text.splitlines()

        added = []
        removed = []

        matcher = difflib.SequenceMatcher(
            a=old_lines,
            b=new_lines,
            autojunk=False,
        )

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in {"replace", "delete"}:
                removed.extend(old_lines[i1:i2])

            if tag in {"replace", "insert"}:
                added.extend(new_lines[j1:j2])

        return {
            "method": "line_sequence_matcher",
            "previous_line_count": len(old_lines),
            "current_line_count": len(new_lines),
            "added_line_count": len(added),
            "removed_line_count": len(removed),
            "changed": bool(added or removed),
            "added_excerpt": added[:30],
            "removed_excerpt": removed[:30],
            "limitations": [
                "Text extraction changes can create apparent differences.",
                "A textual difference does not prove a legal amendment.",
                "Human review is required to determine legal effect.",
            ],
        }

    def _save_global_snapshot(
        self,
        *,
        source_id,
        publication_id,
        content_hash: str,
        content: bytes,
    ) -> str:
        root = settings.storage_root.resolve()

        relative = (
            Path("regulatory_snapshots")
            / str(source_id)
            / str(publication_id)
            / f"{content_hash}.pdf"
        )

        destination = (root / relative).resolve()

        if root not in destination.parents:
            raise ValueError("Invalid regulatory snapshot path.")

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not destination.exists():
            destination.write_bytes(content)

        return relative.as_posix()

    @staticmethod
    def _make_temp_pdf(content: bytes) -> Path:
        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            prefix="regulatory-",
            delete=False,
        ) as handle:
            handle.write(content)
            return Path(handle.name)

    def _parse_pdf(self, content: bytes):
        temporary = self._make_temp_pdf(content)

        try:
            parsed = extract_pdf(temporary)
            pages = parsed.get("pages", [])

            if not pages or not any(
                (page.get("text") or "").strip()
                for page in pages
            ):
                raise ValueError(
                    "Publication PDF has no extractable text. "
                    "OCR is not enabled in this M8 pipeline."
                )

            return pages, self._extract_text(pages)

        finally:
            temporary.unlink(missing_ok=True)

    def _record_publication_version(
        self,
        db: Session,
        *,
        source: RegulatorySource,
        candidate: PublicationCandidate,
        content: bytes,
        pages: list[dict],
        extracted_text: str,
    ):
        content_hash = self._hash(content)
        canonical_url = self.fetcher.canonicalize(candidate.url)

        publication = db.execute(
            select(RegulatoryPublication).where(
                RegulatoryPublication.source_id == source.id,
                RegulatoryPublication.canonical_url == canonical_url,
            )
        ).scalar_one_or_none()

        now = datetime.now(timezone.utc)

        is_new = publication is None

        if is_new:
            publication = RegulatoryPublication(
                source_id=source.id,
                canonical_url=canonical_url,
                title=candidate.title,
                external_id=candidate.external_id,
                published_at=candidate.published_at,
                first_seen_at=now,
                last_seen_at=now,
                current_version_number=0,
                status="discovered",
                metadata_json=candidate.metadata or {},
            )
            db.add(publication)
            db.flush()
        else:
            publication.last_seen_at = now
            publication.title = candidate.title or publication.title

            if candidate.published_at:
                publication.published_at = candidate.published_at

        existing_version = db.execute(
            select(RegulatoryPublicationVersion).where(
                RegulatoryPublicationVersion.publication_id
                == publication.id,
                RegulatoryPublicationVersion.content_hash
                == content_hash,
            )
        ).scalar_one_or_none()

        if existing_version:
            db.flush()
            return publication, existing_version, is_new, False, pages

        previous_version = None

        if publication.current_version_number:
            previous_version = db.execute(
                select(RegulatoryPublicationVersion).where(
                    RegulatoryPublicationVersion.publication_id
                    == publication.id,
                    RegulatoryPublicationVersion.version_number
                    == publication.current_version_number,
                )
            ).scalar_one_or_none()

        version_number = publication.current_version_number + 1

        diff = (
            self._diff_summary(
                previous_version.extracted_text,
                extracted_text,
            )
            if previous_version
            else {
                "method": "initial_publication",
                "changed": True,
                "added_line_count": len(extracted_text.splitlines()),
                "removed_line_count": 0,
                "added_excerpt": [],
                "removed_excerpt": [],
                "limitations": [
                    "This is the first observed version."
                ],
            }
        )

        snapshot_key = self._save_global_snapshot(
            source_id=source.id,
            publication_id=publication.id,
            content_hash=content_hash,
            content=content,
        )

        version = RegulatoryPublicationVersion(
            publication_id=publication.id,
            version_number=version_number,
            content_hash=content_hash,
            snapshot_storage_key=snapshot_key,
            extracted_text=extracted_text,
            diff_summary=diff,
            observed_at=now,
        )

        db.add(version)

        publication.current_version_number = version_number
        publication.status = "processed"

        db.flush()

        return publication, version, is_new,True, pages

    def _set_tenant_context(
        self,
        db: Session,
        *,
        organization_id,
        user_id,
    ):
        db.execute(
            text(
                """
                SELECT set_config(
                    'app.current_org_id',
                    :organization_id,
                    true
                )
                """
            ),
            {"organization_id": str(organization_id)},
        )

        db.execute(
            text(
                """
                SELECT set_config(
                    'app.current_user_id',
                    :user_id,
                    true
                )
                """
            ),
            {"user_id": str(user_id)},
        )

        db.execute(
            text(
                """
                SELECT set_config(
                    'app.current_org_role',
                    'admin',
                    true
                )
                """
            )
        )

    def _index_for_organization(
        self,
        db: Session,
        *,
        organization_id,
        user_id,
        publication: RegulatoryPublication,
        version: RegulatoryPublicationVersion,
        pages: list[dict],
        content: bytes,
    ):
        self._set_tenant_context(
            db,
            organization_id=organization_id,
            user_id=user_id,
        )

        link = db.execute(
            select(RegulatoryDocumentLink).where(
                RegulatoryDocumentLink.organization_id
                == organization_id,
                RegulatoryDocumentLink.publication_id
                == publication.id,
            )
        ).scalar_one_or_none()

        if link is None:
            document = Document(
                organization_id=organization_id,
                title=publication.title[:500],
                source_filename=(
                    re.sub(
                        r"[^A-Za-z0-9._-]+",
                        "_",
                        publication.title,
                    )[:450]
                    + ".pdf"
                ),
                status="processing",
            )

            db.add(document)
            db.flush()

            link = RegulatoryDocumentLink(
                organization_id=organization_id,
                publication_id=publication.id,
                document_id=document.id,
            )

            db.add(link)
            version_number = 1

        else:
            document = db.execute(
                select(Document).where(
                    Document.id == link.document_id,
                    Document.organization_id == organization_id,
                )
            ).scalar_one()

            latest_number = db.scalar(
                select(func.max(DocumentVersion.version_number))
                .where(
                    DocumentVersion.document_id == document.id,
                    DocumentVersion.organization_id == organization_id,
                )
            ) or 0

            version_number = latest_number + 1
            document.title = publication.title[:500]
            document.status = "processing"

        version_id = uuid4()

        temporary = self._make_temp_pdf(content)

        try:
            storage_key = self.storage.store(
                source_path=temporary,
                organization_id=organization_id,
                document_id=document.id,
                version_id=version_id,
            )
        finally:
            temporary.unlink(missing_ok=True)

        document_version = DocumentVersion(
            id=version_id,
            document_id=document.id,
            organization_id=organization_id,
            version_number=version_number,
            content_hash=version.content_hash,
            storage_key=storage_key,
            status="processing",
        )

        db.add(document_version)
        db.flush()

        indexed = self.indexing.index_pages(
            db=db,
            organization_id=organization_id,
            version_id=version_id,
            pages=pages,
        )

        document.status = "indexed"
        document_version.status = "indexed"

        db.flush()

        return document, indexed.chunks_indexed

    def _create_tenant_alert(
        self,
        db: Session,
        *,
        organization_id,
        subscription: RegulatorySubscription,
        source: RegulatorySource,
        publication: RegulatoryPublication,
        version: RegulatoryPublicationVersion,
        document_id,
        is_new: bool,
    ):
        impact = evaluate_subscription_impact(
            filters=subscription.filters,
            title=publication.title,
            extracted_text=version.extracted_text,
            authority=source.authority,
            jurisdiction=source.jurisdiction,
        )

        alert_type = (
            "new_publication" if is_new else "publication_update"
        )

        existing = db.execute(
            select(RegulatoryAlert).where(
                RegulatoryAlert.organization_id == organization_id,
                RegulatoryAlert.publication_version_id == version.id,
                RegulatoryAlert.alert_type == alert_type,
            )
        ).scalar_one_or_none()

        if existing:
            return existing

        diff = version.diff_summary or {}

        if is_new:
            summary = (
                "A new publication was discovered from a subscribed "
                f"source: {source.name}."
            )
            severity = "low"
        else:
            summary = (
                "A changed version was detected. "
                f"{diff.get('added_line_count', 0)} lines were added and "
                f"{diff.get('removed_line_count', 0)} lines were removed."
            )
            severity = "medium"

        summary += " " + impact["reason"]

        alert = RegulatoryAlert(
            organization_id=organization_id,
            publication_id=publication.id,
            publication_version_id=version.id,
            document_id=document_id,
            alert_type=alert_type,
            severity=severity,
            relevance_status=impact["relevance_status"],
            status="pending",
            title=publication.title[:1000],
            summary=summary,
            matched_terms=impact["matched_terms"],
        )

        db.add(alert)
        db.flush()

        return alert

    def _process_tenant_subscriptions(
        self,
        db: Session,
        *,
        source: RegulatorySource,
        publication: RegulatoryPublication,
        version: RegulatoryPublicationVersion,
        pages: list[dict],
        content: bytes,
        is_new: bool,
    ):
        # Organizations are enumerated explicitly. The worker then sets
        # each tenant's transaction context before querying its subscriptions.
        organization_ids = db.execute(
            select(Organization.id).where(
                Organization.is_active.is_(True)
            )
        ).scalars().all()

        for organization_id in organization_ids:
            try:
                # Use the current organization context for RLS.
                db.execute(
                    text(
                        """
                        SELECT set_config(
                            'app.current_org_id',
                            :organization_id,
                            true
                        )
                        """
                    ),
                    {"organization_id": str(organization_id)},
                )

                subscriptions = db.execute(
                    select(RegulatorySubscription).where(
                        RegulatorySubscription.organization_id
                        == organization_id,
                        RegulatorySubscription.source_id == source.id,
                        RegulatorySubscription.active.is_(True),
                    )
                ).scalars().all()

                for subscription in subscriptions:
                    self._set_tenant_context(
                        db,
                        organization_id=organization_id,
                        user_id=subscription.created_by,
                    )

                    document, chunks_indexed = (
                        self._index_for_organization(
                            db,
                            organization_id=organization_id,
                            user_id=subscription.created_by,
                            publication=publication,
                            version=version,
                            pages=pages,
                            content=content,
                        )
                    )

                    self._create_tenant_alert(
                        db,
                        organization_id=organization_id,
                        subscription=subscription,
                        source=source,
                        publication=publication,
                        version=version,
                        document_id=document.id,
                        is_new=is_new,
                    )

                    logger.info(
                        "Regulatory publication indexed",
                        extra={
                            "organization_id": str(organization_id),
                            "publication_id": str(publication.id),
                            "document_id": str(document.id),
                            "chunks_indexed": chunks_indexed,
                        },
                    )

                db.commit()

            except Exception:
                db.rollback()
                logger.exception(
                    "Failed to process regulatory subscription",
                    extra={
                        "organization_id": str(organization_id),
                        "publication_id": str(publication.id),
                    },
                )

    def process_candidate(
        self,
        db: Session,
        *,
        source: RegulatorySource,
        candidate: PublicationCandidate,
    ) -> dict:
        pdf_candidates = self.fetcher.expand_to_pdfs(
            candidate,
            source.allowed_hosts,
        )

        processed = 0
        unchanged = 0

        for pdf_candidate in pdf_candidates:
            content = self.fetcher.download_pdf(
                pdf_candidate.url,
                source.allowed_hosts,
            )

            pages, extracted_text = self._parse_pdf(content)

            publication, version, is_new, changed,pages = (
                self._record_publication_version(
                    db,
                    source=source,
                    candidate=pdf_candidate,
                    content=content,
                    pages=pages,
                    extracted_text=extracted_text,
                )
            )

            if version.observed_at and not is_new:
                # Existing same-hash version is not a new content change.
                if publication.current_version_number > 0:
                    latest = publication.current_version_number
                    if version.version_number < latest:
                        unchanged += 1
                        db.commit()
                        continue

            db.commit()

            self._process_tenant_subscriptions(
                db,
                source=source,
                publication=publication,
                version=version,
                pages=pages,
                content=content,
                is_new=is_new,
            )

            processed += 1

        return {
            "processed": processed,
            "unchanged": unchanged,
        }

    def scan_source(
        self,
        db: Session,
        source: RegulatorySource,
    ) -> dict:
        if not source.enabled:
            return {
                "source_id": str(source.id),
                "status": "disabled",
                "discovered": 0,
                "processed": 0,
                "unchanged": 0,
            }

        discovered = 0
        processed = 0
        unchanged = 0
        errors = []

        try:
            candidates = self.fetcher.discover(
                source_type=source.source_type,
                listing_url=source.listing_url,
                allowed_hosts=source.allowed_hosts,
                selectors=source.selectors,
            )

            candidates = candidates[
                :settings.regulatory_max_items_per_scan
            ]

            # Avoid duplicate feed entries in the same scan.
            unique = {}

            for candidate in candidates:
                unique[self.fetcher.canonicalize(candidate.url)] = candidate

            discovered = len(unique)

            for candidate in unique.values():
                try:
                    result = self.process_candidate(
                        db,
                        source=source,
                        candidate=candidate,
                    )

                    processed += result["processed"]
                    unchanged += result["unchanged"]

                except Exception as exc:
                    errors.append({
                        "url": candidate.url,
                        "error_type": type(exc).__name__,
                    })

                    logger.exception(
                        "Failed to process regulatory candidate",
                        extra={
                            "source_id": str(source.id),
                            "url": candidate.url,
                        },
                    )

            source.last_scanned_at = datetime.now(timezone.utc)
            source.last_error = (
                f"{len(errors)} candidate(s) failed."
                if errors
                else None
            )

            db.commit()

            return {
                "source_id": str(source.id),
                "status": "completed_with_errors" if errors else "completed",
                "discovered": discovered,
                "processed": processed,
                "unchanged": unchanged,
                "errors": errors[:20],
            }

        except Exception as exc:
            db.rollback()

            source = db.get(RegulatorySource, source.id)

            if source:
                source.last_scanned_at = datetime.now(timezone.utc)
                source.last_error = type(exc).__name__
                db.commit()

            logger.exception(
                "Regulatory source scan failed",
                extra={"source_id": str(source.id)},
            )

            return {
                "source_id": str(source.id),
                "status": "failed",
                "discovered": discovered,
                "processed": processed,
                "unchanged": unchanged,
                "errors": [{"error_type": type(exc).__name__}],
            }

    def scan_due_sources(
        self,
        db: Session,
        *,
        limit: int = 20,
    ) -> list[dict]:
        now = datetime.now(timezone.utc)

        sources = db.execute(
            select(RegulatorySource)
            .where(RegulatorySource.enabled.is_(True))
            .order_by(RegulatorySource.last_scanned_at.asc().nullsfirst())
            .limit(limit)
        ).scalars().all()

        results = []

        for source in sources:
            due = (
                source.last_scanned_at is None
                or (
                    now - source.last_scanned_at
                ).total_seconds()
                >= source.scan_interval_minutes * 60
            )

            if not due:
                continue

            results.append(
                self.scan_source(db, source)
            )

        return results