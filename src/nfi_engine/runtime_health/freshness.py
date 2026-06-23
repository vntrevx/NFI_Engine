from __future__ import annotations

from datetime import UTC, datetime

from nfi_engine.dashboard import DashboardReadModels


def latest_dashboard_at(read_models: DashboardReadModels) -> datetime | None:
    timestamps = (
        tuple(point.at for point in read_models.equity_points)
        + tuple(point.at for point in read_models.price_points)
        + tuple(position.updated_at for position in read_models.open_positions)
        + tuple(trade.opened_at for trade in read_models.recent_trades)
        + tuple(
            trade.closed_at for trade in read_models.recent_trades if trade.closed_at is not None
        )
    )
    if not timestamps:
        return None
    return max(_aware(timestamp) for timestamp in timestamps)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
