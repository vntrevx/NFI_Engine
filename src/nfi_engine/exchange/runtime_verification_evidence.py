from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from nfi_engine.exchange.mode_runtime_proofs import (
    RuntimeProofChannel,
    all_runtime_proof_keys,
    runtime_proof_evidence,
)

BATCH_RUNTIME_MODES: Final = all_runtime_proof_keys()

READ_ONLY_BALANCE_EVIDENCE: Final[Mapping[str, str]] = MappingProxyType(
    {
        mode: runtime_proof_evidence(mode, RuntimeProofChannel.READ_ONLY_BALANCE)
        for mode in BATCH_RUNTIME_MODES
    },
)
ORDER_LANE_EVIDENCE: Final[Mapping[str, str]] = MappingProxyType(
    {
        mode: runtime_proof_evidence(mode, RuntimeProofChannel.ORDER_LANE)
        for mode in BATCH_RUNTIME_MODES
    },
)
DRY_RUN_ENVIRONMENT_EVIDENCE: Final[Mapping[str, str]] = MappingProxyType(
    {
        mode: runtime_proof_evidence(mode, RuntimeProofChannel.TEST_ENVIRONMENT)
        for mode in BATCH_RUNTIME_MODES
    },
)
