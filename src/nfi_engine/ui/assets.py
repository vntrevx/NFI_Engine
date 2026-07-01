from __future__ import annotations

from typing import Final

from nfi_engine.ui.assets_style_controls import CONTROL_STYLE
from nfi_engine.ui.assets_style_exchange import EXCHANGE_STYLE
from nfi_engine.ui.assets_style_home import HOME_STYLE
from nfi_engine.ui.assets_style_login import LOGIN_STYLE
from nfi_engine.ui.assets_style_operations import OPERATIONS_STYLE
from nfi_engine.ui.assets_style_operator import OPERATOR_STYLE
from nfi_engine.ui.assets_style_shell import SHELL_STYLE

STYLE: Final = (
    f"{SHELL_STYLE}\n{CONTROL_STYLE}\n{EXCHANGE_STYLE}\n{OPERATIONS_STYLE}\n"
    f"{OPERATOR_STYLE}\n{LOGIN_STYLE}\n{HOME_STYLE}"
)
