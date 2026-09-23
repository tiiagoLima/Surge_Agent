"""Unit tests for InvestmentScannerUseCase with fakes."""

from datetime import UTC, datetime

from surge.application.investment_scanner.use_case import InvestmentScannerUseCase
from surge.domain.models import Opportunity, Quote
from surge.domain.ports import NotificationPort, QuotePort, StoragePort


class FakeQuotePort(QuotePort):
    def __init__(self, quotes: dict[str, Quote | None]) -> None:
        self.quotes = quotes

    def get_quote(self, ticker: str) -> Quote | None:
        return self.quotes.get(ticker)


class FakeNotifier(NotificationPort):
    def __init__(self) -> None:
        self.sent: list[list[Opportunity]] = []
        self.errors: list[str] = []

    def notify(self, opportunities: list[Opportunity]) -> None:
        self.sent.append(list(opportunities))

    def notify_error(self, message: str) -> None:
        self.errors.append(message)


class FakeStorage(StoragePort):
    def __init__(self) -> None:
        self.quotes: list[Quote] = []
        self.opps: list[Opportunity] = []

    def save_quote(self, quote: Quote) -> None:
        self.quotes.append(quote)

    def get_last_quote(self, ticker: str) -> Quote | None:
        for q in reversed(self.quotes):
            if q.ticker == ticker:
                return q
        return None

    def save_opportunity(self, opportunity: Opportunity) -> None:
        self.opps.append(opportunity)


def _quote(ticker: str, price: float, prev: float) -> Quote:
    return Quote(
        ticker=ticker,
        price=price,
        currency="BRL",
        timestamp=datetime.now(UTC),
        source="fake",
        previous_close=prev,
    )


def test_detects_drop_and_notifies():
    qp = FakeQuotePort({"PETR4.SA": _quote("PETR4.SA", 90, 100)})  # -10%
    notifier = FakeNotifier()
    storage = FakeStorage()
    uc = InvestmentScannerUseCase(qp, notifier, storage, drop_threshold_pct=5.0)

    opps = uc.execute(["PETR4.SA"])

    assert len(opps) == 1
    assert opps[0].ticker == "PETR4.SA"
    assert len(notifier.sent) == 1
    assert len(storage.opps) == 1
    assert len(storage.quotes) == 1


def test_no_opportunity_when_no_drop():
    qp = FakeQuotePort({"VALE3.SA": _quote("VALE3.SA", 99, 100)})  # -1%
    notifier = FakeNotifier()
    storage = FakeStorage()
    uc = InvestmentScannerUseCase(qp, notifier, storage, drop_threshold_pct=5.0)

    opps = uc.execute(["VALE3.SA"])

    assert opps == []
    assert notifier.sent == []
    assert len(storage.quotes) == 1
    assert storage.opps == []


def test_skips_missing_quote():
    qp = FakeQuotePort({})  # no data
    notifier = FakeNotifier()
    storage = FakeStorage()
    uc = InvestmentScannerUseCase(qp, notifier, storage)

    opps = uc.execute(["UNKNOWN"])

    assert opps == []
    assert notifier.sent == []


def test_empty_tickers_noop():
    qp = FakeQuotePort({})
    notifier = FakeNotifier()
    storage = FakeStorage()
    uc = InvestmentScannerUseCase(qp, notifier, storage)

    assert uc.execute([]) == []
    assert notifier.sent == []


def test_threshold_validation():
    qp = FakeQuotePort({})
    try:
        InvestmentScannerUseCase(qp, FakeNotifier(), FakeStorage(), drop_threshold_pct=0)
        raise AssertionError("should have raised ValueError")
    except ValueError:
        pass
