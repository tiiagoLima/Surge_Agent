"""Investment scanner — detects significant drops and notifies."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from surge.domain.models import Opportunity
from surge.domain.ports import NotificationPort, QuotePort, StoragePort

logger = logging.getLogger(__name__)


class InvestmentScannerUseCase:
    """Scans tickers for significant drops.

    Depends only on ports — no concrete adapters instantiated here.

    Args:
        quote_port: Fetches market quotes.
        notification_port: Sends alerts (can be composite).
        storage_port: Persists quotes/opportunities.
        drop_threshold_pct: Minimum drop (%) to trigger opportunity. Positive value.
    """

    def __init__(
        self,
        quote_port: QuotePort,
        notification_port: NotificationPort,
        storage_port: StoragePort,
        drop_threshold_pct: float = 5.0,
    ) -> None:
        if drop_threshold_pct <= 0:
            raise ValueError("drop_threshold_pct must be > 0")
        self._quote_port = quote_port
        self._notification_port = notification_port
        self._storage_port = storage_port
        self._threshold = drop_threshold_pct

    @property
    def threshold(self) -> float:
        return self._threshold

    def execute(self, tickers: list[str]) -> list[Opportunity]:
        """Scan tickers, persist quotes, return detected opportunities.

        Side effects: saves each fetched quote and each opportunity via StoragePort,
        then notifies via NotificationPort when opportunities found.

        Args:
            tickers: Symbols to scan (e.g. ["PETR4.SA", "AAPL"]). Empty -> no-op.

        Returns:
            List of detected opportunities (may be empty).
        """
        if not tickers:
            logger.info("No tickers to scan")
            return []

        opportunities: list[Opportunity] = []
        now = datetime.now(UTC)

        for ticker in tickers:
            quote = self._quote_port.get_quote(ticker)
            if quote is None:
                logger.warning("No quote for %s — skipping", ticker)
                continue

            # Persist quote for history/comparison
            try:
                self._storage_port.save_quote(quote)
            except Exception:
                logger.exception("Failed to save quote for %s", ticker)

            if quote.is_significant_drop(self._threshold):
                drop = quote.drop_pct()
                assert drop is not None
                opp = Opportunity(
                    quote=quote,
                    drop_pct=drop,
                    threshold_pct=self._threshold,
                    detected_at=now,
                )
                opportunities.append(opp)
                try:
                    self._storage_port.save_opportunity(opp)
                except Exception:
                    logger.exception("Failed to save opportunity for %s", ticker)
                logger.info("Opportunity: %s", opp.summary())
            else:
                drop = quote.drop_pct()
                logger.debug(
                    "No opportunity for %s: drop=%s threshold=%.1f",
                    ticker,
                    f"{drop:.2f}%" if drop is not None else "N/A",
                    self._threshold,
                )

        if opportunities:
            try:
                self._notification_port.notify(opportunities)
            except Exception:
                logger.exception("Notification failed")
                try:
                    self._notification_port.notify_error(
                        f"Surge: falha ao notificar {len(opportunities)} oportunidades"
                    )
                except Exception:
                    logger.exception("notify_error also failed")
        else:
            logger.info("Scan complete — no opportunities")

        return opportunities
