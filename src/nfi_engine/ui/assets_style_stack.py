from __future__ import annotations

from typing import Final

from nfi_engine.ui.assets_style_stack_base import STACK_BASE_STYLE
from nfi_engine.ui.assets_style_stack_home import STACK_HOME_STYLE
from nfi_engine.ui.assets_style_stack_operator import STACK_OPERATOR_STYLE

STACK_STYLE: Final = f"{STACK_BASE_STYLE}\n{STACK_HOME_STYLE}\n{STACK_OPERATOR_STYLE}"
