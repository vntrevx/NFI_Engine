from __future__ import annotations

from html import escape

from nfi_engine.config import RuntimeSettings
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey


def render_settings_data_lifecycle_panel(*, settings: RuntimeSettings) -> str:
    locale = settings.ui.locale
    disabled = _disabled_attrs(settings)
    return f"""
    <section data-testid="settings-data-lifecycle-panel">
      <h2>{localize(locale, MessageKey.SETTINGS_DATA_LIFECYCLE_TITLE)}</h2>
      <div class="field-grid">
        <label>
          {localize(locale, MessageKey.SETTINGS_DATA_LIFECYCLE_RETENTION_DAYS)}
          <input
            data-testid="data-lifecycle-retention-days"
            type="number"
            min="0"
            max="3650"
            value="7"
          >
        </label>
        <label>
          {localize(locale, MessageKey.SETTINGS_DATA_LIFECYCLE_PREVIEW_ID)}
          <input
            data-testid="data-lifecycle-preview-token"
            type="text"
            readonly
            value=""
          >
        </label>
      </div>
      <div class="toolbar">
        <button type="button" data-testid="data-lifecycle-inspect-button">
          {localize(locale, MessageKey.SETTINGS_DATA_LIFECYCLE_INSPECT)}
        </button>
        <button type="button" data-testid="data-lifecycle-export-button">
          {localize(locale, MessageKey.SETTINGS_DATA_LIFECYCLE_EXPORT_PROFILE)}
        </button>
        <button type="button" data-testid="data-lifecycle-dry-run-button"{disabled}>
          {localize(locale, MessageKey.SETTINGS_DATA_LIFECYCLE_DRY_RUN)}
        </button>
        <button type="button" data-testid="data-lifecycle-apply-button"{disabled}>
          {localize(locale, MessageKey.SETTINGS_DATA_LIFECYCLE_APPLY)}
        </button>
      </div>
      <div class="state" data-testid="data-lifecycle-footprint-state">
        {localize(locale, MessageKey.SETTINGS_DATA_LIFECYCLE_NO_FOOTPRINT)}
      </div>
      <div class="state" data-testid="data-lifecycle-export-state">
        {localize(locale, MessageKey.SETTINGS_DATA_LIFECYCLE_NO_EXPORT)}
      </div>
      <div class="state" data-testid="data-lifecycle-prune-state">
        {localize(locale, MessageKey.SETTINGS_DATA_LIFECYCLE_NO_CLEANUP)}
      </div>
    </section>
"""


def _disabled_attrs(settings: RuntimeSettings) -> str:
    if not settings.ui.read_only:
        return ""
    title = escape(localize(settings.ui.locale, MessageKey.SETTINGS_READONLY_DISABLED_TITLE))
    return f' disabled title="{title}"'
