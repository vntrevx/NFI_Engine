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
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    opened_at: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
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
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    price: Mapped[str] = mapped_column(String(80), nullable=False)
    quantity: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False, index=True)


class PositionRow(Base):
    __tablename__: str = "positions"

    position_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    trade_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    pair: Mapped[str] = mapped_column(String(40), nullable=False)
    side: Mapped[str] = mapped_column(String(16), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    quantity: Mapped[str] = mapped_column(String(80), nullable=False)
    entry_price: Mapped[str] = mapped_column(String(80), nullable=False)
    leverage: Mapped[str] = mapped_column(String(80), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False, index=True)


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


class ExecutionIntentRow(Base):
    __tablename__: str = "execution_intents"

    intent_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    client_order_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    pair: Mapped[str] = mapped_column(String(40), nullable=False)
    side: Mapped[str] = mapped_column(String(16), nullable=False)
    order_type: Mapped[str] = mapped_column(String(16), nullable=False)
    requested_quantity: Mapped[str] = mapped_column(String(80), nullable=False)
    requested_price: Mapped[str | None] = mapped_column(String(80), nullable=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    raw_status_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    exchange_created_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    exchange_updated_at: Mapped[str | None] = mapped_column(String(40), nullable=True)


class ExecutionOrderRow(Base):
    __tablename__: str = "execution_orders"

    execution_order_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    intent_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    client_order_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    exchange_order_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    pair: Mapped[str] = mapped_column(String(40), nullable=False)
    side: Mapped[str] = mapped_column(String(16), nullable=False)
    order_type: Mapped[str] = mapped_column(String(16), nullable=False)
    requested_quantity: Mapped[str] = mapped_column(String(80), nullable=False)
    requested_price: Mapped[str | None] = mapped_column(String(80), nullable=True)
    filled_quantity: Mapped[str] = mapped_column(String(80), nullable=False)
    average_fill_price: Mapped[str | None] = mapped_column(String(80), nullable=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    raw_status_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    exchange_created_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    exchange_updated_at: Mapped[str | None] = mapped_column(String(40), nullable=True)


class ExecutionFillRow(Base):
    __tablename__: str = "execution_fills"

    execution_fill_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    intent_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    execution_order_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    exchange_order_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    pair: Mapped[str] = mapped_column(String(40), nullable=False)
    side: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[str] = mapped_column(String(80), nullable=False)
    price: Mapped[str] = mapped_column(String(80), nullable=False)
    fee_asset: Mapped[str | None] = mapped_column(String(24), nullable=True)
    fee_amount: Mapped[str | None] = mapped_column(String(80), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False)
    filled_at: Mapped[str] = mapped_column(String(40), nullable=False, index=True)


class ExecutionEventRow(Base):
    __tablename__: str = "execution_events"

    event_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    intent_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_status_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
