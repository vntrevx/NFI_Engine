from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TradeRow(Base):
    __tablename__: str = "trades"

    trade_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    pair: Mapped[str] = mapped_column(String(40), nullable=False)
    side: Mapped[str] = mapped_column(String(16), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    opened_at: Mapped[str] = mapped_column(String(40), nullable=False)
    closed_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    entry_price: Mapped[str] = mapped_column(String(80), nullable=False)
    exit_price: Mapped[str | None] = mapped_column(String(80), nullable=True)
    quantity: Mapped[str] = mapped_column(String(80), nullable=False)
    leverage: Mapped[str] = mapped_column(String(80), nullable=False)
    profit: Mapped[str] = mapped_column(String(80), nullable=False)


class OrderRow(Base):
    __tablename__: str = "orders"

    order_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    trade_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    pair: Mapped[str] = mapped_column(String(40), nullable=False)
    side: Mapped[str] = mapped_column(String(16), nullable=False)
    order_type: Mapped[str] = mapped_column(String(16), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    price: Mapped[str] = mapped_column(String(80), nullable=False)
    quantity: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class PositionRow(Base):
    __tablename__: str = "positions"

    position_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    trade_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    pair: Mapped[str] = mapped_column(String(40), nullable=False)
    side: Mapped[str] = mapped_column(String(16), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[str] = mapped_column(String(80), nullable=False)
    entry_price: Mapped[str] = mapped_column(String(80), nullable=False)
    leverage: Mapped[str] = mapped_column(String(80), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False)


class LockRow(Base):
    __tablename__: str = "locks"

    name: Mapped[str] = mapped_column(String(80), primary_key=True)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    acquired_at: Mapped[str] = mapped_column(String(40), nullable=False)
    expires_at: Mapped[str] = mapped_column(String(40), nullable=False)


class EquitySnapshotRow(Base):
    __tablename__: str = "equity_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    captured_at: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    equity: Mapped[str] = mapped_column(String(80), nullable=False)
    available: Mapped[str] = mapped_column(String(80), nullable=False)


class StrategyCustomDataRow(Base):
    __tablename__: str = "strategy_custom_data"

    strategy_name: Mapped[str] = mapped_column(String(120), primary_key=True)
    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False)


class BotStateRow(Base):
    __tablename__: str = "bot_state"

    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)
