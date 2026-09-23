"""Composition root — Surge.

Wires adapters into use cases. No business logic here.
Inbound adapter (CLI) is agnostic — same use cases can be called by Telegram later.
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
from src.application.portfolio.manage_portfolio_use_case import ManagePortfolioUseCase
from src.application.portfolio.scan_portfolio_use_case import ScanPortfolioUseCase
from src.application.radar.market_radar_use_case import MarketRadarUseCase
from src.config import get_settings

logger = logging.getLogger(__name__)


def _build_ports():
    """Build all adapters. Returns ports tuple."""
    settings = get_settings()
    yf = YFinanceAdapter()
    brapi = BrapiAdapter(base_url=settings.brapi_base_url, token=settings.brapi_token or None)
    quote_port = CompositeQuoteAdapter(primary=yf, fallback=brapi)
    # SqliteRepository implements StoragePort and PortfolioPort (ISP)
    repo = SqliteRepository(db_path=settings.db_path)

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
    if not notifiers:
        notifiers.append(EmailNotifier("", 0, "", "", "", "", enabled=False))

    notification_port = CompositeNotifier(notifiers)
    return settings, repo, quote_port, brapi, notification_port, repo


def build_legacy_use_case() -> tuple[InvestmentScannerUseCase, list[str]]:
    """Legacy builder for SURGE_WATCHLIST env-based scan."""
    settings, _, quote_port, _, notification_port, storage_port = _build_ports()
    use_case = InvestmentScannerUseCase(
        quote_port=quote_port,
        notification_port=notification_port,
        storage_port=storage_port,
        drop_threshold_pct=settings.drop_threshold,
    )
    return use_case, settings.tickers


def build_manage_portfolio_use_case() -> ManagePortfolioUseCase:
    _, portfolio_port, quote_port, _, _, _ = _build_ports()
    return ManagePortfolioUseCase(portfolio_port=portfolio_port, quote_port=quote_port)


def build_scan_portfolio_use_case() -> ScanPortfolioUseCase:
    settings, portfolio_port, quote_port, _, notification_port, storage_port = _build_ports()
    return ScanPortfolioUseCase(
        portfolio_port=portfolio_port,
        quote_port=quote_port,
        notification_port=notification_port,
        storage_port=storage_port,
        drop_threshold_pct=settings.drop_threshold,
    )


def build_market_radar_use_case() -> MarketRadarUseCase:
    settings, portfolio_port, _, market_port, notification_port, storage_port = _build_ports()
    return MarketRadarUseCase(
        portfolio_port=portfolio_port,
        market_quote_port=market_port,
        notification_port=notification_port,
        storage_port=storage_port,
        drop_threshold_pct=settings.drop_threshold,
    )


def run_once_legacy() -> None:
    """Run single scan via legacy env watchlist."""
    use_case, tickers = build_legacy_use_case()
    if not tickers:
        logger.warning(
            "SURGE_WATCHLIST vazia — nada para escanear. "
            "Use 'surge portfolio add' ou 'surge scan --portfolio/--radar'"
        )
        return
    logger.info("Surge legacy scan: %d tickers, threshold=%.1f%%", len(tickers), use_case.threshold)
    opps = use_case.execute(tickers)
    logger.info("Surge scan done: %d oportunidades", len(opps))
    for opp in opps:
        print(f"  - {opp.summary()}")


def run_scheduler() -> None:
    """Run with APScheduler (blocking) — scans portfolio + radar daily."""
    settings = get_settings()
    scan_portfolio = build_scan_portfolio_use_case()
    radar = build_market_radar_use_case()

    def job() -> None:
        logger.info("Surge scheduled scan triggered")
        try:
            opps_p = scan_portfolio.execute()
            logger.info("Scheduled portfolio scan: %d opps", len(opps_p))
        except Exception:
            logger.exception("Scheduled portfolio scan failed")
        try:
            opps_r = radar.execute()
            logger.info("Scheduled radar scan: %d opps", len(opps_r))
        except Exception:
            logger.exception("Scheduled radar scan failed")

    logger.info("Surge starting — running initial scheduled scan")
    job()

    trigger = SchedulerTrigger(timezone=settings.timezone)
    trigger.schedule_daily(job, hour=settings.cron_hour, minute=settings.cron_minute)
    trigger.start()


def main() -> None:
    parser = argparse.ArgumentParser(prog="surge", description="Surge — Personal Automation Hub")
    parser.add_argument(
        "--log-level", default=None, help="Override log level (DEBUG, INFO, WARNING)"
    )
    # Legacy flag at top-level for backward compat
    parser.add_argument(
        "--once",
        action="store_true",
        help="Legacy: single scan via SURGE_WATCHLIST (use scan --portfolio)",
    )

    subparsers = parser.add_subparsers(dest="command")

    # portfolio subcommand
    p_parser = subparsers.add_parser(
        "portfolio", help="Manage holdings (agnostic — CLI is just inbound adapter)"
    )
    p_sub = p_parser.add_subparsers(dest="portfolio_cmd", required=True)
    p_add = p_sub.add_parser("add", help="Add holding (validates via Brapi)")
    p_add.add_argument("ticker", help="Ticker e.g. PETR4.SA")
    p_add.add_argument("--qty", type=float, required=True, help="Quantity")
    p_add.add_argument("--avg", type=float, default=None, help="Average price")
    p_add.add_argument("--currency", default="BRL", help="Currency (default BRL)")
    p_sub.add_parser("list", help="List holdings")
    p_rm = p_sub.add_parser("remove", help="Remove holding")
    p_rm.add_argument("ticker", help="Ticker")
    p_get = p_sub.add_parser("get", help="Show holding")
    p_get.add_argument("ticker", help="Ticker")

    # scan subcommand
    s_parser = subparsers.add_parser("scan", help="Run scans")
    s_parser.add_argument("--portfolio", action="store_true", help="Scan portfolio holdings")
    s_parser.add_argument(
        "--radar", action="store_true", help="Scan market radar (Brapi list, excludes holdings)"
    )
    # --once legacy inside scan as well
    s_parser.add_argument("--once", action="store_true", help="Single run (default)")

    args = parser.parse_args()

    settings = get_settings()
    level = (args.log_level or settings.log_level).upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    # No subcommand -> legacy behavior or scheduler
    if args.command is None:
        print("Surge -- Personal Automation Hub")
        holdings_preview = build_manage_portfolio_use_case().list()
        watch = settings.tickers or [h.ticker for h in holdings_preview] or "(vazia)"
        print(f"   holdings={watch} threshold={settings.drop_threshold}%")
        if args.once:
            run_once_legacy()
        else:
            run_scheduler()
        return

    if args.command == "portfolio":
        uc = build_manage_portfolio_use_case()
        if args.portfolio_cmd == "add":
            try:
                h = uc.add(
                    args.ticker, quantity=args.qty, avg_price=args.avg, currency=args.currency
                )
                print(
                    f"Holding adicionado: {h.ticker} "
                    f"qty={h.quantity} avg={h.avg_price} {h.currency}"
                )
            except ValueError as e:
                print(f"Erro: {e}", file=sys.stderr)
                sys.exit(1)
        elif args.portfolio_cmd == "list":
            holdings = uc.list()
            if not holdings:
                print("Carteira vazia. Use 'surge portfolio add TICKER --qty N'")
            else:
                for h in holdings:
                    avg = f" avg={h.avg_price:.2f}" if h.avg_price is not None else ""
                    print(
                        f"{h.ticker:12} qty={h.quantity:g}{avg} {h.currency} (desde {h.added_at})"
                    )
        elif args.portfolio_cmd == "remove":
            removed = uc.remove(args.ticker)
            if removed:
                print(f"Removido {args.ticker.upper()}")
            else:
                print(f"Ticker não encontrado: {args.ticker}", file=sys.stderr)
                sys.exit(1)
        elif args.portfolio_cmd == "get":
            h = uc.get(args.ticker)
            if h is None:
                print(f"Não encontrado: {args.ticker}", file=sys.stderr)
                sys.exit(1)
            print(f"{h.ticker} qty={h.quantity} avg={h.avg_price} {h.currency} added={h.added_at}")
        return

    if args.command == "scan":
        # default if no flag: run both
        do_portfolio = args.portfolio or not args.radar
        do_radar = args.radar or not args.portfolio
        # Actually if neither flagged, run both. If one flagged, run only that.
        if not args.portfolio and not args.radar:
            do_portfolio = do_radar = True
        if do_portfolio:
            print("Scanning portfolio...")
            uc = build_scan_portfolio_use_case()
            opps = uc.execute()
            print(f"Portfolio: {len(opps)} oportunidades")
            for o in opps:
                print(f"  - {o.summary()}")
        if do_radar:
            print("Scanning market radar (Brapi)...")
            uc = build_market_radar_use_case()
            opps = uc.execute()
            print(f"Radar: {len(opps)} oportunidades")
            for o in opps:
                print(f"  - {o.summary()}")
        return


if __name__ == "__main__":
    main()
