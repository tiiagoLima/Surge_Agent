"""Composite QuotePort — tries primary, falls back to secondary."""

from __future__ import annotations

import logging

from surge.domain.models import Quote
from surge.domain.ports import QuotePort

logger = logging.getLogger(__name__)


class CompositeQuoteAdapter(QuotePort):
    """Tries primary QuotePort, falls back to secondary on None."""

    def __init__(self, primary: QuotePort, fallback: QuotePort) -> None:
        self._primary = primary
        self._fallback = fallback

    def get_quote(self, ticker: str) -> Quote | None:
        quote = self._primary.get_quote(ticker)
        if quote is not None:
            return quote
        logger.info("Primary quote failed for %s — trying fallback", ticker)
        return self._fallback.get_quote(ticker)
