"""SQLite storage — StoragePort implementation."""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from src.domain.models import Opportunity, Quote
from src.domain.ports import StoragePort

logger = logging.getLogger(__name__)


class SqliteRepository(StoragePort):
    """Persists quotes and opportunities in SQLite."""

    def __init__(self, db_path: str | Path = "./surge.db") -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    price REAL NOT NULL,
                    currency TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    previous_close REAL
                );
                CREATE INDEX IF NOT EXISTS idx_quotes_ticker_ts ON quotes(ticker, timestamp DESC);

                CREATE TABLE IF NOT EXISTS opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    price REAL NOT NULL,
                    currency TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    previous_close REAL,
                    drop_pct REAL NOT NULL,
                    threshold_pct REAL NOT NULL,
                    detected_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_opps_detected ON opportunities(detected_at DESC);
                """)

    def save_quote(self, quote: Quote) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO quotes "
                "(ticker, price, currency, timestamp, source, previous_close) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    quote.ticker,
                    quote.price,
                    quote.currency,
                    quote.timestamp.isoformat(),
                    quote.source,
                    quote.previous_close,
                ),
            )
            conn.commit()

    def get_last_quote(self, ticker: str) -> Quote | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM quotes WHERE ticker = ? ORDER BY timestamp DESC LIMIT 1",
                (ticker.upper(),),
            ).fetchone()
            if row is None:
                return None
            return Quote(
                ticker=row["ticker"],
                price=row["price"],
                currency=row["currency"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                source=row["source"],
                previous_close=row["previous_close"],
            )

    def save_opportunity(self, opportunity: Opportunity) -> None:
        q = opportunity.quote
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO opportunities
                   (ticker, price, currency, timestamp, source,
                    previous_close, drop_pct, threshold_pct, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    q.ticker,
                    q.price,
                    q.currency,
                    q.timestamp.isoformat(),
                    q.source,
                    q.previous_close,
                    opportunity.drop_pct,
                    opportunity.threshold_pct,
                    opportunity.detected_at.isoformat(),
                ),
            )
            conn.commit()

    def get_recent_opportunities(self, limit: int = 20) -> list[Opportunity]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM opportunities ORDER BY detected_at DESC LIMIT ?", (limit,)
            ).fetchall()
            result: list[Opportunity] = []
            for row in rows:
                quote = Quote(
                    ticker=row["ticker"],
                    price=row["price"],
                    currency=row["currency"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    source=row["source"],
                    previous_close=row["previous_close"],
                )
                result.append(
                    Opportunity(
                        quote=quote,
                        drop_pct=row["drop_pct"],
                        threshold_pct=row["threshold_pct"],
                        detected_at=datetime.fromisoformat(row["detected_at"]),
                    )
                )
            return result
