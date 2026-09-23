"""Unit tests for config parsing."""

from src.config import Settings


def test_tickers_parsing():
    s = Settings(SURGE_WATCHLIST=" PETR4.SA, vale3.sa , AAPL ")  # type: ignore[call-arg]
    assert s.tickers == ["PETR4.SA", "VALE3.SA", "AAPL"]


def test_tickers_empty():
    s = Settings(SURGE_WATCHLIST="")  # type: ignore[call-arg]
    assert s.tickers == []


def test_drop_threshold_default():
    s = Settings()  # type: ignore[call-arg]
    assert s.drop_threshold == 5.0
