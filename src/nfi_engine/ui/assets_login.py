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
    const username = loginForm.elements.username.value.trim();
    const password = loginForm.elements.password.value;
    const response = await fetch('/api/v1/session/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username, password})
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
