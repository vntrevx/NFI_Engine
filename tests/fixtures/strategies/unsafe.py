from __future__ import annotations

import os
import socket
import subprocess
from pathlib import Path
from typing import override

from nfi_engine.exchange import ExchangeOrderRequest
from nfi_engine.strategy import StrategyFrame, StrategyMetadata
from tests.fixtures.strategies.nfi_shape import NFISmokeStrategy


class EnvReadingStrategy(NFISmokeStrategy):
    @override
    def populate_indicators(
        self,
        dataframe: StrategyFrame,
        _metadata: StrategyMetadata,
    ) -> StrategyFrame:
        os.environ.get("NFI_ENGINE_EXCHANGE_KEY")
        return dataframe


class FilesystemWritingStrategy(NFISmokeStrategy):
    @override
    def populate_indicators(
        self,
        dataframe: StrategyFrame,
        _metadata: StrategyMetadata,
    ) -> StrategyFrame:
        Path("nfi-engine-unsafe").write_text("unsafe", encoding="utf-8")
        return dataframe


class SubprocessStrategy(NFISmokeStrategy):
    @override
    def populate_indicators(
        self,
        dataframe: StrategyFrame,
        _metadata: StrategyMetadata,
    ) -> StrategyFrame:
        subprocess.run(["/bin/true"], check=False)
        return dataframe


class NetworkStrategy(NFISmokeStrategy):
    @override
    def populate_indicators(
        self,
        dataframe: StrategyFrame,
        _metadata: StrategyMetadata,
    ) -> StrategyFrame:
        socket.create_connection(("127.0.0.1", 80))
        return dataframe


class DirectExchangeStrategy(NFISmokeStrategy):
    @override
    def populate_indicators(
        self,
        dataframe: StrategyFrame,
        _metadata: StrategyMetadata,
    ) -> StrategyFrame:
        request_type = ExchangeOrderRequest
        if request_type is None:
            return dataframe
        return dataframe
