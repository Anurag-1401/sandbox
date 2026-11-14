"""
Legacy compatibility import.

The authoritative ORM models live in app.models.
"""

from app.models.identity import Organization

__all__ = ["Organization"]