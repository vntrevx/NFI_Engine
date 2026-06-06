from __future__ import annotations

from nfi_engine.compat import load_nfi_metadata, run_nfi_compatibility_check


def test_nfi_metadata_pins_upstream_sha() -> None:
    # Given/When
    metadata = load_nfi_metadata()

    # Then
    assert metadata.upstream_repo == "iterativv/NostalgiaForInfinity"
    assert metadata.upstream_sha == "4de91e1928f6203694733ffb9899023ef62fd7fc"
    assert metadata.full_x7_parity is False


def test_nfi_fixture_reports_supported_adapter_surface() -> None:
    # Given/When
    result = run_nfi_compatibility_check(
        "tests.fixtures.strategies.nfi_shape:NFISmokeStrategy",
    )

    # Then
    assert result.compatible is True
    assert result.full_x7_parity is False
    assert "populate_entry_trend" in result.detected_callbacks
    assert "full_x7_strategy_import" in result.unsupported_surfaces
