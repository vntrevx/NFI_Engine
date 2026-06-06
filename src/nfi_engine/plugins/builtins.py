from __future__ import annotations

from nfi_engine.plugins.models import PluginGroup, PluginManifest, RegisteredPlugin

BUILTIN_SOURCE = "builtin"


def builtin_plugins() -> tuple[RegisteredPlugin, ...]:
    return tuple(_builtin(manifest) for manifest in _builtin_manifests())


def _builtin(manifest: PluginManifest) -> RegisteredPlugin:
    return RegisteredPlugin(manifest=manifest, built_in=True, source=BUILTIN_SOURCE)


def _builtin_manifests() -> tuple[PluginManifest, ...]:
    return (
        PluginManifest(
            name="adapter-smoke-strategy",
            group=PluginGroup.STRATEGY,
            version="0.1.0",
            engine_min_version="0.1.0",
            entrypoint="nfi_engine.strategy.demo:AdapterSmokeStrategy",
            description="built-in smoke strategy adapter",
        ),
        PluginManifest(
            name="simulator-exchange",
            group=PluginGroup.EXCHANGE,
            version="0.1.0",
            engine_min_version="0.1.0",
            entrypoint="nfi_engine.exchange.simulator:DeterministicExchangeSimulator",
            description="deterministic exchange simulator",
        ),
        PluginManifest(
            name="bybit-testnet-exchange",
            group=PluginGroup.EXCHANGE,
            version="0.1.0",
            engine_min_version="0.1.0",
            entrypoint="nfi_engine.exchange.bybit:BybitTestnetAdapter",
            description="Bybit testnet adapter boundary",
        ),
        PluginManifest(
            name="default-risk",
            group=PluginGroup.RISK,
            version="0.1.0",
            engine_min_version="0.1.0",
            entrypoint="nfi_engine.risk.service:quote_order",
            description="built-in risk quote service",
        ),
        PluginManifest(
            name="local-jsonl-notifier",
            group=PluginGroup.NOTIFIER,
            version="0.1.0",
            engine_min_version="0.1.0",
            entrypoint="nfi_engine.notifications:JsonlNotifier",
            description="local JSONL notification adapter",
        ),
        PluginManifest(
            name="fixture-data",
            group=PluginGroup.DATA,
            version="0.1.0",
            engine_min_version="0.1.0",
            entrypoint="nfi_engine.data.loader:load_candle_batch",
            description="fixture candle data loader",
        ),
    )
