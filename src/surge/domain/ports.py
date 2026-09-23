"""Ports — abstract interfaces (Hexagonal). Domain defines, adapters implement."""

from __future__ import annotations

from abc import ABC, abstractmethod

from surge.domain.models import Opportunity, Quote


class QuotePort(ABC):
    """Fetches market quotes for tickers."""

    @abstractmethod
    def get_quote(self, ticker: str) -> Quote | None:
        """Return latest Quote for ticker, or None if unavailable."""

    def get_quotes(self, tickers: list[str]) -> list[Quote]:
        """Batch fetch — default sequential implementation. Adapters may override."""
        result: list[Quote] = []
        for t in tickers:
            q = self.get_quote(t)
            if q is not None:
                result.append(q)
        return result


class NotificationPort(ABC):
    """Sends notifications about opportunities."""

    @abstractmethod
    def notify(self, opportunities: list[Opportunity]) -> None:
        """Notify about detected opportunities. No-op when list empty."""

    @abstractmethod
    def notify_error(self, message: str) -> None:
        """Notify about a system error (optional channel)."""


class StoragePort(ABC):
    """Persists quotes/opportunities and retrieves history."""

    @abstractmethod
    def save_quote(self, quote: Quote) -> None:
        """Persist a quote for later comparison."""

    @abstractmethod
    def get_last_quote(self, ticker: str) -> Quote | None:
        """Return most recent stored quote for ticker, or None."""

    @abstractmethod
    def save_opportunity(self, opportunity: Opportunity) -> None:
        """Persist a detected opportunity."""

    def get_recent_opportunities(self, limit: int = 20) -> list[Opportunity]:
        """Optional: return recent opportunities."""
        return []
