from __future__ import annotations
from zipfile import BadZipFile
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

DATABASE_FILE = Path(__file__).with_name("database.xlsx")
PRICE_COLUMNS = ["item", "price"]
LOG_COLUMNS = ["date", "items bought", "cash received", "change"]

BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BASE_DIR / "database.xlsx"


DEFAULT_PRICES = pd.DataFrame(
    {
        "item": [
            "Adjustable Wrench",
            "Claw Hammer",
            "Electrical Tape",
            "Measuring Tape",
            "Paint Brush",
            "Phillips Screwdriver",
            "PVC Pipe 1 metre",
            "Wall Plug Pack",
        ],
        "price": [
            189000,
            225000,
            32000,
            129000,
            75000,
            89000,
            65000,
            48000,
        ],
    }
)

EMPTY_LOGS = pd.DataFrame(
    columns=[
        "date",
        "items bought",
        "cash received",
        "change",
    ]
)


def create_database():
    """Create a fresh and valid Excel database."""
    prices = DEFAULT_PRICES.sort_values(
        by="item",
        key=lambda column: column.str.lower(),
    ).reset_index(drop=True)

    with pd.ExcelWriter(
        DATABASE_FILE,
        engine="openpyxl",
        mode="w",
    ) as writer:
        prices.to_excel(
            writer,
            sheet_name="prices",
            index=False,
        )

        EMPTY_LOGS.to_excel(
            writer,
            sheet_name="logs",
            index=False,
        )


def ensure_database():
    """Ensure that database.xlsx exists and is a valid Excel file."""
    if not DATABASE_FILE.exists():
        create_database()
        return

    try:
        prices = pd.read_excel(
            DATABASE_FILE,
            sheet_name="prices",
        )

        logs = pd.read_excel(
            DATABASE_FILE,
            sheet_name="logs",
        )

        required_price_columns = {"item", "price"}
        required_log_columns = {
            "date",
            "items bought",
            "cash received",
            "change",
        }

        if not required_price_columns.issubset(prices.columns):
            raise ValueError("The prices sheet has invalid columns.")

        if not required_log_columns.issubset(logs.columns):
            raise ValueError("The logs sheet has invalid columns.")

    except (
        BadZipFile,
        ValueError,
        KeyError,
        OSError,
    ):
        # Rename the damaged file instead of immediately deleting it.
        damaged_file = DATABASE_FILE.with_name(
            "database_corrupted.xlsx"
        )

        if damaged_file.exists():
            damaged_file.unlink()

        DATABASE_FILE.rename(damaged_file)
        create_database()

def format_rupiah(value: float) -> str:
    """Format a numeric value as Indonesian rupiah without decimal cents."""
    rounded = int(round(float(value)))
    return f"Rp {rounded:,}".replace(",", ".")

def _normalize_prices(prices: pd.DataFrame) -> pd.DataFrame:
    prices = prices.reindex(columns=PRICE_COLUMNS).copy()
    prices["item"] = prices["item"].fillna("").astype(str).str.strip()
    prices["price"] = pd.to_numeric(prices["price"], errors="coerce")
    prices = prices[(prices["item"] != "") & prices["price"].notna()]
    return prices.sort_values("item", key=lambda s: s.str.casefold()).reset_index(drop=True)


def _normalize_logs(logs: pd.DataFrame) -> pd.DataFrame:
    logs = logs.reindex(columns=LOG_COLUMNS).copy()
    logs["date"] = pd.to_datetime(logs["date"], errors="coerce")
    logs["cash received"] = pd.to_numeric(logs["cash received"], errors="coerce").fillna(0.0)
    logs["change"] = pd.to_numeric(logs["change"], errors="coerce").fillna(0.0)
    logs["items bought"] = logs["items bought"].fillna("[]").astype(str)
    logs = logs[logs["date"].notna()]
    return logs.sort_values("date", ascending=False).reset_index(drop=True)


def _write_workbook(prices: pd.DataFrame, logs: pd.DataFrame) -> None:
    prices = _normalize_prices(prices)
    logs = _normalize_logs(logs)
    with pd.ExcelWriter(DATABASE_FILE, engine="openpyxl", mode="w") as writer:
        prices.to_excel(writer, sheet_name="prices", index=False)
        logs.to_excel(writer, sheet_name="logs", index=False)


def load_prices() -> pd.DataFrame:
    ensure_database()
    return _normalize_prices(pd.read_excel(DATABASE_FILE, sheet_name="prices"))


def load_logs(include_row_id: bool = False) -> pd.DataFrame:
    ensure_database()
    logs = _normalize_logs(pd.read_excel(DATABASE_FILE, sheet_name="logs"))
    if include_row_id:
        logs = logs.copy()
        logs["_row_id"] = range(len(logs))
    return logs


def save_transaction(items: list[dict[str, Any]], cash_received: float, change: float) -> None:
    prices = load_prices()
    logs = load_logs()
    new_row = pd.DataFrame(
        [{
            "date": datetime.now(),
            "items bought": json.dumps(items, ensure_ascii=False),
            "cash received": float(cash_received),
            "change": float(change),
        }]
    )
    logs = pd.concat([logs, new_row], ignore_index=True)
    _write_workbook(prices, logs)


def update_transaction(row_id: int, date_value: datetime, items: list[dict[str, Any]], cash_received: float, change: float) -> None:
    prices = load_prices()
    logs = load_logs()
    if row_id < 0 or row_id >= len(logs):
        raise IndexError("Transaction no longer exists.")
    logs.loc[row_id, "date"] = pd.Timestamp(date_value)
    logs.loc[row_id, "items bought"] = json.dumps(items, ensure_ascii=False)
    logs.loc[row_id, "cash received"] = float(cash_received)
    logs.loc[row_id, "change"] = float(change)
    _write_workbook(prices, logs)


def delete_transaction(row_id: int) -> None:
    prices = load_prices()
    logs = load_logs()
    if row_id < 0 or row_id >= len(logs):
        raise IndexError("Transaction no longer exists.")
    logs = logs.drop(index=row_id).reset_index(drop=True)
    _write_workbook(prices, logs)


def parse_items(value: str) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def transaction_total(items: list[dict[str, Any]]) -> float:
    return round(sum(float(item.get("subtotal", 0)) for item in items), 2)
