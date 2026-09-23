"""Composition root — Surge.

Wires adapters into use cases. No business logic here.
"""

from __future__ import annotations

import argparse
import logging
import sys

from src.adapters.inbound.scheduler_trigger import SchedulerTrigger
from src.adapters.outbound.brapi_adapter import BrapiAdapter
from src.adapters.outbound.composite_notifier import CompositeNotifier
from src.adapters.outbound.composite_quote_adapter import CompositeQuoteAdapter
from src.adapters.outbound.email_notifier import EmailNotifier
from src.adapters.outbound.sqlite_repository import SqliteRepository
from src.adapters.outbound.telegram_notifier import TelegramNotifier
from src.adapters.outbound.yfinance_adapter import YFinanceAdapter
from src.application.investment_scanner.use_case import InvestmentScannerUseCase
from src.config import get_settings

logger = logging.getLogger(__name__)


def build_use_case() -> tuple[InvestmentScannerUseCase, list[str]]:
    """Build the investment scanner with all adapters injected."""
    settings = get_settings()

    # Quote: yfinance primary + brapi fallback
    yf = YFinanceAdapter()
    brapi = BrapiAdapter(base_url=settings.brapi_base_url, token=settings.brapi_token or None)
    quote_port = CompositeQuoteAdapter(primary=yf, fallback=brapi)

    # Notifications: email + telegram (composite fans out)
    notifiers = []
    if settings.email_enabled:
        notifiers.append(
            EmailNotifier(
                smtp_host=settings.smtp_host,
                smtp_port=settings.smtp_port,
                smtp_user=settings.smtp_user,
                smtp_password=settings.smtp_password,
                email_from=settings.email_from,
                email_to=settings.email_to,
                enabled=True,
            )
        )
    if settings.telegram_enabled:
        notifiers.append(
            TelegramNotifier(
                bot_token=settings.telegram_bot_token,
                chat_id=settings.telegram_chat_id,
                enabled=True,
            )
        )
    # Always have at least a no-op composite (logs only if empty)
    if not notifiers:
        # Use disabled notifiers so we still have a valid NotificationPort
        notifiers.append(EmailNotifier("", 0, "", "", "", "", enabled=False))

    notification_port = CompositeNotifier(notifiers)

    # Storage
    storage_port = SqliteRepository(db_path=settings.db_path)

    use_case = InvestmentScannerUseCase(
        quote_port=quote_port,
        notification_port=notification_port,
        storage_port=storage_port,
        drop_threshold_pct=settings.drop_threshold,
    )

    return use_case, settings.tickers


def run_once() -> None:
    """Run a single scan."""
    use_case, tickers = build_use_case()
    if not tickers:
        logger.warning("SURGE_WATCHLIST vazia — nada para escanear. Configure .env")
        return
    logger.info("Surge scan: %d tickers, threshold=%.1f%%", len(tickers), use_case.threshold)
    opps = use_case.execute(tickers)
    logger.info("Surge scan done: %d oportunidades", len(opps))
    for opp in opps:
        print(f"  - {opp.summary()}")


def run_scheduler() -> None:
    """Run with APScheduler (blocking)."""
    settings = get_settings()
    use_case, tickers = build_use_case()

    def job() -> None:
        if not tickers:
            logger.warning("Watchlist vazia — pulando scan agendado")
            return
        logger.info("Surge scheduled scan triggered")
        use_case.execute(tickers)

    # Run once immediately on startup for feedback
    logger.info("Surge starting — running initial scan")
    job()

    trigger = SchedulerTrigger(timezone=settings.timezone)
    trigger.schedule_daily(job, hour=settings.cron_hour, minute=settings.cron_minute)
    trigger.start()


def main() -> None:
    parser = argparse.ArgumentParser(prog="surge", description="Surge — Personal Automation Hub")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single scan and exit (default: run scheduler)",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="Override log level (DEBUG, INFO, WARNING)",
    )
    args = parser.parse_args()

    settings = get_settings()
    level = (args.log_level or settings.log_level).upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    print("Surge -- Personal Automation Hub")
    print(f"   watchlist={settings.tickers or '(vazia)'} threshold={settings.drop_threshold}%")

    if args.once:
        run_once()
    else:
        run_scheduler()


if __name__ == "__main__":
    main()
