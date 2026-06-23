from __future__ import annotations

from html import escape

from nfi_engine.config import RuntimeSettings
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey


def render_settings_update_panel(*, settings: RuntimeSettings) -> str:
    locale = settings.ui.locale
    disabled = _disabled_attrs(settings)
    return f"""
    <section data-testid="settings-update-panel">
      <h2>{localize(locale, MessageKey.SETTINGS_UPDATE_TITLE)}</h2>
      <p>{localize(locale, MessageKey.SETTINGS_UPDATE_DESCRIPTION)}</p>
      <div class="update-state-grid">
        {
        _update_state(
            test_id="update-preview-state",
            title=localize(locale, MessageKey.SETTINGS_UPDATE_PREVIEW),
            body=localize(locale, MessageKey.SETTINGS_UPDATE_PREVIEW_STATE),
        )
    }
        {
        _update_state(
            test_id="update-apply-state",
            title=localize(locale, MessageKey.SETTINGS_UPDATE_APPLY),
            body=localize(locale, MessageKey.SETTINGS_UPDATE_APPLY_STATE),
        )
    }
        {
        _update_state(
            test_id="update-rollback-state",
            title=localize(locale, MessageKey.SETTINGS_UPDATE_ROLLBACK),
            body=localize(locale, MessageKey.SETTINGS_UPDATE_ROLLBACK_STATE),
        )
    }
      </div>
      <div class="settings-stack">
        <label>
          <span>{localize(locale, MessageKey.SETTINGS_UPDATE_BACKUP_REFERENCE)}</span>
          <input
            data-testid="update-backup-reference"
            name="update.backup_reference"
            type="text"
            placeholder="backups/local-proof.zip"{disabled}
          />
        </label>
        <label>
          <input data-testid="update-acknowledge-unverified" type="checkbox"{disabled} />
          <span>{localize(locale, MessageKey.SETTINGS_UPDATE_ACKNOWLEDGE_UNVERIFIED)}</span>
        </label>
        <label>
          <input data-testid="update-allow-dirty-worktree" type="checkbox"{disabled} />
          <span>{localize(locale, MessageKey.SETTINGS_UPDATE_ALLOW_DIRTY_WORKTREE)}</span>
        </label>
        <input data-testid="update-source" type="hidden" value="local_proof" />
      </div>
      <div class="toolbar">
        <button type="button" data-testid="update-preview-button"{disabled}>
          {localize(locale, MessageKey.SETTINGS_UPDATE_PREVIEW)}
        </button>
        <button type="button" data-testid="update-apply-button"{disabled}>
          {localize(locale, MessageKey.SETTINGS_UPDATE_APPLY)}
        </button>
        <button type="button" data-testid="update-rollback-button"{disabled}>
          {localize(locale, MessageKey.SETTINGS_UPDATE_ROLLBACK)}
        </button>
      </div>
    </section>
"""


def _update_state(*, test_id: str, title: str, body: str) -> str:
    return (
        f'<div class="update-state" data-testid="{test_id}">'
        f"<strong>{title}</strong><span>{body}</span></div>"
    )


def _disabled_attrs(settings: RuntimeSettings) -> str:
    if not settings.ui.read_only:
        return ""
    title = escape(localize(settings.ui.locale, MessageKey.SETTINGS_READONLY_DISABLED_TITLE))
    return f' disabled title="{title}"'
