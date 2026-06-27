from __future__ import annotations

from typing import Final

EXCHANGE_PICKER_SCRIPT: Final = """
<script>
function setExchangeSelectValue(select, value) {
  if (!select || !value || !Array.from(select.options).some((option) => option.value === value)) {
    return;
  }
  select.value = value;
  select.dispatchEvent(new Event('change', {bubbles: true}));
}
document.querySelectorAll('[data-exchange-pick]').forEach((button) => {
  button.onclick = () => {
    const exchange = button.dataset.exchangePick || '';
    const mode = button.dataset.exchangeMode || '';
    [
      ['[name="exchange"]', exchange],
      ['[name="exchange.name"]', exchange],
      ['[name="trading_mode"]', mode],
      ['[name="exchange.trading_mode"]', mode]
    ].forEach(([selector, value]) => setExchangeSelectValue(
      document.querySelector(selector),
      value
    ));
    document.querySelectorAll('[data-exchange-pick]').forEach((item) => {
      item.classList.toggle('is-active', item === button);
    });
  };
});
</script>
"""
