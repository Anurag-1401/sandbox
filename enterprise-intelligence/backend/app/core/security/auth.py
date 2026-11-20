
from __future__ import annotations

from functools import lru_cache
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient, PyJWKClientError
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError,IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security.principal import UserPrincipal
from app.db.session import get_db
from app.models.identity import (
    User,
    Organization,
    OrganizationMembership,
)


def unauthorized() -> HTTPException:
    """Return a standard authentication error."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


@lru_cache(maxsize=1)
def get_jwks_client() -> PyJWKClient:
    """
    Create and cache the JWKS client.

    Caching avoids creating a new client for every API request.
    The client also caches signing keys.
    """
    return PyJWKClient(
        settings.oidc_jwks_url,
        cache_keys=True,
    )


def verify_access_token(token: str) -> dict:
    """
    Verify an OIDC access token.

    Validates:
    - Signature
    - Allowed signing algorithm
    - Issuer
    - Audience
    - Expiration
    - Required claims
    """

    if not all(
        [
            settings.oidc_issuer,
            settings.oidc_audience,
            settings.oidc_jwks_url,
        ]
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC authentication is not configured",
        )

    try:
        signing_key = get_jwks_client().get_signing_key_from_jwt(
            token
        )

        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.oidc_issuer,
            audience=settings.oidc_audience,
            options={
                "require": [
                    "exp",
                    "iat",
                    "sub",
                    "iss",
                    "aud",
                ],
            },
        )

        return claims

    except (
        jwt.InvalidTokenError,
        PyJWKClientError,
        ValueError,
    ) as exc:
        raise unauthorized() from exc

def get_authenticated_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """
    Authenticate an OIDC user without requiring organization membership.

    New users are provisioned automatically after their access token
    has passed signature, issuer, audience and expiry validation.
    """

    if not authorization:
        raise unauthorized()

    scheme, separator, token = authorization.partition(" ")

    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise unauthorized()

    claims = verify_access_token(token.strip())

    subject = claims.get("sub")

    if not isinstance(subject, str) or not subject:
        raise unauthorized()

    email = claims.get("email")
    email_verified = claims.get("email_verified") is True

    # Only persist an email asserted as verified by the identity provider.
    verified_email = (
        email.strip().lower()
        if email_verified and isinstance(email, str)
        else None
    )

    display_name = claims.get("name")

    if not isinstance(display_name, str):
        display_name = None

    try:
        user = db.execute(
            select(User).where(User.external_subject == subject)
        ).scalar_one_or_none()

        if user is None:
            user = User(
                external_subject=subject,
                email=verified_email,
                email_verified=email_verified,
                display_name=display_name,
                is_active=True,
            )

            db.add(user)

            try:
                db.flush()
            except IntegrityError:
                # Handles simultaneous first logins for the same subject.
                db.rollback()

                user = db.execute(
                    select(User).where(
                        User.external_subject == subject
                    )
                ).scalar_one_or_none()

                if user is None:
                    raise

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is inactive.",
            )

        if verified_email:
            user.email = verified_email
            user.email_verified = True

        if display_name and not user.display_name:
            user.display_name = display_name

        db.flush()

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
            {"user_id": str(user.id)},
        )

        return user

    except HTTPException:
        raise

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to register or resolve authenticated user.",
        ) from exc


def set_transaction_context(
    db: Session,
    *,
    user_id: UUID,
    organization_id: UUID | None = None,
) -> None:
    """
    Set PostgreSQL transaction-local security context.

    The third argument to set_config is TRUE, so values are
    automatically reset when the transaction ends.
    """

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
        {
            "user_id": str(user_id),
        },
    )

    if organization_id is not None:
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
            {
                "organization_id": str(organization_id),
            },
        )


def get_current_principal(
    organization_id: UUID | None = Header(
        default=None,
        alias="X-Organization-ID",
    ),
    db: Session = Depends(get_db),
    user: User = Depends(get_authenticated_user),
) -> UserPrincipal:

    # The user is already authenticated and registered.
    # Now resolve their organization membership.

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
        {"user_id": str(user.id)},
    )

    membership_statement = (
        select(
            OrganizationMembership,
            Organization,
        )
        .join(
            Organization,
            Organization.id
            == OrganizationMembership.organization_id,
        )
        .where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.status == "active",
            Organization.is_active.is_(True),
        )
    )

    if organization_id is not None:
        membership_statement = membership_statement.where(
            OrganizationMembership.organization_id == organization_id
        )

    try:
        memberships = db.execute(
            membership_statement
        ).all()

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to resolve organization membership.",
        ) from exc

    if not memberships:
        raise HTTPException(
            status_code=403,
            detail="No active membership found for this organization.",
        )

    if len(memberships) > 1:
        raise HTTPException(
            status_code=400,
            detail=(
                "Multiple organization memberships found. "
                "Select an organization using X-Organization-ID."
            ),
        )

    membership, organization = memberships[0]

    db.execute(
        text(
            """
            SELECT
                set_config('app.current_org_id', :org_id, true),
                set_config('app.current_org_role', :role, true)
            """
        ),
        {
            "org_id": str(organization.id),
            "role": membership.role,
        },
    )

    return UserPrincipal(
        user_id=user.id,
        organization_id=organization.id,
        role=membership.role,
        is_active=user.is_active,
    )
