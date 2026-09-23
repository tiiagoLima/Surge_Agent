"""Unit tests for domain models."""

from datetime import UTC, datetime

from src.domain.models import Opportunity, Quote


def _quote(price: float = 95.0, prev: float = 100.0) -> Quote:
    return Quote(
        ticker="PETR4.SA",
        price=price,
        currency="BRL",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        source="test",
        previous_close=prev,
    )


def test_drop_pct():
    q = _quote(95, 100)
    assert q.drop_pct() == -5.0


def test_drop_pct_none_when_no_prev():
    q = _quote(95, 100)
    q2 = Quote(
        ticker="AAPL",
        price=150,
        currency="USD",
        timestamp=q.timestamp,
        source="t",
        previous_close=None,
    )
    assert q2.drop_pct() is None


def test_is_significant_drop():
    assert _quote(94, 100).is_significant_drop(5.0) is True
    assert _quote(96, 100).is_significant_drop(5.0) is False
    assert _quote(100, 100).is_significant_drop(5.0) is False


def test_opportunity_summary():
    q = _quote(90, 100)
    opp = Opportunity(quote=q, drop_pct=-10.0, threshold_pct=5.0, detected_at=q.timestamp)
    assert "PETR4.SA" in opp.summary()
    assert "10.00%" in opp.summary()
