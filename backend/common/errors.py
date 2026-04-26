"""Domain error taxonomy and a DRF exception handler that produces a uniform
``{detail, code, fields}`` JSON envelope.

The envelope keeps `detail` for backward compatibility with existing frontend
callers that already do ``error.response.data.detail``, while adding ``code``
so clients can switch on a stable identifier and ``fields`` so per-field
shape errors are isolated from prose.
"""

from __future__ import annotations

from typing import Any

from rest_framework import status as http_status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_handler


class DomainError(Exception):
    """Base for application-defined errors raised from the service layer."""

    code: str = "domain_error"
    status_code: int = http_status.HTTP_400_BAD_REQUEST
    default_message: str = "Domain error"

    def __init__(
        self,
        message: str | None = None,
        *,
        fields: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message or self.default_message)
        self.fields = fields

    @property
    def detail(self) -> str:
        return str(self)


class PermissionDeniedError(DomainError):
    code = "permission_denied"
    status_code = http_status.HTTP_403_FORBIDDEN
    default_message = "Permission denied"


class IllegalStateTransition(DomainError):
    code = "illegal_state_transition"
    status_code = http_status.HTTP_400_BAD_REQUEST
    default_message = "Illegal state transition"


class NotFoundError(DomainError):
    code = "not_found"
    status_code = http_status.HTTP_404_NOT_FOUND
    default_message = "Not found"


class ConflictError(DomainError):
    code = "conflict"
    status_code = http_status.HTTP_409_CONFLICT
    default_message = "Conflict"


def _envelope(detail: str, code: str, fields: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"detail": detail, "code": code, "fields": fields}


def _coerce_drf_response(response: Response) -> Response:
    data = response.data
    if isinstance(data, dict) and "detail" in data and "code" in data and "fields" in data:
        return response

    if isinstance(data, dict):
        detail_value = data.get("detail")
        if isinstance(detail_value, str) and len(data) == 1:
            response.data = _envelope(detail_value, code="error")
            return response
        # Field-level validation: `{field: [...]}`
        first_field, first_messages = next(iter(data.items()))
        first_message = (
            first_messages[0]
            if isinstance(first_messages, list) and first_messages
            else str(first_messages)
        )
        response.data = _envelope(
            detail=str(first_message),
            code="validation_error",
            fields=data,
        )
        return response

    if isinstance(data, list):
        first = data[0] if data else "Validation error"
        response.data = _envelope(detail=str(first), code="validation_error")
        return response

    response.data = _envelope(detail=str(data), code="error")
    return response


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """DRF exception handler producing the uniform error envelope.

    Order of precedence:
    1. ``DomainError`` subclasses are rendered directly with their own status.
    2. Anything DRF already understands (validation, auth, etc.) is delegated
       to DRF's default handler, then the response payload is normalized.
    3. Anything we don't recognize falls through to Django's 500 handler.
    """

    if isinstance(exc, DomainError):
        return Response(
            _envelope(detail=exc.detail, code=exc.code, fields=exc.fields),
            status=exc.status_code,
        )

    response = drf_default_handler(exc, context)
    if response is None:
        return None

    response = _coerce_drf_response(response)

    # Override the inferred ``code`` with DRF's well-known codes (e.g.
    # ``not_authenticated``, ``permission_denied``, ``not_found``,
    # ``throttled``) when DRF supplied one. ``validation_error`` is kept as
    # a stable identifier across DRF versions instead of DRF's own
    # ``invalid``.
    drf_code = getattr(exc, "default_code", None) if isinstance(exc, APIException) else None
    if (
        isinstance(response.data, dict)
        and drf_code
        and drf_code != "invalid"
        and response.data.get("code") == "error"
    ):
        response.data["code"] = drf_code
    return response
