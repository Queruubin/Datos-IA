"""Official TRM (Tasa Representativa del Mercado, USD → COP) from datos.gov.co, implementing
`ExchangeRatePort`.

Dataset 32sa-8pi3 (Socrata) publishes one row per validity period with `valor`, `vigenciadesde`
and `vigenciahasta`. The rate for the next business day is published in advance, so the query
asks for the latest row whose `vigenciadesde` is not after today (Bogotá time) instead of simply
the latest row.
"""

import logging
import time
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta, timezone
from typing import Any

import requests

from app.domain import ExchangeRate

logger = logging.getLogger(__name__)

TRM_API_URL = "https://www.datos.gov.co/resource/32sa-8pi3.json"
TRM_SOURCE = "datos.gov.co"
BOGOTA = timezone(timedelta(hours=-5), "America/Bogota")  # Colombia has no daylight saving time
CACHE_SECONDS = 12 * 60 * 60
# After a failure, wait before asking again so a down portal does not slow every chat answer.
RETRY_AFTER_FAILURE_SECONDS = 10 * 60


class TrmParseError(ValueError):
    pass


def parse_trm(payload: Any) -> ExchangeRate:
    """First row of the Socrata JSON → ExchangeRate. Raises `TrmParseError` if unusable."""
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
        raise TrmParseError("TRM response has no rows")
    row = payload[0]
    try:
        value = float(row["valor"])
        valid_from = date.fromisoformat(str(row["vigenciadesde"])[:10])
    except (KeyError, TypeError, ValueError) as error:
        raise TrmParseError(f"Unexpected TRM row: {sorted(row)}") from error
    if value <= 0:
        raise TrmParseError("TRM value must be positive")
    return ExchangeRate(value=value, valid_from=valid_from, source=TRM_SOURCE)


class TrmClient:
    """Fetches the TRM with a short timeout and keeps it in memory for 12 h.

    On failure it uses, in order: the last good value, the `fallback` setting, or reports
    `source="unavailable"` with no value. It never invents a rate and never raises.
    """

    def __init__(
        self,
        url: str = TRM_API_URL,
        timeout_seconds: float = 5,
        fallback: float | None = None,
        session: Any | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._url = url
        self._timeout = timeout_seconds
        self._fallback = fallback
        self._session = session or requests.Session()
        self._monotonic = monotonic
        self._now = now
        self._cached: ExchangeRate | None = None
        self._cached_at: float | None = None
        self._failed_at: float | None = None

    def usd_to_cop(self) -> ExchangeRate:
        current = self._monotonic()
        if self._cached is not None and current - (self._cached_at or 0) < CACHE_SECONDS:
            return self._cached
        recently_failed = (
            self._failed_at is not None and current - self._failed_at < RETRY_AFTER_FAILURE_SECONDS
        )
        if not recently_failed:
            try:
                rate = self._fetch()
            except Exception as error:  # network, HTTP or format problems
                logger.warning("Could not fetch the TRM: %s", type(error).__name__)
                self._failed_at = current
            else:
                self._cached, self._cached_at, self._failed_at = rate, current, None
                return rate
        if self._cached is not None:
            return self._cached  # stale but real
        if self._fallback is not None and self._fallback > 0:
            return ExchangeRate(value=self._fallback, valid_from=None, source="fallback_setting")
        return ExchangeRate(value=None, valid_from=None, source="unavailable")

    def _fetch(self) -> ExchangeRate:
        today = self._now().astimezone(BOGOTA).date()
        response = self._session.get(
            self._url,
            params={
                "$order": "vigenciadesde DESC",
                "$limit": "1",
                "$where": f"vigenciadesde <= '{today.isoformat()}T00:00:00'",
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        return parse_trm(response.json())
