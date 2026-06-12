from __future__ import annotations

from typing import Final

LOGIN_SCRIPT: Final = """
<script>
const loginForm = document.querySelector('[data-testid="login-form"]');
const loginState = document.querySelector('[data-testid="login-state"]');
const loginMsg = (key) => window.NFI_I18N?.[key] || key;
if (loginForm) {
  loginForm.onsubmit = async (event) => {
    event.preventDefault();
    const token = loginForm.elements.token.value.trim();
    const response = await fetch('/api/v1/session/login', {
      method: 'POST',
      headers: {'Authorization': `Bearer ${token}`}
    });
    if (response.ok) {
      window.location.reload();
      return;
    }
    loginState.textContent = `${loginMsg('login.failed')}: HTTP ${response.status}`;
  };
}
</script>
"""
