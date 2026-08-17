import json
import logging
from typing import Any

import httpx
from pydantic import ValidationError

from app.analysis.models import StructuredAnalysis
from app.analysis.provider import AnalysisProviderError
from app.config import get_settings
from app.observability import LLM_REQUESTS


def post_json(
    *, client: httpx.Client, provider: str, url: str, headers: dict[str, str], payload: dict
) -> dict[str, Any]:
    try:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        LLM_REQUESTS.labels(provider, "success").inc()
        _warn_if_quota_low(provider, response.headers)
        return response.json()
    except httpx.HTTPStatusError as exception:
        status = exception.response.status_code
        LLM_REQUESTS.labels(provider, f"http_{status}").inc()
        raise AnalysisProviderError(provider, f"http_{status}", status_code=status) from exception
    except (httpx.HTTPError, ValueError) as exception:
        LLM_REQUESTS.labels(provider, "request_failed").inc()
        raise AnalysisProviderError(provider, "request_failed") from exception


def _warn_if_quota_low(provider: str, headers: httpx.Headers) -> None:
    try:
        limit = int(headers.get("x-ratelimit-limit-requests", "0"))
        remaining = int(headers.get("x-ratelimit-remaining-requests", "0"))
    except ValueError:
        return
    if limit and remaining / limit <= get_settings().quota_warning_ratio:
        logging.getLogger("ataviva.quota").warning(
            "provider_quota_low",
            extra={"provider": provider, "remaining_requests": remaining, "limit_requests": limit},
        )


def validate_analysis(provider: str, raw_json: str) -> StructuredAnalysis:
    try:
        return StructuredAnalysis.model_validate(json.loads(raw_json))
    except (json.JSONDecodeError, ValidationError) as exception:
        raise AnalysisProviderError(provider, "invalid_structured_output") from exception
