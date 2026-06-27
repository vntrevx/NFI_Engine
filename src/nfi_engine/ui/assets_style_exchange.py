from __future__ import annotations

from typing import Final

EXCHANGE_STYLE: Final = """
.exchange-option-list {
  display: grid;
  gap: 8px;
  max-height: 360px;
  overflow: auto;
  padding-right: 2px;
}
.exchange-option {
  display: grid;
  gap: 7px;
  width: 100%;
  min-height: 0;
  padding: 10px;
  text-align: left;
  background: linear-gradient(180deg, var(--panel), var(--panel-subtle));
}
.exchange-option:hover { border-color: var(--accent); background: var(--panel); }
.exchange-option.is-active {
  border-color: var(--accent);
  background: var(--accent-soft);
}
.exchange-option-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.exchange-option-head strong { font-size: 13px; line-height: 1.2; }
.support-badge {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 3px 7px;
  background: var(--panel);
  color: var(--muted);
  font-size: 11px;
  line-height: 1.15;
  white-space: nowrap;
}
.support-verified { border-color: var(--accent); color: var(--accent-strong); }
.support-candidate { border-color: var(--warn); color: var(--warn); }
.support-generic-unverified { border-color: var(--line-strong); color: var(--muted); }
.capability-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.capability-pills span {
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 2px 5px;
  background: var(--panel);
  color: var(--muted);
  font-size: 11px;
}
.exchange-evidence {
  color: var(--muted);
  font-size: 11px;
  line-height: 1.25;
  overflow-wrap: anywhere;
}
.exchange-official {
  color: var(--accent-strong);
  font-size: 11px;
  line-height: 1.25;
  overflow-wrap: anywhere;
}
"""
