#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# ─── How to run ───
# 1. Install uv (if not installed):
#      curl -LsSf https://astral.sh/uv/install.sh | sh
# 2. Run directly (no venv, no pip install needed), for example:
#      uv run scripts/x7_provenance.py \
#        --source <NostalgiaForInfinityX7.py> \
#        --commit <commit> --source-url <raw-url> \
#        --observed-at <YYYY-MM-DD> --output <artifact.md>
# 3. Or make executable and run:
#      chmod +x scripts/x7_provenance.py && ./scripts/x7_provenance.py \
#        --source <NostalgiaForInfinityX7.py> \
#        --commit <commit> --source-url <raw-url> \
#        --observed-at <YYYY-MM-DD> --output <artifact.md>
# ──────────────────

from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / "src/nfi_engine/tools/x7_provenance.py"), run_name="__main__")
