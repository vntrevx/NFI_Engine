from __future__ import annotations

from pathlib import Path

from nfi_engine.exchange.fill_scenarios import load_fill_scenario, simulate_fill_scenario


def test_fill_scenario_models_partial_fill_latency_fees_and_funding() -> None:
    # Given: a configured partial-fill scenario fixture.
    scenario = load_fill_scenario(Path("tests/fixtures/simulator/partial_fill_latency.yaml"))

    # When: the scenario is simulated.
    result = simulate_fill_scenario(scenario)

    # Then: execution details include partial fills, latency, fees, funding, and metadata.
    assert result.scenario_hash != ""
    assert result.seed == 4242
    assert result.order_state == "PARTIALLY_FILLED"
    assert result.filled_quantity == "0.40000000"
    assert result.remaining_quantity == "0.60000000"
    assert result.latency_ms == 250
    assert result.fee_model == "taker"
    assert result.fee_paid == "0.02404800"
    assert result.funding_fee == "0.00400000"
    assert "PARTIAL_FILL" in result.events
    assert "LATENCY_APPLIED" in result.events
    assert "FUNDING_FEE_ACCRUED" in result.events


def test_fill_scenario_flags_slippage_spike_as_circuit_breaker_event() -> None:
    # Given: a slippage spike scenario fixture.
    scenario = load_fill_scenario(Path("tests/fixtures/simulator/slippage_spike.yaml"))

    # When: the scenario is simulated.
    result = simulate_fill_scenario(scenario)

    # Then: abnormal slippage creates a safety event.
    assert result.circuit_breaker_event is True
    assert "SLIPPAGE_ANOMALY" in result.events
    assert result.execution_price == "108.00000000"


def test_fill_scenario_models_exchange_reject_and_liquidation_near_miss() -> None:
    # Given: explicit exchange reject and liquidation near-miss fixtures.
    rejected = load_fill_scenario(Path("tests/fixtures/simulator/exchange_reject.yaml"))
    near_miss = load_fill_scenario(Path("tests/fixtures/simulator/liquidation_near_miss.yaml"))

    # When: both scenarios are simulated.
    rejected_result = simulate_fill_scenario(rejected)
    near_miss_result = simulate_fill_scenario(near_miss)

    # Then: both safety outcomes are surfaced as typed events.
    assert rejected_result.order_state == "REJECTED"
    assert rejected_result.filled_quantity == "0.00000000"
    assert "EXCHANGE_REJECT" in rejected_result.events
    assert near_miss_result.liquidation_near_miss is True
    assert "LIQUIDATION_NEAR_MISS" in near_miss_result.events


def test_fill_scenario_seed_is_deterministic() -> None:
    # Given: the same scenario fixture loaded twice.
    scenario = load_fill_scenario(Path("tests/fixtures/simulator/partial_fill_latency.yaml"))

    # When: simulation runs twice.
    first = simulate_fill_scenario(scenario)
    second = simulate_fill_scenario(scenario)

    # Then: output remains identical for the same seed and scenario hash.
    assert first == second
