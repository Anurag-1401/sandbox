from __future__ import annotations

import ipaddress
import re
import xml.etree.ElementTree as ET

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from ipaddress import ip_address
from urllib.parse import (
    urljoin,
    urlparse,
    urlunparse,
)

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings


@dataclass(frozen=True)
class PublicationCandidate:
    title: str
    url: str
    external_id: str | None = None
    published_at: datetime | None = None
    metadata: dict | None = None


class SourceFetchError(RuntimeError):
    pass


class SafeSourceFetcher:

    def __init__(self):
        self.timeout = settings.regulatory_http_timeout_seconds
        self.max_bytes = (
            settings.regulatory_max_download_mb * 1024 * 1024
        )
        self.user_agent = settings.regulatory_user_agent

    @staticmethod
    def _host_allowed(host: str, allowed_hosts: list[str]) -> bool:
        host = (host or "").lower().rstrip(".")

        try:
            address = ip_address(host)
            return address.is_global
        except ValueError:
            pass

        for allowed in allowed_hosts:
            allowed = str(allowed).lower().strip().rstrip(".")

            if not allowed:
                continue

            if host == allowed or host.endswith("." + allowed):
                return True

        return False

    def validate_url(
        self,
        url: str,
        allowed_hosts: list[str],
    ) -> None:
        parsed = urlparse(url)

        if parsed.scheme != "https":
            raise SourceFetchError("Only HTTPS source URLs are allowed.")

        if not parsed.hostname:
            raise SourceFetchError("Source URL has no hostname.")

        if parsed.username or parsed.password:
            raise SourceFetchError("Credentials in source URLs are forbidden.")

        if not self._host_allowed(
            parsed.hostname,
            allowed_hosts,
        ):
            raise SourceFetchError(
                f"URL host is outside the configured allowlist: "
                f"{parsed.hostname}"
            )

    @staticmethod
    def canonicalize(url: str) -> str:
        parsed = urlparse(url)

        # Remove fragments but preserve query parameters. Some official
        # portals use query parameters as publication identifiers.
        return urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            parsed.params,
            parsed.query,
            "",
        ))

    def _request(
        self,
        url: str,
        allowed_hosts: list[str],
        *,
        headers: dict | None = None,
    ) -> httpx.Response:
        current = url

        with httpx.Client(
            timeout=self.timeout,
            follow_redirects=False,
            trust_env=False,
            headers={
                "User-Agent": self.user_agent,
                "Accept": (
                    "application/rss+xml, application/atom+xml, "
                    "application/xml, text/html, application/pdf, "
                    "*/*;q=0.5"
                ),
                **(headers or {}),
            },
        ) as client:

            for _ in range(6):
                self.validate_url(current, allowed_hosts)

                response = client.get(current)

                if response.status_code in {
                    301, 302, 303, 307, 308
                }:
                    location = response.headers.get("location")

                    if not location:
                        raise SourceFetchError(
                            "Redirect response has no Location header."
                        )

                    current = urljoin(current, location)
                    continue

                response.raise_for_status()
                return response

        raise SourceFetchError("Too many redirects.")

    @staticmethod
    def _parse_date(value: str | None) -> datetime | None:
        if not value:
            return None

        value = value.strip()

        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            pass

        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            return None

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", 1)[-1].lower()

    def _parse_feed(
        self,
        body: bytes,
        base_url: str,
        allowed_hosts: list[str],
    ) -> list[PublicationCandidate]:
        try:
            root = ET.fromstring(body)
        except ET.ParseError as exc:
            raise SourceFetchError("Invalid RSS/Atom XML.") from exc

        candidates = []

        for element in root.iter():
            if self._local_name(element.tag) not in {"item", "entry"}:
                continue

            values = {}

            for child in element:
                key = self._local_name(child.tag)
                values.setdefault(key, []).append(child)

            title_node = (values.get("title") or [None])[0]
            guid_node = (
                values.get("guid")
                or values.get("id")
                or [None]
            )[0]

            title = (
                "".join(title_node.itertext()).strip()
                if title_node is not None
                else "Untitled regulatory publication"
            )

            link = None

            for link_node in values.get("link", []):
                href = link_node.attrib.get("href")
                rel = link_node.attrib.get("rel", "alternate")

                if href and rel in {"alternate", "enclosure"}:
                    link = href
                    if rel == "enclosure":
                        break

                if link_node.text and link_node.text.strip():
                    link = link_node.text.strip()

            if not link:
                continue

            resolved = urljoin(base_url, link)
            self.validate_url(resolved, allowed_hosts)

            date_node = (
                values.get("published")
                or values.get("updated")
                or values.get("pubdate")
                or values.get("date")
                or [None]
            )[0]

            date_value = (
                "".join(date_node.itertext()).strip()
                if date_node is not None
                else None
            )

            guid = (
                "".join(guid_node.itertext()).strip()
                if guid_node is not None
                else None
            )

            candidates.append(
                PublicationCandidate(
                    title=title[:1000],
                    url=self.canonicalize(resolved),
                    external_id=guid,
                    published_at=self._parse_date(date_value),
                    metadata={"discovery_type": "feed"},
                )
            )

        return candidates

    def _parse_html(
        self,
        body: bytes,
        base_url: str,
        allowed_hosts: list[str],
        selectors: dict,
    ) -> list[PublicationCandidate]:
        soup = BeautifulSoup(body, "html.parser")

        selector = selectors.get("link_selector", "a[href]")
        title_selector = selectors.get("title_selector")

        try:
            links = soup.select(selector)
        except Exception as exc:
            raise SourceFetchError(
                "Configured HTML selector is invalid."
            ) from exc

        candidates = []

        for anchor in links:
            href = anchor.get("href")

            if not href:
                continue

            resolved = urljoin(base_url, href)
            self.validate_url(resolved, allowed_hosts)

            if not resolved.lower().split("?")[0].endswith(".pdf"):
                continue

            title = anchor.get_text(" ", strip=True)

            if title_selector:
                parent = anchor.find_parent()
                if parent:
                    title_element = parent.select_one(title_selector)
                    if title_element:
                        title = title_element.get_text(" ", strip=True)

            if not title:
                title = resolved.rsplit("/", 1)[-1]

            candidates.append(
                PublicationCandidate(
                    title=title[:1000],
                    url=self.canonicalize(resolved),
                    metadata={"discovery_type": "html_listing"},
                )
            )

        return candidates

    def discover(
        self,
        *,
        source_type: str,
        listing_url: str,
        allowed_hosts: list[str],
        selectors: dict | None = None,
    ) -> list[PublicationCandidate]:
        self.validate_url(listing_url, allowed_hosts)

        response = self._request(
            listing_url,
            allowed_hosts,
        )

        if source_type in {"rss", "atom"}:
            return self._parse_feed(
                response.content,
                str(response.url),
                allowed_hosts,
            )

        if source_type == "html":
            return self._parse_html(
                response.content,
                str(response.url),
                allowed_hosts,
                selectors or {},
            )

        raise SourceFetchError(
            f"Unsupported source type: {source_type}"
        )

    def expand_to_pdfs(
        self,
        candidate: PublicationCandidate,
        allowed_hosts: list[str],
    ) -> list[PublicationCandidate]:
        """Resolve an RSS detail-page link to its PDF attachments."""

        if candidate.url.lower().split("?")[0].endswith(".pdf"):
            return [candidate]

        response = self._request(
            candidate.url,
            allowed_hosts,
        )

        content_type = response.headers.get(
            "content-type", ""
        ).lower()

        if "pdf" in content_type:
            return [
                PublicationCandidate(
                    title=candidate.title,
                    url=self.canonicalize(str(response.url)),
                    external_id=candidate.external_id,
                    published_at=candidate.published_at,
                    metadata=candidate.metadata,
                )
            ]

        return self._parse_html(
            response.content,
            str(response.url),
            allowed_hosts,
            {"link_selector": "a[href]"},
        )

    def download_pdf(
        self,
        url: str,
        allowed_hosts: list[str],
    ) -> bytes:
        response = self._request(
            url,
            allowed_hosts,
        )

        content = response.content

        if len(content) > self.max_bytes:
            raise SourceFetchError("PDF exceeds configured size limit.")

        if not content.startswith(b"%PDF-"):
            raise SourceFetchError(
                "Discovered publication is not a valid PDF."
            )

        return content