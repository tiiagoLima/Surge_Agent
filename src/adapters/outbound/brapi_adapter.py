"""BRAPI adapter — fallback QuotePort for B3 tickers."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import requests

from src.domain.models import Quote
from src.domain.ports import QuotePort

logger = logging.getLogger(__name__)


class BrapiAdapter(QuotePort):
    """Fetches quotes via brapi.dev (good for B3)."""

    def __init__(
        self,
        base_url: str = "https://brapi.dev",
        token: str | None = None,
        timeout: int = 10,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout

    def get_quote(self, ticker: str) -> Quote | None:
        # Normalize: brapi expects without .SA for B3, but accepts with
        clean = ticker.upper().replace(".SA", "")
        url = f"{self._base_url}/api/quote/{clean}"
        params: dict[str, str] = {}
        if self._token:
            params["token"] = self._token

        try:
            resp = requests.get(url, params=params, timeout=self._timeout)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results") or []
            if not results:
                logger.warning("brapi: no results for %s", ticker)
                return None
            r = results[0]
            price = r.get("regularMarketPrice")
            prev_close = r.get("regularMarketPreviousClose")
            currency = r.get("currency", "BRL")

            if price is None:
                return None

            return Quote(
                ticker=ticker.upper(),
                price=float(price),
                currency=str(currency).upper(),
                timestamp=datetime.now(UTC),
                source="brapi",
                previous_close=float(prev_close) if prev_close is not None else None,
            )
        except Exception:
            logger.exception("brapi error for %s", ticker)
            return None
